![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

# Job Live Tracking

An automatic live job tracking application that visualizes JIRA workflow data in real-time.

## Description

This application provides a real-time visualization of job statuses from JIRA, helping teams track their workflow across different stages (Sample Preparation, Testing, and Other). It features a dynamic line graph that updates automatically and allows for custom date range and stage filtering.

## Features

- Real-time data visualization with automatic 3-minute updates
- Interactive line graph with different colors for each stage
- Date range selection with Monday-Sunday week alignment
- Stage filtering (Sample Preparation, Testing, Other)
- Cumulative view of job counts
- Value labels on data points
- Dark theme interface

## Prerequisites

- Python 3.8 or higher
- JIRA account with API access
- PyQt5
- Required Python packages (see Requirements section)

## Installation

1. Clone the repository:
```
bash

git clone https://github.com/yourusername/job-live-tracking.git

cd job-live-tracking
```
2. Install required packages:
```
bash

pip install -r requirements.txt
```
3. Create a `config.py` file with your JIRA credentials:
```
python

JIRA_URL = "your_jira_url"
JIRA_USERNAME = "your_username"
JIRA_API_TOKEN = "your_api_token"
```

## Usage

1. Run the application:
```
bash
python live_job_tracking.py
```
2. Use the interface to:
   - Select date ranges (automatically aligns to Monday-Sunday weeks)
   - Filter by stages
   - View cumulative job counts
   - Refresh data manually or wait for automatic updates

## Configuration

The application uses the following configuration options:
- Date range: Monday to Sunday week selection
- Update interval: 3 minutes
- Stages: Sample Preparation, Testing, Other
- Graph colors:
  - Sample Preparation: Deep Blue
  - Testing: Orange-Red
  - Other: Yellow-Orange

## Project Structure
job-live-tracking/  
├── live_job_tracking.py # Main entry point  
├── data_processor.py # JIRA data processing  
├── gui.py # PyQt5 user interface  
├── config.py # Configuration (not in repo)  
└── requirements.txt # Package dependencies  

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

MIT License

Copyright (c) 2024 Wayne Kao

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Authors

- Wayne Kao - Initial work - [GitHub](https://github.com/me60714)

## Acknowledgments

- JIRA API documentation
- PyQt5 and PyQtGraph libraries

## Version

- Current Version: 1.0.0
- Last Updated: 2024-11-03