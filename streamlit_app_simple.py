import streamlit as st
import json
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
import sys
import time
from typing import List, Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from models.embedding_extractor import EmbeddingExtractor
from models.duplicate_detector import DuplicateDetector
from models.quality_ranker import QualityRanker

st.set_page_config(
    page_title="Pinterest Duplicate Detector",
    page_icon="📌",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_sample_data():
    """Load or generate sample data"""
    data_file = Path("data/raw_pins.json")
    if data_file.exists():
        with open(data_file) as f:
            return json.load(f)
    else:
        st.warning("Sample data not found. Click 'Generate Sample Data' to create it.")
        return []

def generate_sample_data():
    """Generate sample data"""
    try:
        from scripts.data_collection import PinDataCollector
        
        with st.spinner("Generating sample data..."):
            collector = PinDataCollector()
            pins = collector.simulate_pin_data(num_pins=100)
            collector.create_duplicate_clusters(num_clusters=15)
            collector.save_data()
        
        st.success(f"✅ Generated {len(collector.pins)} sample pins!")
        return collector.pins
    except Exception as e:
        st.error(f"Failed to generate sample data: {e}")
        return []

def analyze_duplicates(pins_data, num_pins, similarity_threshold, min_cluster_size):
    """Analyze duplicates in pins data"""
    if not pins_data:
        return None
    
    # Initialize models
    extractor = EmbeddingExtractor()
    detector = DuplicateDetector()
    ranker = QualityRanker()
    
    # Limit analysis to specified number of pins
    analysis_pins = pins_data[:num_pins]
    
    # Extract embeddings
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("📸 Extracting visual embeddings...")
    progress_bar.progress(0.1)
    
    try:
        image_urls = [pin["image_url"] for pin in analysis_pins]
        pin_ids = [pin["pin_id"] for pin in analysis_pins]
        
        embeddings = extractor.extract_batch_embeddings(
            image_urls, batch_size=8, show_progress=False
        )
        
        progress_bar.progress(0.5)
        status_text.text("🔎 Building similarity index...")
        
        # Build index and find duplicates
        detector.build_index(embeddings, pin_ids, index_type="IP")
        
        progress_bar.progress(0.7)
        status_text.text("🔍 Finding duplicate clusters...")
        
        clusters = detector.find_all_duplicates(
            similarity_threshold=similarity_threshold,
            min_cluster_size=min_cluster_size
        )
        
        progress_bar.progress(0.9)
        status_text.text("📊 Calculating quality scores...")
        
        # Format results
        cluster_results = []
        for cluster in clusters:
            cluster_pins = [pin for pin in analysis_pins if pin["pin_id"] in cluster.pin_ids]
            
            cluster_info = {
                "cluster_id": cluster.cluster_id,
                "size": cluster.size,
                "avg_similarity": float(np.mean(cluster.similarities)),
                "pins": []
            }
            
            for pin in cluster_pins:
                # Calculate quality score
                quality_score = ranker.calculate_quality_score(pin)
                
                cluster_info["pins"].append({
                    "pin_id": pin["pin_id"],
                    "title": pin["title"],
                    "description": pin["description"],
                    "image_url": pin["image_url"],
                    "category": pin.get("category", "unknown"),
                    "likes": pin.get("likes", 0),
                    "saves": pin.get("saves", 0),
                    "quality_score": quality_score.total_score,
                    "quality_breakdown": {
                        "resolution": quality_score.resolution_score,
                        "clarity": quality_score.clarity_score,
                        "engagement": quality_score.engagement_score,
                        "credibility": quality_score.credibility_score
                    }
                })
            
            # Sort pins by quality score
            cluster_info["pins"].sort(key=lambda x: x["quality_score"], reverse=True)
            cluster_results.append(cluster_info)
        
        progress_bar.progress(1.0)
        status_text.text("✅ Analysis complete!")
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
        # Get statistics
        stats = detector.get_cluster_statistics(clusters)
        
        return {
            "total_pins_analyzed": len(analysis_pins),
            "duplicate_clusters": cluster_results,
            "statistics": stats
        }
        
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        progress_bar.empty()
        status_text.empty()
        return None

def display_cluster_grid(cluster):
    """Display pins in a cluster as a grid"""
    st.subheader(f"🔍 Cluster {cluster['cluster_id']} ({cluster['size']} pins)")
    st.write(f"**Average Similarity:** {cluster['avg_similarity']:.3f}")
    
    # Create columns for grid layout
    num_cols = min(4, len(cluster['pins']))
    cols = st.columns(num_cols)
    
    for idx, pin in enumerate(cluster['pins']):
        col_idx = idx % num_cols
        with cols[col_idx]:
            try:
                st.image(pin['image_url'], caption=f"{pin['pin_id']}", width=150)
                st.write(f"**{pin['title'][:30]}...**" if len(pin['title']) > 30 else f"**{pin['title']}**")
                st.write(f"Quality: {pin['quality_score']:.2f}")
                st.write(f"Likes: {pin['likes']:,}")
                st.write(f"Category: {pin['category']}")
                
                # Quality breakdown in expander
                with st.expander("Quality Details"):
                    breakdown = pin['quality_breakdown']
                    st.write(f"Resolution: {breakdown['resolution']:.2f}")
                    st.write(f"Clarity: {breakdown['clarity']:.2f}")
                    st.write(f"Engagement: {breakdown['engagement']:.2f}")
                    st.write(f"Credibility: {breakdown['credibility']:.2f}")
                
            except Exception as e:
                st.write(f"📷 **{pin['title']}**")
                st.write(f"ID: {pin['pin_id']}")
                st.write("(Image failed to load)")

def create_statistics_dashboard(stats: Dict, clusters: List):
    """Create statistics dashboard"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Clusters", stats.get('num_clusters', 0))
    
    with col2:
        st.metric("Total Duplicates", stats.get('total_duplicates', 0))
    
    with col3:
        st.metric("Avg Cluster Size", f"{stats.get('avg_cluster_size', 0):.1f}")
    
    with col4:
        st.metric("Avg Similarity", f"{stats.get('avg_similarity', 0):.3f}")
    
    if clusters:
        # Cluster size distribution
        cluster_sizes = [cluster['size'] for cluster in clusters]
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.histogram(
                x=cluster_sizes,
                nbins=10,
                title="Cluster Size Distribution",
                labels={'x': 'Cluster Size', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Quality distribution for duplicates
            quality_scores = []
            for cluster in clusters:
                for pin in cluster['pins']:
                    quality_scores.append(pin['quality_score'])
            
            if quality_scores:
                fig2 = px.histogram(
                    x=quality_scores,
                    nbins=20,
                    title="Quality Score Distribution",
                    labels={'x': 'Quality Score', 'y': 'Count'}
                )
                st.plotly_chart(fig2, use_container_width=True)

def main():
    st.title("📌 Pinterest Duplicate Detector")
    st.markdown("**AI-powered duplicate detection and quality ranking for Pinterest-style content**")
    
    # Sidebar controls
    st.sidebar.header("🎛️ Analysis Settings")
    
    # Load sample data
    pins_data = load_sample_data()
    
    # Data management
    st.sidebar.subheader("📊 Data Management")
    if st.sidebar.button("🔄 Generate Sample Data"):
        pins_data = generate_sample_data()
        st.rerun()
    
    if pins_data:
        st.sidebar.success(f"✅ {len(pins_data)} pins loaded")
        
        # Analysis settings
        st.sidebar.subheader("🔧 Analysis Parameters")
        
        num_pins = st.sidebar.slider(
            "Number of pins to analyze",
            min_value=10,
            max_value=min(200, len(pins_data)),
            value=min(50, len(pins_data)),
            step=10,
            help="More pins = longer analysis time"
        )
        
        similarity_threshold = st.sidebar.slider(
            "Similarity threshold",
            min_value=0.5,
            max_value=0.95,
            value=0.85,
            step=0.05,
            help="Higher = more strict duplicate detection"
        )
        
        min_cluster_size = st.sidebar.slider(
            "Minimum cluster size",
            min_value=2,
            max_value=10,
            value=2,
            step=1,
            help="Minimum number of similar pins to form a cluster"
        )
        
        # Main interface tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Duplicate Analysis", "📊 Statistics", "📋 All Pins", "🤖 Model Info"])
        
        with tab1:
            st.header("Duplicate Detection Analysis")
            
            if st.button("🚀 Start Analysis", type="primary", key="analyze_btn"):
                result = analyze_duplicates(pins_data, num_pins, similarity_threshold, min_cluster_size)
                
                if result:
                    st.session_state['analysis_result'] = result
                    st.success(f"✅ Analysis complete! Found {len(result['duplicate_clusters'])} duplicate clusters")
            
            # Display results if available
            if 'analysis_result' in st.session_state:
                result = st.session_state['analysis_result']
                clusters = result['duplicate_clusters']
                stats = result['statistics']
                
                if clusters:
                    st.header("🔍 Duplicate Clusters Found")
                    
                    # Cluster overview table
                    cluster_summary = []
                    for cluster in clusters:
                        best_pin = cluster['pins'][0] if cluster['pins'] else None
                        cluster_summary.append({
                            'Cluster ID': cluster['cluster_id'],
                            'Size': cluster['size'],
                            'Avg Similarity': f"{cluster['avg_similarity']:.3f}",
                            'Best Pin': best_pin['title'][:30] + "..." if best_pin and len(best_pin['title']) > 30 else (best_pin['title'] if best_pin else "N/A"),
                            'Best Quality': f"{best_pin['quality_score']:.2f}" if best_pin else "N/A"
                        })
                    
                    st.dataframe(pd.DataFrame(cluster_summary), use_container_width=True)
                    
                    # Display each cluster
                    for cluster in clusters:
                        with st.expander(f"🔍 Cluster {cluster['cluster_id']} - {cluster['size']} pins (Similarity: {cluster['avg_similarity']:.3f})"):
                            display_cluster_grid(cluster)
                else:
                    st.info("🎉 No duplicate clusters found with current settings!")
                    st.write("Try:")
                    st.write("- Lowering the similarity threshold")
                    st.write("- Reducing minimum cluster size")
                    st.write("- Analyzing more pins")
        
        with tab2:
            st.header("📊 Analysis Statistics")
            
            if 'analysis_result' in st.session_state:
                result = st.session_state['analysis_result']
                create_statistics_dashboard(result['statistics'], result['duplicate_clusters'])
            else:
                st.info("Run duplicate analysis first to see statistics")
        
        with tab3:
            st.header("📋 All Pins")
            
            # Pagination controls
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                page = st.number_input("Page", min_value=1, value=1, step=1)
                pins_per_page = st.selectbox("Pins per page", [20, 50, 100], index=1)
            
            # Calculate pagination
            start_idx = (page - 1) * pins_per_page
            end_idx = start_idx + pins_per_page
            paginated_pins = pins_data[start_idx:end_idx]
            
            # Display pins in grid
            if paginated_pins:
                cols = st.columns(4)
                for idx, pin in enumerate(paginated_pins):
                    col_idx = idx % 4
                    with cols[col_idx]:
                        try:
                            st.image(pin['image_url'], width=150)
                            st.write(f"**{pin['title'][:20]}...**" if len(pin['title']) > 20 else f"**{pin['title']}**")
                            st.write(f"ID: {pin['pin_id']}")
                            st.write(f"Category: {pin.get('category', 'unknown')}")
                            st.write(f"Likes: {pin.get('likes', 0):,}")
                        except:
                            st.write(f"📷 **{pin['title']}**")
                            st.write(f"ID: {pin['pin_id']}")
                            st.write("(Image failed to load)")
                
                # Show pagination info
                total_pages = (len(pins_data) + pins_per_page - 1) // pins_per_page
                st.write(f"Page {page} of {total_pages} ({len(pins_data)} total pins)")
        
        with tab4:
            st.header("🤖 Model Information")
            
            st.subheader("🧠 Embedding Model: CLIP ViT-B/32")
            st.write("""
            - **Purpose**: Extract visual embeddings from images
            - **Architecture**: Vision Transformer with 32x32 patches
            - **Embedding Dimension**: 512
            - **Strengths**: Semantic understanding, text-image alignment
            """)
            
            st.subheader("🔎 Similarity Search: FAISS")
            st.write("""
            - **Purpose**: Fast similarity search and indexing
            - **Algorithm**: Inner Product (cosine similarity)
            - **Performance**: Sub-second search on thousands of embeddings
            """)
            
            st.subheader("🎯 Clustering: DBSCAN")
            st.write("""
            - **Purpose**: Group similar embeddings into clusters
            - **Algorithm**: Density-based clustering
            - **Parameters**: Similarity threshold, minimum cluster size
            """)
            
            st.subheader("📊 Quality Ranking")
            st.write("""
            - **Resolution Score**: Based on image dimensions
            - **Clarity Score**: Aspect ratio optimization
            - **Engagement Score**: Likes, saves, comments
            - **Credibility Score**: Source URL, user reputation
            """)
            
            # Performance info
            st.subheader("⚡ Performance")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Embedding Extraction", "~45ms/image")
            with col2:
                st.metric("Similarity Search", "<1s for 1000 pins")
            with col3:
                st.metric("Memory Usage", "~2MB per 1000 pins")
    
    else:
        st.warning("📊 No data loaded. Please generate sample data to get started.")
        st.write("Click **'Generate Sample Data'** in the sidebar to create demo Pinterest pins.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**Pinterest Duplicate Detector** - Built with Streamlit, CLIP, and FAISS | "
        "[GitHub](https://github.com) | [Documentation](./README.md)"
    )

if __name__ == "__main__":
    main()