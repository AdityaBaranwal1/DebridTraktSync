# DebridTraktSync

A Python tool to sync your Real-Debrid download history to Trakt.tv with accurate IMDB titles and IDs.

## Features

- **Real-Debrid Integration**: Fetches your complete download history from Real-Debrid API
- **Smart Title Parsing**: Intelligently cleans filenames to extract accurate movie/show titles
- **TMDB Integration**: Uses TMDB API to find correct titles and IMDB IDs
- **Trakt.tv Export**: Generates perfect JSON format for Trakt.tv import
- **Date Tracking**: Includes download dates as watch dates
- **Secure Configuration**: API keys stored in separate config file (not in code)

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/AdityaBaranwal1/DebridTraktSync.git
cd DebridTraktSync
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
```bash
# Copy the template and add your API keys
cp config_template.py config.py
# Edit config.py with your actual API keys
```

### 4. Get Your API Keys

**Real-Debrid API Token:**
- Go to [Real-Debrid API](https://real-debrid.com/apitoken)
- Copy your API token

**TMDB API Key:**
- Go to [TMDB Settings](https://www.themoviedb.org/settings/api)
- Create account and request API key (v3 auth)

### 5. Run the Tools

**Fetch Real-Debrid History:**
```bash
python real_debrid_history.py
```

**Generate Trakt.tv Import:**
```bash
python trakt_import_generator.py
```

## Configuration

Edit `config.py` with your API keys:

```python
# Real-Debrid API Configuration
REALDEBRID_API_TOKEN = "your_actual_real_debrid_token"

# TMDB API Configuration  
TMDB_API_KEY = "your_actual_tmdb_api_key"

# Optional: Trakt.tv API Configuration (for future features)
TRAKT_CLIENT_ID = "your_trakt_client_id"
TRAKT_CLIENT_SECRET = "your_trakt_client_secret"
```

## Security

- **API keys are never committed to Git** - `config.py` is in `.gitignore`
- **Template-based configuration** - Users copy template and add their own keys
- **No hardcoded secrets** - All sensitive data is externalized

## Output Files

The tools generate:
- `real_debrid_downloads_YYYYMMDD_HHMMSS.json` - Complete download history
- `real_debrid_downloads_YYYYMMDD_HHMMSS.csv` - CSV format for analysis
- `trakt_import_YYYYMMDD_HHMMSS.json` - Trakt.tv import file

## Trakt.tv Import

1. Go to [Trakt.tv Settings](https://trakt.tv/settings/import)
2. Scroll to "JSON" section
3. Upload your generated `trakt_import_*.json` file
4. Select import options (watched history, ratings, etc.)
5. Click "Import"

## Title Parsing Examples

**Input filename:**
```
Love.Island.US.S05E22.1080p.WEB.h264-EDITH[eztv.re].mkv
```

**Parsed title:**
```
Love Island US
```

**Result:**
- Searches TMDB for "Love Island US"
- Finds TV show with IMDB ID
- Adds to Trakt import with download date

## File Structure

```
DebridTraktSync/
├── real_debrid_history.py       # Fetch Real-Debrid download history
├── trakt_import_generator.py    # Generate Trakt.tv import file
├── config_template.py           # Template for API keys
├── config.py                    # Your API keys (not in Git)
├── requirements.txt             # Python dependencies
├── .gitignore                   # Prevents sensitive files from being committed
├── README.md                    # This file
└── README_TRAKT.md             # Detailed Trakt import guide
```

## Troubleshooting

### Configuration Issues
- **"config.py not found"**: Copy `config_template.py` to `config.py`
- **"API keys not configured"**: Edit `config.py` with your actual API keys

### API Issues
- **Real-Debrid errors**: Check your API token is valid
- **TMDB errors**: Verify your API key is correct
- **Rate limiting**: Script includes delays to respect API limits

### Import Issues
- **No results found**: Some filenames may be too obscure
- **Wrong titles**: Check console output for failed lookups

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

If you encounter issues:
1. Check the troubleshooting section
2. Verify your API keys are correct
3. Check the console output for error messages
4. Open an issue on GitHub with details