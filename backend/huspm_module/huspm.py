# huspm.py
import pandas as pd
import logging

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load data
purchases_df = pd.read_csv('C:/Users/sahit/pacecart/backend/data/purchases.csv')
browsing_history_df = pd.read_csv('C:/Users/sahit/pacecart/backend/data/browsing_history.csv')
products_df = pd.read_csv('C:/Users/sahit/pacecart/backend/data/products.csv')

# Fix browsing history column name typo
if 'timest' in browsing_history_df.columns:
    browsing_history_df.rename(columns={'timest': 'timestamp'}, inplace=True)

# Calculate product popularity
def calculate_product_popularity(purchases_df):
    product_popularity = purchases_df.groupby('product_id').size().reset_index(name='popularity')
    product_popularity['popularity'] = product_popularity['popularity'] / product_popularity['popularity'].max()
    logger.debug(f"Product popularity:\n{product_popularity.head()}")
    return product_popularity

# Calculate user preferences
def calculate_user_preference(user_id, purchases_df, browsing_history_df, products_df):
    user_purchases = purchases_df[purchases_df['user_id'] == user_id]
    user_browsing = browsing_history_df[browsing_history_df['user_id'] == user_id]

    user_purchases = user_purchases.merge(products_df[['product_id', 'category']], on='product_id', how='left')
    user_browsing = user_browsing.merge(products_df[['product_id', 'category']], on='product_id', how='left')

    category_purchase_counts = user_purchases.groupby('category').size().reset_index(name='category_purchase_preference')
    category_browse_counts = user_browsing.groupby('category').size().reset_index(name='category_browse_preference')

    # Normalize preferences
    category_purchase_counts['category_purchase_preference'] /= category_purchase_counts['category_purchase_preference'].max()
    category_browse_counts['category_browse_preference'] /= category_browse_counts['category_browse_preference'].max()

    category_preference = pd.merge(category_purchase_counts, category_browse_counts, on='category', how='outer')
    category_preference.fillna(0, inplace=True)

    logger.debug(f"User preferences (categories):\n{category_preference.head()}")
    return category_preference

# Calculate dynamic utility
def calculate_dynamic_utility(frequency, product_popularity, user_preference, seasonality_factor=1.0):
    utility = 1

    if frequency > 5:
        utility *= 1.8

    utility *= (product_popularity * 2)
    utility *= (user_preference * 1.5)
    utility *= seasonality_factor

    return utility

# Get top recommendations
def get_top_recommendations(user_id, purchases_df, browsing_history_df, products_df, product_popularity, top_n=5):
    user_purchases = purchases_df[purchases_df['user_id'] == user_id]
    user_browsing = browsing_history_df[browsing_history_df['user_id'] == user_id]

    purchased_products = user_purchases['product_id'].unique()
    browsed_products = user_browsing['product_id'].unique()

    interacted_products = set(purchased_products).union(set(browsed_products))

    recommendations = []

    category_preference = calculate_user_preference(user_id, purchases_df, browsing_history_df, products_df)

    for product_id in products_df['product_id']:
        if product_id in interacted_products:
            continue

        product_data = products_df[products_df['product_id'] == product_id].iloc[0]
        category = product_data['category']

        # Get category preference value
        category_pref_value = category_preference[
            category_preference['category'] == category
        ]['category_purchase_preference'].values[0] if category in category_preference['category'].values else 1.0

        frequency = len(user_purchases[user_purchases['product_id'] == product_id])

        # Assume seasonality factor = 1 for now
        seasonality_factor = 1.0

        # Product popularity
        product_popularity_score = product_popularity[
            product_popularity['product_id'] == product_id
        ]['popularity'].values[0] if product_id in product_popularity['product_id'].values else 0.5

        # Calculate utility
        utility_score = calculate_dynamic_utility(
            frequency,
            product_popularity_score,
            category_pref_value,
            seasonality_factor
        )

        recommendations.append((product_id, utility_score))

    # Sort recommendations
    recommendations.sort(key=lambda x: x[1], reverse=True)

    # Prepare full product info
    recommended_products = []
    for product_id, score in recommendations[:top_n]:
        product_info = products_df[products_df['product_id'] == product_id].iloc[0]
        recommended_products.append({
            'product_id': product_id,
            'product_name': product_info['product_name'] if 'product_name' in product_info else f"Product {product_id}",
            'category': product_info['category'] if 'category' in product_info else "Unknown",
            'score': score,
            'image_url': product_info['image_url'] if 'image_url' in product_info else None
        })

    return recommended_products

# Initialize on import
product_popularity = calculate_product_popularity(purchases_df)
