#!/usr/bin/env python3
"""
Real-Debrid Download History Fetcher

This script fetches all downloads from your Real-Debrid account using their REST API.
"""

import requests
import json
import csv
from datetime import datetime
from typing import List, Dict, Any
import os

# Configuration
API_TOKEN = "KLL4DOIIRQ3M7IISUNDXACKRHMTPYTI6SIJBBU3UYUDCWAOBJT6Q"
BASE_URL = "https://api.real-debrid.com/rest/1.0"
DOWNLOADS_ENDPOINT = f"{BASE_URL}/downloads"

class RealDebridHistory:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {"Authorization": f"Bearer {api_token}"}
        
    def fetch_downloads(self, limit: int = 5000) -> List[Dict[str, Any]]:
        """
        Fetch downloads from Real-Debrid API
        
        Args:
            limit: Maximum number of downloads to fetch
            
        Returns:
            List of download dictionaries
        """
        try:
            print(f"🔍 Fetching downloads from Real-Debrid (limit: {limit})...")
            
            # Try different parameter combinations
            params_options = [
                {"limit": limit},
                {"limit": limit, "page": 1},
                {"limit": limit, "offset": 0},
                {}  # No parameters
            ]
            
            for i, params in enumerate(params_options):
                try:
                    print(f"   Trying parameters: {params}")
                    response = requests.get(DOWNLOADS_ENDPOINT, headers=self.headers, params=params)
                    response.raise_for_status()
                    
                    # Check if response is valid JSON
                    if response.text.strip():
                        downloads = response.json()
                        if downloads:
                            print(f"✅ Successfully fetched {len(downloads)} downloads")
                            return downloads
                        else:
                            print(f"   Empty response with params: {params}")
                    else:
                        print(f"   Empty response body with params: {params}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"   Request failed with params {params}: {e}")
                except json.JSONDecodeError as e:
                    print(f"   JSON decode error with params {params}: {e}")
                    print(f"   Response text: {response.text[:200]}...")
            
            print("❌ All parameter combinations failed")
            return []
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return []
    
    def display_downloads(self, downloads: List[Dict[str, Any]], max_display: int = 50):
        """
        Display downloads in a formatted table
        
        Args:
            downloads: List of download dictionaries
            max_display: Maximum number of downloads to display
        """
        if not downloads:
            print("No downloads found.")
            return
            
        print(f"\n📋 Displaying first {min(max_display, len(downloads))} downloads:")
        print("-" * 100)
        print(f"{'ID':<12} {'Filename':<50} {'Size (MB)':<12} {'Status':<10}")
        print("-" * 100)
        
        for download in downloads[:max_display]:
            download_id = str(download.get('id', 'N/A'))
            filename = download.get('filename', 'N/A')
            # Truncate filename if too long
            if len(filename) > 47:
                filename = filename[:44] + "..."
            
            # Convert size to MB if available
            size_bytes = download.get('bytes', 0)
            size_mb = size_bytes / (1024 * 1024) if size_bytes else 0
            
            status = download.get('status', 'N/A')
            
            print(f"{download_id:<12} {filename:<50} {size_mb:<12.1f} {status:<10}")
    
    def save_to_json(self, downloads: List[Dict[str, Any]], filename: str = None):
        """
        Save downloads to JSON file
        
        Args:
            downloads: List of download dictionaries
            filename: Output filename (optional)
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"real_debrid_downloads_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(downloads, f, indent=2, ensure_ascii=False)
            print(f"💾 Downloads saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving to JSON: {e}")
    
    def save_to_csv(self, downloads: List[Dict[str, Any]], filename: str = None):
        """
        Save downloads to CSV file
        
        Args:
            downloads: List of download dictionaries
            filename: Output filename (optional)
        """
        if not downloads:
            print("No downloads to save.")
            return
            
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"real_debrid_downloads_{timestamp}.csv"
        
        try:
            # Get all possible fields from downloads
            fieldnames = set()
            for download in downloads:
                fieldnames.update(download.keys())
            fieldnames = sorted(list(fieldnames))
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(downloads)
            
            print(f"💾 Downloads saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving to CSV: {e}")
    
    def get_statistics(self, downloads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics from downloads
        
        Args:
            downloads: List of download dictionaries
            
        Returns:
            Dictionary with statistics
        """
        if not downloads:
            return {}
        
        total_downloads = len(downloads)
        total_size_bytes = sum(d.get('bytes', 0) for d in downloads)
        total_size_gb = total_size_bytes / (1024**3)
        
        # Count by status
        status_counts = {}
        for download in downloads:
            status = download.get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_downloads': total_downloads,
            'total_size_gb': total_size_gb,
            'total_size_bytes': total_size_bytes,
            'status_counts': status_counts
        }

def main():
    """Main function to run the Real-Debrid history fetcher"""
    print("🚀 Real-Debrid Download History Fetcher")
    print("=" * 50)
    
    # Initialize the fetcher
    fetcher = RealDebridHistory(API_TOKEN)
    
    # Fetch downloads - try to get as many as possible
    downloads = fetcher.fetch_downloads(limit=10000)
    
    if not downloads:
        print("❌ No downloads found or error occurred.")
        return
    
    # Display statistics
    stats = fetcher.get_statistics(downloads)
    print(f"\n📊 Statistics:")
    print(f"   Total Downloads: {stats['total_downloads']:,}")
    print(f"   Total Size: {stats['total_size_gb']:.2f} GB")
    print(f"   Status Breakdown:")
    for status, count in stats['status_counts'].items():
        print(f"     {status}: {count:,}")
    
    # Display first 50 downloads
    fetcher.display_downloads(downloads, max_display=50)
    
    # Save to files
    print(f"\n💾 Saving data...")
    fetcher.save_to_json(downloads)
    fetcher.save_to_csv(downloads)
    
    print(f"\n✅ Done! Your Real-Debrid download history has been fetched and saved.")

if __name__ == "__main__":
    main() 