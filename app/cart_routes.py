from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import current_user, login_required
from werkzeug.exceptions import NotFound
from flask import current_app as app
from .models import Cart, CartItem
from .models.purchase import Purchase, PurchaseItem
from .models import Coupon
from .models.saved_product import SavedItem 
from .models.product import Product
from .models.coupon import Coupon

bp = Blueprint('cart', __name__, url_prefix='/cart')

@bp.route('/')
@login_required
def index():
    """Show the user's cart"""
    cart = Cart.get_by_user_id(current_user.id)
    
    # Get product details for each cart item
    for item in cart.items:
        product = Product.get(item.product_id)
        if product:
            item.product = product
        
        # Don't try to load Seller objects, just create a display name from the ID
        if item.seller_id:
            item.seller_display_name = f"Seller #{item.seller_id}"
        
    # Calculate totals
    total_items = sum(item.quantity for item in cart.items)
    total_price = cart.get_total()
    
    # Handle coupon if present in session
    discount_amount = 0
    if 'coupon_code' in session:
        coupon = Coupon.get_by_code(session['coupon_code'])
        if coupon and coupon.is_valid():
            discount_amount = coupon.calculate_discount(total_price)
            total_price -= discount_amount
    
    return render_template('cart/index.html',
                          cart=cart,
                          cart_items=cart.items,
                          total_items=total_items,
                          total_price=total_price,
                          discount_amount=discount_amount)

@bp.route('/add', methods=['POST'])
@login_required
def add_to_cart():
    """Add an item to the user's cart"""
    product_id = int(request.form.get('product_id', 0))
    quantity = int(request.form.get('quantity', 1))
    
    if quantity <= 0:
        flash("Quantity must be positive")
        return redirect(request.referrer or url_for('index.index'))
    
    # Get the user's cart
    cart = Cart.get_by_user_id(current_user.id)
    
    # Add the item
    cart.add_item(product_id, quantity)
    
    # Save the cart
    cart.save()
    
    flash("Item added to cart")
    
    # Return to the previous page or homepage
    return redirect(request.referrer or url_for('index.index'))

@bp.route('/update', methods=['POST'])
@login_required
def update_cart():
    """Update cart item quantity"""
    product_id = int(request.form.get('product_id', 0))
    quantity = int(request.form.get('quantity', 0))
    
    if quantity <= 0:
        flash("Quantity must be positive")
        return redirect(url_for('cart.index'))
    
    cart = Cart.get_by_user_id(current_user.id)
    cart.update_quantity(product_id, quantity)
    
    # Save changes to database
    cart.save()
    
    flash("Cart updated")
    
    return redirect(url_for('cart.index'))

@bp.route('/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    """Remove an item from the cart"""
    cart = Cart.get_by_user_id(current_user.id)
    cart.remove_item(product_id)
    
    # Save the cart
    cart.save()
    
    flash("Item removed from cart")
    
    return redirect(url_for('cart.index'))

@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout process and order creation"""
    if request.method == 'GET':
        cart = Cart.get_by_user_id(current_user.id)
        
        if not cart.items:
            flash("Your cart is empty")
            return redirect(url_for('cart.index'))
        
        # Get product details for each cart item
        for item in cart.items:
            product = Product.get(item.product_id)
            if product:
                item.product = product
            
            # Don't try to load Seller objects, just create a display name from the ID
            if item.seller_id:
                item.seller_display_name = f"Seller #{item.seller_id}"
        
        # Calculate totals
        total_items = sum(item.quantity for item in cart.items)
        total_price = cart.get_total()
        
        # Apply coupon discount if one is stored in session
        discount_amount = 0
        coupon = None
        if 'coupon_code' in session:
            coupon = Coupon.get_by_code(session['coupon_code'])
            if coupon and coupon.is_valid():
                discount_amount = coupon.calculate_discount(total_price)
                total_price -= discount_amount
        
        # Get user balance for display
        user_balance_result = app.db.execute(
            'SELECT balance FROM Accounts WHERE user_id = :user_id',
            user_id=current_user.id
        )
        balance = float(user_balance_result[0][0]) if user_balance_result else 0
        
        return render_template('cart/checkout.html',
                              cart=cart,
                              cart_items=cart.items,
                              total_items=total_items,
                              total_price=total_price,
                              user_balance=balance,
                              discount_amount=discount_amount,
                              coupon=coupon)
    
    else:  # POST request - process the order
        # Get coupon code from session instead of form
        coupon_code = session.get('coupon_code')
        
        success, message, purchase_id = Purchase.create_from_cart(current_user.id, coupon_code)
        
        if success:
            # Clear coupon from session on successful order
            if 'coupon_code' in session:
                session.pop('coupon_code')
                
            flash(message, "success")
            if purchase_id:
                return redirect(url_for('cart.order_confirmation', purchase_id=purchase_id))
            return redirect(url_for('users.profile'))
        else:
            flash(message, "danger")
            return redirect(url_for('cart.checkout'))
        

@bp.route('/confirmation/<int:purchase_id>')
@login_required
def order_confirmation(purchase_id):
    """Display order confirmation page"""
    # Get purchase details
    purchase_results = app.db.execute(
        '''SELECT purchase_id, user_id, total_amount, total_items, status, updated_at
           FROM Purchases
           WHERE purchase_id = :purchase_id AND user_id = :user_id''',
        purchase_id=purchase_id,
        user_id=current_user.id
    )
        
    if not purchase_results:
        flash("Order not found")
        return redirect(url_for('users.profile'))
    
    purchase = purchase_results[0]  # Get the first row
    
    purchase_obj = Purchase(
        purchase_id=purchase[0],
        user_id=purchase[1],
        total_amount=purchase[2],
        total_items=purchase[3],
        status=purchase[4],
        updated_at=purchase[5]
    )
    
    # Get purchase items
    items = app.db.execute(
        '''SELECT pi.product_id, p.name, pi.quantity, pi.unit_price, pi.total_price, pi.fulfillment_status
        FROM Purchase_items pi
        JOIN Products p ON pi.product_id = p.product_id
        WHERE pi.purchase_id = :purchase_id''',
        purchase_id=purchase_id
    )
            
    purchase_obj.items = [
        {
            "product_id": item[0],
            "product_name": item[1],
            "quantity": item[2],
            "unit_price": item[3],
            "total_price": item[4],
            "status": item[5]
        }
        for item in items
    ]
    

    return render_template('cart/order_confirmation.html', purchase=purchase_obj)

@bp.route('/orders')
@login_required
def order_history():
    """Show the user's order history"""
    from datetime import datetime, timedelta
    # Get purchases from the last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    purchases = Purchase.get_all_by_uid_since(current_user.id, thirty_days_ago)
    
    return render_template('cart/order_history.html',
                          purchases=purchases)


@bp.route('/apply_coupon', methods=['POST'])
@login_required
def apply_coupon():
    """Apply a coupon code and return the updated total"""
    from .models.coupon import Coupon
    
    coupon_code = request.form.get('coupon_code', '').strip()
    
    if not coupon_code:
        flash('Please enter a coupon code.', 'warning')
        return redirect(url_for('cart.index'))
    
    # Get the cart
    cart = Cart.get_by_user_id(current_user.id)
    
    # Calculate cart total
    total_price = cart.get_total()
    
    # Validate coupon
    coupon = Coupon.get_by_code(coupon_code)
    
    if not coupon:
        flash(f'Coupon code "{coupon_code}" not found.', 'danger')
        return redirect(url_for('cart.index'))
    
    if not coupon.is_valid():
        flash(f'Coupon code "{coupon_code}" has expired or is inactive.', 'danger')
        return redirect(url_for('cart.index'))
    
    # Calculate discount
    discount_amount = coupon.calculate_discount(total_price)
    new_total = total_price - discount_amount
    
    # Store coupon in session for checkout
    session['coupon_code'] = coupon.code
    
    flash(f'Coupon "{coupon.code}" applied! You saved ${discount_amount:.2f}', 'success')
    
    # If AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'discount_percent': coupon.discount_percent,
            'discount_amount': discount_amount,
            'new_total': new_total
        })
    
    return redirect(url_for('cart.index'))


@bp.route('/remove_coupon')
@login_required
def remove_coupon():
    """Remove the applied coupon"""
    if 'coupon_code' in session:
        coupon_code = session.pop('coupon_code')
        flash(f'Coupon "{coupon_code}" removed.', 'info')
    
    return redirect(url_for('cart.index'))


@bp.route('/saved')
@login_required
def saved_items():
    """Show the user's saved items"""
    saved_items = SavedItem.get_by_user_id(current_user.id)
    
    # Get product details for each saved item
    products = []
    for item in saved_items:
        product = Product.get(item.product_id)
        if product:
            # Ensure product_id is explicitly set
            if not hasattr(product, 'product_id'):
                product.product_id = item.product_id
                
            product.saved_item_id = item.saved_item_id
            product.seller_id = item.seller_id
            products.append(product)
    
    return render_template('cart/saved_items.html', 
                          saved_items=products)

@bp.route('/save/<int:product_id>', methods=['POST'])
@login_required
def save_for_later(product_id):
    """Save an item for later"""
    # If item is in cart, get the seller_id
    seller_id = None
    cart = Cart.get_by_user_id(current_user.id)
    
    for item in cart.items:
        if item.product_id == product_id:
            seller_id = item.seller_id
            # Remove from cart
            cart.remove_item(product_id)
            break
    
    # Add to saved items
    SavedItem.add(current_user.id, product_id, seller_id)
    
    flash("Item saved for later")
    return redirect(url_for('cart.index'))

@bp.route('/move_to_cart/<int:product_id>', methods=['POST'])
@login_required
def move_to_cart(product_id):
    """Move an item from saved items to cart"""
    SavedItem.move_to_cart(current_user.id, product_id)
    
    flash("Item moved to cart")
    return redirect(url_for('cart.saved_items'))