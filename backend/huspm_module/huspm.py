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
        products_query = "SELECT * FROM products"
        products_df = pd.read_sql(products_query, connection)

        purchases_query = "SELECT * FROM purchases"
        purchases_df = pd.read_sql(purchases_query, connection)

        browsing_history_query = "SELECT * FROM browsing_history"
        browsing_history_df = pd.read_sql(browsing_history_query, connection)

        logger.debug("Data loaded successfully.")
        return purchases_df, browsing_history_df, products_df
    finally:
        connection.close()

# Fix browsing history column typo
def fix_browsing_history_columns(browsing_history_df):
    if 'timest' in browsing_history_df.columns:
        browsing_history_df.rename(columns={'timest': 'timestamp'}, inplace=True)
    return browsing_history_df

# Ensure DataFrame type
def ensure_dataframe(df, df_name="DataFrame"):
    if isinstance(df, list):
        logger.warning(f"{df_name} is a list. Converting to DataFrame.")
        df = pd.DataFrame(df)
    elif not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected {df_name} to be a pandas DataFrame, but got {type(df)}.")
    return df

# Calculate product popularity
def calculate_product_popularity(purchases_df):
    purchases_df = ensure_dataframe(purchases_df, "purchases_df")
    if purchases_df.empty:
        logger.warning("purchases_df is empty. Returning default product_popularity.")
        return pd.DataFrame({'product_id': [], 'popularity': []})
    product_popularity = purchases_df.groupby('product_id').size().reset_index(name='popularity')
    product_popularity['popularity'] = product_popularity['popularity'] / product_popularity['popularity'].max()
    logger.debug(f"Product popularity: {len(product_popularity)} items\n{product_popularity.head()}")
    return product_popularity

# Calculate user preference
def calculate_user_preference(user_id, purchases_df, browsing_history_df, products_df):
    purchases_df = ensure_dataframe(purchases_df, "purchases_df")
    browsing_history_df = ensure_dataframe(browsing_history_df, "browsing_history_df")
    products_df = ensure_dataframe(products_df, "products_df")
    
    user_purchases = purchases_df[purchases_df['user_id'] == user_id]
    user_browsing = browsing_history_df[browsing_history_df['user_id'] == user_id]

    logger.debug(f"User {user_id} purchases: {len(user_purchases)} items")
    logger.debug(f"User {user_id} browsing history: {len(user_browsing)} items")

    # Merge category info from products_df
    user_purchases = user_purchases.merge(products_df[['product_id', 'category']], on='product_id', how='left')
    user_browsing = user_browsing.merge(products_df[['product_id', 'category']], on='product_id', how='left')

    # Calculate preference based on category
    category_purchase_counts = user_purchases.groupby('category').size().reset_index(name='category_purchase_preference')
    category_browse_counts = user_browsing.groupby('category').size().reset_index(name='category_browse_preference')

    if not category_purchase_counts.empty:
        category_purchase_counts['category_purchase_preference'] /= category_purchase_counts['category_purchase_preference'].max()
    if not category_browse_counts.empty:
        category_browse_counts['category_browse_preference'] /= category_browse_counts['category_browse_preference'].max()

    category_preference = pd.merge(category_purchase_counts, category_browse_counts, on='category', how='outer')
    category_preference.fillna(0, inplace=True)

    logger.debug(f"User {user_id} preferences: {len(category_preference)} categories\n{category_preference.head()}")
    return category_preference

# Calculate dynamic utility
def calculate_dynamic_utility(frequency, product_popularity, user_preference, seasonality_factor, click_factor):
    utility = 1.0

    if frequency > 5:
        utility *= 2.5  # High weight for frequent purchases

    utility *= (product_popularity * 4.0)  # High weight for popularity
    utility *= (user_preference * 3.0)  # High weight for user preference
    utility *= seasonality_factor  # Dynamic seasonality
    utility *= (1 + click_factor)  # Boost for recent clicks

    return utility

# Get top recommendations
def get_top_recommendations(user_id, purchases_df, browsing_history_df, products_df, product_popularity, top_n=5):
    if not isinstance(product_popularity, pd.DataFrame):
        raise TypeError(f"product_popularity must be a DataFrame, got {type(product_popularity)}")
    
    purchases_df = ensure_dataframe(purchases_df, "purchases_df")
    browsing_history_df = ensure_dataframe(browsing_history_df, "browsing_history_df")
    products_df = ensure_dataframe(products_df, "products_df")

    logger.debug(f"Input data sizes: purchases={len(purchases_df)}, browsing_history={len(browsing_history_df)}, products={len(products_df)}")

    user_purchases = purchases_df[purchases_df['user_id'] == user_id]
    user_browsing = browsing_history_df[browsing_history_df['user_id'] == user_id]

    purchased_products = user_purchases['product_id'].unique()
    browsed_products = user_browsing['product_id'].unique()

    interacted_products = set(purchased_products).union(set(browsed_products))
    logger.debug(f"User {user_id} interacted products: {len(interacted_products)}")

    recommendations = []

    category_preference = calculate_user_preference(user_id, purchases_df, browsing_history_df, products_df)

    # Simulate seasonality (e.g., higher utility in certain months)
    current_month = datetime.now().month
    seasonality_factor = 1.2 if current_month in [11, 12] else 1.0  # Boost for holiday season

    # Calculate click factor based on recent activity
    click_counts = products_df.groupby('product_id')['clicks'].sum().reset_index()
    max_clicks = click_counts['clicks'].max() if click_counts['clicks'].max() > 0 else 1

    for product_id in products_df['product_id']:
        if product_id in interacted_products:
            continue

        product_data = products_df[products_df['product_id'] == product_id]
        if product_data.empty:
            continue
        
        product_row = product_data.iloc[0]
        category = product_row['category'] if 'category' in product_row else "Unknown"

        # Get category preference
        category_pref_value = category_preference[category_preference['category'] == category]['category_purchase_preference'].values[0] \
            if category in category_preference['category'].values else 1.0

        frequency = len(user_purchases[user_purchases['product_id'] == product_id])

        # Get product popularity score
        matching_row = product_popularity[product_popularity['product_id'] == product_id]
        product_popularity_score = matching_row.iloc[0]['popularity'] if not matching_row.empty else 0.5

        # Get click factor
        click_row = click_counts[click_counts['product_id'] == product_id]
        click_factor = click_row.iloc[0]['clicks'] / max_clicks if not click_row.empty else 0.0

        utility_score = calculate_dynamic_utility(frequency, product_popularity_score, category_pref_value, seasonality_factor, click_factor)

        recommendations.append((product_id, utility_score))

    # Deep learning score refinement
    if recommendations:
        product_ids = [pid for pid, _ in recommendations]
        dl_scores = predict_utility_scores(user_id, product_ids, products_df)
        recommendations = [(pid, score * (1 + dl_score)) for (pid, score), dl_score in zip(recommendations, dl_scores)]

    recommendations.sort(key=lambda x: x[1], reverse=True)

    # Normalize scores to 0-1
    if recommendations:
        max_score = max(score for _, score in recommendations)
        if max_score > 0:
            recommendations = [(pid, score / max_score) for pid, score in recommendations]

    recommended_products = []
    for product_id, score in recommendations[:top_n]:
        product_info_row = products_df[products_df['product_id'] == product_id]

        if not product_info_row.empty:
            product_info = product_info_row.iloc[0]
            product_name = product_info['product_name'] if 'product_name' in product_info else f"Product {product_id}"
            category = product_info['category'] if 'category' in product_info else "Unknown"
            image_url = product_info['image_url'] if 'image_url' in product_info else None
            price = float(product_info['price']) if 'price' in product_info else 0.0
            rating = float(product_info['rating']) if 'rating' in product_info else 0.0
            clicks = float(product_info['clicks']) if 'clicks' in product_info else 0.0
            stock = float(product_info['stock']) if 'stock' in product_info else 0.0
        else:
            product_name = f"Product {product_id}"
            category = "Unknown"
            image_url = None
            price = 0.0
            rating = 0.0
            clicks = 0.0
            stock = 0.0

        recommended_products.append({
            'product_id': product_id,
            'product_name': product_name,
            'category': category,
            'price': price,
            'rating': rating,
            'clicks': clicks,
            'stock': stock,
            'score': score,
            'image_url': image_url,
            'source': 'HUSPM'
        })

    # Fallback to popular products if no recommendations
    if not recommended_products:
        logger.warning(f"No HUSPM recommendations for user {user_id}. Using popular products.")
        popular_products = product_popularity['product_id'].head(top_n).tolist()
        for product_id in popular_products:
            if product_id in interacted_products:
                continue
            product_info_row = products_df[products_df['product_id'] == product_id]
            if not product_info_row.empty:
                product_info = product_info_row.iloc[0]
                product_name = product_info['product_name'] if 'product_name' in product_info else f"Product {product_id}"
                category = product_info['category'] if 'category' in product_info else "Unknown"
                image_url = product_info['image_url'] if 'image_url' in product_info else None
                price = float(product_info['price']) if 'price' in product_info else 0.0
                rating = float(product_info['rating']) if 'rating' in product_info else 0.0
                clicks = float(product_info['clicks']) if 'clicks' in product_info else 0.0
                stock = float(product_info['stock']) if 'stock' in product_info else 0.0
                recommended_products.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'category': category,
                    'price': price,
                    'rating': rating,
                    'clicks': clicks,
                    'stock': stock,
                    'score': 0.5,
                    'image_url': image_url,
                    'source': 'HUSPM (Popular Fallback)'
                })
        recommended_products = recommended_products[:top_n]

    logger.debug(f"HUSPM recommendations: {len(recommended_products)} items, scores: {[r['score'] for r in recommended_products]}")
    return recommended_products