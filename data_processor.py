from datetime import datetime, timedelta, timezone
import pandas as pd
from typing import Dict, List
import requests
from urllib.parse import urljoin
import numpy as np
import json
from config import JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN

class JiraDataProcessor:

    def __init__(self):
        self.JIRA_URL = JIRA_URL
        self.JIRA_USERNAME = JIRA_USERNAME
        self.JIRA_API_TOKEN = JIRA_API_TOKEN
        self.debugged_issues = set()

    def fetch_issues(self, jql_query: str) -> List[Dict]:
        """Fetch issues from Jira API."""
        if not self.JIRA_URL:
            raise ValueError("JIRA_URL is not set. Please check your configuration.")
        
        api_endpoint = urljoin(self.JIRA_URL, "/rest/api/2/search")
        headers = {"Accept": "application/json"}
        
        # Modify the JQL query to only fetch top-level tasks
        if "ORDER BY" in jql_query:
            jql_query = jql_query.split("ORDER BY")[0].strip()
        
        jql_query += " AND issuetype = Task AND parent IS EMPTY ORDER BY created DESC"
        
        params = {"jql": jql_query, "maxResults": 300}
        
        try:
            response = requests.get(api_endpoint, headers=headers, params=params, auth=(self.JIRA_USERNAME, self.JIRA_API_TOKEN))
            response.raise_for_status()
            return response.json()['issues']
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error fetching data from Jira: {e}")

    def process_issues(self, issues: List[Dict]) -> pd.DataFrame:
        """Process issues into a DataFrame."""
        processed_data = []
        seen_jobs = set()
        
        for issue in issues:
            job = issue['fields']['summary']
            if job in seen_jobs:
                continue
                
            seen_jobs.add(job)
            data = {
                'job': job,
                'status': issue['fields']['status']['name'],
                'created_date': pd.to_datetime(issue['fields']['created']).tz_localize(None),
                'stage': self.determine_stage(issue['fields']['status']['name'])
            }
            processed_data.append(data)
        
        return pd.DataFrame(processed_data)

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

    def get_data(self, project_key: str, start_date: str = None, end_date: str = None, stages: List[str] = None, view_type: str = 'Daily Count') -> Dict:
        jql_query = f'project = {project_key} ORDER BY created DESC'
        issues = self.fetch_issues(jql_query)
        df = self.process_issues(issues)
        filtered_df = self.filter_issues(df, start_date, end_date, stages)
        
        aggregated_data = self.aggregate_data(filtered_df, view_type)
        
        # Ensure we have data for all days in the selected range
        date_range = pd.date_range(start=start_date, end=end_date)
        aggregated_data = aggregated_data.reindex(date_range, fill_value=0)
        
        return {
            'df': filtered_df,
            'total_issues': self.get_total_issues(filtered_df),
            'percentage_issues': self.get_percentage_issues(filtered_df),
            'aggregated_data': aggregated_data
        }

    def aggregate_data(self, df: pd.DataFrame, view_type: str = 'Daily Count', date_range: pd.DatetimeIndex = None) -> pd.DataFrame:
        """Aggregate data based on view type."""
        df['created_date'] = pd.to_datetime(df['created_date'])
        
        daily_counts = df.groupby([df['created_date'].dt.date, 'stage']).size().unstack(fill_value=0)
        
        if date_range is not None:
            dates = [d.date() for d in date_range]
            daily_counts = daily_counts.reindex(dates, fill_value=0)
        
        if view_type == 'Cumulative':
            return daily_counts.cumsum()
        
        return daily_counts

    def find_specific_jobs(self):
        """Find specific jobs and output their states."""
        target_jobs = [
            "INEW6003.0(6)",
            "PIPW5000.0(5)",
            "INMW7001.0(9-3)",
            "FERV5031.0(16)",
            "FERV5030.0(7)",
            "FERV5029.0(25-2)",
            "LIQW5000.0(8)",
            "AECV6002.0(5)"
        ]
        
        jql_query = 'project = MTEST AND issuetype = Task AND parent IS EMPTY'
        try:
            print("Fetching issues from Jira...")
            issues = self.fetch_issues(jql_query)
            print(f"Found {len(issues)} total issues")
            
            found_issues = []
            not_found = target_jobs.copy()
            
            print("\nJob Status Report:")
            print("-----------------")
            
            for issue in issues:
                summary = issue['fields']['summary']
                if summary in target_jobs:
                    found_issues.append(issue)
                    not_found.remove(summary)
                    print(f"Found: {summary}")
                    print(f"Status: {issue['fields']['status']['name']}")
                    print("---")
            
            print(f"\nFound {len(found_issues)} matching issues")
            
            if found_issues:
                try:
                    file_path = 'jira_issues_for_states.json'
                    print(f"Attempting to save to {file_path}")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json_str = json.dumps(found_issues, indent=2, ensure_ascii=False)
                        print(f"JSON string length: {len(json_str)}")
                        f.write(json_str)
                    print(f"Successfully saved {len(found_issues)} issues to {file_path}")
                except Exception as e:
                    print(f"Error saving to file: {e}")
                    print(f"Error type: {type(e)}")
                    import traceback
                    print(traceback.format_exc())
            else:
                print("\nNo matching issues found to save to file")
            
            if not_found:
                print("\nJobs not found:")
                for job in not_found:
                    print(f"- {job}")
                
        except Exception as e:
            print(f"Error in main process: {e}")
            import traceback
            print(traceback.format_exc())
