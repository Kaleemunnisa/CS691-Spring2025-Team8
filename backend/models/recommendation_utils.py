import pandas as pd
import logging
from db_connection import get_db_connection

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

# Collaborative Filtering: User-based or Item-based
def collaborative_filtering(user_id, purchases, products):
    purchases = ensure_dataframe(purchases, "purchases")
    products = ensure_dataframe(products, "products")
    logger.debug(f"Collaborative Filtering for user_id: {user_id}")
    logger.debug(f"Sample purchases:\n{purchases.head()}")
    
    user_purchases = purchases[purchases['user_id'] == user_id]['product_id'].unique()
    logger.debug(f"User purchases: {user_purchases}")
    
    other_users = purchases[purchases['product_id'].isin(user_purchases) & 
                            (purchases['user_id'] != user_id)]['user_id'].unique()
    
    other_purchases = purchases[purchases['user_id'].isin(other_users)]
    
    product_counts = other_purchases['product_id'].value_counts()
    
    recommendations = products[products['product_id'].isin(product_counts.index) & 
                              ~products['product_id'].isin(user_purchases)].copy()
    
    # Ensure rating is float
    if 'rating' in recommendations.columns:
        recommendations['rating'] = recommendations['rating'].astype(float)
    
    recommendations['score'] = (recommendations['product_id'].map(product_counts).fillna(0) * 
                               recommendations['rating']) / product_counts.max() if not product_counts.empty else 0
    
    # Normalize scores to 0-1
    if not recommendations.empty and recommendations['score'].max() > 0:
        recommendations['score'] = recommendations['score'] / recommendations['score'].max()
    
    recommendations['source'] = 'Collaborative Filtering'
    
    # Fallback if no recommendations
    if recommendations.empty:
        logger.warning(f"No collaborative filtering recommendations for user {user_id}. Using popular products.")
        popular_products = purchases['product_id'].value_counts().head(5).index
        recommendations = products[products['product_id'].isin(popular_products) & 
                                  ~products['product_id'].isin(user_purchases)].copy()
        recommendations['score'] = 0.5
        recommendations['source'] = 'Collaborative Filtering (Popular Fallback)'
    
    logger.debug(f"Collaborative recommendations: {len(recommendations)} items, scores: {recommendations['score'].tolist()}")
    return recommendations.sort_values(by='score', ascending=False)

# Content-Based Filtering: Based on product features (e.g., category)
def content_based_filtering(user_id, purchases, browsing_history, products):
    purchases = ensure_dataframe(purchases, "purchases")
    browsing_history = ensure_dataframe(browsing_history, "browsing_history")
    products = ensure_dataframe(products, "products")
    logger.debug(f"Content-Based Filtering for user_id: {user_id}")
    
    user_history = browsing_history[browsing_history['user_id'] == user_id]['product_id'].unique()
    logger.debug(f"User browsing history: {user_history}")
    
    user_products = products[products['product_id'].isin(user_history)]
    
    if not user_products.empty and 'category' in products.columns:
        recommendations = products[products['category'].isin(user_products['category']) & 
                                  ~products['product_id'].isin(user_history)].copy()
        
        # Ensure rating is float
        if 'rating' in user_products.columns:
            user_products['rating'] = user_products['rating'].astype(float)
        if 'rating' in recommendations.columns:
            recommendations['rating'] = recommendations['rating'].astype(float)
        
        recommendations['score'] = recommendations['rating'] / 5.0  # Simplified scoring
        
        # Normalize scores to 0-1
        if recommendations['score'].max() > 0:
            recommendations['score'] = recommendations['score'] / recommendations['score'].max()
    else:
        recommendations = pd.DataFrame(columns=['product_id', 'product_name', 'price', 'rating', 'clicks', 'stock', 'score', 'source'])
        logger.debug("No content-based recommendations.")
    
    recommendations['source'] = 'Content-Based Filtering'
    logger.debug(f"Content-based recommendations: {len(recommendations)} items, scores: {recommendations['score'].tolist() if not recommendations.empty else []}")
    return recommendations