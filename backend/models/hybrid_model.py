import mysql.connector
import pandas as pd
import logging
from huspm_module.huspm import get_top_recommendations as huspm_recommendations, calculate_product_popularity, ensure_dataframe
from models.recommendation_utils import collaborative_filtering, content_based_filtering
from db_connection import get_db_connection

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


# Hybrid Recommendation: Combine results from HUSPM, Collaborative Filtering, and Content-Based Filtering
def hybrid_recommendation(user_id, purchases, browsing_history, products, product_popularity, top_n=5):
    logger.debug(f"Hybrid Recommendation for user_id: {user_id}")
    
    # Ensure inputs are DataFrames
    purchases = ensure_dataframe(purchases, "purchases")
    browsing_history = ensure_dataframe(browsing_history, "browsing_history")
    products = ensure_dataframe(products, "products")
    
    # Step 1: Get HUSPM-based recommendations
    huspm_recs = huspm_recommendations(user_id, purchases, browsing_history, products, product_popularity, top_n)
    huspm_recs = pd.DataFrame(huspm_recs)
    if not huspm_recs.empty:
        huspm_recs['score'] = huspm_recs['score'] * 1.3  # Boost HUSPM scores
    huspm_product_ids = huspm_recs['product_id'].tolist()
    logger.debug(f"HUSPM recommendations: {len(huspm_recs)} items, product_ids: {huspm_product_ids}, scores: {huspm_recs['score'].tolist() if not huspm_recs.empty else []}")
    
    # Step 2: Get Collaborative Filtering recommendations
    collab_recs = collaborative_filtering(user_id, purchases, products)
    collab_product_ids = collab_recs['product_id'].tolist()
    logger.debug(f"Collaborative filtering recommendations: {len(collab_recs)} items, product_ids: {collab_product_ids}, scores: {collab_recs['score'].tolist()}")
    
    # Step 3: Get Content-Based Filtering recommendations
    content_recs = content_based_filtering(user_id, purchases, browsing_history, products)
    content_product_ids = content_recs['product_id'].tolist()
    logger.debug(f"Content-based filtering recommendations: {len(content_recs)} items, product_ids: {content_product_ids}, scores: {content_recs['score'].tolist()}")
    
    # Step 4: Combine recommendations
    required_columns = ['product_id', 'product_name', 'score', 'source', 'category', 'price', 'rating', 'clicks', 'stock']
    for recs, name in [(huspm_recs, 'HUSPM'), (collab_recs, 'Collaborative'), (content_recs, 'Content-Based')]:
        missing = [col for col in required_columns if col not in recs.columns]
        if missing:
            logger.error(f"{name} recommendations missing columns: {missing}")
    
    all_recommendations = pd.concat([huspm_recs, collab_recs, content_recs], ignore_index=True)
    
    # Step 5: Remove duplicates and select top_n
    if not all_recommendations.empty:
        all_recommendations = all_recommendations.sort_values(by='score', ascending=False) \
                                               .drop_duplicates(subset=['product_id', 'product_name'], keep='first')
        
        # Ensure HUSPM is represented
        final_recommendations = []
        huspm_count = min(len(huspm_recs), (top_n + 1) // 2)  # Reserve at least half for HUSPM
        if huspm_count > 0:
            final_recommendations.append(huspm_recs.head(huspm_count))
        
        remaining_n = top_n - huspm_count
        if remaining_n > 0:
            other_recs = all_recommendations[~all_recommendations['product_id'].isin(huspm_recs['product_id'])]
            final_recommendations.append(other_recs.head(remaining_n))
        
        final_recommendations = pd.concat(final_recommendations, ignore_index=True).head(top_n)
        
        # Calculate diversity
        diversity = len(final_recommendations['category'].unique()) / top_n
        logger.debug(f"Diversity: {diversity:.3f} (unique categories: {final_recommendations['category'].unique()})")
    else:
        logger.warning(f"No recommendations for user {user_id}. Using popular products.")
        popular_products = product_popularity['product_id'].head(top_n).tolist()
        final_recommendations = products[products['product_id'].isin(popular_products)].copy()
        final_recommendations['score'] = 0.5
        final_recommendations['source'] = 'Popular Products'

    logger.debug(f"Final hybrid recommendations: {len(final_recommendations)} items\n{final_recommendations[['product_id', 'product_name', 'score', 'source']]}")
    return final_recommendations

# Example of using the hybrid recommendation function
if __name__ == "__main__":
    purchases_df, browsing_history_df, products_df = load_data()
    product_popularity = calculate_product_popularity(purchases_df)
    user_id = 1
    top_n = 5
    recommendations = hybrid_recommendation(user_id, purchases_df, browsing_history_df, products_df, product_popularity, top_n)
    print("Final Recommendations:")
    print(recommendations[['product_id', 'product_name', 'score', 'source']])