from flask import Flask
from flask_login import LoginManager
from .config import Config
from .db import DB
from .cart_routes import bp as cart_bp

login = LoginManager()
login.login_view = 'users.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.db = DB(app)
    login.init_app(app)

    from .review_product import check_user_purchase
    
    # Register global template function
    @app.template_global()
    def check_user_has_purchased(user_id, product_id):
        return check_user_purchase(user_id, product_id)


    from .index import bp as index_bp
    app.register_blueprint(index_bp)
    
    from .users import bp as users_bp
    app.register_blueprint(users_bp)
    
    # Add this line if it's missing
    from .cart_routes import bp as cart_bp
    app.register_blueprint(cart_bp)
    
    from .product import bp as product_bp
    app.register_blueprint(product_bp)

    from .review_product import bp as review_product_bp
    app.register_blueprint(review_product_bp)

    from .seller import inventory_bp
    app.register_blueprint(inventory_bp)
    return app