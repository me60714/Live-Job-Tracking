![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

# Live Job Tracking

Real-time JIRA workflow visualization tool for tracking job progress.

## Features

- Real-time visualization with 3-minute auto-updates
- Interactive dark theme graph
- Multi-filter support:
  - Date range
  - Job stage
  - Location (YEG/YUL/YYZ)
  - Unit type (Job/Test Number)
- API Management:
  - Automatic token validation
  - 7-day expiration warnings
  - Forced updates for expired tokens
- Rate limiting protection for API calls

## Prerequisites

- Python 3.8+
- JIRA account with API access

## Setup

1. Install:
```bash
git clone https://github.com/me60714/Live-Job-Tracking.git
cd Live-Job-Tracking
pip install -r requirements.txt
```

2. Configure `config.py`:
```python
JIRA_URL = "your_jira_url"
JIRA_USERNAME = "your_username"
JIRA_API_TOKEN = "your_api_token"
TOKEN_CREATED_DATE = "YYYY-MM-DD"
```

3. Run the application:
```bash
python live_job_tracking.py
```

Note: To manually update the API token when needed:
```bash
python api_manager.py
```

## Versions

### 1.1.3 (2024-12-20)
- Improved graph visualization with value labels
- Added cumulative totals display for both job and test numbers

### 1.1.2 (2024-12-06)
- Implemented rate-limiting protection for API requests
- Enhanced error handling for API token validation
- Added automatic token expiration warnings (7-day notice)
- Improved data validation for job number formats

### 1.1.1 (2024-11-22)
- Added unit and location filtering
- Enhanced API token management
- Improved visualization scaling

### 1.1.0 (2024-11-15)
- Added API security features
- New status categories

### 1.0.0 (2024-11-03)
- Initial release

## Author

Wayne Kao - [GitHub](https://github.com/me60714)

MIT License - Copyright (c) 2024 Wayne Kao
