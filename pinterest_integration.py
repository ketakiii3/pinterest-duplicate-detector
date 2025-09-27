#!/usr/bin/env python3
"""
Pinterest API Integration with Duplicate Detection System
"""

import json
import os
from pathlib import Path
from typing import List, Dict
import sys

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from pinterest_api.client import PinterestAPIClient, PinterestPin
from models.embedding_extractor import EmbeddingExtractor
from models.duplicate_detector import DuplicateDetector
from models.quality_ranker import QualityRanker

class PinterestDuplicateAnalyzer:
    """Complete Pinterest duplicate analysis pipeline"""
    
    def __init__(self, pinterest_access_token: str = None):
        """Initialize analyzer with Pinterest API access"""
        self.pinterest_client = PinterestAPIClient(pinterest_access_token)
        self.embedding_extractor = EmbeddingExtractor()
        self.duplicate_detector = DuplicateDetector()
        self.quality_ranker = QualityRanker()
        
    def analyze_board_duplicates(
        self, 
        board_id: str, 
        max_pins: int = 200,
        similarity_threshold: float = 0.85
    ) -> Dict:
        """Analyze duplicates in a Pinterest board"""
        print(f"🔍 Analyzing board {board_id} for duplicates...")
        
        # 1. Fetch pins from board
        print("📌 Fetching pins from Pinterest...")
        pins = self.pinterest_client.get_board_pins(board_id, limit=max_pins)
        print(f"Found {len(pins)} pins")
        
        if len(pins) < 2:
            return {"error": "Need at least 2 pins to detect duplicates"}
        
        # 2. Extract embeddings
        print("🧠 Extracting visual embeddings...")
        image_urls = [pin.image_url for pin in pins]
        pin_ids = [pin.id for pin in pins]
        
        embeddings = self.embedding_extractor.extract_batch_embeddings(
            image_urls, batch_size=16, show_progress=True
        )
        
        # 3. Detect duplicates
        print("🔎 Detecting duplicate clusters...")
        self.duplicate_detector.build_index(embeddings, pin_ids)
        clusters = self.duplicate_detector.find_all_duplicates(
            similarity_threshold=similarity_threshold,
            min_cluster_size=2
        )
        
        # 4. Rank by quality
        print("📊 Ranking pins by quality...")
        cluster_results = []
        
        for cluster in clusters:
            # Create image sources map for quality ranking
            cluster_pins = [pin for pin in pins if pin.id in cluster.pin_ids]
            image_sources = {pin.id: pin.image_url for pin in cluster_pins}
            
            # Rank pins in this cluster by quality
            ranked_pins = self.quality_ranker.rank_duplicates(
                cluster.pin_ids, image_sources
            )
            
            # Compile cluster information
            cluster_info = {
                "cluster_id": cluster.cluster_id,
                "size": cluster.size,
                "avg_similarity": float(np.mean(cluster.similarities)),
                "pins": []
            }
            
            for pin_id, quality_metrics in ranked_pins:
                pin_data = next((p for p in cluster_pins if p.id == pin_id), None)
                if pin_data:
                    cluster_info["pins"].append({
                        "pin_id": pin_id,
                        "title": pin_data.title,
                        "description": pin_data.description,
                        "image_url": pin_data.image_url,
                        "link": pin_data.link,
                        "board_name": pin_data.board_name,
                        "creator_username": pin_data.creator_username,
                        "created_at": pin_data.created_at,
                        "quality_score": quality_metrics.overall_score,
                        "quality_breakdown": {
                            "resolution": quality_metrics.resolution_score,
                            "sharpness": quality_metrics.sharpness_score,
                            "brightness": quality_metrics.brightness_score,
                            "contrast": quality_metrics.contrast_score,
                            "aspect_ratio": quality_metrics.aspect_ratio_score
                        },
                        "pin_metrics": pin_data.pin_metrics
                    })
            
            cluster_results.append(cluster_info)
        
        # 5. Generate statistics
        stats = self.duplicate_detector.get_cluster_statistics(clusters)
        
        return {
            "board_id": board_id,
            "total_pins_analyzed": len(pins),
            "duplicate_clusters": cluster_results,
            "statistics": stats,
            "analysis_config": {
                "similarity_threshold": similarity_threshold,
                "max_pins": max_pins
            }
        }
    
    def analyze_search_duplicates(
        self, 
        search_query: str, 
        max_pins: int = 100,
        similarity_threshold: float = 0.85
    ) -> Dict:
        """Analyze duplicates in Pinterest search results"""
        print(f"🔍 Analyzing search results for '{search_query}' for duplicates...")
        
        # 1. Search for pins
        print("🔎 Searching Pinterest...")
        pins = self.pinterest_client.search_pins(search_query, limit=max_pins)
        print(f"Found {len(pins)} pins")
        
        if len(pins) < 2:
            return {"error": "Need at least 2 pins to detect duplicates"}
        
        # Use the same analysis pipeline as board analysis
        # Convert to board-like structure for reuse
        image_urls = [pin.image_url for pin in pins]
        pin_ids = [pin.id for pin in pins]
        
        # Extract embeddings
        print("🧠 Extracting visual embeddings...")
        embeddings = self.embedding_extractor.extract_batch_embeddings(
            image_urls, batch_size=16, show_progress=True
        )
        
        # Detect duplicates
        print("🔎 Detecting duplicate clusters...")
        self.duplicate_detector.build_index(embeddings, pin_ids)
        clusters = self.duplicate_detector.find_all_duplicates(
            similarity_threshold=similarity_threshold,
            min_cluster_size=2
        )
        
        # Process results (similar to board analysis)
        cluster_results = []
        for cluster in clusters:
            cluster_pins = [pin for pin in pins if pin.id in cluster.pin_ids]
            image_sources = {pin.id: pin.image_url for pin in cluster_pins}
            
            ranked_pins = self.quality_ranker.rank_duplicates(
                cluster.pin_ids, image_sources
            )
            
            cluster_info = {
                "cluster_id": cluster.cluster_id,
                "size": cluster.size,
                "avg_similarity": float(np.mean(cluster.similarities)),
                "pins": []
            }
            
            for pin_id, quality_metrics in ranked_pins:
                pin_data = next((p for p in cluster_pins if p.id == pin_id), None)
                if pin_data:
                    cluster_info["pins"].append({
                        "pin_id": pin_id,
                        "title": pin_data.title,
                        "description": pin_data.description,
                        "image_url": pin_data.image_url,
                        "link": pin_data.link,
                        "board_name": pin_data.board_name,
                        "creator_username": pin_data.creator_username,
                        "created_at": pin_data.created_at,
                        "quality_score": quality_metrics.overall_score,
                        "quality_breakdown": {
                            "resolution": quality_metrics.resolution_score,
                            "sharpness": quality_metrics.sharpness_score,
                            "brightness": quality_metrics.brightness_score,
                            "contrast": quality_metrics.contrast_score,
                            "aspect_ratio": quality_metrics.aspect_ratio_score
                        },
                        "pin_metrics": pin_data.pin_metrics
                    })
            
            cluster_results.append(cluster_info)
        
        stats = self.duplicate_detector.get_cluster_statistics(clusters)
        
        return {
            "search_query": search_query,
            "total_pins_analyzed": len(pins),
            "duplicate_clusters": cluster_results,
            "statistics": stats,
            "analysis_config": {
                "similarity_threshold": similarity_threshold,
                "max_pins": max_pins
            }
        }
    
    def find_pin_duplicates(self, pin_id: str, search_limit: int = 500) -> Dict:
        """Find duplicates of a specific pin across Pinterest"""
        print(f"🔍 Finding duplicates of pin {pin_id}...")
        
        # This would require a more sophisticated approach:
        # 1. Get the target pin
        # 2. Extract its embedding
        # 3. Search Pinterest for similar content
        # 4. Compare embeddings
        
        # Note: This is a simplified version - real implementation would need
        # more sophisticated search strategies
        
        return {
            "error": "Pin-specific duplicate search requires advanced Pinterest API access",
            "suggestion": "Use board or search-based analysis instead"
        }
    
    def save_analysis_results(self, results: Dict, output_path: str):
        """Save analysis results to file"""
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Saved analysis results to {output_path}")

def main():
    """Demo Pinterest integration"""
    print("🔗 Pinterest API Integration Demo")
    print("=" * 40)
    
    # Check for Pinterest access token
    access_token = os.getenv('PINTEREST_ACCESS_TOKEN')
    if not access_token:
        print("❌ Pinterest access token not found!")
        print("\n📝 Setup Instructions:")
        print("1. Go to https://developers.pinterest.com/")
        print("2. Create a Pinterest app")
        print("3. Get your access token")
        print("4. Set environment variable: export PINTEREST_ACCESS_TOKEN='your_token'")
        print("5. Or create a .env file with: PINTEREST_ACCESS_TOKEN=your_token")
        return
    
    try:
        # Initialize analyzer
        analyzer = PinterestDuplicateAnalyzer(access_token)
        
        print("\nChoose analysis type:")
        print("1. Analyze a specific board")
        print("2. Analyze search results")
        print("3. Demo with sample data")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            board_id = input("Enter Pinterest board ID: ").strip()
            max_pins = int(input("Max pins to analyze (default 100): ") or "100")
            
            results = analyzer.analyze_board_duplicates(
                board_id=board_id,
                max_pins=max_pins,
                similarity_threshold=0.85
            )
            
            # Save results
            output_path = f"pinterest_board_{board_id}_analysis.json"
            analyzer.save_analysis_results(results, output_path)
            
        elif choice == "2":
            query = input("Enter search query: ").strip()
            max_pins = int(input("Max pins to analyze (default 50): ") or "50")
            
            results = analyzer.analyze_search_duplicates(
                search_query=query,
                max_pins=max_pins,
                similarity_threshold=0.85
            )
            
            # Save results
            output_path = f"pinterest_search_{query.replace(' ', '_')}_analysis.json"
            analyzer.save_analysis_results(results, output_path)
            
        elif choice == "3":
            print("🎯 Running demo with sample data...")
            print("This will use the existing sample data for demonstration.")
            
            # Use existing sample data
            from scripts.data_collection import PinDataCollector
            collector = PinDataCollector()
            sample_pins = collector.simulate_pin_data(50)
            collector.create_duplicate_clusters(10)
            
            print(f"✅ Generated {len(sample_pins)} sample pins with duplicates")
            print("Run the regular duplicate detection to see results:")
            print("python3 models/duplicate_detector.py")
            
        else:
            print("Invalid choice")
            return
        
        if choice in ["1", "2"]:
            print(f"\n📊 Analysis Summary:")
            if "duplicate_clusters" in results:
                print(f"Found {len(results['duplicate_clusters'])} duplicate clusters")
                print(f"Total pins analyzed: {results['total_pins_analyzed']}")
                
                if results["duplicate_clusters"]:
                    print(f"\n🔍 Sample cluster:")
                    sample_cluster = results["duplicate_clusters"][0]
                    print(f"Cluster {sample_cluster['cluster_id']}: {sample_cluster['size']} pins")
                    print(f"Avg similarity: {sample_cluster['avg_similarity']:.3f}")
                    
                    if sample_cluster["pins"]:
                        best_pin = sample_cluster["pins"][0]
                        print(f"Best quality pin: {best_pin['title']}")
                        print(f"Quality score: {best_pin['quality_score']:.3f}")
            else:
                print("❌ Analysis failed:", results.get("error", "Unknown error"))
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Valid Pinterest API access token")
        print("2. Required dependencies installed")
        print("3. Proper network connectivity")

if __name__ == "__main__":
    main()