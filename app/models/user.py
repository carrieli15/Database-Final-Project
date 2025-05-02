from flask_login import UserMixin
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash
from app import login

class User(UserMixin):
    def __init__(self, id, email, name, user_id, balance, address):
        self.id = id
        self.email = email
        self.name = name
        self.user_id = user_id
        self.balance = balance
        self.address = address

    @staticmethod
    def get(id):
        rows = app.db.execute("""
            SELECT account_id, email, name, user_id, balance, address
            FROM Accounts
            WHERE account_id = :id
        """, id=id)
        return User(*rows[0]) if rows else None

    def get_balance(self):
        result = app.db.execute("""
            SELECT balance FROM Accounts WHERE account_id = :id
        """, id=self.id)
        return result[0][0] if result else 0.0

    def update_balance(self, amount):
        current_balance = self.get_balance()
        new_balance = current_balance + amount

        app.db.execute("""
            UPDATE Accounts SET balance = :new_balance WHERE account_id = :id
        """, new_balance=new_balance, id=self.id)

        app.db.execute("""
            INSERT INTO BalanceHistory(account_id, amount, new_balance)
            VALUES (:id, :amount, :new_balance)
        """, id=self.id, amount=amount, new_balance=new_balance)

    @staticmethod
    def get_by_auth(email, password):
        rows = app.db.execute("""
            SELECT password, account_id, email, name, user_id, balance, address
            FROM Accounts
            WHERE email = :email
        """, email=email)
        if not rows:
            return None
        elif not check_password_hash(rows[0][0], password):
            return None
        else:
            return User(*rows[0][1:])

    @staticmethod
    def email_exists(email):
        rows = app.db.execute("""
            SELECT email FROM Accounts WHERE email = :email
        """, email=email)
        return len(rows) > 0

    @staticmethod
    def register(email, password, full_name, address=None):
        try:
            rows = app.db.execute("""
                INSERT INTO Users DEFAULT VALUES RETURNING user_id
            """)
            user_id = rows[0][0]

            rows = app.db.execute("""
                INSERT INTO Accounts(user_id, email, password, name, address)
                VALUES(:user_id, :email, :password, :name, :address)
                RETURNING account_id, email, name, user_id, balance, address
            """,
            user_id=user_id,
            email=email,
            password=generate_password_hash(password),
            name=full_name,
            address=address)

            return User(*rows[0])
        except Exception as e:
            print("Registration error:", e)
            return None

    @staticmethod
    def get_user_purchases(user_id, product_name=None, seller_name=None, date=None, sort_order='desc', sort_by='date'):
        # Debug information to help diagnose filtering issues
        print(f"DEBUG - Filter params: product_name={product_name}, seller_name={seller_name}, date={date}")
        
        query = """
            SELECT
                p.purchase_id,
                pi.unit_price * pi.quantity AS item_total,
                pi.quantity,
                CASE 
                    WHEN pi.quantity > 1 THEN pr.name || ' (x' || pi.quantity || ')'
                    ELSE pr.name
                END AS product_name,
                pi.fulfillment_status,
                TO_CHAR(pi.updated_at, 'YYYY-MM-DD HH24:MI:SS') AS fulfilled_on,
                a.name AS seller_name
            FROM purchases p
            JOIN purchase_items pi ON p.purchase_id = pi.purchase_id
            JOIN products pr ON pi.product_id = pr.product_id
            JOIN accounts a ON pi.seller_id = a.account_id
            WHERE p.user_id = :user_id
        """

        params = {'user_id': user_id}

        # Only add filter conditions if the parameters are not None and not empty
        if product_name and product_name.strip():
            query += " AND pr.name ILIKE :product_name"
            params['product_name'] = f"%{product_name.strip()}%"
            print(f"DEBUG - Added product filter: {product_name}")

        if seller_name and seller_name.strip():
            query += " AND a.name ILIKE :seller_name"
            params['seller_name'] = f"%{seller_name.strip()}%"
            print(f"DEBUG - Added seller filter: {seller_name}")

        if date and date.strip():
            query += " AND DATE(pi.updated_at) = :date"
            params['date'] = date.strip()
            print(f"DEBUG - Added date filter: {date}")

        # Add ORDER BY clause based on sort parameters
        if sort_by == 'price':
            query += f" ORDER BY item_total {sort_order.upper()}"
        else:
            # Default sort by date
            query += f" ORDER BY pi.updated_at {sort_order.upper()}"
            
        print(f"DEBUG - Final SQL query: {query}")
        print(f"DEBUG - Query parameters: {params}")

        return app.db.execute(query, **params)


@login.user_loader
def load_user(id):
    rows = app.db.execute("""
        SELECT account_id, email, name, user_id, balance, address
        FROM Accounts
        WHERE account_id = :id
    """, id=id)
    return User(*rows[0]) if rows else None