import torch
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from typing import List, Union, Optional
from pathlib import Path
import requests
from io import BytesIO
from tqdm import tqdm

class EmbeddingExtractor:
    """Extract visual embeddings from images using CLIP model"""
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", device: str = None):
        """
        Initialize CLIP model for embedding extraction
        
        Args:
            model_name: HuggingFace model identifier
            device: Computing device ('cuda', 'cpu', or None for auto)
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Loading CLIP model on {self.device}...")
        
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()  # Set to evaluation mode
        
        print("✅ Model loaded successfully")
    
    def load_image(self, image_source: Union[str, Path, Image.Image]) -> Image.Image:
        """
        Load image from various sources
        
        Args:
            image_source: URL, file path, or PIL Image
            
        Returns:
            PIL Image object
        """
        if isinstance(image_source, Image.Image):
            return image_source
        
        # Handle URL
        if isinstance(image_source, str) and image_source.startswith(('http://', 'https://')):
            try:
                response = requests.get(image_source, timeout=10)
                response.raise_for_status()
                return Image.open(BytesIO(response.content)).convert('RGB')
            except Exception as e:
                raise ValueError(f"Failed to load image from URL: {e}")
        
        # Handle file path
        try:
            return Image.open(image_source).convert('RGB')
        except Exception as e:
            raise ValueError(f"Failed to load image from path: {e}")
    
    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """
        Preprocess image for CLIP model
        
        Args:
            image: PIL Image
            
        Returns:
            Preprocessed tensor
        """
        inputs = self.processor(images=image, return_tensors="pt")
        return inputs.pixel_values.to(self.device)
    
    def extract_embedding(self, image_source: Union[str, Path, Image.Image]) -> np.ndarray:
        """
        Extract embedding from a single image
        
        Args:
            image_source: Image source (URL, path, or PIL Image)
            
        Returns:
            Normalized embedding vector
        """
        image = self.load_image(image_source)
        pixel_values = self.preprocess_image(image)
        
        with torch.no_grad():
            image_features = self.model.get_image_features(pixel_values)
            # Normalize embedding
            embedding = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return embedding.cpu().numpy().squeeze()
    
    def extract_batch_embeddings(
        self, 
        image_sources: List[Union[str, Path, Image.Image]], 
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Extract embeddings from multiple images in batches
        
        Args:
            image_sources: List of image sources
            batch_size: Number of images to process at once
            show_progress: Show progress bar
            
        Returns:
            Array of embeddings (num_images x embedding_dim)
        """
        embeddings = []
        
        iterator = tqdm(range(0, len(image_sources), batch_size), 
                       desc="Extracting embeddings") if show_progress else range(0, len(image_sources), batch_size)
        
        for i in iterator:
            batch = image_sources[i:i + batch_size]
            batch_embeddings = []
            
            for img_source in batch:
                try:
                    embedding = self.extract_embedding(img_source)
                    batch_embeddings.append(embedding)
                except Exception as e:
                    print(f"Warning: Failed to process image {img_source}: {e}")
                    # Add zero vector for failed images
                    batch_embeddings.append(np.zeros(512))  # CLIP base dimension
            
            embeddings.extend(batch_embeddings)
        
        return np.array(embeddings)
    
    def save_embeddings(self, embeddings: np.ndarray, output_path: Union[str, Path]):
        """Save embeddings to disk"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(output_path, embeddings)
        print(f"✅ Saved {len(embeddings)} embeddings to {output_path}")
    
    @staticmethod
    def load_embeddings(embeddings_path: Union[str, Path]) -> np.ndarray:
        """Load embeddings from disk"""
        return np.load(embeddings_path)

def main():
    """Demo usage of embedding extractor"""
    extractor = EmbeddingExtractor()
    
    # Example: Extract embeddings from sample images
    sample_urls = [
        "https://picsum.photos/400/600?random=1",
        "https://picsum.photos/400/600?random=2",
        "https://picsum.photos/400/600?random=3"
    ]
    
    print("\nExtracting embeddings from sample images...")
    embeddings = extractor.extract_batch_embeddings(sample_urls, batch_size=2)
    
    print(f"\nEmbedding shape: {embeddings.shape}")
    print(f"Sample embedding (first 5 dims): {embeddings[0][:5]}")
    
    # Save embeddings
    extractor.save_embeddings(embeddings, "data/sample_embeddings.npy")

if __name__ == "__main__":
    main()