from flask import current_app as app
from datetime import datetime
from decimal import Decimal

class Coupon:
    def __init__(self, coupon_id, code, discount_percent, valid_from, valid_until, is_active):
        self.coupon_id = coupon_id
        self.code = code
        self.discount_percent = float(discount_percent)
        self.valid_from = valid_from
        self.valid_until = valid_until
        self.is_active = is_active
    
    @staticmethod
    def get_by_code(code):
        """Get coupon by code"""
        if not code:
            return None
            
        rows = app.db.execute('''
        SELECT coupon_id, code, discount_percent, valid_from, valid_until, is_active
        FROM Coupons
        WHERE code = :code
        ''', code=code.strip().upper())
        
        return Coupon(*(rows[0])) if rows else None
    
    def is_valid(self):
        """Check if coupon is valid (active and within date range)"""
        if not self.is_active:
            return False
            
        now = datetime.now()
        
        # Check if already datetime objects
        if isinstance(self.valid_from, datetime):
            valid_from = self.valid_from
            valid_until = self.valid_until
        else:
            # Parse if they're strings
            valid_from = datetime.strptime(self.valid_from, '%Y-%m-%d %H:%M:%S')
            valid_until = datetime.strptime(self.valid_until, '%Y-%m-%d %H:%M:%S')
        
        return valid_from <= now <= valid_until
    

    def calculate_discount(self, order_total):
        """Calculate discount amount based on order total"""
        if not self.is_valid():
            return 0
        
        # Convert discount_percent to same type as order_total to avoid type mismatch
        if isinstance(order_total, Decimal):
            discount_percent_decimal = Decimal(str(self.discount_percent))
            discount = order_total * (discount_percent_decimal / Decimal('100.0'))
        else:
            discount = float(order_total) * (self.discount_percent / 100.0)
        
        return round(discount, 2)

   
    @staticmethod
    def get_all_active():
        """Get all active coupons"""
        rows = app.db.execute('''
        SELECT coupon_id, code, discount_percent, valid_from, valid_until, is_active
        FROM Coupons
        WHERE is_active = true AND valid_until > NOW()
        ''')
        
        return [Coupon(*row) for row in rows]