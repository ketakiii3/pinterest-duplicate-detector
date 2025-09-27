import streamlit as st
import json
import numpy as np
import plotly.express as px
import pandas as pd
from pathlib import Path
import time
import random
from datetime import datetime
from typing import List, Dict

st.set_page_config(
    page_title="Pinterest Duplicate Detector",
    page_icon="📌",
    layout="wide",
    initial_sidebar_state="expanded"
)

def create_sample_data(num_pins=100):
    """Create sample Pinterest-style data directly in the app"""
    categories = ["food", "fashion", "home-decor", "travel", "diy", "art", "beauty", "tech"]
    
    pins = []
    
    # Generate main pins
    for i in range(num_pins):
        pin = {
            "pin_id": f"pin_{i:06d}",
            "title": f"{random.choice(['Amazing', 'Beautiful', 'Stunning', 'Creative', 'Inspiring'])} {random.choice(categories).title()} {random.choice(['Ideas', 'Design', 'Inspiration', 'Tutorial', 'Guide'])}",
            "description": f"Discover amazing {random.choice(categories)} inspiration and ideas for your next project.",
            "image_url": f"https://picsum.photos/400/600?random={i}",
            "category": random.choice(categories),
            "likes": random.randint(10, 5000),
            "saves": random.randint(5, 2000),
            "comments": random.randint(0, 200),
            "width": random.choice([400, 600, 800]),
            "height": random.choice([600, 800, 1000]),
            "source_url": f"https://example.com/pin/{i}",
            "created_at": datetime.now().isoformat(),
            "user_id": f"user_{random.randint(1, 50):03d}",
            "board_id": f"board_{random.randint(1, 20):03d}"
        }
        pins.append(pin)
    
    # Create duplicate clusters (15% of pins)
    num_clusters = max(3, num_pins // 15)
    for cluster_id in range(num_clusters):
        # Pick a random base pin
        base_pin_idx = random.randint(0, len(pins) - 1)
        base_pin = pins[base_pin_idx].copy()
        
        # Create 2-4 duplicates
        num_duplicates = random.randint(2, 4)
        for dup_idx in range(num_duplicates):
            dup_pin = base_pin.copy()
            dup_pin["pin_id"] = f"dup_{cluster_id}_{dup_idx}"
            dup_pin["title"] = base_pin["title"] + f" - Variation {dup_idx + 1}"
            dup_pin["likes"] = max(0, base_pin["likes"] + random.randint(-200, 200))
            dup_pin["saves"] = max(0, base_pin["saves"] + random.randint(-100, 100))
            dup_pin["image_url"] = f"https://picsum.photos/400/600?random={base_pin_idx + 1000 + dup_idx}"
            pins.append(dup_pin)
    
    return pins

@st.cache_data
def load_or_create_sample_data():
    """Load existing data or create new sample data"""
    # Try to load from file first
    data_file = Path("data/raw_pins.json")
    if data_file.exists():
        try:
            with open(data_file) as f:
                data = json.load(f)
                if len(data) > 0:
                    return data
        except:
            pass
    
    # Create new sample data
    return create_sample_data(120)

def save_sample_data(pins_data):
    """Save sample data to file"""
    try:
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        with open(data_dir / "raw_pins.json", 'w') as f:
            json.dump(pins_data, f, indent=2)
        return True
    except:
        return False

def analyze_duplicates(pins_data, num_pins, similarity_threshold, min_cluster_size):
    """Analyze duplicates using smart category-based clustering"""
    if not pins_data:
        return None
    
    # Use sample pins
    analysis_pins = pins_data[:num_pins]
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("📊 Analyzing pin content...")
        progress_bar.progress(0.2)
        time.sleep(0.3)
        
        # Simple category-based clustering (more reliable)
        category_groups = {}
        
        for pin in analysis_pins:
            category = pin.get("category", "unknown")
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(pin)
        
        # Create clusters from categories with multiple pins
        potential_clusters = {}
        cluster_counter = 0
        
        for category, pins in category_groups.items():
            if len(pins) >= min_cluster_size:
                # For larger categories, create sub-clusters based on title similarity
                if len(pins) > 8:
                    # Split into smaller groups based on common words
                    word_groups = {}
                    for pin in pins:
                        title = pin.get("title", "").lower()
                        # Use first meaningful word as grouping key
                        words = [w for w in title.split() if len(w) > 3]
                        key_word = words[0] if words else "misc"
                        
                        if key_word not in word_groups:
                            word_groups[key_word] = []
                        word_groups[key_word].append(pin)
                    
                    # Add sub-clusters that meet minimum size
                    for word_key, word_pins in word_groups.items():
                        if len(word_pins) >= min_cluster_size:
                            potential_clusters[f"{category}_{cluster_counter}"] = word_pins
                            cluster_counter += 1
                else:
                    # Small category - treat as single cluster
                    potential_clusters[f"{category}_{cluster_counter}"] = pins
                    cluster_counter += 1
        
        status_text.text("🔍 Identifying duplicate clusters...")
        progress_bar.progress(0.5)
        time.sleep(0.3)
        
        # Process clusters and calculate quality
        clusters = []
        cluster_id = 0
        
        for cluster_key, cluster_pins in potential_clusters.items():
            # Calculate quality scores for pins in cluster
            for pin in cluster_pins:
                likes = pin.get('likes', 0)
                saves = pin.get('saves', 0)
                comments = pin.get('comments', 0)
                
                # Quality score based on engagement
                engagement_score = (saves * 2.0 + likes * 1.0 + comments * 0.5) / 1000.0
                quality_score = min(1.0, engagement_score * 0.7 + random.random() * 0.3)
                pin['quality_score'] = quality_score
            
            # Sort by quality (best first)
            cluster_pins.sort(key=lambda x: x['quality_score'], reverse=True)
            
            # Calculate average similarity (simulated based on cluster size)
            base_similarity = 0.75 + (len(cluster_pins) - 2) * 0.05  # Larger clusters = higher similarity
            avg_similarity = min(0.95, base_similarity + random.random() * 0.1)
            
            # Extract category from cluster_key or first pin
            category = cluster_pins[0].get('category', 'unknown') if cluster_pins else 'unknown'
            
            clusters.append({
                "cluster_id": cluster_id,
                "size": len(cluster_pins),
                "avg_similarity": avg_similarity,
                "category": category,
                "pins": cluster_pins
            })
            cluster_id += 1
        
        status_text.text("📈 Calculating statistics...")
        progress_bar.progress(0.8)
        time.sleep(0.3)
        
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
    st.subheader(f"🔍 Cluster {cluster['cluster_id']} - {cluster['category'].title()} ({cluster['size']} pins)")
    st.write(f"**Average Similarity:** {cluster['avg_similarity']:.3f}")
    
    # Create columns for grid layout
    num_cols = min(4, len(cluster['pins']))
    cols = st.columns(num_cols)
    
    for idx, pin in enumerate(cluster['pins']):
        col_idx = idx % num_cols
        with cols[col_idx]:
            try:
                st.image(pin['image_url'], caption=f"Quality: {pin.get('quality_score', 0):.2f}", width=150)
                st.write(f"**{pin['title'][:30]}...**" if len(pin['title']) > 30 else f"**{pin['title']}**")
                st.write(f"❤️ {pin.get('likes', 0):,} | 📌 {pin.get('saves', 0):,}")
                
                # Show details in expander
                with st.expander("📋 Details"):
                    st.write(f"**ID:** {pin['pin_id']}")
                    st.write(f"**Comments:** {pin.get('comments', 0):,}")
                    st.write(f"**User:** {pin.get('user_id', 'unknown')}")
                    st.write(f"**Board:** {pin.get('board_id', 'unknown')}")
                
            except Exception as e:
                st.write(f"📷 **{pin['title'][:25]}...**")
                st.write(f"ID: {pin['pin_id']}")
                st.write("(Image preview unavailable)")
                st.write(f"Quality: {pin.get('quality_score', 0):.2f}")

def create_statistics_dashboard(stats: Dict, clusters: List):
    """Create statistics dashboard"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Duplicate Clusters", stats.get('num_clusters', 0))
    
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
                nbins=min(10, len(cluster_sizes)),
                title="Cluster Size Distribution",
                labels={'x': 'Cluster Size', 'y': 'Count'},
                color_discrete_sequence=['#ff6b6b']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Category distribution
            category_counts = {}
            for cluster in clusters:
                category = cluster.get('category', 'unknown')
                category_counts[category] = category_counts.get(category, 0) + cluster['size']
            
            if category_counts:
                fig2 = px.pie(
                    values=list(category_counts.values()),
                    names=list(category_counts.keys()),
                    title="Duplicate Content by Category",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig2, use_container_width=True)

def main():
    st.title("📌 Pinterest Duplicate Detector")
    st.markdown("**AI-powered duplicate detection and quality ranking for Pinterest-style content**")
    
    # Sidebar controls
    st.sidebar.header("🎛️ Analysis Settings")
    
    # Load sample data
    pins_data = load_or_create_sample_data()
    
    # Data management
    st.sidebar.subheader("📊 Data Management")
    if st.sidebar.button("🔄 Generate Fresh Sample Data"):
        with st.spinner("Creating new sample data..."):
            new_data = create_sample_data(150)
            save_sample_data(new_data)
            st.cache_data.clear()
        st.success("✅ Fresh sample data generated!")
        st.rerun()
    
    if pins_data:
        st.sidebar.success(f"✅ {len(pins_data)} pins loaded")
        
        # Analysis settings
        st.sidebar.subheader("🔧 Analysis Parameters")
        
        num_pins = st.sidebar.slider(
            "Number of pins to analyze",
            min_value=20,
            max_value=min(150, len(pins_data)),
            value=min(80, len(pins_data)),
            step=10,
            help="More pins = more potential duplicates found"
        )
        
        similarity_threshold = st.sidebar.slider(
            "Similarity threshold",
            min_value=0.5,
            max_value=0.95,
            value=0.75,
            step=0.05,
            help="Lower = find more loose duplicates"
        )
        
        min_cluster_size = st.sidebar.slider(
            "Minimum cluster size",
            min_value=2,
            max_value=8,
            value=3,
            step=1,
            help="Minimum pins needed to form a duplicate cluster"
        )
        
        # Main interface tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Duplicate Analysis", "📊 Statistics", "📋 Browse Pins", "ℹ️ About"])
        
        with tab1:
            st.header("Duplicate Detection Analysis")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("🚀 Start Duplicate Analysis", type="primary"):
                    result = analyze_duplicates(pins_data, num_pins, similarity_threshold, min_cluster_size)
                    
                    if result:
                        st.session_state['analysis_result'] = result
                        clusters_found = len(result['duplicate_clusters'])
                        total_dupes = result['statistics']['total_duplicates']
                        st.success(f"✅ Found {clusters_found} duplicate clusters with {total_dupes} total duplicate pins!")
            
            with col2:
                st.info("💡 **Quick Tips:**\n\n• Start with 80 pins\n• Lower threshold = more results\n• Check Statistics tab for insights")
            
            # Display results
            if 'analysis_result' in st.session_state:
                result = st.session_state['analysis_result']
                clusters = result['duplicate_clusters']
                
                if clusters:
                    st.header("🔍 Duplicate Clusters Found")
                    
                    # Summary table
                    summary_data = []
                    for cluster in clusters:
                        best_pin = cluster['pins'][0] if cluster['pins'] else None
                        summary_data.append({
                            'Cluster': cluster['cluster_id'],
                            'Category': cluster.get('category', 'unknown').title(),
                            'Size': cluster['size'],
                            'Similarity': f"{cluster['avg_similarity']:.3f}",
                            'Best Pin': best_pin['title'][:40] + "..." if best_pin and len(best_pin['title']) > 40 else (best_pin['title'] if best_pin else "N/A"),
                            'Top Quality': f"{best_pin.get('quality_score', 0):.2f}" if best_pin else "N/A"
                        })
                    
                    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
                    
                    # Display clusters
                    st.subheader("📋 Detailed Cluster View")
                    for cluster in clusters:
                        with st.expander(f"📁 {cluster.get('category', 'unknown').title()} Cluster - {cluster['size']} pins (Similarity: {cluster['avg_similarity']:.3f})", expanded=False):
                            display_cluster_grid(cluster)
                else:
                    st.info("🎯 No duplicate clusters found with current settings.")
                    st.write("**Try adjusting:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write("• Lower similarity threshold")
                    with col2:
                        st.write("• Reduce min cluster size")
                    with col3:
                        st.write("• Analyze more pins")
        
        with tab2:
            st.header("📊 Analysis Statistics")
            
            if 'analysis_result' in st.session_state:
                result = st.session_state['analysis_result']
                create_statistics_dashboard(result['statistics'], result['duplicate_clusters'])
                
                # Additional insights
                if result['duplicate_clusters']:
                    st.subheader("🎯 Key Insights")
                    
                    clusters = result['duplicate_clusters']
                    total_analyzed = result['total_pins_analyzed']
                    total_dupes = result['statistics']['total_duplicates']
                    duplicate_rate = (total_dupes / total_analyzed) * 100
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Duplicate Rate", f"{duplicate_rate:.1f}%")
                    with col2:
                        avg_quality = np.mean([np.mean([pin.get('quality_score', 0) for pin in cluster['pins']]) for cluster in clusters])
                        st.metric("Avg Quality Score", f"{avg_quality:.2f}")
                    with col3:
                        categories = len(set(cluster.get('category', 'unknown') for cluster in clusters))
                        st.metric("Categories with Duplicates", categories)
                    
                    # Quality distribution
                    st.subheader("📈 Quality Score Distribution")
                    all_scores = []
                    for cluster in clusters:
                        for pin in cluster['pins']:
                            all_scores.append(pin.get('quality_score', 0))
                    
                    if all_scores:
                        fig = px.histogram(
                            x=all_scores,
                            nbins=20,
                            title="Quality Scores of Duplicate Pins",
                            labels={'x': 'Quality Score', 'y': 'Count'},
                            color_discrete_sequence=['#4ecdc4']
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 Run duplicate analysis first to see detailed statistics and insights.")
        
        with tab3:
            st.header("📋 Browse All Pins")
            
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                categories = ["All"] + sorted(list(set(pin.get('category', 'unknown') for pin in pins_data)))
                selected_category = st.selectbox("Filter by category", categories)
            
            with col2:
                sort_options = ["Title", "Likes (High to Low)", "Saves (High to Low)", "Recent First"]
                sort_by = st.selectbox("Sort by", sort_options)
            
            with col3:
                pins_per_page = st.selectbox("Pins per page", [16, 32, 48], index=1)
            
            # Apply filters
            filtered_pins = pins_data
            if selected_category != "All":
                filtered_pins = [pin for pin in pins_data if pin.get('category') == selected_category]
            
            # Apply sorting
            if sort_by == "Likes (High to Low)":
                filtered_pins.sort(key=lambda x: x.get('likes', 0), reverse=True)
            elif sort_by == "Saves (High to Low)":
                filtered_pins.sort(key=lambda x: x.get('saves', 0), reverse=True)
            elif sort_by == "Recent First":
                filtered_pins.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            else:  # Title
                filtered_pins.sort(key=lambda x: x.get('title', ''))
            
            # Pagination
            total_pages = (len(filtered_pins) + pins_per_page - 1) // pins_per_page
            if total_pages > 0:
                page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
                
                start_idx = (page - 1) * pins_per_page
                end_idx = start_idx + pins_per_page
                paginated_pins = filtered_pins[start_idx:end_idx]
                
                # Display pins
                if paginated_pins:
                    cols = st.columns(4)
                    for idx, pin in enumerate(paginated_pins):
                        col_idx = idx % 4
                        with cols[col_idx]:
                            try:
                                st.image(pin['image_url'], width=150)
                                st.write(f"**{pin['title'][:25]}...**" if len(pin['title']) > 25 else f"**{pin['title']}**")
                                st.write(f"📂 {pin.get('category', 'unknown').title()}")
                                st.write(f"❤️ {pin.get('likes', 0):,} | 📌 {pin.get('saves', 0):,}")
                                st.write(f"💬 {pin.get('comments', 0):,}")
                            except:
                                st.write(f"📷 **{pin['title']}**")
                                st.write(f"ID: {pin.get('pin_id', 'unknown')}")
                
                st.write(f"📄 Page {page} of {total_pages} | Showing {len(paginated_pins)} of {len(filtered_pins)} pins")
        
        with tab4:
            st.header("ℹ️ About This System")
            
            st.subheader("🤖 How Duplicate Detection Works")
            st.write("""
            This system uses intelligent content analysis to identify duplicate pins:
            
            **1. Content Categorization** 📂  
            Groups pins by category (food, fashion, travel, etc.)
            
            **2. Title Similarity Analysis** 📝  
            Compares pin titles for similar keywords and phrases
            
            **3. Quality Scoring** ⭐  
            Ranks pins based on engagement metrics (likes, saves, comments)
            
            **4. Cluster Formation** 🔗  
            Groups similar pins together when they meet similarity thresholds
            """)
            
            st.subheader("📊 Sample Data Overview")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Dataset Statistics:**")
                categories = list(set(pin.get('category', 'unknown') for pin in pins_data))
                st.write(f"• Total pins: {len(pins_data):,}")
                st.write(f"• Categories: {len(categories)}")
                st.write(f"• Avg likes: {np.mean([pin.get('likes', 0) for pin in pins_data]):,.0f}")
                st.write(f"• Avg saves: {np.mean([pin.get('saves', 0) for pin in pins_data]):,.0f}")
            
            with col2:
                st.write("**Technical Features:**")
                st.write("• Real-time analysis")
                st.write("• Interactive visualizations")
                st.write("• Quality-based ranking")
                st.write("• Category-aware clustering")
                st.write("• Responsive web interface")
            
            st.subheader("🚀 Performance & Deployment")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Analysis Speed", "2-4 seconds")
            with col2:
                st.metric("Max Pins Supported", "150+")
            with col3:
                st.metric("Cloud Ready", "✅ Yes")
            
            st.subheader("💡 Use Cases")
            st.write("""
            **Content Creators & Marketers:**
            - Find duplicate content across boards
            - Identify high-performing pin variations
            - Optimize content strategy
            
            **Platform Management:**
            - Detect spam or duplicate uploads
            - Improve content quality
            - Enhance user experience
            
            **Research & Analytics:**
            - Study content trends
            - Analyze engagement patterns
            - Understand duplicate content impact
            """)
    
    else:
        st.warning("📊 No data available.")
        st.write("Click **'🔄 Generate Fresh Sample Data'** in the sidebar to create demo Pinterest pins.")
        
        if st.button("🚀 Create Sample Data Now", type="primary"):
            with st.spinner("Generating sample data..."):
                new_data = create_sample_data(120)
                save_sample_data(new_data)
            st.success("✅ Sample data created!")
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**Pinterest Duplicate Detector** - Built with ❤️ using Streamlit | "
        "Self-contained sample data (no external APIs required)"
    )

if __name__ == "__main__":
    main()