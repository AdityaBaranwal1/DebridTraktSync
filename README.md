# Real-Debrid Download History Fetcher

This Python script fetches your complete download history from Real-Debrid using their official REST API.

## Features

- **Complete History**: Fetches up to 5,000 downloads from your Real-Debrid account
- **Statistics**: Provides summary statistics including total downloads and data usage
- **Multiple Formats**: Saves data in both JSON and CSV formats
- **Formatted Display**: Shows a clean table of your downloads in the terminal
- **Error Handling**: Robust error handling for API requests

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **API Token**: The script is already configured with your API token:
   ```
   KLL4DOIIRQ3M7IISUNDXACKRHMTPYTI6SIJBBU3UYUDCWAOBJT6Q
   ```

## Usage

Simply run the script:
```bash
python real_debrid_history.py
```

## Output

The script will:
1. **Fetch** your download history from Real-Debrid
2. **Display** statistics including:
   - Total number of downloads
   - Total data usage in GB
   - Breakdown by download status
3. **Show** a formatted table of the first 50 downloads
4. **Save** complete data to timestamped JSON and CSV files

## Output Files

- `real_debrid_downloads_YYYYMMDD_HHMMSS.json` - Complete data in JSON format
- `real_debrid_downloads_YYYYMMDD_HHMMSS.csv` - Complete data in CSV format

## API Endpoint Used

- **URL**: `https://api.real-debrid.com/rest/1.0/downloads`
- **Method**: GET
- **Authentication**: Bearer token
- **Parameters**: `limit=5000` (maximum downloads to fetch)

## Data Fields

The script captures all available fields from the Real-Debrid API response, including:
- Download ID
- Filename
- File size (bytes)
- Download status
- Timestamps
- And any other fields provided by the API

## Security Note

Your API token is included in the script. For production use, consider:
- Moving the token to an environment variable
- Using a configuration file
- Adding the script to `.gitignore` if using version control 