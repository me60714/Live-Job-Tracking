########################################################################
# This script manages API token validation and updates.                 #
########################################################################

from urllib.parse import urljoin
import requests
from datetime import datetime
import os

class APIManager:
    def __init__(self, url, username, token, token_created_date):
        self.url = url
        self.username = username
        self.token = token
        self.token_created_date = token_created_date
        
    def check_token(self) -> bool:
        """Check if API token is valid and handle expiration."""
        try:
            # Check token validity with Jira
            response = requests.get(
                urljoin(self.url, "/rest/api/2/myself"),
                auth=(self.username, self.token)
            )
            
            if response.status_code == 401:
                print("API Token is invalid or expired")
                self.update_token()  # Force update if invalid
                return False
                
            elif response.status_code == 200:
                # Check token age
                token_created = datetime.strptime(self.token_created_date, "%Y-%m-%d")
                days_old = (datetime.now() - token_created).days
                days_left = 90 - days_old
                
                print("API Token is valid")
                
                # Auto-prompt for token update if near expiration
                if days_left <= 7:  # Warning when 7 days or less remaining
                    print(f"\nWARNING: Token expires in {days_left} days!")
                    if days_left <= 1:  # Force update when 1 day or less
                        print("\nToken expiring very soon. Update required.")
                        self.update_token()
                        return False
                
                return True
                
        except Exception as e:
            print(f"Error checking API token: {e}")
            return False
    
    def update_token(self) -> None:
        """Update the API token in config file."""
        print("\n=== API Token Update Required ===")
        print("Current token is nearing expiration or invalid.")
        
        # Get new token info
        new_token = input("Enter new API token: ").strip()
        
        # Get today's date for token creation
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Read existing config file
            with open('config.py', 'r') as file:
                lines = file.readlines()
            
            # Update the relevant lines
            for i, line in enumerate(lines):
                if 'JIRA_API_TOKEN =' in line:
                    lines[i] = f'JIRA_API_TOKEN = "{new_token}"\n'
                elif 'TOKEN_CREATED_DATE =' in line:
                    lines[i] = f'TOKEN_CREATED_DATE = "{today}" #format: YYYY-MM-DD\n'
            
            # Write back to config file
            with open('config.py', 'w') as file:
                file.writelines(lines)
            
            print("\nToken updated successfully!")
            print(f"Token creation date set to: {today}")
            
            # Update current instance
            self.token = new_token
            self.token_created_date = today
            
        except Exception as e:
            print(f"Error updating token: {e}")
            raise

def get_api_manager():
    """Factory function to create APIManager instance."""
    from config import JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN, TOKEN_CREATED_DATE
    return APIManager(JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN, TOKEN_CREATED_DATE)

if __name__ == "__main__":
    # Can still be run directly for manual updates
    api_manager = get_api_manager()
    api_manager.update_token() 