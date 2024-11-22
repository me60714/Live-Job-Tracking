########################################################################
# This script checks if the API token is valid.                        #
########################################################################

from urllib.parse import urljoin
import requests
from datetime import datetime
from config import TOKEN_CREATED_DATE

def check_api_token(url, username, token):
    """Check if API token is valid and print token age."""
    try:
        response = requests.get(
            urljoin(url, "/rest/api/2/myself"),
            auth=(username, token)
        )
        
        if response.status_code == 401:
            print("API Token is invalid or expired")
            return False
        elif response.status_code == 200:

            token_created = datetime.strptime(TOKEN_CREATED_DATE, "%Y-%m-%d")
            days_old = (datetime.now() - token_created).days
            days_left = 90 - days_old
            
            print("API Token is valid")
            
            if days_left <= 1:
                print("\nWARNING: Token rotation recommended soon!")
            
            return True
            
    except Exception as e:
        print(f"Error checking API token: {e}")
        return False 