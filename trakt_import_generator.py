#!/usr/bin/env python3
"""
Trakt.tv Import Generator from Real-Debrid History

This script converts Real-Debrid download history to Trakt.tv import format
with accurate IMDB titles and IDs.
"""

import requests
import json
import csv
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import time
import os

# Configuration
REALDEBRID_API_TOKEN = "KLL4DOIIRQ3M7IISUNDXACKRHMTPYTI6SIJBBU3UYUDCWAOBJT6Q"
TMDB_API_KEY = "96ef2142c87c8faf881969ab547b27d5"  # Get from https://www.themoviedb.org/settings/api
REALDEBRID_BASE_URL = "https://api.real-debrid.com/rest/1.0"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

class TitleParser:
    """Parse and clean filenames to extract movie/show titles"""
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """Clean filename to extract title"""
        # Remove common file extensions
        filename = re.sub(r'\.(mkv|mp4|avi|mov|wmv|flv|webm|m4v)$', '', filename, flags=re.IGNORECASE)
        
        # Remove quality indicators (but be more careful)
        filename = re.sub(r'\s+(1080p|720p|480p|2160p|4K|HDRip|BRRip|WEBRip|BluRay|HDTV|WEB|HDRip|BRRip)\s*', ' ', filename, flags=re.IGNORECASE)
        
        # Remove codec info
        filename = re.sub(r'\s+(x264|x265|h264|h265|HEVC|AVC|AAC|AC3|DTS|FLAC)\s*', ' ', filename, flags=re.IGNORECASE)
        
        # Remove release group names (usually in brackets or parentheses)
        filename = re.sub(r'\[[^\]]*\]', '', filename)
        filename = re.sub(r'\([^)]*\)', '', filename)
        
        # Remove year patterns like (2023) or [2023] but keep standalone years
        filename = re.sub(r'[\[\(]\d{4}[\]\)]', '', filename)
        
        # Remove episode patterns for TV shows but keep show names
        filename = re.sub(r'\s+S\d{2}E\d{2}\s*', ' ', filename, flags=re.IGNORECASE)
        filename = re.sub(r'\s+\d{1,2}x\d{1,2}\s*', ' ', filename)
        
        # Remove website prefixes
        filename = re.sub(r'^www\.[^.]+\.[a-z]+\s*-\s*', '', filename, flags=re.IGNORECASE)
        
        # Remove special characters and extra spaces
        filename = re.sub(r'[._-]+', ' ', filename)
        filename = re.sub(r'\s+', ' ', filename)
        filename = filename.strip()
        
        return filename
    
    @staticmethod
    def extract_title_and_year(filename: str) -> Tuple[str, Optional[int]]:
        """Extract title and year from filename"""
        # Look for year patterns
        year_match = re.search(r'(\d{4})', filename)
        year = int(year_match.group(1)) if year_match else None
        
        # Remove year from title
        if year:
            filename = re.sub(r'\d{4}', '', filename)
        
        title = TitleParser.clean_filename(filename)
        return title, year

class TMDBLookup:
    """Handle TMDB API lookups for movies and TV shows"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
        # Also try with API key as parameter for older API versions
        self.params = {"api_key": api_key}
    
    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Search for a movie on TMDB"""
        try:
            params = {
                "query": title,
                "include_adult": False,
                "language": "en-US",
                "api_key": self.api_key
            }
            if year:
                params["year"] = year
            
            response = requests.get(f"{TMDB_BASE_URL}/search/movie", params=params)
            response.raise_for_status()
            
            results = response.json().get("results", [])
            if results:
                return results[0]  # Return first (best) match
            return None
            
        except Exception as e:
            print(f"Error searching movie '{title}': {e}")
            return None
    
    def search_tv_show(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Search for a TV show on TMDB"""
        try:
            params = {
                "query": title,
                "include_adult": False,
                "language": "en-US",
                "api_key": self.api_key
            }
            if year:
                params["first_air_date_year"] = year
            
            response = requests.get(f"{TMDB_BASE_URL}/search/tv", params=params)
            response.raise_for_status()
            
            results = response.json().get("results", [])
            if results:
                return results[0]  # Return first (best) match
            return None
            
        except Exception as e:
            print(f"Error searching TV show '{title}': {e}")
            return None
    
    def get_imdb_id(self, tmdb_id: int, media_type: str) -> Optional[str]:
        """Get IMDB ID from TMDB ID"""
        try:
            params = {"api_key": self.api_key}
            response = requests.get(f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}/external_ids", params=params)
            response.raise_for_status()
            
            external_ids = response.json()
            imdb_id = external_ids.get("imdb_id")
            
            if imdb_id and not imdb_id.startswith("tt"):
                imdb_id = f"tt{imdb_id}"
            
            return imdb_id
            
        except Exception as e:
            print(f"Error getting IMDB ID for {media_type} {tmdb_id}: {e}")
            return None

class RealDebridHistory:
    """Fetch Real-Debrid download history"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {"Authorization": f"Bearer {api_token}"}
    
    def fetch_downloads(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch downloads from Real-Debrid API"""
        try:
            print(f"🔍 Fetching downloads from Real-Debrid...")
            response = requests.get(f"{REALDEBRID_BASE_URL}/downloads", headers=self.headers, params={"limit": limit})
            response.raise_for_status()
            
            downloads = response.json()
            print(f"✅ Successfully fetched {len(downloads)} downloads")
            return downloads
            
        except Exception as e:
            print(f"❌ Error fetching downloads: {e}")
            return []

class TraktImportGenerator:
    """Generate Trakt.tv import JSON from Real-Debrid history"""
    
    def __init__(self, tmdb_api_key: str):
        self.tmdb = TMDBLookup(tmdb_api_key)
        self.realdebrid = RealDebridHistory(REALDEBRID_API_TOKEN)
        self.title_parser = TitleParser()
        
        # Cache for API calls
        self.title_cache = {}
        
    def process_downloads(self) -> List[Dict[str, Any]]:
        """Process downloads and generate Trakt import data"""
        downloads = self.realdebrid.fetch_downloads()
        trakt_entries = []
        
        print(f"\n🎬 Processing {len(downloads)} downloads for Trakt import...")
        
        for i, download in enumerate(downloads, 1):
            filename = download.get('filename', '')
            if not filename:
                continue
                
            print(f"   Processing {i}/{len(downloads)}: {filename[:50]}...")
            
            # Parse title and year
            title, year = self.title_parser.extract_title_and_year(filename)
            
            if not title or len(title) < 3:
                continue
            
            # Get download date (use generated date if available)
            generated = download.get('generated')
            if generated:
                try:
                    # Convert timestamp to ISO format
                    download_date = datetime.fromtimestamp(generated)
                    watched_at = download_date.isoformat() + "Z"
                except:
                    watched_at = None
            else:
                watched_at = None
            
            # Look up title on TMDB
            imdb_id = self.lookup_title(title, year)
            
            if imdb_id:
                entry = {
                    "imdb_id": imdb_id,
                    "watched_at": watched_at
                }
                trakt_entries.append(entry)
                print(f"     ✅ Found: {imdb_id} - {title}")
            else:
                print(f"     ❌ Not found: {title}")
            
            # Rate limiting
            time.sleep(0.1)
        
        return trakt_entries
    
    def lookup_title(self, title: str, year: Optional[int] = None) -> Optional[str]:
        """Look up title on TMDB and get IMDB ID"""
        cache_key = f"{title}_{year}"
        
        if cache_key in self.title_cache:
            return self.title_cache[cache_key]
        
        # Try movie search first
        movie_result = self.tmdb.search_movie(title, year)
        if movie_result:
            tmdb_id = movie_result.get("id")
            if tmdb_id:
                imdb_id = self.tmdb.get_imdb_id(tmdb_id, "movie")
                if imdb_id:
                    self.title_cache[cache_key] = imdb_id
                    return imdb_id
        
        # Try TV show search
        tv_result = self.tmdb.search_tv_show(title, year)
        if tv_result:
            tmdb_id = tv_result.get("id")
            if tmdb_id:
                imdb_id = self.tmdb.get_imdb_id(tmdb_id, "tv")
                if imdb_id:
                    self.title_cache[cache_key] = imdb_id
                    return imdb_id
        
        self.title_cache[cache_key] = None
        return None
    
    def save_trakt_json(self, entries: List[Dict[str, Any]], filename: str = None):
        """Save Trakt import data to JSON file"""
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

def main():
    """Main function"""
    print("🎬 Trakt.tv Import Generator from Real-Debrid History")
    print("=" * 60)
    
    # Check if TMDB API key is configured
    if TMDB_API_KEY == "your_tmdb_api_key_here":
        print("❌ Please configure your TMDB API key in the script")
        print("   Get one from: https://www.themoviedb.org/settings/api")
        return
    
    # Initialize generator
    generator = TraktImportGenerator(TMDB_API_KEY)
    
    # Process downloads
    trakt_entries = generator.process_downloads()
    
    if not trakt_entries:
        print("❌ No valid entries found for Trakt import")
        return
    
    # Save to JSON file
    generator.save_trakt_json(trakt_entries)
    
    print(f"\n✅ Done! Your Trakt import file is ready.")
    print(f"📋 Upload it to: https://trakt.tv/settings/import")

if __name__ == "__main__":
    main() 