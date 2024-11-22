![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

# Live Job Tracking

Real-time JIRA workflow visualization tool with automated updates and filtering capabilities.

## Features

- Real-time data visualization with 3-minute auto-updates
- Interactive line graph with dark theme
- Filtering by date, stage, location, and unit type
- Automated API token management with expiration warnings
- Rate limiting protection for API calls

## Prerequisites

- Python 3.8+
- JIRA account with API access

## Quick Start

1. Clone and install:
```bash
git clone https://github.com/me60714/Live-Job-Tracking.git
cd Live-Job-Tracking
pip install -r requirements.txt
```

2. Configure JIRA credentials in `config.py`:
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

## API Token Management

- Automatic validation on startup
- 7-day expiration warnings
- Manual update utility:
```bash
python api_manager.py
```

## Version History

### Version 1.1.1 (2024-11-22)
- Added unit and location filtering
- Enhanced API token management and security
- Improved visualization scaling

### Version 1.1.0 (2024-11-15)
- Added token validation and rate limiting
- New status categories support

### Version 1.0.0 (2024-11-03)
- Initial release

## Author

Wayne Kao - [GitHub](https://github.com/me60714)

## License

MIT License - Copyright (c) 2024 Wayne Kao
