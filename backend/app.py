from flask import Flask, request, jsonify, render_template
import mysql.connector
import pandas as pd
from decimal import Decimal
from models.hybrid_model import hybrid_recommendation
from models.recommendation_utils import calculate_product_popularity
from db_connection import get_db_connection

# Initialize the Flask application
app = Flask(__name__)

# Cache for product popularity
PRODUCT_POPULARITY_CACHE = None

# Database query functions
def get_products():
    connection = get_db_connection()
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        return products
    finally:
        cursor.close()
        connection.close()

def get_purchases():
    connection = get_db_connection()
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM purchases")
        purchases = cursor.fetchall()
        return purchases
    finally:
        cursor.close()
        connection.close()

def get_browsing_history():
    connection = get_db_connection()
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM browsing_history")
        browsing_history = cursor.fetchall()
        return browsing_history
    finally:
        cursor.close()
        connection.close()

# Home page route to render product list
@app.route('/')
def home():
    # Load products from MySQL
    products = get_products()
    
    # Render home page with products
    return render_template('home.html', products=products)

# Recommendations page route
@app.route('/recommendations/<int:user_id>', methods=['GET'])
def recommendations(user_id):
    global PRODUCT_POPULARITY_CACHE
    
    # Load data from MySQL
    products = get_products()
    purchases = get_purchases()
    browsing_history = get_browsing_history()
    
    # Convert lists to DataFrames and handle Decimal types
    products_df = pd.DataFrame(products)
    purchases_df = pd.DataFrame(purchases)
    browsing_history_df = pd.DataFrame(browsing_history)
    
    # Convert Decimal columns to float for all DataFrames
    for df in [products_df, purchases_df, browsing_history_df]:
        for col in df.select_dtypes(include=[object]).columns:
            if df[col].apply(lambda x: isinstance(x, Decimal)).any():
                df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
    
    # Cache product popularity
    if PRODUCT_POPULARITY_CACHE is None:
        PRODUCT_POPULARITY_CACHE = calculate_product_popularity(purchases_df)
    
    # Get top N recommendations using hybrid model
    top_n = 5
    recommendations = hybrid_recommendation(user_id, purchases_df, browsing_history_df, products_df, PRODUCT_POPULARITY_CACHE, top_n)
    
    # Convert recommendations to JSON-serializable format
    recommendations_json = recommendations.to_dict(orient='records')
    
    # Render recommendations page with the recommendations
    return render_template('recommendations.html', recommendations=recommendations_json)

# Product details page route
@app.route('/product/<int:product_id>', methods=['GET'])
def product_details(product_id):
    # Load product details from MySQL
    products = get_products()
    
    # Find the product details
    product = next((p for p in products if p['product_id'] == product_id), None)
    
    # Render product details page
    if product:
        return render_template('product_details.html', product=product)
    else:
        return jsonify({"error": "Product not found"}), 404

# Cart route to simulate adding to cart
@app.route('/cart', methods=['POST'])
def add_to_cart():
    # Simulate adding a product to the cart
    product_id = request.form['product_id']
    
    # Here, you would implement logic to save to a session or database
    return jsonify({"message": f"Product {product_id} added to cart"}), 200

# Login route (can be expanded for authentication)
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Handle user login here (You can implement user authentication logic)
    if request.method == 'POST':
        user_id = request.form['user_id']  # Example login by user_id
        return jsonify({"message": f"User {user_id} logged in"}), 200
    
    return jsonify({"message": "Login page (POST method required)"}), 200

# Main function to run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
