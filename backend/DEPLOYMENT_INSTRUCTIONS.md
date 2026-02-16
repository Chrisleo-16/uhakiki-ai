# 🚀 UHAKIKIAI BACKEND DEPLOYMENT INSTRUCTIONS

## **⚠️ CURRENT ISSUE**
The Docker build is failing due to dependency conflicts between `crewai==1.9.3` and `tokenizers>=0.20.3,<0.21.dev0`. The Docker cache is retaining the old version.

## **🔧 SOLUTION 1: MANUAL DEPLOYMENT**

### **Step 1: Clean Environment**
```bash
# Navigate to backend
cd /home/cb-fx/uhakiki-ai/backend

# Clean Docker cache completely
docker system prune -a -f
docker builder prune -a -f
```

### **Step 2: Direct Backend Deployment**
```bash
# Activate virtual environment
source ../.venv/bin/activate

# Install dependencies manually
pip install -r requirements.txt

# Start the server directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### **Step 3: Test Deployment**
```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Expected response:
{
  "status": "ONLINE",
  "phase": "Phase-2.0",
  "timestamp": "2026-02-15T..."
}
```

## **🔧 SOLUTION 2: DOCKER DEPLOYMENT (FIXED)**

### **Step 1: Update Dockerfile**
```dockerfile
# Add this line before COPY requirements.txt:
RUN pip install "crewai>=0.83.0" "tokenizers>=0.20.3,<0.21.dev0" --no-deps
```

### **Step 2: Build and Deploy**
```bash
# Navigate to deployment directory
cd /home/cb-fx/uhakiki-ai/backend/deploy/konza

# Build with no cache
docker-compose -f docker-compose.prod.yml build --no-cache

# Deploy services
docker-compose -f docker-compose.prod.yml up -d
```

## **🔧 SOLUTION 3: SIMPLIFIED REQUIREMENTS**

### **Create minimal requirements file**
```txt
# requirements-minimal.txt
fastapi>=0.110.0
uvicorn>=0.30.0
pydantic>=2.7.0
httpx>=0.27.0
python-multipart>=0.0.9
numpy>=1.26.4
torch==2.2.1
torchvision==0.17.1
```

### **Deploy with minimal requirements**
```bash
# Use minimal requirements for testing
docker run -p 8000:8000 \
  -e PYTHONPATH=/app \
  -v $(pwd):/app \
  python:3.10-slim \
  bash -c "pip install -r requirements-minimal.txt && uvicorn app.main:app --host 0.0.0.0"
```

## **✅ VERIFICATION CHECKLIST**

### **After Deployment**
- [ ] Backend starts without errors
- [ ] Health endpoint returns 200
- [ ] API documentation accessible at `/docs`
- [ ] All routes functional
- [ ] Logs show no critical errors

### **Test Commands**
```bash
# Health check
curl -f http://localhost:8000/api/v1/health || echo "❌ Health check failed"

# API documentation
curl -f http://localhost:8000/docs || echo "❌ Docs not accessible"

# Service status
docker-compose -f docker-compose.prod.yml ps
```

## **🎯 RECOMMENDED APPROACH**

**Use Solution 1 (Manual Deployment) for immediate testing:**
1. Clean environment
2. Install dependencies manually  
3. Start server directly
4. Verify functionality

**Use Solution 2 (Docker Deployment) for production:**
1. Update Dockerfile with pinned versions
2. Build with --no-cache
3. Deploy full stack

## **📞 TROUBLESHOOTING**

### **Common Issues**
1. **Port already in use**: `sudo lsof -i :8000`
2. **Permission denied**: `sudo chmod +x scripts`
3. **Module not found**: Check PYTHONPATH
4. **Docker build fails**: Clear cache with `docker system prune -a`

### **Get Help**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend-01

# Enter container for debugging
docker exec -it konza-backend-01 bash

# Check Python environment
docker exec konza-backend-01 python -c "import sys; print(sys.path)"
```

---

## **🎉 NEXT STEPS**

Once deployment is successful:
1. **Configure monitoring** - Set up Prometheus/Grafana
2. **Test API endpoints** - Verify all functionality
3. **Load test data** - Test with sample documents
4. **Configure SSL** - Set up HTTPS for production
5. **Scale horizontally** - Add more backend nodes

**Your UhakikiAI backend is ready to transform Kenyan education!** 🇰🇪
