from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import numpy as np
import json
from pathlib import Path
import sys
import uvicorn

# Add parent directory to path to import models
sys.path.append(str(Path(__file__).parent.parent))

from models.embedding_extractor import EmbeddingExtractor
from models.duplicate_detector import DuplicateDetector, DuplicateCluster
from models.quality_ranker import QualityRanker

app = FastAPI(title="Pinterest Duplicate Detector API", version="1.0.0")

# Enable CORS for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to store models
embedding_extractor = None
duplicate_detector = None
quality_ranker = None
pins_data = []

class PinResponse(BaseModel):
    pin_id: str
    title: str
    image_url: str
    quality_score: Optional[float] = None
    is_duplicate: bool = False
    cluster_id: Optional[int] = None

class ClusterResponse(BaseModel):
    cluster_id: int
    size: int
    pins: List[PinResponse]
    avg_similarity: float

class DuplicateAnalysisResponse(BaseModel):
    total_pins: int
    duplicate_clusters: List[ClusterResponse]
    statistics: Dict

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    global embedding_extractor, duplicate_detector, quality_ranker, pins_data
    
    print("🚀 Initializing Pinterest Duplicate Detector API...")
    
    # Initialize models
    embedding_extractor = EmbeddingExtractor()
    duplicate_detector = DuplicateDetector()
    quality_ranker = QualityRanker()
    
    # Load pins data if available
    data_path = Path("data/raw_pins.json")
    if data_path.exists():
        with open(data_path) as f:
            pins_data = json.load(f)
        print(f"✅ Loaded {len(pins_data)} pins from data file")
    else:
        print("⚠️ No pins data found. Generate data first with: python scripts/data_collection.py")
    
    print("✅ API ready!")

@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "healthy",
        "message": "Pinterest Duplicate Detector API",
        "version": "1.0.0",
        "pins_loaded": len(pins_data)
    }

@app.get("/pins", response_model=List[PinResponse])
async def get_pins(limit: int = 50, offset: int = 0):
    """Get paginated list of pins"""
    if not pins_data:
        raise HTTPException(status_code=404, detail="No pins data loaded")
    
    start = offset
    end = offset + limit
    paginated_pins = pins_data[start:end]
    
    return [
        PinResponse(
            pin_id=pin["pin_id"],
            title=pin["title"],
            image_url=pin["image_url"]
        )
        for pin in paginated_pins
    ]

@app.post("/analyze-duplicates")
async def analyze_duplicates(
    num_pins: int = 100,
    similarity_threshold: float = 0.85,
    min_cluster_size: int = 2
):
    """Analyze pins for duplicates"""
    global embedding_extractor, duplicate_detector, quality_ranker, pins_data
    
    if not pins_data:
        raise HTTPException(status_code=404, detail="No pins data loaded")
    
    if not embedding_extractor:
        raise HTTPException(status_code=500, detail="Models not initialized")
    
    try:
        # Limit analysis to specified number of pins
        analysis_pins = pins_data[:num_pins]
        
        print(f"🔍 Analyzing {len(analysis_pins)} pins for duplicates...")
        
        # Extract embeddings
        image_urls = [pin["image_url"] for pin in analysis_pins]
        pin_ids = [pin["pin_id"] for pin in analysis_pins]
        
        print("📸 Extracting embeddings...")
        embeddings = embedding_extractor.extract_batch_embeddings(image_urls, batch_size=16)
        
        # Build index and find duplicates
        print("🔎 Building similarity index...")
        duplicate_detector.build_index(embeddings, pin_ids, index_type="IP")
        
        print("🔍 Finding duplicate clusters...")
        clusters = duplicate_detector.find_all_duplicates(
            similarity_threshold=similarity_threshold,
            min_cluster_size=min_cluster_size
        )
        
        # Calculate quality scores for pins in clusters
        print("📊 Calculating quality scores...")
        pins_in_clusters = set()
        for cluster in clusters:
            pins_in_clusters.update(cluster.pin_ids)
        
        quality_scores = {}
        for pin in analysis_pins:
            if pin["pin_id"] in pins_in_clusters:
                score = quality_ranker.calculate_quality_score(pin)
                quality_scores[pin["pin_id"]] = score.total_score
        
        # Format response
        cluster_responses = []
        for cluster in clusters:
            cluster_pins = []
            for pin_id in cluster.pin_ids:
                pin_data = next((p for p in analysis_pins if p["pin_id"] == pin_id), None)
                if pin_data:
                    cluster_pins.append(PinResponse(
                        pin_id=pin_id,
                        title=pin_data["title"],
                        image_url=pin_data["image_url"],
                        quality_score=quality_scores.get(pin_id),
                        is_duplicate=True,
                        cluster_id=cluster.cluster_id
                    ))
            
            cluster_responses.append(ClusterResponse(
                cluster_id=cluster.cluster_id,
                size=cluster.size,
                pins=cluster_pins,
                avg_similarity=float(np.mean(cluster.similarities))
            ))
        
        # Get statistics
        stats = duplicate_detector.get_cluster_statistics(clusters)
        
        return DuplicateAnalysisResponse(
            total_pins=len(analysis_pins),
            duplicate_clusters=cluster_responses,
            statistics=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/cluster/{cluster_id}")
async def get_cluster_details(cluster_id: int):
    """Get detailed information about a specific duplicate cluster"""
    # This would require storing cluster results in memory or database
    # For simplicity, returning placeholder
    return {"message": f"Cluster {cluster_id} details would be here"}

@app.post("/upload-image")
async def upload_and_find_similar(file: UploadFile = File(...)):
    """Upload an image and find similar pins"""
    if not embedding_extractor:
        raise HTTPException(status_code=500, detail="Models not initialized")
    
    try:
        # Read uploaded image
        contents = await file.read()
        
        # Extract embedding from uploaded image
        from PIL import Image
        from io import BytesIO
        
        image = Image.open(BytesIO(contents)).convert('RGB')
        query_embedding = embedding_extractor.extract_embedding(image)
        
        # Find similar pins (simplified - would need pre-built index)
        return {
            "message": "Image uploaded successfully",
            "filename": file.filename,
            "embedding_shape": query_embedding.shape,
            "similar_pins": []  # Would implement similarity search here
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/statistics")
async def get_system_statistics():
    """Get overall system statistics"""
    return {
        "total_pins": len(pins_data),
        "models_loaded": {
            "embedding_extractor": embedding_extractor is not None,
            "duplicate_detector": duplicate_detector is not None,
            "quality_ranker": quality_ranker is not None
        },
        "api_version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)