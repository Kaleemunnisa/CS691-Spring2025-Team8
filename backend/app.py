from flask import Flask, request, render_template, redirect, url_for, flash, session , jsonify
import mysql.connector
from datetime import datetime
from models.hybrid_model import hybrid_recommendation
from models.recommendation_utils import calculate_product_popularity
from db_connection import get_db_connection
from collections import defaultdict
from flask_login import login_required
import pandas as pd

app = Flask(__name__)
app.secret_key = "a75bf4b28004caa48b9dbd40fe2642d1"
def get_products(order_by=None, category=None, query=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT * FROM products WHERE 1=1"
    params = []

    if category:
        sql += " AND category = %s"
        params.append(category)

    if query:
        sql += " AND product_name LIKE %s"
        params.append(f"%{query}%")

    if order_by:
        sql += f" ORDER BY {order_by}"

    cursor.execute(sql, params)
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return products
def get_trending_products(limit_per_category=2):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    categories = ["Fruits", "Vegetables", "Dairy", "Snacks", "Beverages", "Bakery", "Staples"]
    trending = []

    for category in categories:
        cursor.execute("""
            SELECT * FROM products
            WHERE category = %s
            ORDER BY clicks DESC
            LIMIT %s
        """, (category, limit_per_category))
        trending.extend(cursor.fetchall())

    cursor.close()
    conn.close()
    return trending


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
    products = get_trending_products(limit_per_category=2)
    cart_count = get_cart_count(user_id)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ✅ Improved logic: Get latest viewed product_ids in order, without duplicates
    cursor.execute("""
        SELECT product_id 
        FROM browsing_history 
        WHERE user_id = %s AND action = 'view' 
        ORDER BY timestamp DESC
        LIMIT 20
    """, (user_id,))

    seen = set()
    viewed_ids = []
    for row in cursor.fetchall():
        pid = row['product_id']
        if pid not in seen:
            seen.add(pid)
            viewed_ids.append(pid)
        if len(viewed_ids) == 5:
            break

    all_products = get_products()
    recently_viewed = [p for p in all_products if p['product_id'] in viewed_ids]
    recently_viewed = sorted(recently_viewed, key=lambda x: viewed_ids.index(x['product_id']))

    cursor.close()
    conn.close()

    return render_template(
        'home.html',
        products=products,
        recently_viewed=recently_viewed,
        username=username,
        cart_count=cart_count
    )

@app.route('/search')
def search():
    query = request.args.get('query')
    products = get_products(query=query)
    
    user_id = session.get('user_id')
    username = session.get('username')
    cart_count = get_cart_count(user_id)

    recently_viewed = []
    if user_id:
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

    return render_template('home.html',
                           products=products,
                           recommendations=[],
                           username=username,
                           cart_count=cart_count,
                           recently_viewed=recently_viewed)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    user_id = session.get('user_id')

    if not product_id or not user_id:
        return jsonify({'message': 'Item added to cart (session not active).'})  # No error, just fallback

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT quantity FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("UPDATE cart SET quantity = quantity + 1 WHERE user_id = %s AND product_id = %s", (user_id, product_id))
    else:
        cursor.execute("INSERT INTO cart (user_id, product_id, quantity, added_date) VALUES (%s, %s, %s, NOW())",
                       (user_id, product_id, 1))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Item added to cart ✅'})


from models.hybrid_model import load_data  # Make sure this is imported

@app.route('/recommend_by_category/<category>/<int:user_id>')
def recommend_by_category(category, user_id):
    # ✅ Use the correct function
    purchases_df, browsing_df, products_df = load_data()

    # Filter only products in the given category
    filtered_products = products_df[products_df['category'] == category]

    # Optional: Handle Decimal fields if necessary
    for df in [filtered_products, purchases_df, browsing_df]:
        for col in df.select_dtypes(include=['object']).columns:
            try:
                df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
            except:
                continue

    # Generate or reuse product popularity cache
    global PRODUCT_POPULARITY_CACHE
    if 'PRODUCT_POPULARITY_CACHE' not in globals() or PRODUCT_POPULARITY_CACHE is None:
        PRODUCT_POPULARITY_CACHE = calculate_product_popularity(purchases_df)

    # Run hybrid recommendations
    recs = hybrid_recommendation(user_id, purchases_df, browsing_df, filtered_products, PRODUCT_POPULARITY_CACHE, top_n=8)

    return render_template(
        'recommendations.html',
        recommendations=recs.to_dict(orient='records'),
        title=f"Top {category} Picks for You"
    )


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

@app.route('/recommendations')
def recommendations():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view recommendations.')
        return redirect(url_for('login'))

    from models.hybrid_model import hybrid_recommendation, load_data
    from models.recommendation_utils import calculate_product_popularity

    # Load live data
    purchases_df, browsing_df, products_df = load_data()
    product_popularity = calculate_product_popularity(purchases_df)

    # Run hybrid model (HUSPM → CF → CBF)
    recommendations = hybrid_recommendation(user_id, purchases_df, browsing_df, products_df, product_popularity, top_n=9)
    recommendations = recommendations.to_dict(orient='records')  # Convert to dict for HTML template

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
        elif 'product_id' in request.form:
            product_id = request.form['product_id']
            cursor.execute("SELECT quantity FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
            existing = cursor.fetchone()
            if existing:
             cursor.execute("UPDATE cart SET quantity = quantity + 1 WHERE user_id = %s AND product_id = %s",
                       (user_id, product_id))
            else:
             cursor.execute("INSERT INTO cart (user_id, product_id, quantity, added_date) VALUES (%s, %s, %s, NOW())",
                       (user_id, product_id, 1))
            conn.commit()
            flash(('success', 'Item added to cart!'))


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

@app.route('/product/<int:product_id>')
def product_details(product_id):
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Increment click count
    cursor.execute("UPDATE products SET clicks = clicks + 1 WHERE product_id = %s", (product_id,))
    conn.commit()

    # 2. Get product details
    cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()

    # 3. Save to browsing history
    if user_id:
        cursor.execute("""
            INSERT INTO browsing_history (user_id, product_id, timestamp, action)
            VALUES (%s, %s, NOW(), 'view')
        """, (user_id, product_id))
        conn.commit()

    # 4. Fetch all submitted reviews + username
    cursor.execute("""
        SELECT r.rating, r.review, u.username
        FROM product_ratings r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.product_id = %s AND r.review IS NOT NULL
        ORDER BY r.rating DESC, r.rating DESC
    """, (product_id,))
    reviews = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('product_details.html', product=product, reviews=reviews)




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
    review = request.form.get('review', '').strip()  # Get optional review text

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO product_ratings (user_id, product_id, rating, review)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE rating = %s, review = %s
    """, (user_id, product_id, rating, review, rating, review))
    
    conn.commit()
    cursor.close()
    conn.close()

    flash(('success', 'Review and rating submitted!'))
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
        new_password = request.form.get('password')

        if new_password:
            cursor.execute("""
                UPDATE users SET username = %s, email = %s, password = %s WHERE user_id = %s
            """, (username, email, new_password, user_id))
        else:
            cursor.execute("""
                UPDATE users SET username = %s, email = %s WHERE user_id = %s
            """, (username, email, user_id))

        conn.commit()
        flash(('success', 'Profile updated successfully.'))

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