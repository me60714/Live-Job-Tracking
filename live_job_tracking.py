import requests
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List

# Constants
JIRA_URL = "jiraURL"
JIRA_USERNAME = "email"
JIRA_API_TOKEN = "api-token"

def fetch_issues(jql_query: str) -> List[Dict]:
    """Fetch issues from Jira API."""
    api_endpoint = f"{JIRA_URL}/rest/api/2/search"
    headers = {"Accept": "application/json"}
    params = {"jql": jql_query, "maxResults": 1000}
    
    response = requests.get(api_endpoint, headers=headers, params=params, auth=(JIRA_USERNAME, JIRA_API_TOKEN))
    response.raise_for_status()
    return response.json()['issues']

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
    except requests.RequestException as e:
        print(f"Error fetching data from Jira: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()