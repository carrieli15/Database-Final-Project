from flask_login import LoginManager

login = LoginManager()

from .cart import Cart, CartItem
from .purchase import Purchase, PurchaseItem
from .coupon import Coupon