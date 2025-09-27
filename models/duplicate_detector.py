import numpy as np
import faiss
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from sklearn.cluster import DBSCAN
import json

@dataclass
class DuplicateCluster:
    """Represents a cluster of duplicate pins"""
    cluster_id: int
    pin_ids: List[str]
    similarities: List[float]
    size: int

class DuplicateDetector:
    """Detect duplicate pins using FAISS similarity search"""
    
    def __init__(self, embedding_dim: int = 512):
        """
        Initialize duplicate detector
        
        Args:
            embedding_dim: Dimension of embeddings (512 for CLIP base)
        """
        self.embedding_dim = embedding_dim
        self.index = None
        self.pin_ids = []
        self.embeddings = None
    
    def build_index(self, embeddings: np.ndarray, pin_ids: List[str], index_type: str = "L2"):
        """
        Build FAISS index for fast similarity search
        
        Args:
            embeddings: Array of embeddings (num_pins x embedding_dim)
            pin_ids: List of pin IDs corresponding to embeddings
            index_type: Type of FAISS index ("L2" or "IP" for inner product)
        """
        self.embeddings = embeddings.astype('float32')
        self.pin_ids = pin_ids
        
        # Normalize embeddings for cosine similarity (when using IP)
        if index_type == "IP":
            faiss.normalize_L2(self.embeddings)
        
        # Create FAISS index
        if index_type == "L2":
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        else:  # Inner Product (cosine similarity when normalized)
            self.index = faiss.IndexFlatIP(self.embedding_dim)
        
        self.index.add(self.embeddings)
        print(f"✅ Built FAISS index with {len(embeddings)} embeddings")
    
    def find_similar_pins(
        self, 
        query_idx: int, 
        k: int = 10, 
        threshold: Optional[float] = None
    ) -> List[Tuple[str, float]]:
        """
        Find k most similar pins to a query pin
        
        Args:
            query_idx: Index of query pin
            k: Number of similar pins to return
            threshold: Optional similarity threshold
            
        Returns:
            List of (pin_id, similarity_score) tuples
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")
        
        query_embedding = self.embeddings[query_idx:query_idx+1]
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx == query_idx:  # Skip self
                continue
            
            similarity = 1.0 / (1.0 + dist)  # Convert distance to similarity
            if threshold is None or similarity >= threshold:
                results.append((self.pin_ids[idx], float(similarity)))
        
        return results
    
    def find_all_duplicates(
        self, 
        similarity_threshold: float = 0.85,
        min_cluster_size: int = 2
    ) -> List[DuplicateCluster]:
        """
        Find all duplicate clusters in the dataset
        
        Args:
            similarity_threshold: Minimum similarity to consider duplicates
            min_cluster_size: Minimum number of pins in a cluster
            
        Returns:
            List of DuplicateCluster objects
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")
        
        # Find all pairwise similarities above threshold
        k = min(100, len(self.embeddings))  # Search top-k neighbors
        distances, indices = self.index.search(self.embeddings, k)
        
        # Build adjacency list for clustering
        similarity_matrix = 1.0 / (1.0 + distances)
        
        # Use DBSCAN for clustering
        # Convert similarity to distance for DBSCAN (ensure non-negative)
        distance_matrix = np.maximum(0.0, 1.0 - similarity_matrix)
        clustering = DBSCAN(
            eps=1.0 - similarity_threshold, 
            min_samples=min_cluster_size,
            metric='precomputed'
        ).fit(distance_matrix)
        
        # Group pins by cluster
        clusters = {}
        for pin_idx, cluster_id in enumerate(clustering.labels_):
            if cluster_id == -1:  # Noise point
                continue
            
            if cluster_id not in clusters:
                clusters[cluster_id] = {
                    'pin_ids': [],
                    'pin_indices': []
                }
            
            clusters[cluster_id]['pin_ids'].append(self.pin_ids[pin_idx])
            clusters[cluster_id]['pin_indices'].append(pin_idx)
        
        # Create DuplicateCluster objects
        duplicate_clusters = []
        for cluster_id, cluster_data in clusters.items():
            if len(cluster_data['pin_ids']) >= min_cluster_size:
                # Calculate average similarities within cluster
                pin_indices = cluster_data['pin_indices']
                similarities = []
                for i in pin_indices:
                    cluster_sims = similarity_matrix[i][indices[i]]
                    similarities.append(float(np.mean(cluster_sims[:len(pin_indices)])))
                
                duplicate_clusters.append(DuplicateCluster(
                    cluster_id=cluster_id,
                    pin_ids=cluster_data['pin_ids'],
                    similarities=similarities,
                    size=len(cluster_data['pin_ids'])
                ))
        
        print(f"✅ Found {len(duplicate_clusters)} duplicate clusters")
        return duplicate_clusters
    
    def get_cluster_statistics(self, clusters: List[DuplicateCluster]) -> Dict:
        """Get statistics about duplicate clusters"""
        if not clusters:
            return {"num_clusters": 0, "total_duplicates": 0}
        
        stats = {
            "num_clusters": len(clusters),
            "total_duplicates": sum(c.size for c in clusters),
            "avg_cluster_size": np.mean([c.size for c in clusters]),
            "max_cluster_size": max(c.size for c in clusters),
            "min_cluster_size": min(c.size for c in clusters),
            "avg_similarity": np.mean([np.mean(c.similarities) for c in clusters])
        }
        return stats
    
    def save_clusters(self, clusters: List[DuplicateCluster], output_path: str):
        """Save duplicate clusters to JSON file"""
        clusters_data = [
            {
                "cluster_id": int(c.cluster_id),
                "pin_ids": c.pin_ids,
                "similarities": c.similarities,
                "size": int(c.size)
            }
            for c in clusters
        ]
        
        with open(output_path, 'w') as f:
            json.dump(clusters_data, f, indent=2)
        
        print(f"✅ Saved {len(clusters)} clusters to {output_path}")

def main():
    """Demo usage of duplicate detector"""
    # Generate sample embeddings (normally would load from embedding_extractor)
    np.random.seed(42)
    num_pins = 100
    embedding_dim = 512
    
    # Create some duplicate groups
    embeddings = []
    pin_ids = []
    
    # Create 20 groups with 3-5 duplicates each
    for group in range(20):
        base_embedding = np.random.randn(embedding_dim)
        num_duplicates = np.random.randint(3, 6)
        
        for dup in range(num_duplicates):
            # Add small noise to create near-duplicates
            noise = np.random.randn(embedding_dim) * 0.1
            duplicate_embedding = base_embedding + noise
            # Normalize
            duplicate_embedding = duplicate_embedding / np.linalg.norm(duplicate_embedding)
            
            embeddings.append(duplicate_embedding)
            pin_ids.append(f"pin_{group}_{dup}")
    
    embeddings = np.array(embeddings, dtype='float32')
    
    # Initialize detector
    detector = DuplicateDetector(embedding_dim=embedding_dim)
    
    # Build index
    print("Building FAISS index...")
    detector.build_index(embeddings, pin_ids, index_type="IP")
    
    # Find duplicates
    print("\nFinding duplicate clusters...")
    clusters = detector.find_all_duplicates(similarity_threshold=0.85, min_cluster_size=2)
    
    # Get statistics
    stats = detector.get_cluster_statistics(clusters)
    print("\n📊 Duplicate Detection Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Show sample clusters
    print("\n🔍 Sample Duplicate Clusters:")
    for cluster in clusters[:3]:
        print(f"\nCluster {cluster.cluster_id} ({cluster.size} pins):")
        print(f"  Pin IDs: {', '.join(cluster.pin_ids)}")
        print(f"  Avg Similarity: {np.mean(cluster.similarities):.3f}")
    
    # Save results
    detector.save_clusters(clusters, "data/duplicate_clusters.json")

if __name__ == "__main__":
    main()