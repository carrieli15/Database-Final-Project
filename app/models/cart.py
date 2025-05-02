from flask import current_app as app
from flask_login import current_user
from .product import Product

class Cart:
    """
    Represents a user's shopping cart
    """
    def __init__(self, user_id, cart_id=None):
        self.user_id = user_id
        self.cart_id = cart_id
        self.items = []
    
    def add_item(self, product_id, quantity=1):
        """Add an item to the cart"""
        # Check if item is already in cart
        for item in self.items:
            if item.product_id == product_id:
                item.quantity += quantity
                return
        
        # Otherwise add new item
        self.items.append(CartItem(self.user_id, product_id, quantity))
    
    def remove_item(self, product_id):
        """Remove an item from the cart"""
        self.items = [item for item in self.items if item.product_id != product_id]
    
    def update_quantity(self, product_id, quantity):
        """Update the quantity of an item"""
        for item in self.items:
            if item.product_id == product_id:
                if quantity <= 0:
                    self.remove_item(product_id)
                else:
                    item.quantity = quantity
                    # Recalculate total_price immediately when quantity changes
                    if item.unit_price:
                        item.total_price = item.unit_price * quantity
    
    def get_total(self):
        """Calculate the total cost of items in the cart"""
        total = 0
        for item in self.items:
            if hasattr(item, 'unit_price') and item.unit_price:
                total += item.unit_price * item.quantity
            else:
                product = Product.get(item.product_id)
                if product:
                    total += product.price * item.quantity
        return total
    
    def save(self):
        """Save cart and cart items to database"""
        # If cart doesn't exist in database yet, create it
        if not hasattr(self, 'cart_id') or not self.cart_id:
            rows = app.db.execute('''
INSERT INTO Cart(user_id, updated_at)
VALUES(:user_id, NOW())
RETURNING cart_id
''',
                            user_id=self.user_id)
            self.cart_id = rows[0][0]
        else:
            # Update the cart's timestamp
            app.db.execute('''
UPDATE Cart
SET updated_at = NOW()
WHERE cart_id = :cart_id
''',
                    cart_id=self.cart_id)
        
        # Get existing cart items from database
        existing_items = app.db.execute('''
SELECT cart_item_id, product_id
FROM Cart_items
WHERE cart_id = :cart_id
''',
                           cart_id=self.cart_id)
        
        # Track which items to keep (items in current cart)
        current_product_ids = {item.product_id for item in self.items}
        
        # Delete items that are no longer in the cart
        for row in existing_items:
            cart_item_id, product_id = row[0], row[1]
            if product_id not in current_product_ids:
                app.db.execute('''
DELETE FROM Cart_items
WHERE cart_item_id = :cart_item_id
''',
                          cart_item_id=cart_item_id)
        
        # Now save all current cart items
        for item in self.items:
            item.save(self.cart_id)
    
    @staticmethod
    def get_by_user_id(user_id):
        """Get a cart by user_id"""
        # First get the cart ID for this user
        cart_rows = app.db.execute('''
SELECT cart_id 
FROM Cart
WHERE user_id = :user_id
''',
                             user_id=user_id)
        
        # If there's no cart for this user, create an empty cart
        if not cart_rows:
            return Cart(user_id)
        
        cart_id = cart_rows[0][0]
        cart = Cart(user_id, cart_id)
        
        # Load cart items from database
        cart.items = CartItem.get_by_cart_id(cart_id)
        
        return cart


class CartItem:
    """
    Represents an item in a shopping cart
    """
    def __init__(self, user_id=None, product_id=None, quantity=1, cart_item_id=None, seller_id=None, unit_price=None, total_price=None):
        self.cart_item_id = cart_item_id
        self.user_id = user_id
        self.product_id = product_id  
        self.quantity = quantity
        self.seller_id = seller_id
        self.unit_price = unit_price
        self.total_price = total_price
    
    def get_subtotal(self):
        """Calculate the subtotal for this item"""
        # Always calculate based on current quantity rather than using stored total_price
        if self.unit_price:
            return self.unit_price * self.quantity
        
        product = Product.get(self.product_id)
        if product:
            return product.price * self.quantity
        
        # Fall back to stored total_price only if we can't calculate
        if self.total_price:
            return self.total_price
        
        return 0
    
    def save(self, cart_id):
        """Save cart item to database"""
        # Check if this item already exists in the database
        rows = app.db.execute('''
SELECT cart_item_id
FROM Cart_items
WHERE cart_id = :cart_id AND product_id = :product_id
''',
                        cart_id=cart_id,
                        product_id=self.product_id)
        
        subtotal = self.get_subtotal()
        
        if rows:  # Item exists, update it
            cart_item_id = rows[0][0]
            app.db.execute('''
UPDATE Cart_items
SET quantity = :quantity, total_price = :total_price
WHERE cart_item_id = :cart_item_id
''',
                    cart_item_id=cart_item_id,
                    quantity=self.quantity,
                    total_price=subtotal)
        else:  # Item doesn't exist, insert it
            # Get product details for pricing if needed
            product = Product.get(self.product_id)
            unit_price = self.unit_price or (product.price if product else 0)
            
            app.db.execute('''
INSERT INTO Cart_items(cart_id, product_id, seller_id, quantity, unit_price, total_price)
VALUES(:cart_id, :product_id, :seller_id, :quantity, :unit_price, :total_price)
''',
                    cart_id=cart_id,
                    product_id=self.product_id,
                    seller_id=self.seller_id or 1,  # Default seller_id if not set
                    quantity=self.quantity,
                    unit_price=unit_price,
                    total_price=subtotal)
        
    @staticmethod
    def get_by_user_id(user_id):
        """Get all cart items for a specific user by finding their cart first"""
        # First get the cart ID for this user
        cart_rows = app.db.execute('''
SELECT cart_id 
FROM Cart
WHERE user_id = :user_id
''',
                             user_id=user_id)
        
        # If there's no cart for this user, return empty list
        if not cart_rows:
            return []
        
        cart_id = cart_rows[0][0]
        
        # Now get items for this cart
        return CartItem.get_by_cart_id(cart_id)
    
    @staticmethod
    def get_by_cart_id(cart_id):
        """Get all cart items for a specific cart"""
        rows = app.db.execute('''
SELECT cart_item_id, product_id, seller_id, quantity, unit_price, total_price
FROM Cart_items
WHERE cart_id = :cart_id
''',
                              cart_id=cart_id)
        
        # Convert database rows to CartItem objects
        return [CartItem(
            product_id=row[1],
            quantity=row[3],
            cart_item_id=row[0],
            seller_id=row[2],
            unit_price=row[4],
            total_price=row[5]
        ) for row in rows]