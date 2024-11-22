#######################################################################
# This script updates the Jira API token in the config file.          #
#######################################################################
import os
from datetime import datetime

def update_token():
    print("=== API Token Update Utility ===")
    
    # Get new token info
    new_token = input("Enter new API token: ").strip()
    
    # Get today's date for token creation
    today = datetime.now().strftime("%Y-%m-%d")
    
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

if __name__ == "__main__":
    update_token() 