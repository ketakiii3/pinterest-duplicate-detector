# Pinterest Duplicate Detector

A simplified AI-powered system to detect duplicate images and rank them by quality using CLIP embeddings, FAISS similarity search, and computer vision techniques.

## Features

- **🔍 Image Similarity Detection**: Uses CLIP embeddings to find visually similar pins
- **🔎 Duplicate Detection**: FAISS-powered fast similarity search with clustering
- **📊 Quality Ranking**: Multi-metric quality assessment (resolution, sharpness, contrast, etc.)
- **🌐 Web Interface**: Streamlit dashboard for easy visualization
- **⚡ API**: FastAPI backend for programmatic access

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Sample Data

```bash
python3 scripts/data_collection.py
```

### 3. Run the System

#### Option A: Use the Runner Script
```bash
python3 run.py
```

#### Option B: Manual Setup

**Start API (Terminal 1):**
```bash
python3 -m uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```

**Start Web Interface (Terminal 2):**
```bash
python3 -m streamlit run app/streamlit_ui.py --server.port 8501
```

**Access the Interface:**
- Web Dashboard: http://localhost:8501
- API Documentation: http://localhost:8000/docs

## System Components

### 1. Embedding Extractor (`models/embedding_extractor.py`)
- Uses OpenAI's CLIP model to extract visual embeddings
- Supports batch processing for efficiency
- Handles both URLs and local images

### 2. Duplicate Detector (`models/duplicate_detector.py`)
- FAISS-based similarity search
- DBSCAN clustering for grouping duplicates
- Configurable similarity thresholds

### 3. Quality Ranker (`models/quality_ranker.py`)
- Multi-metric quality assessment:
  - Resolution score
  - Sharpness (Laplacian variance)
  - Brightness optimization
  - Contrast measurement
  - Aspect ratio preferences
- Weighted scoring system

### 4. Web Interface (`app/streamlit_ui.py`)
- Interactive duplicate analysis
- Visual cluster display
- Statistics dashboard
- Real-time configuration

### 5. API (`app/api.py`)
- RESTful endpoints
- Batch processing
- Real-time analysis
- JSON responses

## Usage Examples

### Basic Analysis
```python
from models.embedding_extractor import EmbeddingExtractor
from models.duplicate_detector import DuplicateDetector
from models.quality_ranker import QualityRanker

# Extract embeddings
extractor = EmbeddingExtractor()
embeddings = extractor.extract_batch_embeddings(image_urls)

# Find duplicates
detector = DuplicateDetector()
detector.build_index(embeddings, pin_ids)
clusters = detector.find_all_duplicates(similarity_threshold=0.85)

# Rank by quality
ranker = QualityRanker()
for cluster in clusters:
    ranked = ranker.rank_duplicates(cluster.pin_ids, image_sources)
    best_pin = ranked[0]  # Highest quality
```

### API Usage
```python
import requests

# Analyze duplicates
response = requests.post("http://localhost:8000/analyze-duplicates", params={
    "num_pins": 100,
    "similarity_threshold": 0.85,
    "min_cluster_size": 2
})

result = response.json()
print(f"Found {len(result['duplicate_clusters'])} clusters")
```

## Configuration

### Similarity Thresholds
- **0.95**: Very strict (nearly identical)
- **0.85**: Standard (recommended)
- **0.75**: Loose (similar style/content)

### Quality Metrics Weights
```python
weights = {
    'resolution': 0.25,    # Image size/quality
    'sharpness': 0.30,     # Focus quality
    'brightness': 0.15,    # Optimal lighting
    'contrast': 0.20,      # Dynamic range
    'aspect_ratio': 0.10   # Pinterest preferences
}
```

## Performance Notes

- **Embedding extraction**: ~100 images/minute (CPU), ~1000 images/minute (GPU)
- **Duplicate detection**: Sub-second for 1000 embeddings
- **Memory usage**: ~4MB per 1000 embeddings
- **Recommended batch size**: 16-32 images

## File Structure

```
pinterest-duplicate-detector/
├── app/
│   ├── api.py              # FastAPI backend
│   └── streamlit_ui.py     # Web interface
├── models/
│   ├── embedding_extractor.py  # CLIP embeddings
│   ├── duplicate_detector.py   # FAISS similarity
│   └── quality_ranker.py       # Quality metrics
├── scripts/
│   └── data_collection.py      # Sample data generation
├── data/
│   └── raw_pins.json          # Sample Pinterest data
├── requirements.txt           # Dependencies
├── run.py                    # Simple runner
└── README.md                 # This file
```

## Requirements

- Python 3.8+
- PyTorch (for CLIP)
- FAISS (for similarity search)
- OpenCV (for image analysis)
- Streamlit (for web interface)
- FastAPI (for API)

## Limitations

This is a simplified version focusing on core functionality:
- Uses sample/simulated data instead of real Pinterest API
- Basic quality metrics (could be enhanced with ML models)
- Simple clustering approach
- No production optimizations

## Next Steps

For production use, consider:
- Real Pinterest API integration
- Advanced quality ML models
- Scalable infrastructure (Redis, PostgreSQL)
- Enhanced similarity algorithms
- User authentication
- Performance optimizations