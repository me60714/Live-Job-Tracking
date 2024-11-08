from datetime import datetime, timedelta, timezone
import pandas as pd
from typing import Dict, List
import requests
from urllib.parse import urljoin
import numpy as np
import json
from config import JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
import re

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
        
        # Only filter for parent issues and label including CIPP
        base_query = jql_query.replace(' ORDER BY created DESC', '')
        jql_query = f'{base_query} AND parent IS EMPTY AND labels in (CIPP) ORDER BY created DESC'
        print(f"JQL Query: {jql_query}")
        
        all_issues = []
        start_at = 0
        max_results = 2000
        
        while True:
            try:
                params = {
                    "jql": jql_query,
                    "maxResults": max_results,
                    "startAt": start_at
                }
                
                response = requests.get(
                    api_endpoint, 
                    headers=headers, 
                    params=params,
                    auth=(self.JIRA_USERNAME, self.JIRA_API_TOKEN)
                )
                response.raise_for_status()
                
                data = response.json()
                issues = data['issues']
                
                print(f"Total available issues: {data['total']}")
                print(f"Fetched {len(issues)} issues in this request")
                
                if not issues:
                    break
                    
                all_issues.extend(issues)
                start_at += max_results
                
                if len(all_issues) >= data['total']:
                    break
                    
            except Exception as e:
                print(f"Error fetching data: {e}")
                break
        
        print(f"Number of issues fetched: {len(all_issues)}")
        return all_issues

    def process_issues(self, issues: List[Dict]) -> pd.DataFrame:
        """Process issues into a DataFrame."""
        import re
        
        job_pattern = r'^[A-Z]{4}\d{4}\.\d\s+\([^)]*\)'
        
        processed_data = []
        invalid_jobs = []
        
        # Print header
        print("\nProcessing issues:")
        print(f"{'Key':<12} {'Job Number':<35} {'Status':<15} {'Created':<16} {'Stage':<15}")
        print("-" * 90)
        
        for issue in issues:
            job_number = issue['fields']['summary']
            
            if not job_number.startswith(tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ')):
                invalid_jobs.append({
                    'key': issue['key'],
                    'job': job_number
                })
                print(f"Warning: Invalid job number format - Key: {issue['key']}, Job: {job_number}")
                continue
            
            # Validate job number format
            if not re.match(job_pattern, job_number):
                invalid_jobs.append({
                    'key': issue['key'],
                    'job': job_number
                })
                print(f"Warning: Invalid job number format - Key: {issue['key']}, Job: {job_number}")
                continue
                
            created_date = pd.to_datetime(issue['fields']['created']).tz_localize(None)
            formatted_date = created_date.strftime('%Y-%m-%d %H:%M')
            
            data = {
                'key': issue['key'],
                'job': job_number,
                'status': issue['fields']['status']['name'],
                'created_date': created_date,
                'stage': self.determine_stage(issue['fields']['status']['name'])
            }
            processed_data.append(data)
            
            # Print formatted row
            print(f"{data['key']:<12} {data['job']:<35} {data['status']:<15} {formatted_date:<16} {data['stage']:<15}")
        
        if invalid_jobs:
            print("\nWarning: Found issues with invalid job number format:")
            for invalid in invalid_jobs:
                print(f"Key: {invalid['key']}, Job: {invalid['job']}")
            print(f"Total invalid jobs: {len(invalid_jobs)}")
        
        return pd.DataFrame(processed_data)

    def determine_stage(self, status: str) -> str:
        """Determine the stage based on the issue status."""
        status = status.lower()  #for case-insensitive comparison
        
        # Define status mappings with variations
        testing_statuses = [
            'testing'
        ]
        
        sample_prep_statuses = [
            'sample prep',
            'sample preparation'
        ]
        
        other_statuses = [
            'quotation',
            'in progress',
            'open',
            'report',
            'review',
            'reported',
            'invoiced',
            'on hold',
            'cancelled',
            'other' 
        ]
        
        if status in testing_statuses:
            return 'Testing'
        elif status in sample_prep_statuses:
            return 'Sample Preparation'
        else:
            return 'Other'

    def filter_issues(self, df: pd.DataFrame, start_date: str = None, end_date: str = None, stages: List[str] = None) -> pd.DataFrame:
        """Filter issues based on date range and stages."""
        print("\nFiltering data:")
        
        if start_date:
            print(f"Start date: {start_date}")
        if end_date:
            print(f"End date: {end_date}")
        
        filtered_df = df.copy()
        
        # Convert both dates to datetime
        if start_date:
            start_date = pd.to_datetime(start_date)
        if end_date:
            end_date = pd.to_datetime(end_date)
        
        # Filter by date range
        if start_date and end_date:
            filtered_df = filtered_df[
                (filtered_df['created_date'] <= end_date)
            ]
        
        if stages:
            filtered_df = filtered_df[filtered_df['stage'].isin(stages)]
        
        print(f"Number of issues after filtering: {len(filtered_df)}")
        
        if not filtered_df.empty:
            print(f"Date range of data: {filtered_df['created_date'].min()} to {filtered_df['created_date'].max()}")
        
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
        
        # Create complete date range with all dates
        if date_range is not None:
            dates = [d.date() for d in date_range]
            daily_counts = pd.DataFrame(0, index=dates, columns=STAGE_ORDER)
            
            if not df.empty:
                # Get the count of jobs before the start date (for cumulative view)
                start_date = date_range[0]
                previous_jobs = df[df['created_date'] < start_date].groupby('stage').size()
                
                # Group by date and stage, count jobs for the selected period
                period_counts = df[df['created_date'] >= start_date].groupby([df['created_date'].dt.date, 'stage']).size().unstack(fill_value=0)
                
                # Ensure all columns exist in period_counts
                for stage in STAGE_ORDER:
                    if stage not in period_counts.columns:
                        period_counts[stage] = 0
                
                # Add counts to the appropriate dates
                for date in period_counts.index:
                    if date in daily_counts.index:
                        daily_counts.loc[date] = period_counts.loc[date]
                
                # For cumulative view, add previous totals once and then cumsum
                if view_type == 'Cumulative':
                    # Add previous counts only to the first day
                    for stage in STAGE_ORDER:
                        if stage in previous_jobs:
                            daily_counts.loc[daily_counts.index[0], stage] += previous_jobs[stage]
                    
                    # Fill NaN with 0 before cumsum
                    daily_counts = daily_counts.fillna(0)
                    # Now do the cumulative sum
                    daily_counts = daily_counts.cumsum()
        
        return daily_counts