# Trakt.tv Import Generator from Real-Debrid History

This script converts your Real-Debrid download history into a Trakt.tv import file with accurate IMDB titles and IDs.

## Features

- **Smart Title Parsing**: Cleans filenames to extract accurate movie/show titles
- **TMDB Integration**: Uses TMDB API to find correct titles and IMDB IDs
- **Trakt Format**: Generates proper JSON format for Trakt.tv import
- **Date Tracking**: Includes download dates as watch dates
- **Caching**: Caches API calls to avoid duplicates
- **Error Handling**: Robust error handling and logging

## Setup

### 1. Get TMDB API Key
1. Go to [TMDB Settings](https://www.themoviedb.org/settings/api)
2. Create an account if you don't have one
3. Request an API key (v3 auth)
4. Copy your API key

### 2. Configure the Script
Edit `trakt_import_generator.py` and replace:
```python
TMDB_API_KEY = "your_tmdb_api_key_here"
```
with your actual TMDB API key.

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage

Run the script:
```bash
python trakt_import_generator.py
```

The script will:
1. **Fetch** your Real-Debrid download history
2. **Parse** filenames to extract titles and years
3. **Look up** each title on TMDB to find accurate IMDB IDs
4. **Generate** a Trakt.tv import JSON file
5. **Save** the file with timestamp

## Output

The script generates a JSON file like:
```json
[
  {
    "imdb_id": "tt0068646",
    "watched_at": "2024-10-25T20:00:00Z"
  },
  {
    "imdb_id": "tt15239678",
    "watched_at": "2024-04-30T11:00:00Z"
  }
]
```

## Import to Trakt.tv

1. Go to [Trakt.tv Settings](https://trakt.tv/settings/import)
2. Scroll to "JSON" section
3. Upload your generated JSON file
4. Select import options (watched history, ratings, etc.)
5. Click "Import"

## Title Parsing

The script intelligently cleans filenames by removing:
- File extensions (.mkv, .mp4, etc.)
- Quality indicators (1080p, 720p, BluRay, etc.)
- Codec info (x264, h265, etc.)
- Release group names [EDITH], (ShAaNiG), etc.
- Episode patterns (S01E02, 1x02)
- Special characters and extra spaces

## Examples

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

## Rate Limiting

The script includes rate limiting (0.1s between API calls) to respect TMDB's API limits.

## Troubleshooting

### No TMDB API Key
- Get a free API key from TMDB
- Replace the placeholder in the script

### No Results Found
- Some filenames may be too obscure
- Check the console output for failed lookups
- Consider manual corrections for important titles

### API Errors
- Check your internet connection
- Verify TMDB API key is correct
- Wait and try again (TMDB may be temporarily unavailable)

## File Structure

```
RealDebridHistory/
├── trakt_import_generator.py    # Main script
├── real_debrid_history.py       # Original history script
├── requirements.txt             # Dependencies
├── README_TRAKT.md             # This file
└── trakt_import_YYYYMMDD_HHMMSS.json  # Generated output
``` 