![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

# Live Job Tracking

An automatic live job tracking application that visualizes JIRA workflow data in real-time.

## Features

### Core Functionality
- Real-time JIRA data visualization with 3-minute auto-updates
- Cumulative view of job progression through workflow stages
- Manual refresh option

### Visualization
- Interactive line graph with value labels, dark theme, and dynamic scaling
- Stage-specific color coding for better readability

### Filtering Options
- Date range selection (Monday-Friday work week)
- Stage filtering (Open, Sample Preparation, Testing, Report)
- Location filtering (Toronto, Montreal, Edmonton)
- Unit display options (Job Numbers/Test Numbers)

### Security & Performance
- API token validation with 90-day rotation policy
- Rate limiting protection for JIRA API calls

## Prerequisites

- Python 3.8 or higher
- JIRA account with API access
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:  
```bash
git clone https://github.com/me60714/Live-Job-Tracking.git
cd Live-Job-Tracking
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `config.py` file with your JIRA credentials:
```python
JIRA_URL = "your_jira_url"
JIRA_USERNAME = "your_username"
JIRA_API_TOKEN = "your_api_token"
```

## Configuration

### Display Settings
- Work week: Monday-Friday
- Update interval: 3 minutes

### Visualization Colors
- Open: Yellow (#FFBB00)
- Sample Preparation: Deep Blue (#375E97)
- Testing: Orange-Red (#FB6542)
- Report: Green (#008000)

### Locations
- Toronto (default)
- Montreal
- Edmonton

## Project Structure
```
Live-Job-Tracking/  
├── live_job_tracking.py #Main entry point  
├── data_processor.py    #JIRA data processing  
├── gui.py              #PyQt5 user interface  
├── config.py           #Configuration (not in repo)  
├── api_checker.py      #API token validation   
├── rate_limiter.py     #Rate limit protection  
└── requirements.txt    #Package dependencies  
```

## Version History

### Version 1.1.1 (2024-11-22)
- Better y-axis scaling
- Added unit selection filter (Job Number/Test Number)
- Added location filtering
- Enhanced status change history tracking

### Version 1.1.0 (2024-11-15)
- Added API token validation and rate limiting
- Added new status categories and visualization support

### Version 1.0.0 (2024-11-03)
- Initial release with basic job tracking functionality

## Authors

- Wayne Kao - [GitHub](https://github.com/me60714)

## License

MIT License - Copyright (c) 2024 Wayne Kao

[Full license text](https://opensource.org/licenses/MIT)
