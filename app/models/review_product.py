from flask import current_app as app

class ProductReview:
    def __init__(self, product_review_id, user_id, product_id, review_text, rating, updated_at, upvote_count=0):
        self.product_review_id = product_review_id
        self.user_id = user_id
        self.product_id = product_id
        self.review_text = review_text
        self.rating = rating
        self.updated_at = updated_at
        self.upvote_count = upvote_count

    @staticmethod
    def get(product_review_id):
        rows = app.db.execute('''
SELECT product_review_id, user_id, product_id, review_text, rating, updated_at, upvote_count
FROM product_reviews
WHERE product_review_id = :product_review_id
''',
                             product_review_id=product_review_id)
        return ProductReview(*(rows[0])) if rows else None

    @staticmethod
    def add(user_id, product_id, review_text, rating, updated_at):
        rows = app.db.execute("""
    INSERT INTO product_reviews(user_id, product_id, review_text, rating, updated_at)
    VALUES(:user_id, :product_id, :review_text, :rating, :updated_at)
    RETURNING product_review_id
    """,
                             user_id=user_id,
                             product_id=product_id,
                             review_text=review_text,
                             rating=rating,
                             updated_at=updated_at)
        product_review_id = rows[0][0]
        return ProductReview.get(product_review_id)

    @staticmethod
    def get_user_id_from_account_id(account_id):
        """Get the user_id corresponding to an account_id"""
        rows = app.db.execute('''
        SELECT user_id FROM accounts WHERE account_id = :account_id
        ''', account_id=account_id)
        return rows[0][0] if rows else None
        
    @staticmethod
    def get_all_by_user_id_since(user_id, since):
        rows = app.db.execute('''
SELECT product_review_id, user_id, product_id, review_text, rating, updated_at, upvote_count
FROM product_reviews
WHERE user_id = :user_id
AND updated_at >= :since
ORDER BY updated_at DESC
''',
                             user_id=user_id,
                             since=since)
        return [ProductReview(*row) for row in rows]
    
    @staticmethod
    def get_all_by_product_id(product_id):
        rows = app.db.execute('''
SELECT product_review_id, user_id, product_id, review_text, rating, updated_at, upvote_count
FROM product_reviews
WHERE product_id = :product_id
ORDER BY updated_at DESC
''',
                             product_id=product_id)
        return [ProductReview(*row) for row in rows]
    
    @staticmethod
    def update(product_review_id, review_text, rating, updated_at):
        rows = app.db.execute('''
UPDATE product_reviews
SET review_text = :review_text,
    rating = :rating,
    updated_at = :updated_at
WHERE product_review_id = :product_review_id
RETURNING product_review_id
''',
                             product_review_id=product_review_id,
                             review_text=review_text,
                             rating=rating,
                             updated_at=updated_at)
        return ProductReview.get(product_review_id) if rows else None
    
    @staticmethod
    def delete(product_review_id):
        app.db.execute('''
DELETE FROM product_reviews
WHERE product_review_id = :product_review_id
''',
                      product_review_id=product_review_id)
        return True

    @staticmethod
    def upvote(review_id, user_id):
        """Add an upvote to a review from a user"""
        try:
            # First try to insert the upvote record
            app.db.execute('''
            INSERT INTO review_upvotes(review_id, user_id, created_at)
            VALUES(:review_id, :user_id, NOW())
            ''', 
            review_id=review_id, 
            user_id=user_id)

            # Then increment the upvote count
            app.db.execute('''
            UPDATE product_reviews
            SET upvote_count = upvote_count + 1
            WHERE product_review_id = :review_id
            ''', 
            review_id=review_id)

            return True
        except Exception as e:
            # If the user has already upvoted, this will fail due to the UNIQUE constraint
            print(f"Error upvoting review: {e}")
            return False

    @staticmethod
    def remove_upvote(review_id, user_id):
        """Remove an upvote from a review"""
        try:
            # First remove the upvote record
            result = app.db.execute('''
            DELETE FROM review_upvotes
            WHERE review_id = :review_id AND user_id = :user_id
            RETURNING id
            ''', 
            review_id=review_id, 
            user_id=user_id)

            # If a record was deleted, decrement the upvote count
            if result:
                app.db.execute('''
                UPDATE product_reviews
                SET upvote_count = upvote_count - 1
                WHERE product_review_id = :review_id
                ''', 
                review_id=review_id)
                return True
            return False
        except Exception as e:
            print(f"Error removing upvote: {e}")
            return False

    @staticmethod
    def has_user_upvoted(review_id, user_id):
        """Check if a user has upvoted a specific review"""
        rows = app.db.execute('''
        SELECT 1 FROM review_upvotes
        WHERE review_id = :review_id AND user_id = :user_id
        ''', 
        review_id=review_id, 
        user_id=user_id)

        return len(rows) > 0

    @staticmethod
    def get_all_by_product_id_sorted(product_id, sort):
        """Get all reviews for a product, sorted by the specified criteria"""
        sort_clause = 'updated_at DESC'  # Default sort

        if sort == 'date_asc':
            sort_clause = 'updated_at ASC'
        elif sort == 'date_desc':
            sort_clause = 'updated_at DESC'
        elif sort == 'rating_asc':
            sort_clause = 'rating ASC'
        elif sort == 'rating_desc':
            sort_clause = 'rating DESC'
        elif sort == 'upvotes_asc':
            sort_clause = 'upvote_count ASC'
        elif sort == 'upvotes_desc':
            sort_clause = 'upvote_count DESC'

        query = f'''
        SELECT product_review_id, user_id, product_id, review_text, rating, updated_at, upvote_count
        FROM product_reviews
        WHERE product_id = :product_id
        ORDER BY {sort_clause}
        '''
        
        rows = app.db.execute(query, product_id=product_id)
        return [ProductReview(*row) for row in rows]