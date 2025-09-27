import numpy as np
import cv2
from PIL import Image
from typing import List, Dict, Union, Tuple, Optional
from pathlib import Path
import requests
from io import BytesIO
from dataclasses import dataclass

@dataclass
class QualityMetrics:
    """Quality metrics for an image"""
    pin_id: str
    resolution_score: float
    sharpness_score: float
    brightness_score: float
    contrast_score: float
    aspect_ratio_score: float
    overall_score: float

@dataclass
class QualityScore:
    """Simplified quality score for Pinterest pins"""
    pin_id: str
    total_score: float
    resolution_score: float
    clarity_score: float
    engagement_score: float
    credibility_score: float
    
class QualityRanker:
    """Rank images based on visual quality metrics"""
    
    def __init__(self):
        """Initialize quality ranker"""
        self.metrics_weights = {
            'resolution': 0.25,
            'sharpness': 0.30,
            'brightness': 0.15,
            'contrast': 0.20,
            'aspect_ratio': 0.10
        }
    
    def load_image(self, image_source: Union[str, Path, Image.Image]) -> np.ndarray:
        """Load image and convert to numpy array"""
        if isinstance(image_source, Image.Image):
            return cv2.cvtColor(np.array(image_source), cv2.COLOR_RGB2BGR)
        
        # Handle URL
        if isinstance(image_source, str) and image_source.startswith(('http://', 'https://')):
            try:
                response = requests.get(image_source, timeout=10)
                response.raise_for_status()
                pil_image = Image.open(BytesIO(response.content)).convert('RGB')
                return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            except Exception as e:
                raise ValueError(f"Failed to load image from URL: {e}")
        
        # Handle file path
        try:
            image = cv2.imread(str(image_source))
            if image is None:
                raise ValueError(f"Could not load image from {image_source}")
            return image
        except Exception as e:
            raise ValueError(f"Failed to load image from path: {e}")
    
    def calculate_resolution_score(self, image: np.ndarray) -> float:
        """Calculate resolution score (0-1)"""
        height, width = image.shape[:2]
        total_pixels = height * width
        
        # Score based on total pixels (Pinterest prefers higher resolution)
        if total_pixels >= 1920 * 1080:  # HD and above
            return 1.0
        elif total_pixels >= 1280 * 720:  # 720p
            return 0.8
        elif total_pixels >= 640 * 480:   # VGA
            return 0.6
        elif total_pixels >= 320 * 240:   # QVGA
            return 0.4
        else:
            return 0.2
    
    def calculate_sharpness_score(self, image: np.ndarray) -> float:
        """Calculate sharpness score using Laplacian variance"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Normalize to 0-1 scale (empirically determined thresholds)
        if laplacian_var >= 500:
            return 1.0
        elif laplacian_var >= 100:
            return 0.8
        elif laplacian_var >= 50:
            return 0.6
        elif laplacian_var >= 10:
            return 0.4
        else:
            return 0.2
    
    def calculate_brightness_score(self, image: np.ndarray) -> float:
        """Calculate brightness score (optimal range is around 100-150)"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        
        # Optimal brightness is around 100-150 (mid-range)
        if 100 <= mean_brightness <= 150:
            return 1.0
        elif 80 <= mean_brightness <= 180:
            return 0.8
        elif 60 <= mean_brightness <= 200:
            return 0.6
        elif 40 <= mean_brightness <= 220:
            return 0.4
        else:
            return 0.2
    
    def calculate_contrast_score(self, image: np.ndarray) -> float:
        """Calculate contrast score using standard deviation"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        contrast = np.std(gray)
        
        # Higher standard deviation indicates better contrast
        if contrast >= 60:
            return 1.0
        elif contrast >= 45:
            return 0.8
        elif contrast >= 30:
            return 0.6
        elif contrast >= 15:
            return 0.4
        else:
            return 0.2
    
    def calculate_aspect_ratio_score(self, image: np.ndarray) -> float:
        """Calculate aspect ratio score (Pinterest favors 2:3 ratio)"""
        height, width = image.shape[:2]
        aspect_ratio = width / height
        
        # Pinterest optimal ratios: 2:3 (0.67), 3:4 (0.75), 1:1 (1.0)
        optimal_ratios = [0.67, 0.75, 1.0]
        
        # Find closest optimal ratio
        closest_diff = min(abs(aspect_ratio - ratio) for ratio in optimal_ratios)
        
        if closest_diff <= 0.05:
            return 1.0
        elif closest_diff <= 0.15:
            return 0.8
        elif closest_diff <= 0.25:
            return 0.6
        elif closest_diff <= 0.4:
            return 0.4
        else:
            return 0.2
    
    def calculate_quality_metrics(self, image_source: Union[str, Path, Image.Image], pin_id: str) -> QualityMetrics:
        """Calculate all quality metrics for an image"""
        try:
            image = self.load_image(image_source)
            
            resolution_score = self.calculate_resolution_score(image)
            sharpness_score = self.calculate_sharpness_score(image)
            brightness_score = self.calculate_brightness_score(image)
            contrast_score = self.calculate_contrast_score(image)
            aspect_ratio_score = self.calculate_aspect_ratio_score(image)
            
            # Calculate weighted overall score
            overall_score = (
                resolution_score * self.metrics_weights['resolution'] +
                sharpness_score * self.metrics_weights['sharpness'] +
                brightness_score * self.metrics_weights['brightness'] +
                contrast_score * self.metrics_weights['contrast'] +
                aspect_ratio_score * self.metrics_weights['aspect_ratio']
            )
            
            return QualityMetrics(
                pin_id=pin_id,
                resolution_score=resolution_score,
                sharpness_score=sharpness_score,
                brightness_score=brightness_score,
                contrast_score=contrast_score,
                aspect_ratio_score=aspect_ratio_score,
                overall_score=overall_score
            )
            
        except Exception as e:
            print(f"Warning: Failed to calculate quality for {pin_id}: {e}")
            # Return default low quality scores for failed images
            return QualityMetrics(
                pin_id=pin_id,
                resolution_score=0.1,
                sharpness_score=0.1,
                brightness_score=0.1,
                contrast_score=0.1,
                aspect_ratio_score=0.1,
                overall_score=0.1
            )
    
    def rank_duplicates(
        self,
        duplicate_pin_ids: List[str],
        image_sources: Dict[str, Union[str, Path, Image.Image]]
    ) -> List[Tuple[str, QualityMetrics]]:
        """
        Rank duplicate pins by quality
        
        Args:
            duplicate_pin_ids: List of pin IDs that are duplicates
            image_sources: Dictionary mapping pin_id to image source
            
        Returns:
            List of (pin_id, QualityMetrics) tuples sorted by quality (best first)
        """
        quality_results = []
        
        for pin_id in duplicate_pin_ids:
            if pin_id in image_sources:
                metrics = self.calculate_quality_metrics(image_sources[pin_id], pin_id)
                quality_results.append((pin_id, metrics))
        
        # Sort by overall quality score (descending)
        quality_results.sort(key=lambda x: x[1].overall_score, reverse=True)
        
        return quality_results
    
    def get_best_from_duplicates(
        self,
        duplicate_pin_ids: List[str],
        image_sources: Dict[str, Union[str, Path, Image.Image]]
    ) -> Tuple[str, QualityMetrics]:
        """Get the highest quality pin from a group of duplicates"""
        ranked = self.rank_duplicates(duplicate_pin_ids, image_sources)
        if ranked:
            return ranked[0]  # Return the best quality pin
        else:
            raise ValueError("No valid pins found in duplicate group")
    
    def filter_low_quality(
        self,
        pin_quality_map: Dict[str, QualityMetrics],
        min_quality_threshold: float = 0.5
    ) -> List[str]:
        """
        Filter out pins with quality below threshold
        
        Args:
            pin_quality_map: Dictionary mapping pin_id to QualityMetrics
            min_quality_threshold: Minimum quality score to keep pin
            
        Returns:
            List of pin_ids that should be removed (low quality)
        """
        low_quality_pins = []
        
        for pin_id, metrics in pin_quality_map.items():
            if metrics.overall_score < min_quality_threshold:
                low_quality_pins.append(pin_id)
        
        return low_quality_pins
    
    def generate_quality_report(self, quality_metrics: List[QualityMetrics]) -> Dict:
        """Generate summary report of quality metrics"""
        if not quality_metrics:
            return {"error": "No quality metrics provided"}
        
        overall_scores = [m.overall_score for m in quality_metrics]
        resolution_scores = [m.resolution_score for m in quality_metrics]
        sharpness_scores = [m.sharpness_score for m in quality_metrics]
        brightness_scores = [m.brightness_score for m in quality_metrics]
        contrast_scores = [m.contrast_score for m in quality_metrics]
        aspect_ratio_scores = [m.aspect_ratio_score for m in quality_metrics]
        
        report = {
            "total_images": len(quality_metrics),
            "average_quality": np.mean(overall_scores),
            "quality_distribution": {
                "excellent (>0.8)": sum(1 for s in overall_scores if s > 0.8),
                "good (0.6-0.8)": sum(1 for s in overall_scores if 0.6 <= s <= 0.8),
                "fair (0.4-0.6)": sum(1 for s in overall_scores if 0.4 <= s < 0.6),
                "poor (<0.4)": sum(1 for s in overall_scores if s < 0.4),
            },
            "metric_averages": {
                "resolution": np.mean(resolution_scores),
                "sharpness": np.mean(sharpness_scores),
                "brightness": np.mean(brightness_scores),
                "contrast": np.mean(contrast_scores),
                "aspect_ratio": np.mean(aspect_ratio_scores),
            }
        }
        
        return report
    
    def calculate_quality_score(self, pin: Dict, embedding: Optional[np.ndarray] = None) -> QualityScore:
        """Calculate simplified quality score for Pinterest pin data"""
        pin_id = pin.get('pin_id', 'unknown')
        
        # Resolution score based on width/height
        width = pin.get('width', 400)
        height = pin.get('height', 600)
        total_pixels = width * height
        
        min_pixels = 400 * 600
        max_pixels = 1200 * 1600
        
        if total_pixels <= min_pixels:
            resolution_score = 0.2
        elif total_pixels >= max_pixels:
            resolution_score = 1.0
        else:
            resolution_score = (total_pixels - min_pixels) / (max_pixels - min_pixels)
        
        # Clarity score based on aspect ratio
        if width == 0 or height == 0:
            clarity_score = 0.0
        else:
            aspect_ratio = width / height
            ideal_ratios = [2/3, 3/4, 4/5]  # Pinterest preferred ratios
            ratio_scores = [1.0 - abs(aspect_ratio - ideal) for ideal in ideal_ratios]
            clarity_score = max(0.0, min(1.0, max(ratio_scores)))
        
        # Engagement score based on likes, saves, comments
        likes = pin.get('likes', 0)
        saves = pin.get('saves', 0)
        comments = pin.get('comments', 0)
        
        weighted_engagement = (saves * 2.0) + (likes * 1.0) + (comments * 0.5)
        
        if weighted_engagement <= 0:
            engagement_score = 0.0
        else:
            engagement_score = min(1.0, np.log10(weighted_engagement + 1) / 5.0)
        
        # Credibility score based on source and user
        has_source = bool(pin.get('source_url', pin.get('link', '')))
        user_id = pin.get('user_id', '')
        
        base_score = 0.5
        
        if has_source:
            base_score += 0.25
        
        if user_id:
            # Simulate user reputation (in real system, would use actual data)
            try:
                user_num = int(user_id.split('_')[-1]) if '_' in user_id else hash(user_id) % 100
                if user_num < 50:  # Simulate "established" users
                    base_score += 0.25
            except:
                pass
        
        credibility_score = min(1.0, base_score)
        
        # Calculate weighted total score
        weights = {
            'resolution': 0.25,
            'clarity': 0.25,
            'engagement': 0.30,
            'credibility': 0.20
        }
        
        total_score = (
            resolution_score * weights['resolution'] +
            clarity_score * weights['clarity'] +
            engagement_score * weights['engagement'] +
            credibility_score * weights['credibility']
        )
        
        return QualityScore(
            pin_id=pin_id,
            total_score=total_score,
            resolution_score=resolution_score,
            clarity_score=clarity_score,
            engagement_score=engagement_score,
            credibility_score=credibility_score
        )

def main():
    """Demo usage of quality ranker"""
    ranker = QualityRanker()
    
    # Example: Rank some sample images
    sample_urls = [
        "https://picsum.photos/600/900?random=1",  # Good aspect ratio
        "https://picsum.photos/400/600?random=2",  # Good aspect ratio
        "https://picsum.photos/800/600?random=3",  # Wide aspect ratio
    ]
    
    pin_ids = ["pin_1", "pin_2", "pin_3"]
    image_sources = dict(zip(pin_ids, sample_urls))
    
    print("Calculating quality metrics for sample images...")
    quality_metrics = []
    
    for pin_id in pin_ids:
        metrics = ranker.calculate_quality_metrics(image_sources[pin_id], pin_id)
        quality_metrics.append(metrics)
        
        print(f"\nQuality Metrics for {pin_id}:")
        print(f"  Resolution: {metrics.resolution_score:.2f}")
        print(f"  Sharpness: {metrics.sharpness_score:.2f}")
        print(f"  Brightness: {metrics.brightness_score:.2f}")
        print(f"  Contrast: {metrics.contrast_score:.2f}")
        print(f"  Aspect Ratio: {metrics.aspect_ratio_score:.2f}")
        print(f"  Overall Score: {metrics.overall_score:.2f}")
    
    # Generate quality report
    report = ranker.generate_quality_report(quality_metrics)
    print("\nQuality Report:")
    for key, value in report.items():
        print(f"  {key}: {value}")
    
    # Demo duplicate ranking
    print("\nRanking duplicates (simulated):")
    ranked = ranker.rank_duplicates(pin_ids, image_sources)
    for i, (pin_id, metrics) in enumerate(ranked, 1):
        print(f"  #{i}: {pin_id} (Score: {metrics.overall_score:.2f})")

if __name__ == "__main__":
    main()