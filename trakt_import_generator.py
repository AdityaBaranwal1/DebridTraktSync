#!/usr/bin/env python3
"""
Trakt.tv Import Generator from Real-Debrid History

This script converts Real-Debrid download history to a Trakt.tv import file
with accurate IMDB titles and IDs.  It includes robust filename parsing,
fallback searches against TMDB, and caching to reduce duplicate lookups.
"""

import requests
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import time

# Attempt to load configuration.  A separate config.py file (ignored by Git)
# should define REALDEBRID_API_TOKEN and TMDB_API_KEY.  If config.py is
# missing, instruct the user to copy config_template.py and fill in their
# credentials.
try:
    from config import REALDEBRID_API_TOKEN, TMDB_API_KEY
except ImportError:
    print("❌ Error: config.py not found!")
    print("   Please copy config_template.py to config.py and add your API keys")
    exit(1)

# Base URLs for Real-Debrid and TMDB APIs
REALDEBRID_BASE_URL = "https://api.real-debrid.com/rest/1.0"
TMDB_BASE_URL = "https://api.themoviedb.org/3"


class TitleParser:
    """Parse and clean filenames to extract movie/show titles and years."""

    # A list of common tokens found in release names that should be stripped from
    # filenames.  These include streaming platforms, encoding information,
    # release group tags and various quality descriptors.  The list is kept
    # separate so it can be easily extended.
    EXTRA_TOKENS = [
        "AMZN", "NF", "IP", "PCOK", "DSNP", "DSNY", "WEB", "WEB-DL", "WEBRip", "BluRay",
        "BRRip", "HDRip", "Remux", "HDTS", "HDTC", "DVDRip", "HDTV", "HDR", "HDCAM",
        "DDP", "DD+", "DD", "AAC", "AC3", "DTS", "FLAC",
        "10bit", "12bit", "HEVC", "H265", "H264", "x264", "x265", "AVC", "VP9",
        "MeGusta", "EDITH", "Bearfish", "RAWR", "NIXON", "Kitsune"
    ]

    @staticmethod
    def clean_filename(filename: str) -> str:
        """Clean a filename by removing common noise words and patterns.

        The cleaning routine performs the following steps:
        1. Normalize separators (dots, underscores, dashes) to spaces.
        2. Remove file extensions.
        3. Remove content within brackets [] or parentheses ().
        4. Remove known tokens such as release group names, codecs and
           streaming platform identifiers.
        5. Remove season/episode markers (SxxEyy, 1x02).
        6. Remove website prefixes like 'www.somesite.com - '.
        7. Remove leftover single-character tokens and orphan digits.
        8. Collapse multiple spaces and trim leading/trailing whitespace.

        Args:
            filename: The raw filename from Real‑Debrid history.

        Returns:
            A cleaned string suitable for TMDB search.
        """
        # Step 1: normalise separators to spaces
        cleaned = re.sub(r'[._-]+', ' ', filename)

        # Step 2: remove common file extensions at the end of the filename
        cleaned = re.sub(r'\.(mkv|mp4|avi|mov|wmv|flv|webm|m4v)$', '', cleaned, flags=re.IGNORECASE)

        # Step 3: remove bracketed release group names or notes
        cleaned = re.sub(r'\[[^\]]*\]', ' ', cleaned)  # remove [xxx]
        cleaned = re.sub(r'\([^)]*\)', ' ', cleaned)    # remove (xxx)

        # Step 4: remove season/episode markers (e.g. S01E02, 1x02) anywhere in the string
        cleaned = re.sub(r'S\d{1,2}E\d{1,2}', ' ', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\b\d{1,2}x\d{1,2}\b', ' ', cleaned, flags=re.IGNORECASE)

        # Step 5: remove website prefixes such as 'www.somesite.com - '
        cleaned = re.sub(r'^www\.[^\s]+\s*-\s*', '', cleaned, flags=re.IGNORECASE)

        # Step 6: remove quality indicators and codecs (but be more conservative)
        quality_patterns = [
            r'\b(1080p|720p|480p|2160p|4k|hdr)\b',
            r'\b(web|web-dl|webrip|bluray|hdtv|remux|cam|dvdrip|hdrip|brrip)\b',
            r'\b(x264|x265|h264|h265|hevc|avc|aac|ac3|dts|flac|vp9)\b',
            r'\b(ddp|dd\+|dd|10bit|12bit)\b'
        ]
        
        for pattern in quality_patterns:
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)

        # Step 7: remove release group names and streaming platforms (but preserve show titles)
        release_groups = [
            r'\b(edith|megusta|bearfish|rawr|nixon|kitsune|bae|trollhd|2hd|shaanig|tombdoc|syncup|hdhub4u)\b',
            r'\b(amzn|nf|ip|pcok|dsnp|dsny)\b'
        ]
        
        for pattern in release_groups:
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)

        # Step 8: split on whitespace and remove single-character tokens or orphan digits
        tokens = [tok for tok in cleaned.split() if len(tok) > 1 and not tok.isdigit()]
        cleaned = ' '.join(tokens)

        # Step 9: collapse multiple spaces and trim
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned

    @staticmethod
    def extract_title_and_year(filename: str) -> Tuple[str, Optional[int]]:
        """Extract a cleaned title and an optional release year from a filename.

        The function looks for a four‑digit year between 1900 and 2099.  If a
        valid year is found, it is removed from the string prior to cleaning.

        Args:
            filename: The raw filename.

        Returns:
            A tuple of (title, year) where year may be None if no year was detected.
        """
        # Find a four‑digit year in range 1900–2099
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', filename)
        year = int(year_match.group(1)) if year_match else None

        # Remove the year (only first occurrence) from the filename for title extraction
        if year_match:
            filename_no_year = re.sub(year_match.group(1), ' ', filename, count=1)
        else:
            filename_no_year = filename

        # Clean the remaining filename to get the title
        title = TitleParser.clean_filename(filename_no_year)
        return title, year


class TMDBLookup:
    """Handle TMDB API lookups for movies, TV shows and mixed results."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search_movie_with_external_ids(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Search for a movie on TMDB and get external IDs in one request."""
        try:
            params: Dict[str, Any] = {
                "query": title,
                "include_adult": False,
                "language": "en-US",
                "api_key": self.api_key,
            }
            if year:
                params["year"] = year
            resp = requests.get(f"{TMDB_BASE_URL}/search/movie", params=params)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if not results:
                return None
            
            # Get the first result and fetch its external IDs
            movie = results[0]
            tmdb_id = movie.get("id")
            if tmdb_id:
                # Use append_to_response to get external IDs in one call
                detail_params = {"api_key": self.api_key, "append_to_response": "external_ids"}
                detail_resp = requests.get(f"{TMDB_BASE_URL}/movie/{tmdb_id}", params=detail_params)
                detail_resp.raise_for_status()
                detail_data = detail_resp.json()
                
                # Extract IMDB ID from external_ids
                external_ids = detail_data.get("external_ids", {})
                imdb_id = external_ids.get("imdb_id")
                if imdb_id and not imdb_id.startswith("tt"):
                    imdb_id = f"tt{imdb_id}"
                
                # Add IMDB ID to the movie result
                movie["imdb_id"] = imdb_id
                return movie
            return None
        except Exception as e:
            print(f"Error searching movie '{title}': {e}")
            return None

    def search_tv_show_with_external_ids(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Search for a TV show on TMDB and get external IDs in one request."""
        try:
            params: Dict[str, Any] = {
                "query": title,
                "include_adult": False,
                "language": "en-US",
                "api_key": self.api_key,
            }
            if year:
                params["first_air_date_year"] = year
            resp = requests.get(f"{TMDB_BASE_URL}/search/tv", params=params)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if not results:
                return None
            
            # Get the first result and fetch its external IDs
            tv_show = results[0]
            tmdb_id = tv_show.get("id")
            if tmdb_id:
                # Use append_to_response to get external IDs in one call
                detail_params = {"api_key": self.api_key, "append_to_response": "external_ids"}
                detail_resp = requests.get(f"{TMDB_BASE_URL}/tv/{tmdb_id}", params=detail_params)
                detail_resp.raise_for_status()
                detail_data = detail_resp.json()
                
                # Extract IMDB ID from external_ids
                external_ids = detail_data.get("external_ids", {})
                imdb_id = external_ids.get("imdb_id")
                if imdb_id and not imdb_id.startswith("tt"):
                    imdb_id = f"tt{imdb_id}"
                
                # Add IMDB ID to the TV show result
                tv_show["imdb_id"] = imdb_id
                return tv_show
            return None
        except Exception as e:
            print(f"Error searching TV show '{title}': {e}")
            return None

    def search_multi_with_external_ids(self, title: str) -> List[Dict[str, Any]]:
        """Search TMDB across movies, TV shows and get external IDs for each result."""
        try:
            params = {
                "query": title,
                "include_adult": False,
                "language": "en-US",
                "api_key": self.api_key,
            }
            resp = requests.get(f"{TMDB_BASE_URL}/search/multi", params=params)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            
            # Filter to only movies and TV shows, and get external IDs for each
            valid_results = []
            for item in results:
                media_type = item.get("media_type")
                if media_type in ("movie", "tv"):
                    tmdb_id = item.get("id")
                    if tmdb_id:
                        # Use append_to_response to get external IDs
                        detail_params = {"api_key": self.api_key, "append_to_response": "external_ids"}
                        detail_resp = requests.get(f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}", params=detail_params)
                        detail_resp.raise_for_status()
                        detail_data = detail_resp.json()
                        
                        # Extract IMDB ID
                        external_ids = detail_data.get("external_ids", {})
                        imdb_id = external_ids.get("imdb_id")
                        if imdb_id and not imdb_id.startswith("tt"):
                            imdb_id = f"tt{imdb_id}"
                        
                        # Add IMDB ID to the result
                        item["imdb_id"] = imdb_id
                        valid_results.append(item)
            
            return valid_results
        except Exception as e:
            print(f"Error performing multi search for '{title}': {e}")
            return []

    # Keep the old methods for backward compatibility
    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Search for a movie on TMDB.  Returns the first result if found."""
        return self.search_movie_with_external_ids(title, year)

    def search_tv_show(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Search for a TV show on TMDB.  Returns the first result if found."""
        return self.search_tv_show_with_external_ids(title, year)

    def search_multi(self, title: str) -> List[Dict[str, Any]]:
        """Search TMDB across movies, TV shows and other media types."""
        return self.search_multi_with_external_ids(title)

    def get_imdb_id(self, tmdb_id: int, media_type: str) -> Optional[str]:
        """Retrieve the IMDB ID for a given TMDB ID and media type (movie or tv)."""
        try:
            params = {"api_key": self.api_key}
            resp = requests.get(f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}/external_ids", params=params)
            resp.raise_for_status()
            external_ids = resp.json()
            imdb_id = external_ids.get("imdb_id")
            if imdb_id and not imdb_id.startswith("tt"):
                imdb_id = f"tt{imdb_id}"
            return imdb_id
        except Exception as e:
            print(f"Error getting IMDB ID for {media_type} {tmdb_id}: {e}")
            return None


class RealDebridHistory:
    """Fetch Real‑Debrid download history."""

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {"Authorization": f"Bearer {api_token}"}

    def fetch_downloads(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch downloads from Real‑Debrid.  Returns an empty list on error."""
        try:
            print("🔍 Fetching downloads from Real‑Debrid...")
            resp = requests.get(f"{REALDEBRID_BASE_URL}/downloads", headers=self.headers, params={"limit": limit})
            resp.raise_for_status()
            downloads = resp.json()
            print(f"✅ Successfully fetched {len(downloads)} downloads")
            return downloads
        except Exception as e:
            print(f"❌ Error fetching downloads: {e}")
            return []


class TraktImportGenerator:
    """Generate Trakt.tv import JSON from Real‑Debrid download history."""

    def __init__(self, tmdb_api_key: str):
        self.tmdb = TMDBLookup(tmdb_api_key)
        self.realdebrid = RealDebridHistory(REALDEBRID_API_TOKEN)
        self.title_parser = TitleParser()
        self.title_cache: Dict[str, Optional[str]] = {}

    def process_downloads(self) -> List[Dict[str, Any]]:
        """Process downloads and assemble a list of Trakt import entries."""
        downloads = self.realdebrid.fetch_downloads()
        trakt_entries: List[Dict[str, Any]] = []
        print(f"\n🎬 Processing {len(downloads)} downloads for Trakt import...")
        for i, download in enumerate(downloads, 1):
            filename = download.get('filename', '')
            if not filename:
                continue
            print(f"   Processing {i}/{len(downloads)}: {filename[:50]}...")
            title, year = self.title_parser.extract_title_and_year(filename)
            if not title or len(title) < 3:
                continue
            # Derive watched date from 'generated' timestamp if present
            generated = download.get('generated')
            watched_at: Optional[str]
            if generated:
                try:
                    dt = datetime.fromtimestamp(generated)
                    watched_at = dt.isoformat() + "Z"
                except Exception:
                    watched_at = None
            else:
                watched_at = None
            imdb_id = self.lookup_title(title, year)
            if imdb_id:
                trakt_entries.append({"imdb_id": imdb_id, "watched_at": watched_at})
                print(f"     ✅ Found: {imdb_id} - {title}")
            else:
                print(f"     ❌ Not found: {title}")
            # Short delay to respect TMDB rate limits
            time.sleep(0.1)
        return trakt_entries

    def lookup_title(self, title: str, year: Optional[int] = None) -> Optional[str]:
        """Look up a title on TMDB using multiple strategies and return an IMDB ID."""
        cache_key = f"{title}_{year}"
        if cache_key in self.title_cache:
            return self.title_cache[cache_key]

        def attempt_lookup(search_title: str, search_year: Optional[int]) -> Optional[str]:
            """Try movie, TV and multi searches for a given title/year combination."""
            # Try movie search (now includes external IDs)
            result = self.tmdb.search_movie(search_title, search_year)
            if result and result.get("imdb_id"):
                return result.get("imdb_id")
            
            # Try TV search (now includes external IDs)
            result = self.tmdb.search_tv_show(search_title, search_year)
            if result and result.get("imdb_id"):
                return result.get("imdb_id")
            
            # Try multi search (now includes external IDs)
            multi_results = self.tmdb.search_multi(search_title)
            for item in multi_results:
                if item.get("imdb_id"):
                    return item.get("imdb_id")
            return None

        # Strategy 1: Title with provided year
        imdb = attempt_lookup(title, year)
        
        # Strategy 2: Title without year if the first attempt failed
        if not imdb and year is not None:
            imdb = attempt_lookup(title, None)
        
        # Strategy 3: Remove region suffixes and retry
        if not imdb:
            region_suffixes = [" US", " UK", " AU", " CA", " NZ"]
            for suffix in region_suffixes:
                if title.endswith(suffix):
                    trimmed = title[: -len(suffix)].strip()
                    imdb = attempt_lookup(trimmed, year)
                    if imdb:
                        break
                    imdb = attempt_lookup(trimmed, None)
                    if imdb:
                        break
        
        # Strategy 4: Try with just the first few words (for long titles)
        if not imdb and len(title.split()) > 3:
            words = title.split()
            # Try first 2-3 words
            for word_count in [3, 2]:
                if len(words) >= word_count:
                    short_title = ' '.join(words[:word_count])
                    imdb = attempt_lookup(short_title, year)
                    if imdb:
                        break
                    imdb = attempt_lookup(short_title, None)
                    if imdb:
                        break
        
        # Strategy 5: Remove common words that might interfere
        if not imdb:
            common_words = ["the", "a", "an"]
            for word in common_words:
                if title.lower().startswith(word + " "):
                    trimmed = title[len(word):].strip()
                    imdb = attempt_lookup(trimmed, year)
                    if imdb:
                        break
                    imdb = attempt_lookup(trimmed, None)
                    if imdb:
                        break
        
        # Cache the result (even if None) to avoid repeated lookups
        self.title_cache[cache_key] = imdb
        return imdb

    def save_trakt_json(self, entries: List[Dict[str, Any]], filename: str = None) -> None:
        """Save Trakt import data to a JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trakt_import_{timestamp}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
            print(f"💾 Trakt import data saved to {filename}")
            print(f"📊 Total entries: {len(entries)}")
        except Exception as e:
            print(f"❌ Error saving Trakt JSON: {e}")


def main() -> None:
    """Entry point for generating a Trakt.tv import file."""
    print("🎬 Trakt.tv Import Generator from Real‑Debrid History")
    print("=" * 60)
    # Ensure API keys are configured
    if TMDB_API_KEY == "your_tmdb_api_key_here" or REALDEBRID_API_TOKEN == "your_real_debrid_api_token_here":
        print("❌ Please configure your API keys in config.py")
        print("   Copy config_template.py to config.py and add your API keys")
        return
    generator = TraktImportGenerator(TMDB_API_KEY)
    entries = generator.process_downloads()
    if not entries:
        print("❌ No valid entries found for Trakt import")
        return
    generator.save_trakt_json(entries)
    print(f"\n✅ Done! Your Trakt import file is ready.")
    print(f"📋 Upload it to: https://trakt.tv/settings/import")


if __name__ == "__main__":
    main()