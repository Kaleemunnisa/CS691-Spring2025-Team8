import pandas as pd
import logging
import numpy as np
from datetime import datetime
from db_connection import get_db_connection
from models.deep_learning_model import predict_utility_scores

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load data from MySQL
def load_data():
    logger.debug("Loading data from MySQL...")
    connection = get_db_connection()

    if connection is None:
        logger.error("Database connection failed. Cannot load data.")
        return None, None, None

    try:
        products_df = pd.read_sql("SELECT * FROM products", connection)
        purchases_df = pd.read_sql("SELECT * FROM purchases", connection)
        browsing_df = pd.read_sql("SELECT * FROM browsing_history", connection)
        logger.debug("Data loaded successfully.")
        return purchases_df, browsing_df, products_df
    finally:
        connection.close()

# Ensure DataFrame type
def ensure_dataframe(df, df_name="DataFrame"):
    if isinstance(df, list):
        logger.warning(f"{df_name} is a list. Converting to DataFrame.")
        df = pd.DataFrame(df)
    elif not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected {df_name} to be a pandas DataFrame, but got {type(df)}.")
    return df

# Product popularity
def calculate_product_popularity(purchases_df):
    purchases_df = ensure_dataframe(purchases_df, "purchases_df")
    if purchases_df.empty:
        return pd.DataFrame({'product_id': [], 'popularity': []})
    counts = purchases_df.groupby('product_id').size().reset_index(name='popularity')
    counts['popularity'] /= counts['popularity'].max()
    return counts

# User preference
def calculate_user_preference(user_id, purchases_df, browsing_df, products_df):
    user_purchases = purchases_df[purchases_df['user_id'] == user_id]
    user_browsing = browsing_df[browsing_df['user_id'] == user_id]

    user_purchases = user_purchases.merge(products_df[['product_id', 'category']], on='product_id', how='left')
    user_browsing = user_browsing.merge(products_df[['product_id', 'category']], on='product_id', how='left')

    purchase_pref = user_purchases.groupby('category').size().reset_index(name='category_purchase_preference')
    browse_pref = user_browsing.groupby('category').size().reset_index(name='category_browse_preference')

    if not purchase_pref.empty:
        purchase_pref['category_purchase_preference'] /= purchase_pref['category_purchase_preference'].max()
    if not browse_pref.empty:
        browse_pref['category_browse_preference'] /= browse_pref['category_browse_preference'].max()

    preference = pd.merge(purchase_pref, browse_pref, on='category', how='outer').fillna(0)
    return preference

# Dynamic utility function
def calculate_dynamic_utility(frequency, popularity, preference, seasonality, click_factor):
    utility = 1.0
    if frequency > 5:
        utility *= 2.5
    utility *= popularity * 4.0
    utility *= preference * 3.0
    utility *= seasonality
    utility *= (1 + click_factor)
    return utility

# Get top recommendations
def get_top_recommendations(user_id, purchases_df, browsing_df, products_df, popularity_df, top_n=5):
    user_purchases = purchases_df[purchases_df['user_id'] == user_id]
    user_browsing = browsing_df[browsing_df['user_id'] == user_id]

    interacted_products = set(user_purchases['product_id']).union(set(user_browsing['product_id']))
    category_pref = calculate_user_preference(user_id, purchases_df, browsing_df, products_df)

    current_month = datetime.now().month
    seasonality_factor = 1.2 if current_month in [11, 12] else 1.0
    click_counts = products_df.groupby('product_id')['clicks'].sum().reset_index()
    max_clicks = click_counts['clicks'].max() or 1

    recommendations = []

    for _, row in products_df.iterrows():
        product_id = row['product_id']
        product_name = row['product_name']

        user_product_purchases = user_purchases[user_purchases['product_id'] == product_id]
        frequency = len(user_product_purchases)

        skip = False
        if not user_product_purchases.empty:
            last_purchase = user_product_purchases['purchase_date'].max()
            days_since = (datetime.now().date() - last_purchase).days
            if days_since < 7 and frequency < 3:
                skip = True

        if skip:
            continue

        category = row['category']
        preference = category_pref[category_pref['category'] == category]['category_purchase_preference'].values[0] if category in category_pref['category'].values else 1.0
        pop_score = popularity_df[popularity_df['product_id'] == product_id]['popularity'].values[0] if product_id in popularity_df['product_id'].values else 0.5
        click_factor = click_counts[click_counts['product_id'] == product_id]['clicks'].values[0] / max_clicks if product_id in click_counts['product_id'].values else 0.0

        utility = calculate_dynamic_utility(frequency, pop_score, preference, seasonality_factor, click_factor)
        recommendations.append((product_id, utility))

    if recommendations:
        product_ids = [pid for pid, _ in recommendations]
        dl_scores = predict_utility_scores(user_id, product_ids, products_df)
        recommendations = [(pid, score * (1 + dl_score)) for (pid, score), dl_score in zip(recommendations, dl_scores)]

    recommendations.sort(key=lambda x: x[1], reverse=True)

    max_score = max(score for _, score in recommendations) if recommendations else 1
    recommendations = [(pid, score / max_score) for pid, score in recommendations if max_score > 0]

    results = []
    for product_id, score in recommendations[:top_n]:
        info = products_df[products_df['product_id'] == product_id].iloc[0]
        results.append({
            'product_id': product_id,
            'product_name': info.get('product_name', f"Product {product_id}"),
            'category': info.get('category', 'Unknown'),
            'price': float(info.get('price', 0)),
            'rating': float(info.get('rating', 0)),
            'clicks': float(info.get('clicks', 0)),
            'stock': float(info.get('stock', 0)),
            'score': score,
            'image_url': info.get('image_url', None),
            'source': 'HUSPM'
        })

    return results


