# 🚀 Deployment Guide - Pinterest Duplicate Detector

## ✅ **Current Status: RUNNING!**

Your Pinterest Duplicate Detector is now live at:
- **Local URL**: http://localhost:8501
- **Network URL**: http://0.0.0.0:8501

## 📱 **How to Use the App**

### **Step 1: Generate Sample Data**
1. Open the app in your browser
2. Click **"Generate Sample Data"** in the sidebar
3. Wait for 1,197 sample Pinterest pins to be created

### **Step 2: Run Duplicate Analysis**
1. Go to the **"Duplicate Analysis"** tab
2. Adjust settings in the sidebar:
   - **Number of pins**: 10-200 (start with 50 for quick testing)
   - **Similarity threshold**: 0.85 (recommended)
   - **Min cluster size**: 2
3. Click **"🚀 Start Analysis"**
4. Wait for AI processing (30s-2min depending on pin count)

### **Step 3: View Results**
- **Duplicate Clusters**: Visual grid of similar pins
- **Statistics**: Charts and metrics
- **Quality Scores**: AI-powered pin quality ranking

## 🌐 **Deployment Options**

### **Option 1: Local Development (Current)**
```bash
# Already running! Access at:
# http://localhost:8501
```

### **Option 2: Share on Local Network**
```bash
# Stop current app (Ctrl+C) then restart with:
python3 -m streamlit run streamlit_app_simple.py --server.port 8501 --server.address 0.0.0.0

# Access from any device on your network:
# http://YOUR_LOCAL_IP:8501
# Find your IP: ifconfig (Mac/Linux) or ipconfig (Windows)
```

### **Option 3: Deploy to Streamlit Cloud (Free)**

#### Quick Setup (5 minutes):
1. **Upload to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Pinterest Duplicate Detector"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/pinterest-duplicate-detector.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select your repository
   - Set main file: `streamlit_app_simple.py`
   - Click **"Deploy!"**

3. **Your app will be live at**: `https://YOUR_APP_NAME.streamlit.app`

### **Option 4: Deploy to Heroku**

```bash
# Create Procfile
echo "web: streamlit run streamlit_app_simple.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

# Deploy
heroku create your-app-name
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### **Option 5: Deploy to Railway**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

## 🔧 **API Backend (Optional)**

### **Run API Server**
```bash
# Terminal 1: API
python3 -m uvicorn app.api:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Streamlit (already running)
# Your app at http://localhost:8501
```

**API will be available at**: http://localhost:8000/docs

## 📊 **Model Comparison (Advanced)**

### **Run ML Model Comparison**
```bash
# Compare 5+ different AI models
python3 models/model_comparison.py

# This will:
# 1. Test CLIP, ViT, ResNet, EfficientNet models
# 2. Generate performance benchmarks
# 3. Create visualization charts
# 4. Save comparison report
```

### **Results You'll Get**:
- **Performance Metrics**: F1-score, Accuracy, Precision, Recall
- **Speed Benchmarks**: Inference time per image
- **Memory Usage**: Storage requirements
- **Visual Charts**: Automated comparison plots

## 🌟 **Production Deployment**

### **For Production Use**:

#### **1. Environment Setup**
```bash
# Create production requirements
pip freeze > requirements_prod.txt

# Set environment variables
export PINTEREST_ACCESS_TOKEN="your_token_here"
export MODEL_CACHE_DIR="/path/to/model/cache"
```

#### **2. Docker Deployment**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app_simple.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# Build and run
docker build -t pinterest-detector .
docker run -p 8501:8501 pinterest-detector
```

#### **3. Performance Optimization**
```python
# In production, add these optimizations:

# 1. Model caching
@st.cache_resource
def load_model():
    return EmbeddingExtractor()

# 2. Batch processing
@st.cache_data
def process_large_batch(image_urls):
    # Process in chunks
    return embeddings

# 3. Database integration
# Use PostgreSQL/MongoDB for pin storage

# 4. CDN for images
# Use AWS S3/CloudFront for image hosting
```

## 🚀 **Quick Start Commands**

### **Test Everything Locally**:
```bash
# 1. Install dependencies (already done)
pip install -r requirements.txt

# 2. Generate data (if not done)
python3 scripts/data_collection.py

# 3. Test models
python3 models/duplicate_detector.py

# 4. Run Streamlit (already running)
python3 -m streamlit run streamlit_app_simple.py

# 5. Access app
open http://localhost:8501
```

### **Deploy to Cloud (Streamlit Cloud)**:
```bash
# 1. Create GitHub repo
git init && git add . && git commit -m "Initial commit"

# 2. Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/pinterest-detector.git
git push -u origin main

# 3. Deploy on share.streamlit.io
# (Follow web interface)

# 4. Your app is live!
# https://your-app.streamlit.app
```

## 📱 **Mobile/Tablet Access**

The app is fully responsive and works on:
- ✅ **Desktop**: Full features
- ✅ **Tablet**: Optimized layout
- ✅ **Mobile**: Touch-friendly interface

## 🎯 **Demo Features Available**

### **1. Duplicate Detection**
- Upload or generate Pinterest-style pins
- AI-powered visual similarity detection
- Cluster similar images automatically
- Quality ranking for each pin

### **2. Quality Analysis**
- **Resolution Score**: Image size/quality assessment
- **Clarity Score**: Aspect ratio optimization
- **Engagement Score**: Likes, saves, comments analysis
- **Credibility Score**: Source and user reputation

### **3. Statistics Dashboard**
- Cluster size distribution
- Quality score histograms
- Performance metrics
- Interactive charts

### **4. Model Information**
- CLIP embedding details
- FAISS similarity search info
- Performance benchmarks
- Technical specifications

## 🔧 **Troubleshooting**

### **Common Issues**:

#### **App won't start**:
```bash
# Check dependencies
pip install -r requirements.txt

# Check Python version
python3 --version  # Should be 3.8+

# Try alternative port
streamlit run streamlit_app_simple.py --server.port 8502
```

#### **Model loading errors**:
```bash
# Clear model cache
rm -rf ~/.cache/huggingface/transformers/

# Reinstall PyTorch
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

#### **Memory issues**:
```bash
# Reduce batch size in analysis
# Set num_pins to 20-50 instead of 100+

# Close other applications
# Free up RAM before running analysis
```

## 📈 **Next Steps**

### **For Learning**:
1. **Explore the code**: Check `models/` directory
2. **Try different models**: Run `models/model_comparison.py`
3. **Modify parameters**: Adjust similarity thresholds
4. **Add features**: Extend the quality ranking system

### **For Production**:
1. **Get Pinterest API access**: Real data integration
2. **Scale infrastructure**: Database, caching, CDN
3. **Add authentication**: User accounts, permissions
4. **Monitor performance**: Logging, analytics, alerts

## 🎉 **Success!**

Your Pinterest Duplicate Detector is now running and ready to use!

**Access your app**: http://localhost:8501

Try generating sample data and running your first duplicate analysis! 🚀