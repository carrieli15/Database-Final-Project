from flask import jsonify, url_for, redirect, render_template, request, flash
from flask_login import current_user
import datetime
from humanize import naturaltime

# Fix the import path to use the correct file
from .models.review_product import ProductReview

from flask import Blueprint
bp = Blueprint('product_reviews', __name__)

def humanize_time(dt):
    return naturaltime(datetime.datetime.now() - dt)


def check_user_purchase(user_id, product_id):
    from flask import current_app as app
    
    # Query to check if the user has purchased the product
    rows = app.db.execute('''
        SELECT 1
        FROM purchases p
        JOIN purchase_items pi ON p.purchase_id = pi.purchase_id
        WHERE p.user_id = :user_id
        AND pi.product_id = :product_id
        AND p.status = 'completed'
        LIMIT 1
    ''', user_id=user_id, product_id=product_id)
    
    return len(rows) > 0

@bp.route('/product_reviews')
def product_reviews():
    if current_user.is_authenticated:
        # Get the user_id from the account_id
        user_id = ProductReview.get_user_id_from_account_id(current_user.id)
        if user_id:
            print(f"Account ID: {current_user.id}, User ID: {user_id}")
            
            # Get reviews with the correct user_id
            reviews = ProductReview.get_all_by_user_id_since(
                user_id, datetime.datetime(1980, 9, 14, 0, 0, 0))
            
            print(f"Found {len(reviews)} reviews for user_id {user_id}")
            
            return render_template('product_reviews.html',
                                  reviews=reviews,
                                  humanize_time=humanize_time)
        else:
            print(f"No user_id found for account_id {current_user.id}")
            return jsonify({"error": "User not found"}), 404
    else:
        return jsonify({"error": "Not authenticated"}), 404

@bp.route('/product/<int:product_id>/review/add', methods=['GET', 'POST'])
def add_product_review(product_id):
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))
    
    # Check if user has purchased the product
    user_id = ProductReview.get_user_id_from_account_id(current_user.id)
    if not user_id or not check_user_purchase(user_id, product_id):
        flash('You can only review products you have purchased.', 'error')
        return redirect(url_for('products.product_detail', product_id=product_id))
    
    if request.method == 'POST':
        review_text = request.form.get('review_text')
        rating = int(request.form.get('rating'))
        
        # Validate the input
        if not review_text or not rating or rating < 1 or rating > 5:
            flash('Please provide a valid review and rating (1-5)', 'error')
            return redirect(url_for('product_reviews.add_product_review', product_id=product_id))
        
        # Add the review
        ProductReview.add(
            user_id, 
            product_id, 
            review_text, 
            rating, 
            datetime.datetime.now()
        )
        
        flash('Your review has been added successfully!', 'success')
        return redirect(url_for('product_reviews.product_reviews_by_product', product_id=product_id))
    
    # GET request - show the review form
    return render_template('add_product_review.html', product_id=product_id)

@bp.route('/product/review/<int:review_id>/edit', methods=['GET', 'POST'])
def edit_product_review(review_id):
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))
    
    # Get the user_id corresponding to the current account_id
    user_id = ProductReview.get_user_id_from_account_id(current_user.id)
    if not user_id:
        flash('User information not found', 'error')
        return redirect(url_for('index.index'))
    
    review = ProductReview.get(review_id)
    
    # Check if review exists and belongs to the current user
    if not review or review.user_id != user_id:
        flash('Review not found or you do not have permission to edit it', 'error')
        return redirect(url_for('product_reviews.product_reviews'))
    
    if request.method == 'POST':
        review_text = request.form.get('review_text')
        rating = int(request.form.get('rating'))
        
        # Validate the input
        if not review_text or not rating or rating < 1 or rating > 5:
            flash('Please provide a valid review and rating (1-5)', 'error')
            return redirect(url_for('product_reviews.edit_product_review', review_id=review_id))
        
        # Update the review
        ProductReview.update(
            review_id,
            review_text,
            rating,
            datetime.datetime.now()
        )
        
        flash('Your review has been updated successfully!', 'success')
        return redirect(url_for('product_reviews.product_reviews_by_product', product_id=review.product_id))
    
    # GET request - show the edit form
    return render_template('edit_product_review.html', review=review)

@bp.route('/product/review/<int:review_id>/delete', methods=['POST'])
def delete_product_review(review_id):
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))
    
    # Get the user_id corresponding to the current account_id
    user_id = ProductReview.get_user_id_from_account_id(current_user.id)
    if not user_id:
        flash('User information not found', 'error')
        return redirect(url_for('index.index'))
    
    review = ProductReview.get(review_id)
    
    # Check if review exists and belongs to the current user
    if not review or review.user_id != user_id:
        flash('Review not found or you do not have permission to delete it', 'error')
        return redirect(url_for('product_reviews.product_reviews'))
    
    product_id = review.product_id
    
    # Delete the review
    ProductReview.delete(review_id)
    
    flash('Your review has been deleted successfully!', 'success')
    return redirect(url_for('product_reviews.product_reviews_by_product', product_id=product_id))

@bp.route('/product/<int:product_id>/reviews')
def product_reviews_by_product(product_id):
    """
    Display all reviews for a specific product
    """
    # Get all reviews for this product
    sort = request.args.get('sort', 'date_desc')
    
    # Use the method that supports sorting
    reviews = ProductReview.get_all_by_product_id_sorted(product_id, sort)
    
    # If user is logged in, check which reviews they've upvoted
    user_upvoted_reviews = set()
    if current_user.is_authenticated:
        user_id = ProductReview.get_user_id_from_account_id(current_user.id)
        if user_id:
            for review in reviews:
                if ProductReview.has_user_upvoted(review.product_review_id, user_id):
                    user_upvoted_reviews.add(review.product_review_id)
    
    return render_template('product_reviews_by_product.html', 
                          reviews=reviews, 
                          product_id=product_id,
                          humanize_time=humanize_time,
                          user_upvoted_reviews=user_upvoted_reviews,
                          sort=sort)  # Pass the sort parameter to the template

@bp.route('/product/review/<int:review_id>/upvote', methods=['POST'])
def upvote_review(review_id):
    """Add an upvote to a review"""
    if not current_user.is_authenticated:
        return jsonify({"error": "You must be logged in to upvote reviews"}), 401
    
    user_id = ProductReview.get_user_id_from_account_id(current_user.id)
    if not user_id:
        return jsonify({"error": "User information not found"}), 404
    
    review = ProductReview.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404
    
    # Check if the user has already upvoted this review
    if ProductReview.has_user_upvoted(review_id, user_id):
        # If already upvoted, remove the upvote (toggle behavior)
        success = ProductReview.remove_upvote(review_id, user_id)
        if success:
            return jsonify({"status": "success", "action": "removed", "upvote_count": review.upvote_count - 1})
        else:
            return jsonify({"error": "Failed to remove upvote"}), 500
    else:
        # Add the upvote
        success = ProductReview.upvote(review_id, user_id)
        if success:
            return jsonify({"status": "success", "action": "added", "upvote_count": review.upvote_count + 1})
        else:
            return jsonify({"error": "Failed to add upvote"}), 500