import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from config import JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN

class JiraDataFetcher:
    def __init__(self):
        self.base_url = JIRA_URL
        self.auth = (JIRA_USERNAME, JIRA_API_TOKEN)

    def fetch_issues(self, jql_query):
        api_endpoint = f"{self.base_url}/rest/api/2/search"
        headers = {"Accept": "application/json"}
        params = {
            "jql": jql_query,
            "maxResults": 1000  # Adjust as needed
        }

        response = requests.get(api_endpoint, headers=headers, params=params, auth=self.auth)
        response.raise_for_status()
        return response.json()['issues']

class DataProcessor:
    @staticmethod
    def process_issues(issues):
        data = []
        for issue in issues:
            data.append({
                'key': issue['key'],
                'status': issue['fields']['status']['name'],
                'created_date': issue['fields']['created'],
                # Add more fields as needed
            })
        return pd.DataFrame(data)

    @staticmethod
    def clean_data(df):
        df['created_date'] = pd.to_datetime(df['created_date'])
        # Add more cleaning steps as needed
        return df

class Visualizer:
    @staticmethod
    def plot_issues_over_time(df):
        df_grouped = df.groupby('created_date').size().cumsum()
        plt.figure(figsize=(12, 6))
        plt.plot(df_grouped.index, df_grouped.values)
        plt.title('Cumulative Issues Over Time')
        plt.xlabel('Date')
        plt.ylabel('Number of Issues')
        plt.show()

def main():
    fetcher = JiraDataFetcher()
    processor = DataProcessor()
    visualizer = Visualizer()

    # Fetch data
    jql_query = 'project = YourProjectKey ORDER BY created DESC'
    issues = fetcher.fetch_issues(jql_query)

    # Process and clean data
    df = processor.process_issues(issues)
    df_cleaned = processor.clean_data(df)

    # Visualize data
    visualizer.plot_issues_over_time(df_cleaned)

if __name__ == "__main__":
    main()