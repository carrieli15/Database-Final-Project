"""
seller.py
----------
This module provides the seller dashboard, product management, and order management functionalities.

Features include:
- Dashboard summary and visualizations
- Product listing, adding, updating, and deleting
- Order listing, order fulfillment, and order item deletion
- User access control with login_required
"""

from collections import defaultdict
from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from flask import Blueprint, jsonify, request, render_template, current_app, flash, redirect, url_for
from flask_login import login_required, current_user

# ===== Blueprint =====
inventory_bp = Blueprint('seller', __name__)

# ===== Dashboard Page =====
@inventory_bp.route('/seller/dashboard')
@login_required
def seller_dashboard():
    """Display overall sales summary, inventory, product trends, recent reviews and orders."""
    account_id = current_user.id

    # ----- retrieve seller_id ----- 
    seller_query = f"SELECT seller_id FROM accounts WHERE account_id = {account_id}"
    results = current_app.db.execute(seller_query)
    if not results or not results[0][0]:
        flash("You are not a seller!")
        return redirect(url_for('index.index'))
    seller_id = results[0][0]

    # ----- get the latest order update time for "today" -----
    latest_order_query = f"""
        SELECT MAX(spi.updated_at)
        FROM seller_purchase_items spi
        JOIN seller_purchases sp ON spi.seller_purchase_id = sp.seller_purchase_id
        WHERE sp.seller_id = {seller_id}
    """
    latest_order_result = current_app.db.execute(latest_order_query)[0][0]
    # use the system time if there are no orders (to prevent NULL errors)
    reference_today = latest_order_result.date() if latest_order_result else date.today()

    # ----- get seller name -----
    name_query = f"SELECT name FROM sellers WHERE seller_id = {seller_id}"
    name_results = current_app.db.execute(name_query)
    seller_name = name_results[0][0] if name_results else "Unknown Seller"

    # ----- 1. time windows for monthly comparison -----
    first_day_this_month = reference_today.replace(day=1)
    first_day_last_month = first_day_this_month - relativedelta(months=1)
    first_day_next_month = first_day_this_month + relativedelta(months=1)
    six_months_ago = first_day_this_month - relativedelta(months=6)

    # 2. last month's orders and revenue
    last_month_query = f"""
        SELECT COUNT(*), SUM(spi.total_price)
        FROM seller_purchase_items spi
        JOIN seller_purchases sp ON spi.seller_purchase_id = sp.seller_purchase_id
        WHERE sp.seller_id = {seller_id}
        AND spi.updated_at >= '{first_day_last_month}'
        AND spi.updated_at < '{first_day_this_month}'
    """
    last_month_results = current_app.db.execute(last_month_query)
    last_month_orders, last_month_revenue = last_month_results[0]
    last_month_orders = last_month_orders or 0
    last_month_revenue = float(last_month_revenue or 0)

    # 3. current month's orders and revenue
    current_month_query = f"""
        SELECT COUNT(*), SUM(spi.total_price)
        FROM seller_purchase_items spi
        JOIN seller_purchases sp ON spi.seller_purchase_id = sp.seller_purchase_id
        WHERE sp.seller_id = {seller_id}
        AND spi.updated_at >= '{first_day_this_month}'
        AND spi.updated_at < '{first_day_next_month}'
    """
    current_month_results = current_app.db.execute(current_month_query)
    current_orders, current_revenue = current_month_results[0]
    current_orders = current_orders or 0
    current_revenue = float(current_revenue or 0)

    # ----- 4. calculate monthly change or fallback to 6-month average -----
    avg_orders = avg_revenue = None
    # default year-over-year logic (prioritize using last month's data)
    if last_month_orders != 0:
        order_change = round(((current_orders - last_month_orders) / last_month_orders) * 100, 2)
        order_diff = current_orders - last_month_orders
        order_basis = "last month"
    else:
        # if last month's value is 0, fallback to the average of the past 6 months
        avg_query = f"""
            SELECT COUNT(*), SUM(spi.total_price)
            FROM seller_purchase_items spi
            JOIN seller_purchases sp ON spi.seller_purchase_id = sp.seller_purchase_id
            WHERE sp.seller_id = {seller_id}
            AND spi.updated_at >= '{six_months_ago}'
        """
        avg_result = current_app.db.execute(avg_query)[0]
        total_six_month_orders = avg_result[0] or 0
        total_six_month_revenue = float(avg_result[1]) if avg_result[1] else 0.0

        avg_orders = total_six_month_orders / 6 if total_six_month_orders else 0
        avg_revenue = float(total_six_month_revenue) / 6 if total_six_month_revenue else 0

        order_change = round(((current_orders - avg_orders) / avg_orders) * 100, 2) if avg_orders else None
        order_diff = round(current_orders - avg_orders) if avg_orders else None
        order_basis = "6-month average"

    # ----- same for revenue -----
    if last_month_revenue != 0:
        revenue_change = round(((current_revenue - last_month_revenue) / last_month_revenue) * 100, 2)
        revenue_diff = round(current_revenue - last_month_revenue, 2)
        revenue_basis = "last month"
    else:
        revenue_change = round(((current_revenue - avg_revenue) / avg_revenue) * 100, 2) if avg_revenue else None
        revenue_diff = round(current_revenue - avg_revenue, 2) if avg_revenue else None
        revenue_basis = "6-month average"

    # ----- fetch all seller products -----
    product_query = f"""
        SELECT p.product_id, p.name, c.name AS category,
           i.quantity, i.price, i.created_at,
           i.publish_status, i.low_stock_quantity
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE i.seller_id = {seller_id}
        ORDER BY i.created_at DESC
    """
    product_results = current_app.db.execute(product_query)
    products = []
    for row in product_results:
        product_id, name, category, stock, price, created_at, publish_status, low_stock_quantity = row
        lowStock_status = "Low Stock" if stock < low_stock_quantity else "Normal"
        products.append({
            "id": product_id,
            "name": name,
            "category": category,
            "stock": stock,
            "price": f"${price:.2f}",
            "lowStock_status": lowStock_status,
            "status": publish_status or "Published",
            "date_added": created_at.strftime('%d %b %Y')
        })

    # ----- summary stats for total orders, revenue, average order value -----
    summary_query = f"""
        SELECT 
            COUNT(*) AS total_orders,
            SUM(spi.total_price) AS total_revenue,
            AVG(spi.total_price) AS avg_order_value
        FROM seller_purchase_items spi
        JOIN seller_purchases sp ON spi.seller_purchase_id = sp.seller_purchase_id
        WHERE sp.seller_id = {seller_id}
    """
    summary_result = current_app.db.execute(summary_query)[0]
    summary = {
        "total_orders": summary_result[0] or 0,
        "total_revenue": f"{summary_result[1]:.2f}" if summary_result[1] else "0.00",
        "avg_order_value": f"{summary_result[2]:.2f}" if summary_result[2] else "0.00"}

    # ----- get product-level daily sales trend -----
    trend_query = f"""
        SELECT p.name, spi.updated_at::date AS date, TO_CHAR(spi.updated_at::date, 'YYYY Mon DD') AS day_label, SUM(spi.quantity) AS total_sold
        FROM seller_purchase_items spi
        JOIN seller_purchases sp ON spi.seller_purchase_id = sp.seller_purchase_id
        JOIN products p ON spi.product_id = p.product_id
        WHERE sp.seller_id = {seller_id}
        GROUP BY p.name, date, day_label
        ORDER BY date
    """
    trend_results = current_app.db.execute(trend_query)

    product_trend = defaultdict(lambda: defaultdict(int))
    label_lookup = {}  # key: raw date, value: 'Mon DD'

    for name, raw_date, label, qty in trend_results:
        product_trend[name][raw_date] += qty
        label_lookup[raw_date] = label
    
    # ----- inventory vs. total sales comparison -----
    inv_vs_sales_query = f"""
        SELECT p.name,
            i.quantity,
            COALESCE(SUM(spi.quantity), 0) AS total_sold
        FROM products p
        JOIN inventory i ON i.product_id = p.product_id
        LEFT JOIN seller_purchase_items spi ON spi.product_id = p.product_id
        LEFT JOIN seller_purchases sp ON spi.seller_purchase_id = sp.seller_purchase_id
            AND sp.seller_id = {seller_id}
        WHERE i.seller_id = {seller_id}
        GROUP BY p.name, i.quantity
        ORDER BY p.name
    """
    ivs_results = current_app.db.execute(inv_vs_sales_query)

    inventory_sales_data = {
        "labels": [],
        "inventory": [],
        "sold": [],
        "sell_through": []
    }

    for name, inv, sold in ivs_results:
        inv = inv or 0
        sold = sold or 0

        inventory_sales_data["labels"].append(name)
        inventory_sales_data["inventory"].append(min(inv, 200))  # clip inventory to 200 to avoid distortion
        inventory_sales_data["sold"].append(sold or 0)

        safe_inv = inv if inv is not None else 0
        safe_sold = sold if sold is not None else 0

        rate = round(safe_sold / safe_inv, 2) if safe_inv > 0 else 0
        rate = min(rate, 1)  # force max sell_through = 1
        inventory_sales_data["sell_through"].append(rate)

    # ----- top products by order count -----
    product_popularity_query = f"""
        SELECT p.name, COUNT(*) AS order_count
        FROM seller_purchase_items spi
        JOIN seller_purchases sp ON spi.seller_purchase_id = sp.seller_purchase_id
        JOIN products p ON spi.product_id = p.product_id
        WHERE sp.seller_id = {seller_id}
        GROUP BY p.name
        ORDER BY order_count DESC
        LIMIT 5
    """
    popularity_results = current_app.db.execute(product_popularity_query)

    product_popularity_data = {
        "labels": [row[0] for row in popularity_results],
        "data": [row[1] if row[1] is not None else 0 for row in popularity_results]
    }

    # ----- order status distribution -----
    order_status_query = f"""
        SELECT spi.fulfillment_status, COUNT(*) 
        FROM seller_purchase_items spi
        JOIN seller_purchases sp ON spi.seller_purchase_id = sp.seller_purchase_id
        WHERE sp.seller_id = {seller_id}
        GROUP BY spi.fulfillment_status
    """
    status_results = current_app.db.execute(order_status_query)

    order_status_data = {
        "labels": [],
        "counts": []
    }
    for row in status_results:
        status, count = row
        order_status_data["labels"].append(status or "Unknown")
        order_status_data["counts"].append(count)

    # ----- top buyers ----- 
    buyer_query = f"""
        SELECT u.name, COUNT(*) AS num_orders, SUM(spi.total_price) AS total_spent
        FROM seller_purchase_items spi
        JOIN seller_purchases sp ON spi.seller_purchase_id = sp.seller_purchase_id
        JOIN accounts u ON sp.user_id = u.user_id
        WHERE sp.seller_id = {seller_id}
        GROUP BY u.name
        ORDER BY total_spent DESC
        LIMIT 4
    """
    buyer_results = current_app.db.execute(buyer_query)
    top_buyers = [{"name": row[0], "num_orders": row[1], "total_spent": float(row[2])} for row in buyer_results]

    # ----- recent reviews ----- 
    review_query = f"""
    SELECT p.name, a.name, pr.rating, pr.review_text, pr.updated_at
    FROM product_reviews pr
    JOIN products p ON pr.product_id = p.product_id
    JOIN accounts a ON pr.user_id = a.user_id
    WHERE p.creator_id = {seller_id}
    ORDER BY pr.updated_at DESC
    LIMIT 4
"""
    review_results = current_app.db.execute(review_query)

    recent_reviews = [{
        "product_name": row[0],
        "reviewer": row[1],
        "rating": row[2],
        "comment": row[3],
        "updated_at": row[4].strftime('%b %d, %Y') if row[4] else "Unknown"
    } for row in review_results]

    # ----- recent orders ----- 
    recent_orders_query = f"""
    SELECT p.name, spi.total_price, spi.quantity, spi.fulfillment_status, spi.updated_at, a.name
    FROM seller_purchase_items spi
    JOIN seller_purchases sp ON spi.seller_purchase_id = sp.seller_purchase_id
    JOIN products p ON spi.product_id = p.product_id
    JOIN accounts a ON sp.user_id = a.user_id
    WHERE sp.seller_id = {seller_id}
    ORDER BY spi.updated_at DESC
    LIMIT 4
"""
    recent_order_rows = current_app.db.execute(recent_orders_query)

    recent_orders = []
    for row in recent_order_rows:
        product_name, price, quantity, status, raw_date, buyer_name = row
        if isinstance(raw_date, str):
            raw_date = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")
        recent_orders.append({
            "product_name": product_name,
            "price": f"${price:.2f}",
            "quantity": quantity,
            "status": status,
            "order_date": raw_date.strftime('%b %d'),
            "buyer_name": buyer_name
        })

    # ----- final render ----- 
    return render_template('seller/dashboard.html',
                       seller_name=seller_name,
                       seller_id=seller_id,
                       orders=recent_orders,
                       inventory=products,
                       top_buyers=top_buyers,
                       recent_reviews=recent_reviews,
                       summary=summary,
                       current_orders=current_orders,
                       current_revenue=current_revenue,
                       avg_order_value=round(current_revenue / current_orders, 2) if current_orders > 0 else 0,
                       order_diff=order_diff,
                       revenue_diff=revenue_diff,
                       order_change=order_change,
                       revenue_change=revenue_change,
                       order_basis=order_basis,
                       revenue_basis=revenue_basis,
                       inventory_sales_data=inventory_sales_data,
                       product_popularity_data=product_popularity_data,
                       order_status_data=order_status_data)


# ===== Product Management Page =====
@inventory_bp.route('/seller/products')
@login_required
def seller_products():
    """Display seller's product management page with all listed products."""
    account_id = current_user.id

    # ----- retrieve seller_id ----- 
    seller_query = f"SELECT seller_id FROM accounts WHERE account_id = {account_id}"
    results = current_app.db.execute(seller_query)
    if not results or not results[0][0]:
        flash("You are not a seller!")
        return redirect(url_for('index.index'))
    seller_id = results[0][0]

    # ----- get seller name -----
    name_query = f"SELECT name FROM sellers WHERE seller_id = {seller_id}"
    name_results = current_app.db.execute(name_query)
    seller_name = name_results[0][0] if name_results else "Unknown Seller"

    # ----- query all products for this seller -----
    product_query = f"""
        SELECT p.product_id, p.name, c.name AS category,
            i.quantity, i.price, i.created_at,
            i.publish_status, i.low_stock_quantity
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE i.seller_id = {seller_id}
        ORDER BY i.created_at DESC
    """
    product_results = current_app.db.execute(product_query)

    # ----- format product information -----
    products = []
    for row in product_results:
        product_id, name, category, stock, price, created_at, publish_status, low_stock_quantity = row
        lowStock_status = "Low Stock" if stock < low_stock_quantity else "Normal"
        products.append({
            "id": product_id,
            "name": name,
            "category": category,
            "stock": stock,
            "price": f"${price:.2f}",
            "lowStock_status": lowStock_status,
            "status": publish_status or "Published",
            "date_added": created_at.strftime('%d %b %Y'),
            "low_stock_quantity": low_stock_quantity
        })

    return render_template('seller/product_management.html',
                           seller_name=seller_name,
                           seller_id=seller_id,
                           products=products)


@inventory_bp.route('/seller/update_product', methods=['POST'])
@login_required
def update_product():
    """Update product details for a seller, including name, stock, price, status, and category."""
    try:
        data = request.json

        product_id = data.get('id')
        name = data.get('name')
        stock = data.get('stock')
        price = data.get('price').replace('$', '') if data.get('price') else None
        status = data.get('status') or 'Published'
        low_stock_quantity = data.get('low_stock_quantity') or 50
        category_name = data.get('category')

        if not all([product_id, name, stock is not None, price]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        account_id = current_user.id

        # ----- retrieve seller_id ----- 
        seller_query = f"SELECT seller_id FROM accounts WHERE account_id = {account_id}"
        results = current_app.db.execute(seller_query)
        if not results or not results[0][0]:
            flash("You are not a seller!")
            return redirect(url_for('index.index'))
        seller_id = results[0][0]

        # ----- 1. search category_id -----
        if category_name:
            category_query = f"SELECT category_id FROM categories WHERE LOWER(name) = LOWER('{category_name}')"
            category_results = current_app.db.execute(category_query)
            if not category_results:
                return jsonify({"success": False, "error": f"Category '{category_name}' not found."}), 400
            category_id = category_results[0][0]
        else:
            return jsonify({"success": False, "error": "Category name missing"}), 400

        # 2. update products table (for name and category_id)
        update_product_query = f"""
            UPDATE products
            SET name = '{name}',
                category_id = {category_id}
            WHERE product_id = {product_id}
        """
        current_app.db.execute(update_product_query)

        # ----- 3. update inventory table -----
        update_inventory_query = f"""
            UPDATE inventory
            SET quantity = {stock},
                price = {price},
                publish_status = '{status}',
                low_stock_quantity = {low_stock_quantity}
            WHERE product_id = {product_id} AND seller_id = {seller_id}
        """
        current_app.db.execute(update_inventory_query)

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@inventory_bp.route('/seller/add_product', methods=['POST'])
@login_required
def add_product():
    """Add a new product for a seller, including name, category, stock, price, and initial status."""
    try:
        data = request.json

        name = data.get('name')
        category_name = data.get('category')
        stock = data.get('stock')
        price = data.get('price').replace('$', '') if data.get('price') else None
        status = data.get('status') or 'Published'
        low_stock_quantity = data.get('low_stock_quantity') or 50

        # check required fields are provided
        if not all([name, category_name, stock is not None, price]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        account_id = current_user.id

        # ----- retrieve seller_id ----- 
        seller_query = f"SELECT seller_id FROM accounts WHERE account_id = {account_id}"
        results = current_app.db.execute(seller_query)
        if not results or not results[0][0]:
            flash("You are not a seller!")
            return redirect(url_for('index.index'))
        seller_id = results[0][0]
        # 2. check category id according to category name
        category_query = f"SELECT category_id FROM categories WHERE LOWER(name) = LOWER('{category_name}')"
        category_results = current_app.db.execute(category_query)
        if not category_results:
            return jsonify({"success": False, "error": f"Category '{category_name}' not found."}), 400
        category_id = category_results[0][0]

        # 3. insert new peoduct
        insert_product_query = f"""
            INSERT INTO products (name, category_id, creator_id)
            VALUES ('{name}', {category_id}, {seller_id})
            RETURNING product_id
        """
        product_insert_result = current_app.db.execute(insert_product_query)
        product_id = product_insert_result[0][0]
        print(f"Inserted new product with ID {product_id}")

        # ----- 4. insert into inventory -----
        insert_inventory_query = f"""
            INSERT INTO inventory (seller_id, product_id, price, quantity, created_at, publish_status, low_stock_quantity)
            VALUES ({seller_id}, {product_id}, {price}, {stock}, CURRENT_TIMESTAMP, '{status}', {low_stock_quantity})
        """
        current_app.db.execute(insert_inventory_query)
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@inventory_bp.route('/seller/delete_product', methods=['POST'])
@login_required
def delete_product():
    """Delete a product from a seller's inventory and optionally from products table if no inventory remains."""
    try:
        data = request.json
        product_id = data.get('id')

        account_id = current_user.id

        # ----- retrieve seller_id ----- 
        seller_query = f"SELECT seller_id FROM accounts WHERE account_id = {account_id}"
        results = current_app.db.execute(seller_query)
        if not results or not results[0][0]:
            flash("You are not a seller!")
            return redirect(url_for('index.index'))
        seller_id = results[0][0]

        # 2. delete from inventory
        delete_inventory_query = f"""
            DELETE FROM inventory
            WHERE product_id = {product_id} AND seller_id = {seller_id}
        """
        current_app.db.execute(delete_inventory_query)

        # ----- 3. if no inventory exists for the product, delete from products table ----- 
        check_query = f"""
            SELECT 1 FROM inventory WHERE product_id = {product_id} LIMIT 1
        """
        still_exists = current_app.db.execute(check_query)
        if not still_exists:
            delete_product_query = f"""
                DELETE FROM products
                WHERE product_id = {product_id}
            """
            current_app.db.execute(delete_product_query)

        return jsonify({'success': True})

    except Exception as e:
        print("Error deleting product:", e)
        return jsonify({'success': False, 'error': str(e)}), 500


# ===== Order Management Page =====
@inventory_bp.route('/seller/orders')
@login_required
def seller_orders():
    """Display seller's order management page with all purchase orders."""
    account_id = current_user.id

    # ----- retrieve seller_id ----- 
    seller_query = f"SELECT seller_id FROM accounts WHERE account_id = {account_id}"
    results = current_app.db.execute(seller_query)
    if not results or not results[0][0]:
        flash("You are not a seller!")
        return redirect(url_for('index.index'))
    seller_id = results[0][0]

    # ----- get seller name ----- 
    name_query = f"SELECT name FROM sellers WHERE seller_id = {seller_id}"
    name_results = current_app.db.execute(name_query)
    seller_name = name_results[0][0] if name_results else "Unknown Seller"

    # ----- get seller order ----- 
    orders_query = f"""
        SELECT sp.seller_purchase_id,
               spi.seller_purchase_item_id,
               spi.product_id,
               p.name AS product_name,
               spi.quantity,
               spi.unit_price,
               spi.total_price,
               spi.fulfillment_status,
               sp.updated_at,
               u.name AS buyer_name,
               u.address AS buyer_address
        FROM seller_purchase_items spi
        JOIN seller_purchases sp ON spi.seller_purchase_id = sp.seller_purchase_id
        JOIN products p ON spi.product_id = p.product_id
        JOIN accounts u ON sp.user_id = u.user_id 
        WHERE sp.seller_id = {seller_id}
        ORDER BY sp.updated_at DESC
"""
    order_results = current_app.db.execute(orders_query)

    # ----- format product information -----
    orders = []
    for row in order_results:
        updated_at_raw = row[8]
        updated_at_str = updated_at_raw.strftime('%d %b %Y') if updated_at_raw else "N/A"

        orders.append({
            "order_id": row[0],
            "order_item_id": row[1],
            "product_id": row[2],
            "product_name": row[3],
            "quantity": row[4],
            "unit_price": f"${row[5]:.2f}",
            "total_price": f"${row[6]:.2f}",
            "status": row[7],
            "updated_at": updated_at_str,
            "buyer_name": row[9],
            "buyer_address": row[10]
        })

    return render_template('seller/order_management.html',
                           seller_name=seller_name,
                           seller_id=seller_id,
                           orders=orders,)


@inventory_bp.route('/seller/delete_order_item', methods=['POST'])
@login_required
def delete_order_item():
    """Delete a specific order item from seller's orders."""
    data = request.json
    item_id = data.get('id')

    try:
        delete_query = f"""
            DELETE FROM seller_purchase_items
            WHERE seller_purchase_item_id = {item_id}
        """
        current_app.db.execute(delete_query)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@inventory_bp.route('/seller/fulfill_order_item', methods=['POST'])
@login_required
def fulfill_order_item():
    """Mark a specific order item as fulfilled."""
    try:
        data = request.get_json()
        item_id = data.get('id')

        if not item_id:
            return jsonify({'success': False, 'error': 'Missing item ID'}), 400

        fulfill_query = f"""
            UPDATE seller_purchase_items
            SET fulfillment_status = 'Fulfilled'
            WHERE seller_purchase_item_id = {item_id}
        """
        current_app.db.execute(fulfill_query)
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

 # ===== Reviews Management =====
@inventory_bp.route('/seller/reviews')
@login_required
def seller_reviews():
    """
    Display all reviews for the current seller.
    
    Fetches reviews from the seller_reviews table and passes them to the template.
    Shows review summary statistics and allows sorting by various criteria.
    """
    # Get current seller's ID
    seller_id = current_user.id
    
    # Query to fetch all reviews for the current seller
    query = f"""
        SELECT sr.seller_review_id, sr.user_id, sr.review_text, sr.rating, 
               sr.updated_at, a.name as customer_name
        FROM seller_reviews sr
        JOIN accounts a ON sr.user_id = a.user_id
        WHERE sr.seller_id = {seller_id}
        """
    
    # Execute query without sorting in SQL
    reviews = current_app.db.execute(query)
    
    # Get sort order from request args
    sort = request.args.get('sort', 'date_desc')
    
    # Convert reviews to a list to be able to sort it
    reviews_list = list(reviews)
    
    # Sort reviews based on the query parameter
    if sort == 'date_asc':
        reviews_list.sort(key=lambda x: x.updated_at)
    elif sort == 'date_desc':
        reviews_list.sort(key=lambda x: x.updated_at, reverse=True)
    elif sort == 'rating_asc':
        reviews_list.sort(key=lambda x: x.rating)
    elif sort == 'rating_desc':
        reviews_list.sort(key=lambda x: x.rating, reverse=True)
    
    def humanize_time(datetime_obj):
        """Return a human-friendly time string showing days since the review"""
        now = datetime.now()
        diff = now - datetime_obj
        
        if diff.days == 0:
            return "today"
        elif diff.days == 1:
            return "yesterday"
        else:
            return f"{diff.days} days ago"
    
    return render_template('seller/seller_reviews.html', 
                          reviews=reviews_list, 
                          humanize_time=humanize_time)
       