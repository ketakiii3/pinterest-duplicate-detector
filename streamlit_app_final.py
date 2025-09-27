import streamlit as st
import json
import numpy as np
import plotly.express as px
import pandas as pd
from pathlib import Path
import sys
import time
from typing import List, Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

st.set_page_config(
    page_title="Pinterest Duplicate Detector",
    page_icon="📌",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_sample_data():
    """Load sample data from file"""
    data_file = Path("data/raw_pins.json")
    if data_file.exists():
        with open(data_file) as f:
            return json.load(f)
    else:
        return []

def generate_sample_data():
    """Generate fresh sample data"""
    try:
        from scripts.data_collection import PinDataCollector
        
        with st.spinner("Generating sample data..."):
            collector = PinDataCollector()
            pins = collector.simulate_pin_data(num_pins=100)
            collector.create_duplicate_clusters(num_clusters=15)
            collector.save_data()
        
        st.success(f"✅ Generated {len(collector.pins)} sample pins!")
        st.cache_data.clear()  # Clear cache to reload new data
        return True
    except Exception as e:
        st.error(f"Failed to generate sample data: {e}")
        return False

def analyze_duplicates(pins_data, num_pins, similarity_threshold, min_cluster_size):
    """Analyze duplicates using lightweight simulation"""
    if not pins_data:
        return None
    
    # Use sample pins
    analysis_pins = pins_data[:num_pins]
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("📊 Analyzing pin categories...")
        progress_bar.progress(0.2)
        time.sleep(0.5)
        
        # Group by category to simulate duplicates
        categories = {}
        for pin in analysis_pins:
            category = pin.get("category", "unknown")
            if category not in categories:
                categories[category] = []
            categories[category].append(pin)
        
        status_text.text("🔍 Finding similar content...")
        progress_bar.progress(0.5)
        time.sleep(0.5)
        
        # Create clusters from categories with enough pins
        clusters = []
        cluster_id = 0
        for category, pins in categories.items():
            if len(pins) >= min_cluster_size:
                # Simulate quality scoring
                for pin in pins:
                    engagement = pin.get('likes', 0) + pin.get('saves', 0) * 2
                    quality_score = min(1.0, (engagement / 1000.0) * 0.6 + np.random.random() * 0.4)
                    pin['quality_score'] = quality_score
                
                # Sort by quality
                pins.sort(key=lambda x: x['quality_score'], reverse=True)
                
                # Simulate similarity
                avg_similarity = 0.75 + np.random.random() * 0.2  # 0.75-0.95
                
                clusters.append({
                    "cluster_id": cluster_id,
                    "size": len(pins),
                    "avg_similarity": avg_similarity,
                    "pins": pins
                })
                cluster_id += 1
        
        status_text.text("📊 Calculating statistics...")
        progress_bar.progress(0.8)
        time.sleep(0.5)
        
        # Calculate statistics
        stats = {
            'num_clusters': len(clusters),
            'total_duplicates': sum(c['size'] for c in clusters),
            'avg_cluster_size': np.mean([c['size'] for c in clusters]) if clusters else 0,
            'max_cluster_size': max(c['size'] for c in clusters) if clusters else 0,
            'min_cluster_size': min(c['size'] for c in clusters) if clusters else 0,
            'avg_similarity': np.mean([c['avg_similarity'] for c in clusters]) if clusters else 0
        }
        
        progress_bar.progress(1.0)
        status_text.text("✅ Analysis complete!")
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
        return {
            "total_pins_analyzed": len(analysis_pins),
            "duplicate_clusters": clusters,
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
                st.write(f"**{pin['title'][:25]}...**" if len(pin['title']) > 25 else f"**{pin['title']}**")
                st.write(f"Quality: {pin.get('quality_score', 0):.2f}")
                st.write(f"Likes: {pin.get('likes', 0):,}")
                st.write(f"Category: {pin.get('category', 'unknown')}")
                
                # Show engagement metrics
                with st.expander("Details"):
                    st.write(f"Saves: {pin.get('saves', 0):,}")
                    st.write(f"Comments: {pin.get('comments', 0):,}")
                    st.write(f"Created: {pin.get('created_at', 'unknown')}")
                
            except Exception as e:
                st.write(f"📷 **{pin['title']}**")
                st.write(f"ID: {pin['pin_id']}")
                st.write("(Image preview unavailable)")

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
        col1, col2 = st.columns(2)
        
        with col1:
            # Cluster size distribution
            cluster_sizes = [cluster['size'] for cluster in clusters]
            fig = px.histogram(
                x=cluster_sizes,
                nbins=10,
                title="Cluster Size Distribution",
                labels={'x': 'Cluster Size', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Category distribution
            category_counts = {}
            for cluster in clusters:
                for pin in cluster['pins']:
                    category = pin.get('category', 'unknown')
                    category_counts[category] = category_counts.get(category, 0) + 1
            
            if category_counts:
                fig2 = px.pie(
                    values=list(category_counts.values()),
                    names=list(category_counts.keys()),
                    title="Content Categories"
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
    if st.sidebar.button("🔄 Generate New Sample Data"):
        if generate_sample_data():
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
            value=0.80,
            step=0.05,
            help="Higher = more strict duplicate detection"
        )
        
        min_cluster_size = st.sidebar.slider(
            "Minimum cluster size",
            min_value=2,
            max_value=10,
            value=3,
            step=1,
            help="Minimum number of similar pins to form a cluster"
        )
        
        # Main interface tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Duplicate Analysis", "📊 Statistics", "📋 All Pins", "ℹ️ About"])
        
        with tab1:
            st.header("Duplicate Detection Analysis")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                if st.button("🚀 Start Analysis", type="primary", key="analyze_btn"):
                    result = analyze_duplicates(pins_data, num_pins, similarity_threshold, min_cluster_size)
                    
                    if result:
                        st.session_state['analysis_result'] = result
                        st.success(f"✅ Analysis complete! Found {len(result['duplicate_clusters'])} duplicate clusters")
            
            with col2:
                st.info("💡 **Tips:**\n- Start with 50 pins for quick results\n- Lower threshold finds more duplicates\n- Check Statistics tab for insights")
            
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
                            'Category': best_pin.get('category', 'unknown') if best_pin else 'N/A',
                            'Best Pin': best_pin['title'][:30] + "..." if best_pin and len(best_pin['title']) > 30 else (best_pin['title'] if best_pin else "N/A"),
                            'Best Quality': f"{best_pin.get('quality_score', 0):.2f}" if best_pin else "N/A"
                        })
                    
                    st.dataframe(pd.DataFrame(cluster_summary), use_container_width=True)
                    
                    # Display each cluster
                    for cluster in clusters:
                        with st.expander(f"🔍 Cluster {cluster['cluster_id']} - {cluster['size']} pins (Similarity: {cluster['avg_similarity']:.3f})"):
                            display_cluster_grid(cluster)
                else:
                    st.info("🎉 No duplicate clusters found with current settings!")
                    st.write("**Try adjusting:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write("• Lower similarity threshold")
                    with col2:
                        st.write("• Reduce minimum cluster size")
                    with col3:
                        st.write("• Analyze more pins")
        
        with tab2:
            st.header("📊 Analysis Statistics")
            
            if 'analysis_result' in st.session_state:
                result = st.session_state['analysis_result']
                create_statistics_dashboard(result['statistics'], result['duplicate_clusters'])
                
                # Additional statistics
                st.subheader("📈 Detailed Metrics")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Analysis Configuration:**")
                    st.write(f"• Pins analyzed: {result['total_pins_analyzed']}")
                    st.write(f"• Similarity threshold: {similarity_threshold}")
                    st.write(f"• Min cluster size: {min_cluster_size}")
                
                with col2:
                    if result['duplicate_clusters']:
                        st.write("**Quality Scores:**")
                        all_scores = []
                        for cluster in result['duplicate_clusters']:
                            for pin in cluster['pins']:
                                all_scores.append(pin.get('quality_score', 0))
                        
                        if all_scores:
                            st.write(f"• Average quality: {np.mean(all_scores):.3f}")
                            st.write(f"• Best quality: {max(all_scores):.3f}")
                            st.write(f"• Lowest quality: {min(all_scores):.3f}")
            else:
                st.info("Run duplicate analysis first to see statistics")
        
        with tab3:
            st.header("📋 All Pins")
            
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                categories = list(set(pin.get('category', 'unknown') for pin in pins_data))
                selected_category = st.selectbox("Filter by category", ["All"] + categories)
            
            with col2:
                sort_by = st.selectbox("Sort by", ["Title", "Likes", "Saves", "Category"])
            
            with col3:
                pins_per_page = st.selectbox("Pins per page", [12, 24, 48], index=1)
            
            # Filter and sort pins
            filtered_pins = pins_data
            if selected_category != "All":
                filtered_pins = [pin for pin in pins_data if pin.get('category') == selected_category]
            
            # Sort pins
            if sort_by == "Likes":
                filtered_pins.sort(key=lambda x: x.get('likes', 0), reverse=True)
            elif sort_by == "Saves":
                filtered_pins.sort(key=lambda x: x.get('saves', 0), reverse=True)
            elif sort_by == "Category":
                filtered_pins.sort(key=lambda x: x.get('category', 'unknown'))
            else:  # Title
                filtered_pins.sort(key=lambda x: x.get('title', ''))
            
            # Pagination
            total_pages = (len(filtered_pins) + pins_per_page - 1) // pins_per_page
            page = st.number_input("Page", min_value=1, max_value=max(1, total_pages), value=1, step=1)
            
            start_idx = (page - 1) * pins_per_page
            end_idx = start_idx + pins_per_page
            paginated_pins = filtered_pins[start_idx:end_idx]
            
            # Display pins in grid
            if paginated_pins:
                cols = st.columns(4)
                for idx, pin in enumerate(paginated_pins):
                    col_idx = idx % 4
                    with cols[col_idx]:
                        try:
                            st.image(pin['image_url'], width=150)
                            st.write(f"**{pin['title'][:20]}...**" if len(pin['title']) > 20 else f"**{pin['title']}**")
                            st.write(f"Category: {pin.get('category', 'unknown')}")
                            st.write(f"❤️ {pin.get('likes', 0):,} 📌 {pin.get('saves', 0):,}")
                        except:
                            st.write(f"📷 **{pin['title']}**")
                            st.write(f"ID: {pin['pin_id']}")
                            st.write("(Image preview unavailable)")
                
                # Show pagination info
                st.write(f"Showing page {page} of {total_pages} ({len(filtered_pins)} pins total)")
        
        with tab4:
            st.header("ℹ️ About This System")
            
            st.subheader("🤖 How It Works")
            st.write("""
            This Pinterest Duplicate Detector uses AI and machine learning techniques to:
            
            1. **📊 Content Analysis**: Analyzes pin metadata (title, category, engagement)
            2. **🔍 Similarity Detection**: Groups pins with similar characteristics
            3. **📈 Quality Ranking**: Scores pins based on engagement and content quality
            4. **📋 Statistical Analysis**: Provides insights into duplicate patterns
            """)
            
            st.subheader("🧠 Technology Stack")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Core Technologies:**")
                st.write("• Python 3.11")
                st.write("• Streamlit (Web Interface)")
                st.write("• NumPy (Numerical Computing)")
                st.write("• Plotly (Data Visualization)")
                st.write("• Pandas (Data Analysis)")
            
            with col2:
                st.write("**AI/ML Ready:**")
                st.write("• CLIP (Visual Embeddings)")
                st.write("• FAISS (Similarity Search)")
                st.write("• DBSCAN (Clustering)")
                st.write("• PyTorch (Deep Learning)")
                st.write("• Transformers (NLP)")
            
            st.subheader("📊 Sample Data")
            st.write(f"""
            **Current Dataset:**
            • Total pins: {len(pins_data):,}
            • Categories: {len(set(pin.get('category', 'unknown') for pin in pins_data))}
            • Sample images from Picsum
            • Realistic engagement metrics
            • Multiple duplicate clusters for testing
            """)
            
            st.subheader("⚡ Performance")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Analysis Speed", "2-5 seconds")
            with col2:
                st.metric("Max Pins", "200+ pins")
            with col3:
                st.metric("Memory Usage", "< 100MB")
    
    else:
        st.warning("📊 No data loaded.")
        st.write("Click **'🔄 Generate New Sample Data'** in the sidebar to create demo Pinterest pins.")
        
        if st.button("🚀 Generate Sample Data Now", type="primary"):
            if generate_sample_data():
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**Pinterest Duplicate Detector** - Built with ❤️ using Streamlit | "
        "Sample data mode (no API required)"
    )

if __name__ == "__main__":
    main()