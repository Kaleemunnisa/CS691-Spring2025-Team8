import pandas as pd
import logging

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load datasets
def load_data():
    # Loading the datasets
    products = pd.read_csv('data/products.csv')
    purchases = pd.read_csv('data/purchases.csv')
    browsing_history = pd.read_csv('data/browsing_history.csv')
    logger.debug("Data loaded successfully.")
    return products, purchases, browsing_history

# Collaborative Filtering: User-based or Item-based
def collaborative_filtering(user_id, purchases, products):
    logger.debug(f"Collaborative Filtering for user_id: {user_id}")
    
    # Get the products that the user has purchased
    user_purchases = purchases[purchases['user_id'] == user_id]['product_id'].unique()
    logger.debug(f"User purchases: {user_purchases}")
    
    # Find other users who have bought the same products
    other_users = purchases[purchases['product_id'].isin(user_purchases) & 
                            (purchases['user_id'] != user_id)]['user_id'].unique()
    
    # Get the products that these other users have bought
    other_purchases = purchases[purchases['user_id'].isin(other_users)]
    
    # Calculate frequency of each product being bought
    product_counts = other_purchases['product_id'].value_counts()
    
    # Create a recommendation list
    recommendations = products[products['product_id'].isin(product_counts.index) & 
                               ~products['product_id'].isin(user_purchases)].copy()
    
    # Scoring: Frequency of purchases * Product rating
    recommendations['score'] = (recommendations['product_id'].map(product_counts).fillna(0) * 
                                recommendations['rating']) / product_counts.max()
    recommendations['source'] = 'Collaborative Filtering'
    logger.debug(f"Collaborative recommendations:\n{recommendations[['product_id', 'score', 'source']]}")
    return recommendations.sort_values(by='score', ascending=False)

# Content-Based Filtering: Based on product features (e.g., category)
def content_based_filtering(user_id, purchases, browsing_history, products):
    logger.debug(f"Content-Based Filtering for user_id: {user_id}")
    
    # Get the user's browsing history
    user_history = browsing_history[browsing_history['user_id'] == user_id]['product_id'].unique()
    logger.debug(f"User browsing history: {user_history}")
    
    # Find products that are in the same category as the user’s viewed products
    user_products = products[products['product_id'].isin(user_history)]
    
    if not user_products.empty and 'category' in products.columns:
        recommendations = products[products['category'].isin(user_products['category']) & 
                                   ~products['product_id'].isin(user_history)].copy()
        
        # Scoring: Average rating of browsed products in category
        avg_rating = user_products['rating'].mean()
        recommendations['score'] = recommendations['rating'] / 5.0 * avg_rating
    else:
        recommendations = pd.DataFrame(columns=['product_id', 'product_name', 'price', 'rating', 'score', 'source'])
        logger.debug("No content-based recommendations.")
    
    recommendations['source'] = 'Content-Based Filtering'
    logger.debug(f"Content-based recommendations:\n{recommendations[['product_id', 'score', 'source']]}")
    return recommendations

# Hybrid Recommendation: Combine collaborative filtering and content-based filtering
def hybrid_recommendation(user_id, purchases, browsing_history, products):
    logger.debug(f"Hybrid Recommendation for user_id: {user_id}")
    
    # Get the user’s purchase and browsing history
    user_purchases = purchases[purchases['user_id'] == user_id]['product_id'].unique()
    user_browsed = browsing_history[browsing_history['user_id'] == user_id]['product_id'].unique()
    user_history = set(user_purchases).union(user_browsed)
    logger.debug(f"User history (purchases + browsed): {user_history}")

    # Get collaborative and content-based recommendations
    collab_recs = collaborative_filtering(user_id, purchases, products)
    content_recs = content_based_filtering(user_id, purchases, browsing_history, products)

    # Combine both recommendations
    all_recommendations = pd.concat([collab_recs, content_recs], ignore_index=True)
    logger.debug(f"Combined recommendations:\n{all_recommendations[['product_id', 'score', 'source']]}")
    
    # If no recommendations, add popular products
    if all_recommendations.empty:
        logger.debug("No recommendations; adding popular products.")
        popular_products = purchases['product_id'].value_counts().head(3).index
        all_recommendations = products[products['product_id'].isin(popular_products) & 
                                      ~products['product_id'].isin(user_history)].copy()
        all_recommendations['score'] = 0.5
        all_recommendations['source'] = 'Popular Products'

    final_recommendations = all_recommendations.sort_values(by='score', ascending=False) \
                                               .drop_duplicates(subset=['product_id'], keep='first')
    logger.debug(f"Final hybrid recommendations:\n{final_recommendations[['product_id', 'score', 'source']]}")
    
    return final_recommendations
