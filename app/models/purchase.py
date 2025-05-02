from flask import current_app as app
from ..models.cart import Cart
from ..models.coupon import Coupon
from sqlalchemy import text 
from datetime import datetime
import traceback

class Purchase:
    def __init__(self, purchase_id, user_id, total_amount, total_items, 
                 status="pending", updated_at=None):
        self.purchase_id = purchase_id
        self.user_id = user_id
        self.total_amount = total_amount
        self.total_items = total_items
        self.status = status
        self.updated_at = updated_at
        self.items = []  # Will hold PurchaseItem objects

    @staticmethod
    def get(purchase_id):
        rows = app.db.execute('''
SELECT purchase_id, user_id, total_amount, total_items, status, updated_at
FROM Purchases
WHERE purchase_id = :purchase_id
''',
                              purchase_id=purchase_id)
        return Purchase(*(rows[0])) if rows else None

    @staticmethod
    def get_all_by_uid_since(user_id, since):
        rows = app.db.execute('''
SELECT purchase_id, user_id, total_amount, total_items, status, updated_at
FROM Purchases
WHERE user_id = :user_id
AND updated_at >= :since
ORDER BY updated_at DESC
''',
                              user_id=user_id,
                              since=since)
        return [Purchase(*row) for row in rows]

    @staticmethod
    def create_from_cart(user_id, coupon_code=None):
        """
        Create a purchase from the user's cart with proper inventory and balance checks
        Returns: (success, message, purchase_id)
        """
        purchase_id = None
        
        try:
            # Get the user's cart
            from .cart import Cart
            cart = Cart.get_by_user_id(user_id)
            
            if not cart.items:
                return (False, "Your cart is empty", None)
            
            # Check inventory availability and get up-to-date prices
            inventory_issues = []
            total_price = 0
            purchase_items = []
            seller_payments = {}  # seller_id -> amount to pay
            
            # Get buyer's account - FIXED: no more fetchone()
            buyer_account_results = app.db.execute(
                'SELECT balance FROM Accounts WHERE user_id = :user_id',
                user_id=user_id
            )
            
            if not buyer_account_results:
                return (False, "Account not found", None)
            
            buyer_balance = float(buyer_account_results[0][0])
            
            for item in cart.items:
                # Get current inventory status - FIXED: no more fetchone()
                inventory_results = app.db.execute(
                    '''SELECT quantity, price, seller_id 
                       FROM Inventory 
                       WHERE product_id = :product_id AND seller_id = :seller_id''',
                    product_id=item.product_id,
                    seller_id=item.seller_id
                )
                
                if not inventory_results or inventory_results[0][0] < item.quantity:
                    available = inventory_results[0][0] if inventory_results else 0
                    inventory_issues.append(
                        f"Insufficient inventory for product #{item.product_id} - only {available} available"
                    )
                    continue
                
                # Get current price (may have changed since adding to cart)
                inventory = inventory_results[0]
                current_price = inventory[1]
                item_total = float(current_price) * item.quantity
                
                # Track seller payments
                seller_id = inventory[2]
                if seller_id in seller_payments:
                    seller_payments[seller_id] += item_total
                else:
                    seller_payments[seller_id] = item_total
                
                total_price += item_total
                
                purchase_items.append({
                    "product_id": item.product_id,
                    "seller_id": seller_id,
                    "quantity": item.quantity,
                    "unit_price": current_price,
                    "total_price": item_total
                })
            
            # Check if inventory checks passed
            if inventory_issues:
                return (False, "Inventory issues: " + "; ".join(inventory_issues), None)
            
            # Apply coupon if provided
            discount = 0
            if coupon_code:
                from .coupon import Coupon
                coupon = Coupon.get_by_code(coupon_code)
                if coupon and coupon.is_valid():
                    discount = coupon.calculate_discount(total_price)
                    total_price -= discount
            
            # Check buyer's balance
            if buyer_balance < total_price:
                return (False, f"Insufficient balance (${buyer_balance:.2f}) to complete purchase (${total_price:.2f})", None)
            
            # FIXED: Use a proper context manager for the transaction
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Use a with statement for transaction management
            with app.db.engine.connect() as connection:
                with connection.begin():
                    # Create purchase record

                    purchase_results = app.db.execute(
                        '''INSERT INTO Purchases(user_id, total_amount, total_items, status, updated_at)
                        VALUES(:user_id, :total_amount, :total_items, 'completed', :updated_at)
                        RETURNING purchase_id''',
                        user_id=user_id,
                        total_amount=total_price,
                        total_items=sum(item["quantity"] for item in purchase_items),
                        updated_at=now
                    )

                    purchase_id = purchase_results[0][0]
                    
                    # Create purchase items and update inventory
                    for item in purchase_items:
                        # Create purchase item

                        # Line ~162 - Change the column name from 'status' to 'fulfillment_status'
                        app.db.execute(
                            '''INSERT INTO Purchase_items(purchase_id, product_id, seller_id, quantity, unit_price, total_price, fulfillment_status, updated_at)
                            VALUES(:purchase_id, :product_id, :seller_id, :quantity, :unit_price, :total_price, 'pending', :updated_at)''',
                            purchase_id=purchase_id,
                            product_id=item["product_id"],
                            seller_id=item["seller_id"],
                            quantity=item["quantity"],
                            unit_price=item["unit_price"],
                            total_price=item["total_price"],
                            updated_at=now
                        )
                        
                        # Create seller purchase record
                        seller_purchase_results = app.db.execute(
                            '''INSERT INTO Seller_purchases(user_id, seller_id, purchase_id, total_amount, total_items, status, updated_at)
                            VALUES(:user_id, :seller_id, :purchase_id, :total_amount, :total_items, 'pending', :updated_at)
                            RETURNING seller_purchase_id''',
                            user_id=user_id,
                            seller_id=item["seller_id"],
                            purchase_id=purchase_id,
                            total_amount=item["total_price"],
                            total_items=item["quantity"],
                            updated_at=now
                        )
                        seller_purchase_id = seller_purchase_results[0][0]
                        
                        # Create seller purchase item
                        app.db.execute(
                            '''INSERT INTO Seller_purchase_items(seller_purchase_id, product_id, quantity, unit_price, total_price, fulfillment_status, updated_at)
                              VALUES(:seller_purchase_id, :product_id, :quantity, :unit_price, :total_price, 'pending', :updated_at)''',
                            seller_purchase_id=seller_purchase_id,
                            product_id=item["product_id"],
                            quantity=item["quantity"],
                            unit_price=item["unit_price"],
                            total_price=item["total_price"],
                            updated_at=now
                        )
                        
                        # Update inventory
                        app.db.execute(
                            '''UPDATE Inventory
                              SET quantity = quantity - :order_quantity
                              WHERE product_id = :product_id AND seller_id = :seller_id''',
                            order_quantity=item["quantity"],
                            product_id=item["product_id"],
                            seller_id=item["seller_id"]
                        )
                    
                    # Update buyer's balance
                    app.db.execute(
                        '''UPDATE Accounts
                          SET balance = balance - :order_amount
                          WHERE user_id = :user_id''',
                        order_amount=total_price,
                        user_id=user_id
                    )
                    
                    # Update each seller's balance
                    for seller_id, amount in seller_payments.items():
                        app.db.execute(
                            '''UPDATE Accounts 
                              SET balance = balance + :amount 
                              WHERE seller_id = :seller_id''',
                            amount=amount,
                            seller_id=seller_id
                        )
                    
                    # Empty cart
                    app.db.execute(
                        '''DELETE FROM Cart_items
                          WHERE cart_id IN (
                              SELECT cart_id FROM Cart WHERE user_id = :user_id
                          )''',
                        user_id=user_id
                    )
                    
                    # Transaction will be automatically committed if no exceptions are raised
            
            return (True, f"Order placed successfully! Total: ${total_price:.2f}", purchase_id)
            
        except Exception as e:
            # Transaction will be automatically rolled back if an exception occurs
            print(f"Error creating purchase: {str(e)}")
            traceback.print_exc()
            return (False, f"Error processing order: {str(e)}", None)


class PurchaseItem:
    def __init__(self, purchase_item_id, purchase_id, product_id, quantity, unit_price):
        self.purchase_item_id = purchase_item_id
        self.purchase_id = purchase_id
        self.product_id = product_id
        self.quantity = quantity
        self.unit_price = unit_price  # Changed from price_per_unit to unit_price
    
    def get_subtotal(self):
        """Calculate the subtotal for this purchase item"""
        return self.unit_price * self.quantity  # Changed from price_per_unit to unit_price
    
    @staticmethod
    def get_items_by_purchase_id(purchase_id):
        rows = app.db.execute('''
SELECT purchase_item_id, purchase_id, product_id, quantity, unit_price
FROM Purchase_items
WHERE purchase_id = :purchase_id
''',
                              purchase_id=purchase_id)
        return [PurchaseItem(*row) for row in rows]
    
    @staticmethod
    def get(purchase_item_id):
        rows = app.db.execute('''
SELECT purchase_item_id, purchase_id, product_id, quantity, unit_price
FROM Purchase_items
WHERE purchase_item_id = :purchase_item_id
''',
                              purchase_item_id=purchase_item_id)
        return PurchaseItem(*(rows[0])) if rows else None
    
    def update_fulfillment_status(self):
        """Update the purchase status based on its items' fulfillment status"""
        purchase_items = PurchaseItem.get_items_by_purchase_id(self.purchase_id)
        
        if not purchase_items:
            return False
        
        # Check if all items are fulfilled
        all_fulfilled = all(item.fulfillment_status == 'delivered' for item in purchase_items)
        
        if all_fulfilled and self.status != 'fulfilled':
            # Update the purchase status to fulfilled
            app.db.execute('''
UPDATE Purchases 
SET status = :status, updated_at = NOW() 
WHERE purchase_id = :purchase_id
''', status='fulfilled', purchase_id=self.purchase_id)
            return True
        
        return False
    
    @staticmethod
    def get_status_counts_by_user(user_id):
        """Get counts of orders in each status for a user"""
        rows = app.db.execute('''
SELECT status, COUNT(*) as count
FROM Purchases
WHERE user_id = :user_id
GROUP BY status
''', user_id=user_id)
        
        return {row[0]: row[1] for row in rows}