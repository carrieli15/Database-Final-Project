from flask import current_app as app

class Product:
    def __init__(self, id, name, price, available, image=None, description=None, category=None, subcategory=None, rating=None):
        self.id = id
        self.name = name
        self.price = price
        self.available = available
        self.image = image
        self.description = description
        self.category = category   
        self.subcategory = subcategory  
        self.rating = rating

    
    @staticmethod
    def get(id):
        rows = app.db.execute('''
        SELECT Products.product_id, Products.name, Products.description, Products.image, 
            Products.category_id, Products.creator_id, Inventory.price, Inventory.quantity,
            Categories.name AS category_name, 
            Subcategories.name AS subcategory_name,
            AVG(product_reviews.rating) AS average_rating
        FROM Products
        JOIN Inventory ON Products.product_id = Inventory.product_id
        LEFT JOIN Categories ON Products.category_id = Categories.category_id
        LEFT JOIN Categories AS Subcategories ON Categories.parent_id = Subcategories.category_id
        LEFT JOIN product_reviews ON Products.product_id = product_reviews.product_id
        WHERE Products.product_id = :id
        GROUP BY Products.product_id, Products.name, Products.description, Products.image, 
                Products.category_id, Products.creator_id, Inventory.price, Inventory.quantity,
                Categories.name, Subcategories.name
    ''',
                              id=id)
                              
        if not rows:
            return None
            
        product = Product(
            id=rows[0][0],       # product_id
            name=rows[0][1],     # name
            price=rows[0][6],    # price from inventory
            available=(rows[0][7] > 0),  # available based on quantity
            image=rows[0][3], 
            description=rows[0][2],  # description
            category=rows[0][8],     # <- category_name  
            subcategory=rows[0][9]   # <- subcategory_name  
        )
        
        product.product_id = rows[0][0]  # Ensure product_id is set
        product.image = rows[0][3]
        product.category_id = rows[0][4]
        product.creator_id = rows[0][5]
        product.quantity = rows[0][7]
        product.rating = rows[0][10]  

        
        return product
    
    @staticmethod
    def get_all(available=True):
        rows = app.db.execute('''
        SELECT Products.product_id, Products.name, Inventory.price, 
               CASE WHEN Inventory.quantity > 0 THEN TRUE ELSE FALSE END AS available, 
               Products.image, Products.description,
               Categories.name AS category_name,
               Subcategories.name AS subcategory_name,
               AVG(product_reviews.rating) AS average_rating
        FROM Products
        JOIN Inventory ON Products.product_id = Inventory.product_id
        LEFT JOIN Categories ON Products.category_id = Categories.category_id
        LEFT JOIN Categories AS Subcategories ON Categories.parent_id = Subcategories.category_id
        LEFT JOIN product_reviews ON Products.product_id = product_reviews.product_id 
        WHERE CASE WHEN Inventory.quantity > 0 THEN TRUE ELSE FALSE END = :available
        GROUP BY Products.product_id, Products.name, Inventory.price, Inventory.quantity, 
                 Products.image, Products.description, Categories.name, Subcategories.name
        ''',
                              available=available)
        return [Product(*row) for row in rows]


    @staticmethod
    def get_by_category(category_id, available=True):
        rows = app.db.execute('''
        SELECT Products.product_id, Products.name, Inventory.price, 
            CASE WHEN Inventory.quantity > 0 THEN TRUE ELSE FALSE END as available, 
            Products.image, Products.description,
            Categories.name as category_name,
            Subcategories.name as subcategory_name
        FROM Products
        JOIN Inventory ON Products.product_id = Inventory.product_id
        LEFT JOIN Categories ON Products.category_id = Categories.category_id
        LEFT JOIN Categories AS Subcategories ON Categories.parent_id = Subcategories.category_id
        WHERE 
            CASE WHEN Inventory.quantity > 0 THEN TRUE ELSE FALSE END = :available
            AND Products.category_id = :category_id
        ''',
                            available=available,
                            category_id=category_id)
        return [Product(*row) for row in rows]

    @staticmethod
    def search(search_term, available=True):
        """
        Search products by name or description
        """
        rows = app.db.execute('''
        SELECT Products.product_id, Products.name, Inventory.price, 
            CASE WHEN Inventory.quantity > 0 THEN TRUE ELSE FALSE END as available, 
            Products.image, Products.description,
            Categories.name as category_name,
            Subcategories.name as subcategory_name
        FROM Products
        JOIN Inventory ON Products.product_id = Inventory.product_id
        LEFT JOIN Categories ON Products.category_id = Categories.category_id
        LEFT JOIN Categories AS Subcategories ON Categories.parent_id = Subcategories.category_id
        WHERE 
            CASE WHEN Inventory.quantity > 0 THEN TRUE ELSE FALSE END = :available
            AND (LOWER(Products.name) LIKE LOWER(:search_pattern) OR LOWER(Products.description) LIKE LOWER(:search_pattern))
        ''',
                            available=available,
                            search_pattern=f'%{search_term}%')
        return [Product(*row) for row in rows]

    @staticmethod
    def get_sellers_inventory(product_id):
        """
        Get all sellers and their inventory quantities for a specific product
        """
        rows = app.db.execute('''
        SELECT products.product_id, products.name, inventory.quantity, 
            inventory.price, sellers.seller_id, sellers.name AS seller_name
        FROM products 
        JOIN inventory ON inventory.product_id = products.product_id 
        JOIN sellers ON inventory.seller_id = sellers.seller_id
        WHERE products.product_id = :product_id
        ORDER BY inventory.price ASC
        ''',
                            product_id=product_id)
    
        return rows
