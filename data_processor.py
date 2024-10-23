from datetime import datetime, timedelta, timezone
import pandas as pd
from typing import Dict, List
import requests
from urllib.parse import urljoin
import numpy as np
import json

class JiraDataProcessor:
    def __init__(self):
        self.JIRA_URL = ""
        self.JIRA_USERNAME = ""
        self.JIRA_API_TOKEN = ""

    def fetch_issues(self, jql_query: str) -> List[Dict]:
        """Fetch issues from Jira API."""
        if not self.JIRA_URL:
            raise ValueError("JIRA_URL is not set. Please check your configuration.")
        
        api_endpoint = urljoin(self.JIRA_URL, "/rest/api/2/search")
        headers = {"Accept": "application/json"}
        
        # Modify the JQL query to only fetch top-level tasks
        # Remove the ORDER BY clause if present
        if "ORDER BY" in jql_query:
            jql_query = jql_query.split("ORDER BY")[0].strip()
        
        # Add the conditions for Task type and no parent
        jql_query += " AND issuetype = Task AND parent IS EMPTY"
        
        # Add the ORDER BY clause at the end
        jql_query += " ORDER BY created DESC"
        
        params = {"jql": jql_query, "maxResults": 300}
        
        try:
            response = requests.get(api_endpoint, headers=headers, params=params, auth=(self.JIRA_USERNAME, self.JIRA_API_TOKEN))
            response.raise_for_status()
            issues = response.json()['issues']
            
            # Debug: Write specific issue to file
            self.debug_print_issue(issues, "MTEST-5160")
            
            return issues
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error fetching data from Jira: {e}")

    def debug_print_issue(self, issues: List[Dict], target_key: str):
        """Write a specific issue to a file for debugging purposes."""
        for issue in issues:
            if issue['key'] == target_key:
                filename = f"jira_issue_{target_key}_debug.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(issue, f, indent=4, sort_keys=True, ensure_ascii=False)
                print(f"Debug: Issue {target_key} has been written to {filename}")
                break
        else:
            print(f"Debug: Issue {target_key} not found in the fetched data.")

    def process_issues(self, issues: List[Dict]) -> pd.DataFrame:
        return pd.DataFrame([
            {
                'key': issue['key'],
                'status': issue['fields']['status']['name'],
                'created_date': pd.to_datetime(issue['fields']['created']).tz_localize(None),
                'stage': self.determine_stage(issue['fields']['status']['name'])
            }
            for issue in issues
        ])

    def determine_stage(self, status: str) -> str:
        if status == 'Testing':
            return 'Testing'
        else:
            return 'Sample Preparation'

    @staticmethod
    def filter_issues(df: pd.DataFrame, start_date: str = None, end_date: str = None, stages: List[str] = None) -> pd.DataFrame:
        filtered_df = df.copy()
        if start_date:
            start_date = pd.to_datetime(start_date)
            filtered_df = filtered_df[filtered_df['created_date'] >= start_date]
        if end_date:
            end_date = pd.to_datetime(end_date)
            filtered_df = filtered_df[filtered_df['created_date'] <= end_date]
        if stages and 'All' not in stages:
            filtered_df = filtered_df[filtered_df['stage'].isin(stages)]
        return filtered_df

    def get_total_issues(self, df: pd.DataFrame) -> Dict[str, int]:
        return df['stage'].value_counts().to_dict()

    def get_percentage_issues(self, df: pd.DataFrame) -> Dict[str, float]:
        total = len(df)
        return (df['stage'].value_counts() / total * 100).to_dict()

    def get_running_average(self, df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
        # Ensure created_date is a datetime
        df['created_date'] = pd.to_datetime(df['created_date'])
        
        # Group by date and stage, count the number of issues
        daily_counts = df.groupby([df['created_date'].dt.date, 'stage']).size().unstack(fill_value=0)
        
        # Calculate the rolling average
        running_avg = daily_counts.rolling(window=window).mean()
        
        # Reset the index to make 'date' a column
        running_avg = running_avg.reset_index()
        running_avg.columns.name = None  # Remove the name of the columns index
        
        # Ensure 'created_date' is a datetime object
        running_avg['created_date'] = pd.to_datetime(running_avg['created_date'])
        
        # Return only the last 7 days of data
        return running_avg.tail(7)

    def get_data(self, project_key: str, start_date: str = None, end_date: str = None, stages: List[str] = None) -> Dict:
        jql_query = f'project = {project_key} ORDER BY created DESC'
        issues = self.fetch_issues(jql_query)
        df = self.process_issues(issues)
        filtered_df = self.filter_issues(df, start_date, end_date, stages)
        
        aggregated_data = self.aggregate_data(filtered_df)
        
        # Ensure we have data for all days in the selected range
        date_range = pd.date_range(start=start_date, end=end_date)
        aggregated_data = aggregated_data.reindex(date_range, fill_value=0)
        
        return {
            'df': filtered_df,
            'total_issues': self.get_total_issues(filtered_df),
            'percentage_issues': self.get_percentage_issues(filtered_df),
            'aggregated_data': aggregated_data
        }

    def aggregate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df['created_date'] = pd.to_datetime(df['created_date'])
        daily_counts = df.groupby([df['created_date'].dt.date, 'stage']).size().unstack(fill_value=0)
        cumulative = daily_counts.cumsum()
        return cumulative.reset_index().rename(columns={'created_date': 'date'}).set_index('date')
