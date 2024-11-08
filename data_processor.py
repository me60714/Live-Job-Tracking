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
                    "startAt": start_at,
                    "expand": "changelog"
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
        
        for issue in issues:
            job_number = issue['fields']['summary']
            
            if not job_number.startswith(tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ')):
                invalid_jobs.append({
                    'key': issue['key'],
                    'job': job_number
                })
                continue
            
            # Validate job number format
            if not re.match(job_pattern, job_number):
                invalid_jobs.append({
                    'key': issue['key'],
                    'job': job_number
                })
                continue
                
            created_date = pd.to_datetime(issue['fields']['created']).tz_localize(None)
            current_status = issue['fields']['status']['name']
            
            # Get status change history
            status_changes = []
            if 'changelog' in issue:
                for history in issue['changelog']['histories']:
                    for item in history['items']:
                        if item['field'] == 'status':
                            change_date = pd.to_datetime(history['created']).tz_localize(None)
                            status_changes.append({
                                'date': change_date,
                                'from_status': item['fromString'],
                                'to_status': item['toString']
                            })
            
            # Add initial status
            data = {
                'key': issue['key'],
                'job': job_number,
                'status': current_status,
                'created_date': created_date,
                'stage': self.determine_stage(current_status),
                'status_changes': status_changes
            }
            processed_data.append(data)

        # Convert to DataFrame for easier sorting
        df = pd.DataFrame(processed_data)
        
        # Create status priority mapping based on the order in other_statuses
        other_status_priority = {status.lower(): idx for idx, status in enumerate([
            'quotation',
            'in progress',
            'review',
            'reported',
            'invoiced',
            'on hold',
            'cancelled',
            'other'
        ])}
        
        # Create stage priority mapping
        stage_priority = {
            'Open': 0,
            'Sample Preparation': 1,
            'Testing': 2,
            'Report': 3
        }
        
        # Add priority columns for sorting
        df['stage_priority'] = df['stage'].map(stage_priority)
        df['status_priority'] = df['status'].str.lower().map(lambda x: other_status_priority.get(x, len(other_status_priority)))
        
        # Sort by stage priority, then status priority for 'Other' stage, then created_date
        df = df.sort_values(['stage_priority', 'status_priority', 'created_date'])
        
        # Print header
        print("\nProcessing issues:")
        print(f"{'Key':<12} {'Job Number':<35} {'Status':<15} {'Created':<16} {'Stage':<15}")
        print("-" * 100)
        
        # Print sorted rows
        for _, row in df.iterrows():
            formatted_date = row['created_date'].strftime('%Y-%m-%d %H:%M')
            print(f"{row['key']:<12} {row['job']:<35} {row['status']:<15} {formatted_date:<16} {row['stage']:<15}")

        # Print invalid jobs warning if any
        if invalid_jobs:
            print("\nWarning: Found issues with invalid job number format:")
            for invalid in invalid_jobs:
                print(f"Key: {invalid['key']}, Job: {invalid['job']}")
            print(f"Total invalid jobs: {len(invalid_jobs)}")
        
        # Drop the temporary sorting columns before returning
        df = df.drop(['stage_priority', 'status_priority'], axis=1)
        return df

    def determine_stage(self, status: str) -> str:
        """Determine the stage based on the issue status."""
        status = status.lower()
        
        open_statuses = [
            'open'
        ]

        testing_statuses = [
            'testing'
        ]
        
        sample_prep_statuses = [
            'sample prep',
            'sample preparation'
        ]

        report_statuses = [
            'report'
        ]
        
        other_statuses = [
            'quotation',
            'in progress',
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
        elif status in open_statuses:
            return 'Open'
        elif status in report_statuses:
            return 'Report'
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
        
        STAGE_ORDER = ['Open', 'Sample Preparation', 'Testing', 'Report', 'Other']
        
        if date_range is not None:
            dates = [d.date() for d in date_range]
            daily_counts = pd.DataFrame(0, index=dates, columns=STAGE_ORDER)
            
            if not df.empty:
                # Create a snapshot of issue states for each date
                for date in dates:
                    # Reset counts for this date
                    stage_counts = {stage: 0 for stage in STAGE_ORDER}
                    
                    for _, issue in df.iterrows():
                        # Skip if issue wasn't created yet
                        if issue['created_date'].date() > date:
                            continue
                        
                        # Start with the initial stage
                        current_stage = issue['stage']
                        
                        # Check status changes up to this date
                        relevant_changes = [
                            change for change in issue['status_changes']
                            if change['date'].date() <= date
                        ]
                        
                        if relevant_changes:
                            # Get the most recent change
                            last_change = sorted(relevant_changes, key=lambda x: x['date'])[-1]
                            current_stage = self.determine_stage(last_change['to_status'])
                        
                        # Count this issue in its current stage
                        stage_counts[current_stage] += 1
                    
                    # Update daily counts with the snapshot
                    for stage in STAGE_ORDER:
                        daily_counts.loc[date, stage] = stage_counts[stage]
                
                if view_type != 'Cumulative':
                    # For non-cumulative view, subtract previous day's count
                    daily_counts = daily_counts - daily_counts.shift(1).fillna(0)
        
        return daily_counts