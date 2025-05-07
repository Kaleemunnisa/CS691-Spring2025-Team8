from flask import Flask, request, render_template, redirect, url_for, flash, session
import mysql.connector
from datetime import datetime
from models.hybrid_model import hybrid_recommendation
from models.recommendation_utils import calculate_product_popularity
from db_connection import get_db_connection
from collections import defaultdict


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def get_products(order_by=None, category=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM products"
    if category:
        query += f" WHERE category = %s"
        if order_by:
            query += f" ORDER BY {order_by}"
        cursor.execute(query, (category,))
    else:
        if order_by:
            query += f" ORDER BY {order_by}"
        cursor.execute(query)
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return products

def get_cart_count(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(quantity) FROM cart WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result[0] else 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    user_id = session.get('user_id')
    username = session.get('username')
    products = get_products()
    cart_count = get_cart_count(user_id)

    recently_viewed = []
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT product_id FROM browsing_history
        WHERE user_id = %s AND action = 'view'
        GROUP BY product_id ORDER BY MAX(timestamp) DESC LIMIT 5
    """, (user_id,))
    viewed_ids = [row['product_id'] for row in cursor.fetchall()]
    all_products = get_products()
    recently_viewed = [p for p in all_products if p['product_id'] in viewed_ids]
    recently_viewed = sorted(recently_viewed, key=lambda x: viewed_ids.index(x['product_id']))
    cursor.close()
    conn.close()

    return render_template('home.html', products=products, recently_viewed=recently_viewed, username=username, cart_count=cart_count)

@app.route('/recommend_by_category/<category>/<int:user_id>')
def recommend_by_category(category, user_id):
    products = get_products(category=category)
    return render_template('category.html', products=products, category_name=category)

@app.route('/category/<name>')
def filter_category(name):
    products = get_products(category=name)
    return render_template('category.html', products=products, category_name=name)

@app.route('/all_products')
def all_products():
    page = request.args.get('page', 1, type=int)
    limit = 48
    offset = (page - 1) * limit

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as total FROM products")
    total = cursor.fetchone()['total']
    total_pages = (total + limit - 1) // limit

    cursor.execute("SELECT * FROM products ORDER BY clicks DESC LIMIT %s OFFSET %s", (limit, offset))
    products = cursor.fetchall()

    viewed_ids = []
    if 'user_id' in session:
        cursor.execute("SELECT product_id FROM browsing_history WHERE user_id = %s", (session['user_id'],))
        viewed_ids = [row['product_id'] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return render_template('all_products.html', products=products, current_page=page, total_pages=total_pages, viewed_product_ids=viewed_ids)

@app.route('/recommendations/<int:user_id>')
def recommendations(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.*, p.product_name, p.category, p.image_url, p.price, p.rating
        FROM recommendations r
        JOIN products p ON r.product_id = p.product_id
        WHERE r.user_id = %s
        ORDER BY r.recommendation_score DESC
    """, (user_id,))
    recommendations = cursor.fetchall()

    # Ensure fallback source field is present for HTML display
    for rec in recommendations:
        if 'source' not in rec or not rec['source']:
            rec['source'] = 'HUSPM (DB)'
        if 'recommendation_score' not in rec or rec['recommendation_score'] is None:
            rec['recommendation_score'] = 0.0

    cursor.close()
    conn.close()
    return render_template('recommendations.html', recommendations=recommendations)

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        if 'remove_id' in request.form:
            cursor.execute("DELETE FROM cart WHERE user_id = %s AND product_id = %s", (user_id, request.form['remove_id']))
            conn.commit()
            flash(('success', 'Item removed from cart.'))

        elif 'update_id' in request.form:
            cursor.execute("UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s", (
                request.form['quantity'], user_id, request.form['update_id']))
            conn.commit()
            flash(('success', 'Quantity updated.'))

        elif 'checkout' in request.form:
            cursor.execute("""
                SELECT c.product_id, c.quantity, p.price
                FROM cart c
                JOIN products p ON c.product_id = p.product_id
                WHERE c.user_id = %s
            """, (user_id,))
            items = cursor.fetchall()

            for item in items:
                total_price = item['quantity'] * item['price']
                cursor.execute(
                    "INSERT INTO purchases (user_id, product_id, purchase_date, quantity, total_price) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, item['product_id'], datetime.now(), item['quantity'], total_price)
                )

            cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
            conn.commit()
            flash(('success', 'Payment successful! Order placed.'))
            return redirect(url_for('order_history'))

    # Always show current cart contents
    cursor.execute("""
        SELECT c.product_id, c.quantity, p.product_name, p.image_url, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = %s
    """, (user_id,))
    cart_items = cursor.fetchall()
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)

    cursor.close()
    conn.close()

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)


@app.route('/order-history')
def order_history():
    user_id = session.get('user_id')
    if not user_id:
        flash(('error', 'You must be logged in to view orders.'))
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.product_name, pr.product_id, pr.quantity, pr.total_price,
               pr.purchase_date, p.image_url
        FROM purchases pr
        JOIN products p ON pr.product_id = p.product_id
        WHERE pr.user_id = %s
        ORDER BY pr.purchase_date DESC
    """, (user_id,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    # Group by date (e.g., '2025-05-06')
    orders_by_date = defaultdict(list)
    for row in results:
        date_str = row['purchase_date'].strftime('%B %d, %Y')  # or use .date() for '2025-05-06'
        orders_by_date[date_str].append(row)

    return render_template('order_history.html', orders_by_date=orders_by_date)



@app.route('/rate_product', methods=['POST'])
def rate_product():
    user_id = request.form['user_id']
    product_id = request.form['product_id']
    rating = request.form['rating']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO product_ratings (user_id, product_id, rating)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE rating = %s
    """, (user_id, product_id, rating, rating))
    conn.commit()
    cursor.close()
    conn.close()

    flash('success', 'Rating submitted!')
    return redirect(url_for('order_history'))


@app.route('/sort/<criteria>')
def sort_products(criteria):
    sort_map = {
        'price_low': 'price ASC',
        'price_high': 'price DESC',
        'rating': 'rating DESC',
        'clicks': 'clicks DESC'
    }
    order = sort_map.get(criteria)
    if not order:
        return redirect(url_for('home'))

    products = get_products(order_by=order)
    user_id = session.get('user_id')
    username = session.get('username')
    cart_count = get_cart_count(user_id)

    # Recently viewed is optional here
    return render_template('home.html', products=products, recently_viewed=[], username=username, cart_count=cart_count)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        cursor.execute("UPDATE users SET username = %s, email = %s WHERE user_id = %s", (username, email, user_id))
        conn.commit()
        flash(('success', 'Profile updated successfully'))
    cursor.execute("SELECT username, email, registration_date FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.fetchall()
        cursor.close()
        conn.close()
        if user:
            session['username'] = user['username']
            session['user_id'] = user['user_id']
            return redirect(url_for('home'))
        else:
            flash('error', 'Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']
        if password != confirm:
            flash(('error', 'Passwords do not match'))
            return render_template('signup.html')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        if cursor.fetchone():
            flash('error', 'Username or email already exists')
            return render_template('signup.html')
        cursor.execute("INSERT INTO users (username, email, password, registration_date) VALUES (%s, %s, %s, %s)", (username, email, password, datetime.now()))
        conn.commit()
        cursor.close()
        conn.close()
        flash('success', 'Account created. Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
