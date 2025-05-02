from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import current_user
from .models.product import Product
from .models.category import Category

bp = Blueprint('products', __name__)

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    # Get product by ID
    product = Product.get(product_id)
    
    # If product doesn't exist, show an error
    if product is None:
        flash('Product not found')
        return redirect(url_for('index.index'))
    
    # Get sellers and their inventory for this product
    sellers_inventory = Product.get_sellers_inventory(product_id)
    
    from .review_product import check_user_purchase
    # Render template with product details
    return render_template('product_detail.html', 
                          title=product.name, 
                          product=product,
                          sellers_inventory=sellers_inventory,
                          check_user_purchase=check_user_purchase)


@bp.route('/products')
def products():
   # Get sort parameter from request
   sort = request.args.get('sort', default=None)
   
   # Get limit parameter from request (how many products to show)
   limit = request.args.get('limit', default=None, type=int)
   
   # Get category parameter from request
   selected_category = request.args.get('category', default=None)
   
   # Get search parameter from request
   search_term = request.args.get('search', default=None)
   
   # Default: get all available products
   products = []
   
   # Apply search if specified
   if search_term and search_term.strip():
       products = Product.search(search_term.strip(), available=True)
   # Apply category filter if specified
   elif selected_category and selected_category != '':
       # Convert selected_category to integer for comparison
       selected_category_id = int(selected_category)
       # Get products by category
       products = Product.get_by_category(selected_category_id, available=True)
   else:
       # Get all available products
       products = Product.get_all(available=True)
   
   # Apply sorting if specified
   if sort == 'price_asc':
       products = sorted(products, key=lambda x: x.price)
   elif sort == 'price_desc':
       products = sorted(products, key=lambda x: x.price, reverse=True)
   
   # Apply limit if specified
   if limit and limit > 0:
       products = products[:limit]
   
   # Get all categories for the dropdown
   categories = Category.get_parent_categories()
   
   # Render template with product list
   return render_template('index.html', 
                         title='Products', 
                         avail_products=products,
                         current_limit=limit or '',
                         categories=categories,
                         selected_category=selected_category,
                         search_term=search_term or '')