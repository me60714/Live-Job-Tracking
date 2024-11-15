########################################################################
# This script checks if the API token is valid.                        #
########################################################################

from urllib.parse import urljoin
import requests

def check_api_token(url, username, token):
    """Check if API token is valid."""
    try:
        response = requests.get(
            urljoin(url, "/rest/api/2/myself"),
            auth=(username, token)
        )
        
        if response.status_code == 401:
            print("API Token is invalid or expired")
            return False
        elif response.status_code == 200:
            print("API Token is valid")
            return True
            
    except Exception as e:
        print(f"Error checking API token: {e}")
        return False 