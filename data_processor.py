#######################################################################
# This script processes Jira issues and aggregates data.              #
#######################################################################

from datetime import datetime, timedelta, timezone
import pandas as pd
from typing import Dict, List
import requests
from urllib.parse import urljoin
import numpy as np
import json
from config import JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
import re
from rate_limiter import RateLimiter
from api_manager import get_api_manager

class JiraDataProcessor:

    def __init__(self):
        self.JIRA_URL = JIRA_URL
        self.JIRA_USERNAME = JIRA_USERNAME
        self.JIRA_API_TOKEN = JIRA_API_TOKEN
        
        self.api_manager = get_api_manager()
        if not self.api_manager.check_token():
            raise ValueError("Invalid or expired API token")
            
        self.rate_limiter = RateLimiter()
        self.debugged_issues = set()
        
        # Pre-compile regex patterns for better performance
        self.PARENS_PATTERN = re.compile(r'\(([^)]+)\)')
        self.ARROW_NUM_PATTERN = re.compile(r'-->[^(]*\((\d+)\)')
        self.NUM_IN_PARENS_PATTERN = re.compile(r'\((\d+)\)')
        self.NUMBER_PATTERN = re.compile(r'\d+')

        self._cached_issues = None
        self._last_fetch_time = None
        self.CACHE_DURATION = timedelta(minutes=3)

    def fetch_issues(self, jql_query: str) -> List[Dict]:
        """Fetch issues from Jira API."""
        if not self.JIRA_URL:
            raise ValueError("JIRA_URL is not set")
        
        api_endpoint = urljoin(self.JIRA_URL, "/rest/api/2/search")
        headers = {"Accept": "application/json"}
        
        base_query = jql_query.replace(' ORDER BY created DESC', '')
        jql_query = f'{base_query} AND parent IS EMPTY AND labels in (CIPP) AND created >= "2024-01-01" ORDER BY created DESC'
        
        all_issues = []
        start_at = 0
        max_results = 2000
        
        while True:
            try:
                self.rate_limiter.wait_if_needed()
                
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
                
                # Add detailed debug info
                print(f"Batch info:")
                print(f"  Start at: {start_at}")
                
                issues = data['issues']
                if not issues:
                    break
                    
                all_issues.extend(issues)
                start_at += len(issues)
                
                if len(all_issues) >= data['total']:
                    break
                    
            except Exception as e:
                print(f"Error fetching data: {e}")
                break
        
        print(f"\nFetch summary:")
        print(f"Total issues fetched: {len(all_issues)}")
        # if all_issues:
        #     earliest = min(issue['fields']['created'] for issue in all_issues)
        #     latest = max(issue['fields']['created'] for issue in all_issues)
            # print(f"Date range: {earliest} to {latest}")
        
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
            
            # Determine location based on labels
            labels = [label.upper() for label in issue['fields'].get('labels', [])]
            if 'YEG' in labels:
                location = 'Edmonton'
            elif 'YUL' in labels:
                location = 'Montreal'
            else:
                location = 'Toronto'
            
            data = {
                'key': issue['key'],
                'job_number': job_number,
                'status': current_status,
                'created_date': created_date,
                'stage': self.determine_stage(current_status),
                'status_changes': status_changes,
                'location': location
            }
            processed_data.append(data)

        # Convert to DataFrame for easier sorting
        df = pd.DataFrame(processed_data)
        
        
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
        print(f"{'Key':<12} {'Job Number':<35} {'Status':<15} {'Location':<12} {'Created':<16} {'Stage':<15}")
        print("-" * 105)
        
        # Print sorted rows
        for _, row in df.iterrows():
            formatted_date = row['created_date'].strftime('%Y-%m-%d %H:%M')
            print(f"{row['key']:<12} {row['job_number']:<35} {row['status']:<15} {row['location']:<12} {formatted_date:<16} {row['stage']:<15}")

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

    def filter_issues(self, df: pd.DataFrame, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Filter issues based on date range."""
        print("\nFiltering data:")
        
        if start_date:
            print(f"Start date: {start_date}")
        if end_date:
            print(f"End date: {end_date}")
        
        filtered_df = df.copy()
        
        # Convert end date to datetime
        if end_date:
            end_date = pd.to_datetime(end_date)
        
        # Don't filter the data - we need all historical data for proper cumulative counts
        # The date range will be used in aggregate_data instead
        
        print(f"Number of issues after filtering: {len(filtered_df)}")
        
        if not filtered_df.empty:
            min_date = filtered_df['created_date'].min().strftime('%Y-%m-%d %H:%M')
            max_date = filtered_df['created_date'].max().strftime('%Y-%m-%d %H:%M')
            print(f"Date range of data: {min_date} to {max_date}")
        
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

    def get_data(self, project_key: str, start_date: str = None, end_date: str = None, 
                 stages: List[str] = None, locations: List[str] = None, 
                 unit: str = 'Job Number', force_refresh: bool = False) -> Dict:
        """
        Get data with caching. force_refresh=True will bypass cache.
        """
        current_time = datetime.now()
        
        # Fetch new data if:
        # 1. Cache is empty OR
        # 2. Cache has expired OR
        # 3. Force refresh requested
        if (self._cached_issues is None or 
            self._last_fetch_time is None or
            current_time - self._last_fetch_time > self.CACHE_DURATION or
            force_refresh):
            
            print(f"Fetching fresh data for project {project_key}")
            jql_query = f'project = {project_key} ORDER BY created DESC'
            self._cached_issues = self.fetch_issues(jql_query)
            self._last_fetch_time = current_time
        else:
            print("Using cached data")
        
        # Use cached data for processing
        df = self.process_issues(self._cached_issues)
        
        # Filter by location if specified
        if locations:
            df = df[df['location'].isin(locations)]
        
        filtered_df = self.filter_issues(df, start_date, end_date)
        
        # Create complete date range
        date_range = pd.date_range(start=start_date, end=end_date)
        aggregated_data = self.aggregate_data(filtered_df, date_range, unit, stages)
        
        return {
            'df': filtered_df,
            'total_issues': self.get_total_issues(filtered_df),
            'percentage_issues': self.get_percentage_issues(filtered_df),
            'aggregated_data': aggregated_data
        }

    def extract_test_number(self, job_number: str) -> int:
        """Extract test number from job number string."""
        try:
            # Find all text within parentheses using cached pattern
            numbers = self.PARENS_PATTERN.findall(job_number)
            
            if not numbers:
                return 0
            
            # Check if content within parentheses contains month names
            months = ['January', 'February', 'March', 'April', 'May', 'June', 
                     'July', 'August', 'September', 'October', 'November', 'December',
                     'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            if any(month in numbers[0] for month in months):
                return 0

            # Handle arrow notation
            if '-->' in job_number:
                last_num = self.ARROW_NUM_PATTERN.search(job_number)
                if last_num:
                    return int(last_num.group(1))
                
                first_num = self.NUM_IN_PARENS_PATTERN.search(job_number)
                if first_num:
                    return int(first_num.group(1))
                return 0
                
            # Handle other formats
            if '-' in numbers[0]:  # Format: (9-3) or (41-11 = 30)
                nums = self.NUMBER_PATTERN.findall(numbers[0].split('=')[0])
                if len(nums) >= 2:
                    a, b = map(int, nums[:2])
                    return abs(a - b)
            elif '+' in numbers[0]:  # Format: (3+3)
                nums = self.NUMBER_PATTERN.findall(numbers[0])
                return sum(map(int, nums))
            else:
                match = self.NUMBER_PATTERN.search(numbers[0])
                return int(match.group()) if match else 0
                
        except Exception as e:
            print(f"Error extracting test number from {job_number}: {e}")
            return 0

    def aggregate_data(self, df: pd.DataFrame, date_range: pd.DatetimeIndex = None, 
                      unit: str = 'Job Number', stages: List[str] = None) -> pd.DataFrame:
        """Aggregate data based on unit type and stages."""
        # print("\nAggregating data:")
        # print(f"Input DataFrame shape: {df.shape}")
        
        STAGE_ORDER = ['Open', 'Sample Preparation', 'Testing', 'Report']
        stages_to_show = stages if stages else STAGE_ORDER
        
        if date_range is not None:
            dates = [d.date() for d in date_range]
            cumulative_counts = pd.DataFrame(0, index=dates, columns=stages_to_show)
            
            if not df.empty:
                for date in dates:
                    stage_counts = {stage: 0 for stage in stages_to_show}
                    
                    for _, issue in df.iterrows():
                        if issue['created_date'].date() > date:
                            continue
                        
                        # Determine the stage of the issue on this date
                        current_stage = issue['stage']
                        relevant_changes = [
                            change for change in issue['status_changes']
                            if change['date'].date() <= date
                        ]
                        
                        if relevant_changes:
                            last_change = sorted(relevant_changes, key=lambda x: x['date'])[-1]
                            current_stage = self.determine_stage(last_change['to_status'])
                        
                        # Only count if we're showing all stages or this is the selected stage
                        if current_stage in stages_to_show:
                            if unit == 'Test Number':
                                count = self.extract_test_number(issue['job_number'])
                            else:
                                count = 1
                            stage_counts[current_stage] += count
                    
                    for stage in stages_to_show:
                        cumulative_counts.loc[date, stage] = stage_counts[stage]
        
        return cumulative_counts