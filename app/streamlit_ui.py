import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# API Configuration
API_BASE_URL = "http://localhost:8000"

def check_api_connection():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_pins(limit: int = 50, offset: int = 0):
    """Get pins from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/pins", params={"limit": limit, "offset": offset})
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch pins: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error fetching pins: {e}")
        return []

def analyze_duplicates(num_pins: int, similarity_threshold: float, min_cluster_size: int):
    """Analyze duplicates via API"""
    try:
        with st.spinner("Analyzing duplicates... This may take a few minutes."):
            response = requests.post(
                f"{API_BASE_URL}/analyze-duplicates",
                params={
                    "num_pins": num_pins,
                    "similarity_threshold": similarity_threshold,
                    "min_cluster_size": min_cluster_size
                },
                timeout=300  # 5 minute timeout
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Analysis failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error during analysis: {e}")
        return None

def display_cluster_grid(cluster):
    """Display pins in a cluster as a grid"""
    st.subheader(f"🔍 Cluster {cluster['cluster_id']} ({cluster['size']} pins)")
    st.write(f"Average Similarity: {cluster['avg_similarity']:.3f}")
    
    # Create columns for grid layout
    cols = st.columns(min(4, len(cluster['pins'])))
    
    for idx, pin in enumerate(cluster['pins']):
        col_idx = idx % len(cols)
        with cols[col_idx]:
            try:
                st.image(pin['image_url'], caption=f"{pin['pin_id']}", width=150)
                if pin.get('quality_score'):
                    st.write(f"Quality: {pin['quality_score']:.2f}")
            except:
                st.write(f"📷 {pin['pin_id']}")
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
    
    # Cluster size distribution
    if clusters:
        cluster_sizes = [cluster['size'] for cluster in clusters]
        
        fig = px.histogram(
            x=cluster_sizes,
            nbins=10,
            title="Cluster Size Distribution",
            labels={'x': 'Cluster Size', 'y': 'Count'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Quality distribution for duplicates
        quality_scores = []
        for cluster in clusters:
            for pin in cluster['pins']:
                if pin.get('quality_score'):
                    quality_scores.append(pin['quality_score'])
        
        if quality_scores:
            fig2 = px.histogram(
                x=quality_scores,
                nbins=20,
                title="Quality Score Distribution (Duplicates)",
                labels={'x': 'Quality Score', 'y': 'Count'}
            )
            st.plotly_chart(fig2, use_container_width=True)

def main():
    st.set_page_config(
        page_title="Pinterest Duplicate Detector",
        page_icon="📌",
        layout="wide"
    )
    
    st.title("📌 Pinterest Duplicate Detector")
    st.write("Find and analyze duplicate pins with AI-powered image similarity detection")
    
    # Check API connection
    if not check_api_connection():
        st.error("🚨 API is not running! Please start the API first:")
        st.code("uvicorn app.api:app --reload")
        st.stop()
    
    st.success("✅ Connected to API")
    
    # Sidebar controls
    st.sidebar.header("🎛️ Analysis Settings")
    
    num_pins = st.sidebar.slider(
        "Number of pins to analyze",
        min_value=10,
        max_value=500,
        value=100,
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
    tab1, tab2, tab3 = st.tabs(["🔍 Duplicate Analysis", "📊 Statistics", "📋 All Pins"])
    
    with tab1:
        st.header("Duplicate Detection Analysis")
        
        if st.button("🚀 Start Analysis", type="primary", key="analyze_btn"):
            result = analyze_duplicates(num_pins, similarity_threshold, min_cluster_size)
            
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
                
                # Cluster overview
                cluster_data = []
                for cluster in clusters:
                    cluster_data.append({
                        'Cluster ID': cluster['cluster_id'],
                        'Size': cluster['size'],
                        'Avg Similarity': f"{cluster['avg_similarity']:.3f}"
                    })
                
                st.dataframe(pd.DataFrame(cluster_data), use_container_width=True)
                
                # Display each cluster
                for cluster in clusters:
                    with st.expander(f"Cluster {cluster['cluster_id']} - {cluster['size']} pins"):
                        display_cluster_grid(cluster)
                        
                        # Show pin details
                        st.subheader("Pin Details")
                        pin_details = []
                        for pin in cluster['pins']:
                            pin_details.append({
                                'Pin ID': pin['pin_id'],
                                'Title': pin['title'],
                                'Quality Score': f"{pin.get('quality_score', 0):.2f}",
                                'Image URL': pin['image_url']
                            })
                        st.dataframe(pd.DataFrame(pin_details))
            else:
                st.info("🎉 No duplicate clusters found with current settings!")
    
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
        
        offset = (page - 1) * pins_per_page
        pins = get_pins(limit=pins_per_page, offset=offset)
        
        if pins:
            # Display pins in grid
            cols = st.columns(4)
            for idx, pin in enumerate(pins):
                col_idx = idx % 4
                with cols[col_idx]:
                    try:
                        st.image(pin['image_url'], caption=pin['title'], width=150)
                        st.write(f"ID: {pin['pin_id']}")
                    except:
                        st.write(f"📷 {pin['title']}")
                        st.write(f"ID: {pin['pin_id']}")
                        st.write("(Image failed to load)")
        else:
            st.warning("No pins found. Make sure to generate data first!")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**Pinterest Duplicate Detector** - Built with Streamlit, FastAPI, and CLIP embeddings"
    )

if __name__ == "__main__":
    main()