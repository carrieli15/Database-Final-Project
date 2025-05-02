from flask import current_app as app

class SavedItem:
    def __init__(self, saved_item_id, user_id, product_id, seller_id=None, added_at=None):
        self.saved_item_id = saved_item_id
        self.user_id = user_id
        self.product_id = product_id
        self.seller_id = seller_id
        self.added_at = added_at
    
    @staticmethod
    def get_by_user_id(user_id):
        """Get all saved items for a user"""
        rows = app.db.execute('''
SELECT saved_item_id, user_id, product_id, seller_id, added_at
FROM Saved_items
WHERE user_id = :user_id
ORDER BY added_at DESC
''', user_id=user_id)
        
        return [SavedItem(*row) for row in rows]
    
    @staticmethod
    def add(user_id, product_id, seller_id=None):
        """Add an item to saved items"""
        app.db.execute('''
INSERT INTO Saved_items(user_id, product_id, seller_id)
VALUES(:user_id, :product_id, :seller_id)
''', user_id=user_id, product_id=product_id, seller_id=seller_id)
    
    @staticmethod
    def remove(user_id, product_id):
        """Remove an item from saved items"""
        app.db.execute('''
DELETE FROM Saved_items
WHERE user_id = :user_id AND product_id = :product_id
''', user_id=user_id, product_id=product_id)
    
    @staticmethod
    def move_to_cart(user_id, product_id):
        """Move an item from saved items to cart"""
        # Get cart
        from .cart import Cart
        cart = Cart.get_by_user_id(user_id)
        
        # Add item to cart with quantity 1
        cart.add_item(product_id, 1)
        cart.save()
        
        # Remove from saved items
        SavedItem.remove(user_id, product_id)