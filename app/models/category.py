# models/category.py
from flask import current_app as app

class Category:
    @staticmethod
    def get_parent_categories():
        rows = app.db.execute('''
        SELECT category_id, name 
        FROM Categories
        WHERE parent_id IS NULL
        ''')
        return [category for category in rows]
