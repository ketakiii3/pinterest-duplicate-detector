import numpy as np
import torch
import torch.nn as nn
from transformers import CLIPProcessor, CLIPModel, ViTFeatureExtractor, ViTModel
from torchvision import models, transforms
from PIL import Image
import timm
import time
from typing import List, Dict, Tuple, Union
from pathlib import Path
import json
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
import requests
from io import BytesIO

@dataclass
class ModelMetrics:
    """Metrics for model evaluation"""
    model_name: str
    embedding_dim: int
    inference_time_ms: float
    memory_usage_mb: float
    similarity_accuracy: float
    precision: float
    recall: float
    f1_score: float
    top_k_accuracy: Dict[int, float]

class BaseEmbeddingModel:
    """Base class for embedding models"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    def extract_embedding(self, image: Union[str, Path, Image.Image]) -> np.ndarray:
        """Extract embedding from image"""
        raise NotImplementedError
    
    def get_embedding_dim(self) -> int:
        """Get embedding dimension"""
        raise NotImplementedError

class CLIPEmbeddingModel(BaseEmbeddingModel):
    """CLIP-based embedding model"""
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        super().__init__(model_name)
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()
    
    def extract_embedding(self, image: Union[str, Path, Image.Image]) -> np.ndarray:
        if isinstance(image, str) and image.startswith(('http://', 'https://')):
            response = requests.get(image, timeout=10)
            image = Image.open(BytesIO(response.content)).convert('RGB')
        elif isinstance(image, (str, Path)):
            image = Image.open(image).convert('RGB')
        
        inputs = self.processor(images=image, return_tensors="pt")
        pixel_values = inputs.pixel_values.to(self.device)
        
        with torch.no_grad():
            image_features = self.model.get_image_features(pixel_values)
            embedding = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return embedding.cpu().numpy().squeeze()
    
    def get_embedding_dim(self) -> int:
        return 512

class ViTEmbeddingModel(BaseEmbeddingModel):
    """Vision Transformer embedding model"""
    
    def __init__(self, model_name: str = "google/vit-base-patch16-224"):
        super().__init__(model_name)
        self.model = ViTModel.from_pretrained(model_name).to(self.device)
        self.feature_extractor = ViTFeatureExtractor.from_pretrained(model_name)
        self.model.eval()
    
    def extract_embedding(self, image: Union[str, Path, Image.Image]) -> np.ndarray:
        if isinstance(image, str) and image.startswith(('http://', 'https://')):
            response = requests.get(image, timeout=10)
            image = Image.open(BytesIO(response.content)).convert('RGB')
        elif isinstance(image, (str, Path)):
            image = Image.open(image).convert('RGB')
        
        inputs = self.feature_extractor(images=image, return_tensors="pt")
        pixel_values = inputs.pixel_values.to(self.device)
        
        with torch.no_grad():
            outputs = self.model(pixel_values)
            # Use [CLS] token representation
            embedding = outputs.last_hidden_state[:, 0, :]
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        
        return embedding.cpu().numpy().squeeze()
    
    def get_embedding_dim(self) -> int:
        return 768

class ResNetEmbeddingModel(BaseEmbeddingModel):
    """ResNet-based embedding model"""
    
    def __init__(self, model_name: str = "resnet50"):
        super().__init__(model_name)
        if model_name == "resnet50":
            self.model = models.resnet50(pretrained=True)
        elif model_name == "resnet101":
            self.model = models.resnet101(pretrained=True)
        else:
            raise ValueError(f"Unsupported ResNet model: {model_name}")
        
        # Remove final classification layer
        self.model = nn.Sequential(*list(self.model.children())[:-1])
        self.model = self.model.to(self.device)
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def extract_embedding(self, image: Union[str, Path, Image.Image]) -> np.ndarray:
        if isinstance(image, str) and image.startswith(('http://', 'https://')):
            response = requests.get(image, timeout=10)
            image = Image.open(BytesIO(response.content)).convert('RGB')
        elif isinstance(image, (str, Path)):
            image = Image.open(image).convert('RGB')
        
        image_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            embedding = self.model(image_tensor)
            embedding = embedding.squeeze().cpu().numpy()
            # Normalize
            embedding = embedding / np.linalg.norm(embedding)
        
        return embedding
    
    def get_embedding_dim(self) -> int:
        return 2048

class EfficientNetEmbeddingModel(BaseEmbeddingModel):
    """EfficientNet-based embedding model"""
    
    def __init__(self, model_name: str = "efficientnet_b0"):
        super().__init__(model_name)
        self.model = timm.create_model(model_name, pretrained=True, num_classes=0)
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # Get model's data config for preprocessing
        data_config = timm.data.resolve_model_data_config(self.model)
        self.transform = timm.data.create_transform(**data_config, is_training=False)
    
    def extract_embedding(self, image: Union[str, Path, Image.Image]) -> np.ndarray:
        if isinstance(image, str) and image.startswith(('http://', 'https://')):
            response = requests.get(image, timeout=10)
            image = Image.open(BytesIO(response.content)).convert('RGB')
        elif isinstance(image, (str, Path)):
            image = Image.open(image).convert('RGB')
        
        image_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            embedding = self.model(image_tensor)
            embedding = embedding.squeeze().cpu().numpy()
            # Normalize
            embedding = embedding / np.linalg.norm(embedding)
        
        return embedding
    
    def get_embedding_dim(self) -> int:
        # EfficientNet-B0 typically has 1280 features
        return 1280 if "b0" in self.model_name.lower() else 2048

class ModelComparison:
    """Compare different embedding models for duplicate detection"""
    
    def __init__(self, test_images: List[str], ground_truth_pairs: List[Tuple[int, int]]):
        """
        Initialize model comparison
        
        Args:
            test_images: List of image URLs or paths
            ground_truth_pairs: List of (idx1, idx2) pairs that are known duplicates
        """
        self.test_images = test_images
        self.ground_truth_pairs = set(ground_truth_pairs)
        self.models = {}
        self.results = {}
    
    def add_model(self, model: BaseEmbeddingModel):
        """Add a model to comparison"""
        self.models[model.model_name] = model
    
    def evaluate_model(self, model: BaseEmbeddingModel, similarity_threshold: float = 0.85) -> ModelMetrics:
        """Evaluate a single model"""
        print(f"Evaluating {model.model_name}...")
        
        # Extract embeddings and measure time
        embeddings = []
        start_time = time.time()
        
        for i, image in enumerate(self.test_images):
            try:
                embedding = model.extract_embedding(image)
                embeddings.append(embedding)
            except Exception as e:
                print(f"Failed to process image {i}: {e}")
                embeddings.append(np.zeros(model.get_embedding_dim()))
        
        inference_time = (time.time() - start_time) * 1000 / len(self.test_images)
        embeddings = np.array(embeddings)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(embeddings)
        
        # Generate predictions
        predictions = []
        true_labels = []
        
        for i in range(len(self.test_images)):
            for j in range(i + 1, len(self.test_images)):
                similarity = similarity_matrix[i, j]
                is_duplicate = similarity >= similarity_threshold
                predictions.append(is_duplicate)
                true_labels.append((i, j) in self.ground_truth_pairs)
        
        # Calculate metrics
        accuracy = accuracy_score(true_labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_labels, predictions, average='binary', zero_division=0
        )
        
        # Calculate top-k accuracy
        top_k_accuracy = {}
        for k in [1, 3, 5, 10]:
            top_k_acc = self._calculate_top_k_accuracy(similarity_matrix, k)
            top_k_accuracy[k] = top_k_acc
        
        # Estimate memory usage (rough approximation)
        memory_usage = embeddings.nbytes / (1024 * 1024)  # Convert to MB
        
        return ModelMetrics(
            model_name=model.model_name,
            embedding_dim=model.get_embedding_dim(),
            inference_time_ms=inference_time,
            memory_usage_mb=memory_usage,
            similarity_accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            top_k_accuracy=top_k_accuracy
        )
    
    def _calculate_top_k_accuracy(self, similarity_matrix: np.ndarray, k: int) -> float:
        """Calculate top-k accuracy for duplicate detection"""
        correct = 0
        total = 0
        
        for i, j in self.ground_truth_pairs:
            if i < len(similarity_matrix) and j < len(similarity_matrix):
                # Get top-k most similar images to image i (excluding itself)
                similarities = similarity_matrix[i].copy()
                similarities[i] = -1  # Exclude self
                top_k_indices = np.argsort(similarities)[-k:]
                
                if j in top_k_indices:
                    correct += 1
                total += 1
        
        return correct / total if total > 0 else 0.0
    
    def run_comparison(self, similarity_threshold: float = 0.85) -> Dict[str, ModelMetrics]:
        """Run comparison on all models"""
        results = {}
        
        for model_name, model in self.models.items():
            try:
                metrics = self.evaluate_model(model, similarity_threshold)
                results[model_name] = metrics
                self.results[model_name] = metrics
            except Exception as e:
                print(f"Failed to evaluate {model_name}: {e}")
        
        return results
    
    def create_comparison_report(self, output_path: str = "model_comparison_report.json"):
        """Create detailed comparison report"""
        report = {
            "experiment_config": {
                "num_test_images": len(self.test_images),
                "num_ground_truth_pairs": len(self.ground_truth_pairs),
                "device": str(torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
            },
            "results": {}
        }
        
        for model_name, metrics in self.results.items():
            report["results"][model_name] = {
                "embedding_dimension": metrics.embedding_dim,
                "inference_time_ms": metrics.inference_time_ms,
                "memory_usage_mb": metrics.memory_usage_mb,
                "accuracy": metrics.similarity_accuracy,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1_score": metrics.f1_score,
                "top_k_accuracy": metrics.top_k_accuracy
            }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Saved comparison report to {output_path}")
        return report
    
    def visualize_results(self, save_path: str = "model_comparison.png"):
        """Create visualization of model comparison"""
        if not self.results:
            print("No results to visualize. Run comparison first.")
            return
        
        # Prepare data for visualization
        models = list(self.results.keys())
        metrics = ['accuracy', 'precision', 'recall', 'f1_score']
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Performance metrics comparison
        performance_data = {
            'Model': [],
            'Metric': [],
            'Value': []
        }
        
        for model_name, result in self.results.items():
            for metric in metrics:
                performance_data['Model'].append(model_name)
                performance_data['Metric'].append(metric.capitalize())
                performance_data['Value'].append(getattr(result, f"similarity_{metric}" if metric == 'accuracy' else metric))
        
        # Performance metrics heatmap
        perf_matrix = np.array([[getattr(self.results[model], f"similarity_{metric}" if metric == 'accuracy' else metric) 
                               for metric in metrics] for model in models])
        
        sns.heatmap(perf_matrix, xticklabels=[m.capitalize() for m in metrics], 
                   yticklabels=models, annot=True, fmt='.3f', ax=ax1, cmap='YlOrRd')
        ax1.set_title('Performance Metrics Comparison')
        
        # Inference time comparison
        inference_times = [self.results[model].inference_time_ms for model in models]
        ax2.bar(models, inference_times, color='skyblue')
        ax2.set_title('Inference Time (ms per image)')
        ax2.set_ylabel('Time (ms)')
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        # Memory usage comparison
        memory_usage = [self.results[model].memory_usage_mb for model in models]
        ax3.bar(models, memory_usage, color='lightgreen')
        ax3.set_title('Memory Usage (MB)')
        ax3.set_ylabel('Memory (MB)')
        plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
        
        # Top-K accuracy comparison
        k_values = [1, 3, 5, 10]
        for model in models:
            top_k_accs = [self.results[model].top_k_accuracy.get(k, 0) for k in k_values]
            ax4.plot(k_values, top_k_accs, marker='o', label=model)
        
        ax4.set_title('Top-K Accuracy')
        ax4.set_xlabel('K')
        ax4.set_ylabel('Accuracy')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"✅ Saved comparison visualization to {save_path}")

def create_test_dataset() -> Tuple[List[str], List[Tuple[int, int]]]:
    """Create a test dataset with known duplicate pairs"""
    # Generate sample image URLs (using picsum for consistent images)
    test_images = []
    ground_truth_pairs = []
    
    # Create groups of similar images
    for group in range(5):
        base_seed = group * 100
        group_images = []
        
        # Add original and similar variations
        for variation in range(4):
            # Use same seed for similar images
            image_url = f"https://picsum.photos/seed/{base_seed + variation}/400/600"
            test_images.append(image_url)
            group_images.append(len(test_images) - 1)
        
        # Mark all pairs in this group as duplicates
        for i in range(len(group_images)):
            for j in range(i + 1, len(group_images)):
                ground_truth_pairs.append((group_images[i], group_images[j]))
    
    # Add some non-duplicate images
    for i in range(10):
        image_url = f"https://picsum.photos/400/600?random={i + 1000}"
        test_images.append(image_url)
    
    return test_images, ground_truth_pairs

def main():
    """Run comprehensive model comparison"""
    print("🔬 Starting Comprehensive ML Model Comparison")
    print("=" * 50)
    
    # Create test dataset
    print("📊 Creating test dataset...")
    test_images, ground_truth_pairs = create_test_dataset()
    print(f"Created dataset with {len(test_images)} images and {len(ground_truth_pairs)} duplicate pairs")
    
    # Initialize comparison
    comparison = ModelComparison(test_images, ground_truth_pairs)
    
    # Add models to compare
    print("\n🤖 Loading models...")
    
    models_to_test = [
        ("CLIP ViT-B/32", lambda: CLIPEmbeddingModel("openai/clip-vit-base-patch32")),
        ("CLIP ViT-L/14", lambda: CLIPEmbeddingModel("openai/clip-vit-large-patch14")),
        ("ViT Base", lambda: ViTEmbeddingModel("google/vit-base-patch16-224")),
        ("ResNet-50", lambda: ResNetEmbeddingModel("resnet50")),
        ("EfficientNet-B0", lambda: EfficientNetEmbeddingModel("efficientnet_b0")),
    ]
    
    for model_name, model_constructor in models_to_test:
        try:
            print(f"Loading {model_name}...")
            model = model_constructor()
            comparison.add_model(model)
        except Exception as e:
            print(f"Failed to load {model_name}: {e}")
    
    # Run comparison
    print(f"\n🚀 Running comparison on {len(comparison.models)} models...")
    results = comparison.run_comparison()
    
    # Create report
    print("\n📈 Generating results...")
    comparison.create_comparison_report()
    comparison.visualize_results()
    
    # Print summary
    print("\n📋 Summary Results:")
    print("-" * 80)
    print(f"{'Model':<20} {'F1-Score':<10} {'Accuracy':<10} {'Time(ms)':<10} {'Memory(MB)':<12}")
    print("-" * 80)
    
    for model_name, metrics in results.items():
        print(f"{model_name:<20} {metrics.f1_score:<10.3f} {metrics.similarity_accuracy:<10.3f} "
              f"{metrics.inference_time_ms:<10.1f} {metrics.memory_usage_mb:<12.1f}")
    
    print("\n🏆 Best Models:")
    best_f1 = max(results.values(), key=lambda x: x.f1_score)
    best_speed = min(results.values(), key=lambda x: x.inference_time_ms)
    best_memory = min(results.values(), key=lambda x: x.memory_usage_mb)
    
    print(f"Best F1-Score: {best_f1.model_name} ({best_f1.f1_score:.3f})")
    print(f"Fastest: {best_speed.model_name} ({best_speed.inference_time_ms:.1f}ms)")
    print(f"Most Memory Efficient: {best_memory.model_name} ({best_memory.memory_usage_mb:.1f}MB)")

if __name__ == "__main__":
    main()