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

# Fair distribution and deduplication

def fair_hybrid_distribution(huspm_recs, collab_recs, content_recs, top_n=9):
    huspm_recs = pd.DataFrame(huspm_recs)
    collab_recs = pd.DataFrame(collab_recs)
    content_recs = pd.DataFrame(content_recs)

    combined = pd.concat([huspm_recs, collab_recs, content_recs], ignore_index=True)

    # Remove duplicate product_ids, keep highest score
    combined.sort_values(by='score', ascending=False, inplace=True)
    combined.drop_duplicates(subset='product_id', keep='first', inplace=True)

    # Limit to top N
    final_recommendations = combined.head(top_n).reset_index(drop=True)
    return final_recommendations

# Hybrid Recommendation

def hybrid_recommendation(user_id, purchases, browsing_history, products, product_popularity, top_n=9):
    logger.debug(f"Hybrid Recommendation for user_id: {user_id}")

    purchases = ensure_dataframe(purchases, "purchases")
    browsing_history = ensure_dataframe(browsing_history, "browsing_history")
    products = ensure_dataframe(products, "products")

    huspm_recs = huspm_recommendations(user_id, purchases, browsing_history, products, product_popularity, top_n)
    huspm_recs = pd.DataFrame(huspm_recs)
    if not huspm_recs.empty:
        huspm_recs['score'] = huspm_recs['score'] * 1.3

    collab_recs = collaborative_filtering(user_id, purchases, products)
    collab_recs = pd.DataFrame(collab_recs)

    content_recs = pd.DataFrame()
    if huspm_recs.empty and collab_recs.empty:
        content_recs = content_based_filtering(user_id, purchases, browsing_history, products)
        content_recs = pd.DataFrame(content_recs)

    required_columns = ['product_id', 'product_name', 'score', 'source', 'category', 'price', 'rating', 'clicks', 'stock']
    for recs, name in [(huspm_recs, 'HUSPM'), (collab_recs, 'Collaborative'), (content_recs, 'Content-Based')]:
        missing = [col for col in required_columns if col not in recs.columns]
        if missing:
            logger.error(f"{name} recommendations missing columns: {missing}")

    final_recommendations = fair_hybrid_distribution(huspm_recs, collab_recs, content_recs, top_n)
    logger.debug(f"Final hybrid recommendations: {len(final_recommendations)} items\n{final_recommendations[['product_id', 'product_name', 'score', 'source']]}")
    return final_recommendations

if __name__ == "__main__":
    purchases_df, browsing_history_df, products_df = load_data()
    product_popularity = calculate_product_popularity(purchases_df)
    user_id = 1
    top_n = 9
    recommendations = hybrid_recommendation(user_id, purchases_df, browsing_history_df, products_df, product_popularity, top_n)
    print("Final Recommendations:")
    print(recommendations[['product_id', 'product_name', 'score', 'source']])
