# Pinterest API Integration & ML Model Comparison Guide

## 📌 Pinterest API Integration

### Setup Instructions

#### 1. Create Pinterest Developer Account
1. Go to [Pinterest Developers](https://developers.pinterest.com/)
2. Sign in with your Pinterest account
3. Create a new app
4. Get your **Access Token**

#### 2. Set Environment Variables
```bash
# Option 1: Export in terminal
export PINTEREST_ACCESS_TOKEN="your_access_token_here"

# Option 2: Create .env file
echo "PINTEREST_ACCESS_TOKEN=your_access_token_here" > .env
```

#### 3. Install Additional Dependencies
```bash
pip install python-dotenv
```

### Usage Examples

#### Analyze Board Duplicates
```python
from pinterest_integration import PinterestDuplicateAnalyzer

# Initialize analyzer
analyzer = PinterestDuplicateAnalyzer()

# Analyze a specific board
results = analyzer.analyze_board_duplicates(
    board_id="your_board_id",
    max_pins=200,
    similarity_threshold=0.85
)

print(f"Found {len(results['duplicate_clusters'])} duplicate clusters")
```

#### Analyze Search Results
```python
# Search for duplicates in specific topics
results = analyzer.analyze_search_duplicates(
    search_query="machine learning",
    max_pins=100,
    similarity_threshold=0.85
)
```

#### Run Integration Demo
```bash
python3 pinterest_integration.py
```

### Pinterest API Capabilities

#### Available Endpoints
- **Boards**: Get user boards, board details
- **Pins**: Get board pins, search pins
- **Search**: Search pins, boards, users
- **User**: Get user profile, following, followers

#### Current Limitations
- **Rate Limits**: 1000 requests per hour (adjustable)
- **Data Access**: Limited to public pins and your own content
- **Real-time**: Not real-time, requires API calls
- **Permissions**: Requires appropriate scopes

#### Sample Pinterest Data Structure
```json
{
  "pin_id": "123456789",
  "title": "Machine Learning Tutorial",
  "description": "Learn ML basics...",
  "image_url": "https://i.pinimg.com/...",
  "board_name": "Tech Tutorials",
  "creator_username": "techguru",
  "pin_metrics": {
    "saves": 150,
    "comments": 12
  }
}
```

---

## 🤖 ML Model Comparison Framework

### Available Models for Comparison

#### 1. **CLIP Models** (Current Default)
- **CLIP ViT-B/32**: 512-dim embeddings, balanced performance
- **CLIP ViT-L/14**: 768-dim embeddings, higher accuracy
- **Strengths**: Semantic understanding, text-image alignment
- **Use Case**: Best for Pinterest content (mixed text/visual)

#### 2. **Vision Transformers (ViT)**
- **ViT-Base**: 768-dim embeddings, pure visual features
- **ViT-Large**: 1024-dim embeddings, more detailed features
- **Strengths**: Pure visual analysis, good for fine details
- **Use Case**: When visual similarity is most important

#### 3. **ResNet Models**
- **ResNet-50**: 2048-dim embeddings, classic CNN
- **ResNet-101**: 2048-dim embeddings, deeper features
- **Strengths**: Robust feature extraction, proven performance
- **Use Case**: General purpose, good baseline

#### 4. **EfficientNet Models**
- **EfficientNet-B0**: 1280-dim embeddings, efficient
- **EfficientNet-B7**: 2560-dim embeddings, highest accuracy
- **Strengths**: Efficiency, scalable architecture
- **Use Case**: Production deployment, resource constraints

#### 5. **Other Advanced Models** (Extensible)
- **DINO**: Self-supervised vision transformer
- **ConvNeXt**: Modern CNN architecture
- **SWIN**: Hierarchical vision transformer
- **Custom Models**: Fine-tuned on Pinterest data

### Running Model Comparison

#### Quick Comparison
```bash
python3 models/model_comparison.py
```

#### Programmatic Comparison
```python
from models.model_comparison import ModelComparison, CLIPEmbeddingModel, ViTEmbeddingModel

# Create test dataset
test_images, ground_truth = create_test_dataset()

# Initialize comparison
comparison = ModelComparison(test_images, ground_truth)

# Add models
comparison.add_model(CLIPEmbeddingModel("openai/clip-vit-base-patch32"))
comparison.add_model(ViTEmbeddingModel("google/vit-base-patch16-224"))

# Run comparison
results = comparison.run_comparison(similarity_threshold=0.85)

# Generate report
comparison.create_comparison_report()
comparison.visualize_results()
```

### Evaluation Metrics

#### Performance Metrics
- **Accuracy**: Overall duplicate detection accuracy
- **Precision**: True duplicates / (True duplicates + False positives)
- **Recall**: True duplicates / (True duplicates + False negatives)
- **F1-Score**: Harmonic mean of precision and recall
- **Top-K Accuracy**: Duplicate found in top-K similar results

#### Efficiency Metrics
- **Inference Time**: Milliseconds per image
- **Memory Usage**: MB for embedding storage
- **Embedding Dimension**: Feature vector size
- **Model Size**: Storage requirements

#### Similarity Metrics
- **Cosine Similarity**: Dot product of normalized vectors
- **Euclidean Distance**: L2 distance between embeddings
- **Manhattan Distance**: L1 distance between embeddings

### Model Selection Guidelines

#### For Pinterest Duplicate Detection

**Recommendation: CLIP ViT-B/32**
- ✅ Best semantic understanding
- ✅ Handles text in images
- ✅ Good balance of speed/accuracy
- ✅ Pre-trained on diverse internet data

#### Alternative Choices

**High Accuracy Needed**: CLIP ViT-L/14
- Higher accuracy but slower
- Larger memory requirements
- Best for quality over speed

**Speed Critical**: EfficientNet-B0
- Fastest inference
- Smallest memory footprint
- Good for real-time applications

**Pure Visual Similarity**: ResNet-50
- No text understanding
- Robust feature extraction
- Good baseline performance

### Custom Model Integration

#### Adding New Models
```python
class CustomEmbeddingModel(BaseEmbeddingModel):
    def __init__(self, model_name: str):
        super().__init__(model_name)
        # Load your custom model
        
    def extract_embedding(self, image) -> np.ndarray:
        # Implement embedding extraction
        pass
        
    def get_embedding_dim(self) -> int:
        # Return embedding dimension
        return 512

# Add to comparison
comparison.add_model(CustomEmbeddingModel("my-custom-model"))
```

---

## 🔧 Production Considerations

### Pinterest API Production Setup

#### Authentication
```python
# Production: Use secure token storage
import os
from azure.keyvault.secrets import SecretClient

# Get token from secure storage
access_token = secret_client.get_secret("pinterest-api-token").value
```

#### Rate Limiting
```python
# Implement exponential backoff
import time
from functools import wraps

def rate_limit_retry(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
            raise
        return wrapper
    return decorator
```

#### Caching
```python
# Cache API responses
import redis
import json

redis_client = redis.Redis()

def cached_api_call(key, api_function, ttl=3600):
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    
    result = api_function()
    redis_client.setex(key, ttl, json.dumps(result))
    return result
```

### ML Model Production Setup

#### Model Serving
```python
# Use model serving framework
from torchserve import serve

# Deploy model with TorchServe
serve.start_model_server(
    model_name="pinterest_duplicate_detector",
    model_file="model.mar",
    handler="embedding_handler.py"
)
```

#### Batch Processing
```python
# Process large batches efficiently
def process_batch(images, batch_size=64):
    results = []
    for i in range(0, len(images), batch_size):
        batch = images[i:i + batch_size]
        embeddings = model.extract_batch_embeddings(batch)
        results.extend(embeddings)
    return results
```

#### GPU Optimization
```python
# Multi-GPU support
import torch.nn as nn

if torch.cuda.device_count() > 1:
    model = nn.DataParallel(model)
    model = model.cuda()
```

### Monitoring & Logging

#### API Monitoring
```python
import logging
from prometheus_client import Counter, Histogram

# Metrics
api_requests = Counter('pinterest_api_requests_total')
processing_time = Histogram('duplicate_detection_seconds')

@processing_time.time()
def analyze_duplicates(pins):
    api_requests.inc()
    # Process duplicates
    pass
```

#### Error Handling
```python
# Comprehensive error handling
try:
    results = analyzer.analyze_board_duplicates(board_id)
except PinterestAPIError as e:
    logger.error(f"Pinterest API error: {e}")
    # Fallback to cached data or sample data
except ModelInferenceError as e:
    logger.error(f"Model inference error: {e}")
    # Use simpler model or return error
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Graceful degradation
```

---

## 📊 Performance Benchmarks

### Model Comparison Results (Sample)

| Model | F1-Score | Accuracy | Speed (ms) | Memory (MB) |
|-------|----------|----------|------------|-------------|
| CLIP ViT-B/32 | 0.892 | 0.867 | 45.2 | 2.1 |
| CLIP ViT-L/14 | 0.924 | 0.901 | 89.7 | 3.8 |
| ViT-Base | 0.834 | 0.812 | 38.9 | 3.1 |
| ResNet-50 | 0.798 | 0.776 | 23.4 | 8.2 |
| EfficientNet-B0 | 0.812 | 0.789 | 18.7 | 5.1 |

### Pinterest API Performance

- **Rate Limit**: 1000 requests/hour
- **Typical Response Time**: 200-500ms
- **Batch Size**: Up to 100 pins per request
- **Image Processing**: 50-100 images/minute

### Scalability Estimates

#### Small Scale (< 10K pins)
- **Processing Time**: 5-10 minutes
- **Memory Required**: < 1GB
- **Recommended**: Single GPU/CPU

#### Medium Scale (10K-100K pins)
- **Processing Time**: 30-60 minutes
- **Memory Required**: 2-5GB
- **Recommended**: GPU acceleration

#### Large Scale (> 100K pins)
- **Processing Time**: 2-10 hours
- **Memory Required**: 10-50GB
- **Recommended**: Distributed processing