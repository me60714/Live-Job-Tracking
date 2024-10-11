import requests
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List
from urllib.parse import urljoin

# Constants
JIRA_URL = "https://paragonsystemstesting.atlassian.net"  # Ensure this is correct
JIRA_USERNAME = "your-email@example.com"  # Replace with your actual email
JIRA_API_TOKEN = "your-api-token"  # Replace with your actual API token

def fetch_issues(jql_query: str) -> List[Dict]:
    """Fetch issues from Jira API."""
    if not JIRA_URL:
        raise ValueError("JIRA_URL is not set. Please check your configuration.")
    
    api_endpoint = urljoin(JIRA_URL, "/rest/api/2/search")
    headers = {"Accept": "application/json"}
    params = {"jql": jql_query, "maxResults": 1000}
    
    print(f"Attempting to access: {api_endpoint}")  # Debugging line
    
    try:
        response = requests.get(api_endpoint, headers=headers, params=params, auth=(JIRA_USERNAME, JIRA_API_TOKEN))
        response.raise_for_status()
        return response.json()['issues']
    except requests.exceptions.MissingSchema:
        raise ValueError(f"Invalid URL: {api_endpoint}. Make sure JIRA_URL includes the scheme (http:// or https://)")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"Failed to connect to {api_endpoint}. Check your internet connection and Jira URL.")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error fetching data from Jira: {e}")

def process_issues(issues: List[Dict]) -> pd.DataFrame:
    """Process issues into a pandas DataFrame."""
    return pd.DataFrame([
        {
            'key': issue['key'],
            'status': issue['fields']['status']['name'],
            'created_date': pd.to_datetime(issue['fields']['created'])
        }
        for issue in issues
    ])

def plot_issues_over_time(df: pd.DataFrame) -> None:
    """Plot cumulative issues over time."""
    df_grouped = df.groupby('created_date').size().cumsum()
    
    plt.figure(figsize=(12, 6))
    plt.plot(df_grouped.index, df_grouped.values)
    plt.title('Cumulative Issues Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Issues')
    plt.tight_layout()
    plt.show()

def main():
    jql_query = 'project = YourProjectKey ORDER BY created DESC'
    
    try:
        issues = fetch_issues(jql_query)
        df = process_issues(issues)
        plot_issues_over_time(df)
    except ValueError as e:
        print(f"Configuration error: {e}")
    except ConnectionError as e:
        print(f"Connection error: {e}")
    except RuntimeError as e:
        print(f"Runtime error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()