import requests
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class PinterestPin:
    """Pinterest Pin data structure"""
    id: str
    title: str
    description: str
    image_url: str
    link: str
    board_id: str
    board_name: str
    creator_id: str
    creator_username: str
    created_at: str
    pin_metrics: Dict
    media: Dict

class PinterestAPIClient:
    """Pinterest API v5 Client"""
    
    def __init__(self, access_token: str = None):
        """
        Initialize Pinterest API client
        
        Args:
            access_token: Pinterest API access token
        """
        self.access_token = access_token or os.getenv('PINTEREST_ACCESS_TOKEN')
        if not self.access_token:
            raise ValueError("Pinterest access token required. Set PINTEREST_ACCESS_TOKEN environment variable.")
        
        self.base_url = "https://api.pinterest.com/v5"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        self.rate_limit_remaining = 1000
        self.rate_limit_reset = 0
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with rate limiting"""
        url = f"{self.base_url}{endpoint}"
        
        # Check rate limit
        if self.rate_limit_remaining <= 1:
            sleep_time = max(0, self.rate_limit_reset - time.time())
            if sleep_time > 0:
                print(f"Rate limit reached. Sleeping for {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            # Update rate limit info
            self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 1000))
            self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', time.time() + 3600))
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise
    
    def get_user_boards(self, fields: List[str] = None) -> List[Dict]:
        """Get user's boards"""
        if fields is None:
            fields = ["id", "name", "description", "pin_count", "created_at"]
        
        params = {"fields": ",".join(fields)}
        response = self._make_request("/boards", params)
        return response.get("items", [])
    
    def get_board_pins(
        self, 
        board_id: str, 
        limit: int = 100,
        fields: List[str] = None
    ) -> List[PinterestPin]:
        """Get pins from a specific board"""
        if fields is None:
            fields = [
                "id", "title", "description", "link", "media", 
                "board_id", "board_name", "created_at", "pin_metrics"
            ]
        
        pins = []
        bookmark = None
        
        while len(pins) < limit:
            params = {
                "fields": ",".join(fields),
                "page_size": min(100, limit - len(pins))
            }
            if bookmark:
                params["bookmark"] = bookmark
            
            response = self._make_request(f"/boards/{board_id}/pins", params)
            
            items = response.get("items", [])
            if not items:
                break
            
            for item in items:
                pin = self._parse_pin_data(item)
                if pin:
                    pins.append(pin)
            
            bookmark = response.get("bookmark")
            if not bookmark:
                break
            
            # Respect rate limits
            time.sleep(0.1)
        
        return pins[:limit]
    
    def search_pins(
        self, 
        query: str, 
        limit: int = 100,
        fields: List[str] = None
    ) -> List[PinterestPin]:
        """Search for pins"""
        if fields is None:
            fields = [
                "id", "title", "description", "link", "media", 
                "board_id", "board_name", "created_at", "pin_metrics"
            ]
        
        pins = []
        bookmark = None
        
        while len(pins) < limit:
            params = {
                "query": query,
                "fields": ",".join(fields),
                "limit": min(100, limit - len(pins))
            }
            if bookmark:
                params["bookmark"] = bookmark
            
            response = self._make_request("/search/pins", params)
            
            items = response.get("items", [])
            if not items:
                break
            
            for item in items:
                pin = self._parse_pin_data(item)
                if pin:
                    pins.append(pin)
            
            bookmark = response.get("bookmark")
            if not bookmark:
                break
            
            time.sleep(0.1)
        
        return pins[:limit]
    
    def get_trending_pins(
        self, 
        limit: int = 100,
        category: str = None
    ) -> List[PinterestPin]:
        """Get trending pins (Note: This might require special permissions)"""
        # Pinterest API v5 doesn't have a direct trending endpoint
        # Alternative: Search for popular terms or use feed endpoint if available
        popular_queries = [
            "trending", "popular", "viral", "new", "creative", 
            "inspiration", "design", "fashion", "food", "home"
        ]
        
        all_pins = []
        pins_per_query = limit // len(popular_queries)
        
        for query in popular_queries:
            if len(all_pins) >= limit:
                break
            
            try:
                pins = self.search_pins(query, limit=pins_per_query)
                all_pins.extend(pins)
            except Exception as e:
                print(f"Failed to get pins for query '{query}': {e}")
                continue
        
        # Remove duplicates and return top pins
        seen_ids = set()
        unique_pins = []
        for pin in all_pins:
            if pin.id not in seen_ids:
                seen_ids.add(pin.id)
                unique_pins.append(pin)
        
        return unique_pins[:limit]
    
    def _parse_pin_data(self, raw_data: Dict) -> Optional[PinterestPin]:
        """Parse raw Pinterest API data into PinterestPin object"""
        try:
            media = raw_data.get("media", {})
            image_url = None
            
            # Extract image URL from media object
            if "images" in media:
                images = media["images"]
                # Get the highest resolution image
                for size in ["orig", "736x", "564x", "474x", "236x"]:
                    if size in images:
                        image_url = images[size]["url"]
                        break
            
            if not image_url:
                return None
            
            return PinterestPin(
                id=raw_data.get("id", ""),
                title=raw_data.get("title", ""),
                description=raw_data.get("description", ""),
                image_url=image_url,
                link=raw_data.get("link", ""),
                board_id=raw_data.get("board_id", ""),
                board_name=raw_data.get("board_name", ""),
                creator_id=raw_data.get("creator", {}).get("id", ""),
                creator_username=raw_data.get("creator", {}).get("username", ""),
                created_at=raw_data.get("created_at", ""),
                pin_metrics=raw_data.get("pin_metrics", {}),
                media=media
            )
        except Exception as e:
            print(f"Failed to parse pin data: {e}")
            return None
    
    def save_pins_to_file(self, pins: List[PinterestPin], filename: str):
        """Save pins to JSON file"""
        pins_data = []
        for pin in pins:
            pins_data.append({
                "pin_id": pin.id,
                "title": pin.title,
                "description": pin.description,
                "image_url": pin.image_url,
                "link": pin.link,
                "board_id": pin.board_id,
                "board_name": pin.board_name,
                "creator_id": pin.creator_id,
                "creator_username": pin.creator_username,
                "created_at": pin.created_at,
                "pin_metrics": pin.pin_metrics,
                "media": pin.media
            })
        
        with open(filename, 'w') as f:
            json.dump(pins_data, f, indent=2)
        
        print(f"✅ Saved {len(pins)} pins to {filename}")

def main():
    """Demo Pinterest API usage"""
    try:
        client = PinterestAPIClient()
        
        print("🔍 Searching for pins...")
        pins = client.search_pins("machine learning", limit=50)
        print(f"Found {len(pins)} pins")
        
        # Save to file
        output_dir = Path("data")
        output_dir.mkdir(exist_ok=True)
        client.save_pins_to_file(pins, "data/pinterest_pins.json")
        
        # Show sample pin
        if pins:
            pin = pins[0]
            print(f"\nSample Pin:")
            print(f"  ID: {pin.id}")
            print(f"  Title: {pin.title}")
            print(f"  Image URL: {pin.image_url}")
            print(f"  Board: {pin.board_name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n📝 To use Pinterest API:")
        print("1. Create a Pinterest Developer account")
        print("2. Create an app and get access token")
        print("3. Set PINTEREST_ACCESS_TOKEN environment variable")

if __name__ == "__main__":
    main()