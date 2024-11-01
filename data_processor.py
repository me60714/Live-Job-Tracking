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
            raise ValueError("JIRA_URL is not set")
        
        api_endpoint = urljoin(self.JIRA_URL, "/rest/api/2/search")
        headers = {"Accept": "application/json"}
        
        # Print the final JQL query for debugging
        print(f"JQL Query: {jql_query}")
        
        params = {"jql": jql_query, "maxResults": 300}
        
        try:
            response = requests.get(api_endpoint, headers=headers, params=params, 
                                  auth=(self.JIRA_USERNAME, self.JIRA_API_TOKEN))
            response.raise_for_status()
            issues = response.json()['issues']
            print(f"Number of issues fetched: {len(issues)}")
            return issues
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []

    def process_issues(self, issues: List[Dict]) -> pd.DataFrame:
        """Process issues into a DataFrame."""
        processed_data = []
        seen_jobs = set()
        
        print("\nProcessing issues:")
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
            print(f"Job: {job}, Status: {data['status']}, Created: {data['created_date']}, Stage: {data['stage']}")
        
        return pd.DataFrame(processed_data)

    def determine_stage(self, status: str) -> str:
        """Determine the stage based on the issue status."""
        # Define status mappings
        testing_statuses = [
            'Testing'
        ]
        
        sample_prep_statuses = [
            'Open',
            'Sample Prep',
            'In Progress',
            'Quotation'
        ]
        
        # All other statuses will be categorized as 'Other'
        # Including: Report, Reported, Review, Invoiced, On Hold, Cancelled, Others
        
        if status in testing_statuses:
            return 'Testing'
        elif status in sample_prep_statuses:
            return 'Sample Preparation'
        else:
            return 'Other'

    def filter_issues(self, df: pd.DataFrame, start_date: str = None, end_date: str = None, stages: List[str] = None) -> pd.DataFrame:
        """Filter issues based on date range and stages."""
        if df.empty:
            return df
            
        # Convert dates to datetime
        df['created_date'] = pd.to_datetime(df['created_date'])
        
        if start_date:
            start = pd.to_datetime(start_date)
            df = df[df['created_date'].dt.date >= start.date()]
        
        if end_date:
            end = pd.to_datetime(end_date) + pd.Timedelta(days=1)
            df = df[df['created_date'].dt.date < end.date()]
        
        if stages and 'All' not in stages:
            df = df[df['stage'].isin(stages)]
        
        print(f"\nFiltering data:")
        print(f"Start date: {start_date}")
        print(f"End date: {end_date}")
        print(f"Number of issues after filtering: {len(df)}")
        print(f"Date range of data: {df['created_date'].min() if not df.empty else 'No data'} to {df['created_date'].max() if not df.empty else 'No data'}")
        
        return df

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
        print(f"\nFetching data with parameters:")
        print(f"Project: {project_key}")
        print(f"Date range: {start_date} to {end_date}")
        print(f"Stages: {stages}")
        print(f"View type: {view_type}")
        
        jql_query = f'project = {project_key} ORDER BY created DESC'
        issues = self.fetch_issues(jql_query)
        df = self.process_issues(issues)
        filtered_df = self.filter_issues(df, start_date, end_date, stages)
        
        # Create complete date range
        date_range = pd.date_range(start=start_date, end=end_date)
        aggregated_data = self.aggregate_data(filtered_df, view_type, date_range)
        
        return {
            'df': filtered_df,
            'total_issues': self.get_total_issues(filtered_df),
            'percentage_issues': self.get_percentage_issues(filtered_df),
            'aggregated_data': aggregated_data
        }

    def aggregate_data(self, df: pd.DataFrame, view_type: str = 'Daily Count', date_range: pd.DatetimeIndex = None) -> pd.DataFrame:
        """Aggregate data based on view type."""
        print("\nAggregating data:")
        print(f"Input DataFrame shape: {df.shape}")
        
        # Define fixed order of stages
        STAGE_ORDER = ['Sample Preparation', 'Testing', 'Other']
        
        if df.empty and date_range is not None:
            # Create empty DataFrame with ordered stages
            dates = [d.date() for d in date_range]
            daily_counts = pd.DataFrame(0, index=dates, columns=STAGE_ORDER)
        else:
            # Group by date and stage, count jobs
            daily_counts = df.groupby([df['created_date'].dt.date, 'stage']).size().unstack(fill_value=0)
            
            # Ensure all stages are present and in correct order
            for stage in STAGE_ORDER:
                if stage not in daily_counts.columns:
                    daily_counts[stage] = 0
            
            # Reorder columns
            daily_counts = daily_counts[STAGE_ORDER]
        
        # Ensure all dates in range are included
        if date_range is not None:
            dates = [d.date() for d in date_range]
            daily_counts = daily_counts.reindex(dates, fill_value=0)
        
        if view_type == 'Cumulative':
            daily_counts = daily_counts.cumsum()
        
        return daily_counts

    def find_specific_jobs(self):
        """Find specific jobs and output their states."""
        target_jobs = [
            "INEW6003.0 (6)",
            "PIPW5000.0 (5)",
            "INMW7001.0 (9-3)",
            "FERV5031.0 (16)",
            "FERV5030.0 (7)",
            "FERV5029.0 (25-2)",
            "LIQW5000.0 (8)",
            "AECV6002.0 (5)"
        ]
        
        jql_query = 'project = MTEST AND issuetype = Task AND parent IS EMPTY'
        try:
            print("Fetching issues from Jira...")
            issues = self.fetch_issues(jql_query)
            
            # Dictionary to store all unique states
            all_states = set()
            
            print("\nStates for each job:")
            print("-------------------")
            
            for issue in issues:
                summary = issue['fields']['summary']
                # Try different formats
                summary_variants = [
                    summary,
                    summary.replace(" ", ""),
                    summary.replace("(", " (")
                ]
                
                for target in target_jobs:
                    target_variants = [
                        target,
                        target.replace(" ", ""),
                        target.replace("(", " (")
                    ]
                    
                    if any(s in target_variants for s in summary_variants):
                        status = issue['fields']['status']['name']
                        all_states.add(status)
                        print(f"Job: {summary}")
                        print(f"Status: {status}")
                        print("---")
            
            print("\nAll unique states found:")
            print("----------------------")
            for state in sorted(all_states):
                print(f"- {state}")
                
        except Exception as e:
            print(f"Error in main process: {e}")
            import traceback
            print(traceback.format_exc())
