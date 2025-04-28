import pandas as pd
import logging
from .recommender_utils import collaborative_filtering, content_based_filtering, hybrid_recommendation

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Final recommendation method that encapsulates the logic
def get_top_n_recommendations(user_id, purchases, browsing_history, products, top_n=10):
    logger.debug(f"Getting top {top_n} recommendations for user_id: {user_id}")
    
    # Call hybrid recommendation to get a combined list
    recommendations = hybrid_recommendation(user_id, purchases, browsing_history, products)
    
    # Return the top N products based on score
    top_recommendations = recommendations.head(top_n)
    logger.debug(f"Top {top_n} recommendations:\n{top_recommendations[['product_id', 'score', 'source']]}")
    
    return top_recommendations
