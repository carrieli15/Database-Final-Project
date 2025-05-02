from flask import render_template, redirect, url_for, flash, request
from flask import Blueprint
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo        
from .models.user import User  
from flask import current_app as app

bp = Blueprint('users', __name__)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    address = StringField('Address')
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        if User.email_exists(email.data):
            raise ValidationError('Already a user with this email.')

class ChangeAddressForm(FlaskForm):
    new_address = StringField('New Address', validators=[DataRequired()])
    submit = SubmitField('Change Address')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Update Password')

class ChangeEmailForm(FlaskForm):
    new_email = StringField('New Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Change Email')

    def validate_new_email(self, new_email):
        if User.email_exists(new_email.data):
            raise ValidationError("That email is already registered.")

class BalanceForm(FlaskForm):
    amount = StringField('Amount', validators=[DataRequired()])
    submit = SubmitField('Add Money')

# ---------------------- Routes ---------------------- #

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_auth(form.email.data, form.password.data)
        if user is None:
            flash('Invalid email or password')
            return redirect(url_for('users.login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index.index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        full_name = f"{form.firstname.data} {form.lastname.data}"
        if User.register(
            email=form.email.data,
            password=form.password.data,
            full_name=full_name,
            address=form.address.data
        ):
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index.index'))

@bp.route('/profile')
@login_required
def profile():
    # Get filter parameters from request - with debug prints
    product_name = request.args.get('product_name', '')
    seller_name = request.args.get('seller_name', '')
    date = request.args.get('date', '')
    sort_order = request.args.get('sort_order', 'desc')
    sort_by = request.args.get('sort_by', 'date')
    
    # Print debug information
    print(f"Route DEBUG - Received filter params: product={product_name}, seller={seller_name}, date={date}")
    print(f"Route DEBUG - Sorting: by={sort_by}, order={sort_order}")
    
    # Get purchase history with filters
    purchase_history = User.get_user_purchases(
        current_user.user_id,
        product_name=product_name,
        seller_name=seller_name,
        date=date,
        sort_order=sort_order,
        sort_by=sort_by
    )
    
    print(f"Route DEBUG - Found {len(purchase_history)} purchase records")
    
    return render_template(
        'profile.html',
        user=current_user,
        purchase_history=purchase_history,
        request=request  # Pass request to access args in template
    )

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user_row = app.db.execute("""
            SELECT password FROM Accounts WHERE account_id = :id
        """, id=current_user.id)
        
        if not user_row or not check_password_hash(user_row[0][0], form.old_password.data):
            flash("Incorrect current password.")
            return redirect(url_for('users.change_password'))

        app.db.execute("""
            UPDATE Accounts SET password = :password WHERE account_id = :id
        """, password=generate_password_hash(form.new_password.data), id=current_user.id)

        flash("Password updated successfully.")
        return redirect(url_for('users.profile'))

    return render_template('change_password.html', form=form)

@bp.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        app.db.execute("""
            UPDATE Accounts SET email = :email WHERE account_id = :id
        """, email=form.new_email.data, id=current_user.id)
        flash("Email updated!")
        return redirect(url_for('users.profile'))
    return render_template('change_email.html', form=form)

@bp.route('/balance', methods=['GET', 'POST'])
@login_required
def balance():
    form = BalanceForm()
    user_id = current_user.id

    if request.method == 'POST' and form.validate_on_submit():
        try:
            amount = float(form.amount.data)
            if amount < 0:
                flash("You can't add negative money.")
            else:
                app.db.execute("""
                    INSERT INTO Account_transactions (account_id, amount, transaction_type, created_at)
                    VALUES (:account_id, :amount, 'deposit', CURRENT_TIMESTAMP)
                """, account_id=user_id, amount=amount)

                flash(f"${amount:.2f} deposited to your account!")
                return redirect(url_for('users.balance'))
        except ValueError:
            flash("Please enter a valid number.")

    result = app.db.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM Account_transactions
        WHERE account_id = :account_id
    """, account_id=user_id)

    current_balance = result[0][0] if result else 0.0

    history = app.db.execute("""
        SELECT amount, transaction_type AS type, created_at AS time
        FROM Account_transactions
        WHERE account_id = :account_id
        ORDER BY created_at DESC
    """, account_id=user_id)

    return render_template(
        'balance.html',
        form=form,
        current_balance=current_balance,
        history=history
    )

@bp.route('/change_address', methods=['GET', 'POST'])
@login_required
def change_address():
    form = ChangeAddressForm()
    if form.validate_on_submit():
        app.db.execute("""
            UPDATE Accounts SET address = :address WHERE account_id = :id
        """, address=form.new_address.data, id=current_user.id)
        flash("Address updated!")
        return redirect(url_for('users.profile'))
    return render_template('change_address.html', form=form)