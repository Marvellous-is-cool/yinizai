# 🚀 Production Deployment Guide

Complete guide to deploy your ML service to production using Render + Aiven MySQL

## 📋 Prerequisites

- ✅ GitHub repository with your code
- ✅ Aiven account (free tier available)
- ✅ Render account (free tier available)

## 🗄️ Step 1: Set Up Aiven MySQL Database

### 1.1 Create MySQL Service

1. Go to [Aiven Console](https://console.aiven.io)
2. Click "Create Service"
3. Choose **MySQL**
4. Select region closest to your users
5. Choose plan (free tier: "Startup-1")
6. Name your service: `yinizai-mysql-prod`
7. Click "Create Service"

### 1.2 Configure Database Access

1. Wait for service to start (2-3 minutes)
2. Go to "Overview" tab
3. Copy connection details:
   - **Host**: `yinizai-mysql-prod-xxx.aivencloud.com`
   - **Port**: `12345`
   - **User**: `avnadmin`
   - **Password**: `generated_password`
   - **Database**: `defaultdb`

### 1.3 Allow External Access

1. Go to "Access Control" tab
2. Add IP range: `0.0.0.0/0` (for Render access)
3. Save configuration

## 🚢 Step 2: Deploy to Render

### 2.1 Create Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure service:
   - **Name**: `yinizai-ml-service`
   - **Environment**: Python
   - **Build Command**: `./build.sh`
   - **Start Command**: `./start_production.sh`
   - **Instance Type**: Free (or Starter for better performance)

### 2.2 Set Environment Variables

Add these in Render Dashboard → Environment:

```bash
# Database Configuration (from Aiven)
DB_HOST=yinizai-mysql-prod-xxx.aivencloud.com
DB_PORT=12345
DB_USER=avnadmin
DB_PASSWORD=your_aiven_password
DB_NAME=defaultdb

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=another-secret-key-for-jwt-tokens

# ML Configuration
MODEL_PATH=/opt/render/project/src/models
ENABLE_CORS=true
LOG_LEVEL=INFO
MAX_WORKERS=2

# Production Settings
ENVIRONMENT=production
DEBUG=false
```

### 2.3 Deploy Service

1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes)
3. Monitor logs for any errors

## 🔧 Step 3: Initialize Database

### 3.1 Run Database Setup

Once your service is deployed:

```bash
# Option 1: Via deployed service API
curl -X POST https://your-service.onrender.com/setup/initialize

# Option 2: Manual setup (if needed)
python setup_production_db.py
```

### 3.2 Verify Database

Check that tables were created:

```bash
curl https://your-service.onrender.com/health/database
```

## ✅ Step 4: Test Your Service

### 4.1 Health Checks

```bash
# Basic health
curl https://your-service.onrender.com/health

# Database health
curl https://your-service.onrender.com/health/database

# Service info
curl https://your-service.onrender.com/
```

### 4.2 Test ML Endpoints

```bash
# Analyze question difficulty
curl -X POST https://your-service.onrender.com/analyze/question \
  -H "Content-Type: application/json" \
  -d '{"question_text": "What is the capital of France?"}'

# Score student answer
curl -X POST https://your-service.onrender.com/analyze/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "What is the capital of France?",
    "student_answer": "Paris",
    "correct_answer": "Paris"
  }'
```

## 🔐 Step 5: Security Configuration

### 5.1 Update CORS Settings

In your main app, ensure CORS is configured for your frontend domain:

```python
# In main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Update this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5.2 SSL Certificate

Render automatically provides SSL certificates for all services.
Your service will be available at: `https://your-service.onrender.com`

## 🔗 Step 6: Connect from Node.js App

Update your Node.js application to use the production ML service:

```javascript
// config/production.js
module.exports = {
  mlService: {
    baseUrl: "https://your-service.onrender.com",
    timeout: 30000,
    retries: 3,
  },
};

// services/mlService.js
const ML_SERVICE_URL =
  process.env.ML_SERVICE_URL || "https://your-service.onrender.com";

async function analyzeQuestion(questionText) {
  const response = await fetch(`${ML_SERVICE_URL}/analyze/question`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question_text: questionText }),
  });
  return response.json();
}
```

## 📊 Step 7: Monitoring & Maintenance

### 7.1 Monitor Service Health

- Render provides built-in monitoring
- Check logs in Render Dashboard
- Set up alerts for service downtime

### 7.2 Database Monitoring

- Monitor Aiven MySQL metrics
- Set up alerts for high CPU/memory usage
- Monitor disk space usage

### 7.3 Performance Optimization

- Monitor API response times
- Scale up Render instance if needed
- Optimize database queries
- Add Redis caching if needed

## 🚨 Troubleshooting

### Common Issues

**1. Database Connection Errors**

```bash
# Check environment variables
curl https://your-service.onrender.com/health/database

# Solutions:
- Verify Aiven service is running
- Check environment variables in Render
- Ensure IP whitelist includes 0.0.0.0/0
```

**2. Service Won't Start**

```bash
# Check logs in Render Dashboard

# Common fixes:
- Ensure build.sh is executable
- Check Python requirements
- Verify start_production.sh script
```

**3. Slow Performance**

```bash
# Solutions:
- Upgrade Render instance type
- Optimize database queries
- Add caching layer
- Use connection pooling
```

## 💰 Cost Estimation

### Free Tier (Development)

- **Render**: Free (sleeps after 15min inactivity)
- **Aiven MySQL**: $0/month (1 month free trial)
- **Total**: $0/month

### Production Tier

- **Render Starter**: $7/month
- **Aiven MySQL Startup-1**: $19/month
- **Total**: $26/month

## 🔄 Continuous Deployment

Set up automatic deployments:

1. Connect GitHub repository to Render
2. Enable auto-deploy on push to `main` branch
3. Use GitHub Actions for testing before deployment

## 📞 Support

If you encounter issues:

1. Check Render logs for service errors
2. Check Aiven metrics for database issues
3. Review API documentation for correct usage
4. Test endpoints individually to isolate problems

---

🎉 **Your ML service is now production-ready!**

The service will automatically:

- Scale based on demand
- Restart if it crashes
- Provide SSL certificates
- Monitor health and performance

```
ml_service/
├── app/
│   ├── main.py
│   ├── models/
│   └── services/
├── requirements.txt
├── build.sh               # ← Build script
├── start_production.sh    # ← Start script
├── .env.production        # ← Environment template
└── Dockerfile (optional)
```

### **2.2 Create Render Service**

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Configure service:

   ```
   Name: yinizai-ml-service
   Runtime: Python 3
   Build Command: bash build.sh
   Start Command: bash start_production.sh
   ```

### **2.3 Environment Variables**

Add these to Render Environment Variables section:

```bash
# Database (from Aiven)
DB_HOST=your-aiven-host.aivencloud.com
DB_PORT=12345
DB_USER=avnadmin
DB_PASSWORD=your-aiven-password
DB_NAME=yinizai_ml

# Service Config
ENVIRONMENT=production
PORT=10000

# CORS (add your Node.js domain)
ALLOWED_ORIGINS=https://your-nodejs-app.onrender.com,https://yourdomain.com

# ML Settings
MIN_TRAINING_SAMPLES=10
LOG_LEVEL=info
```

## 🔗 Step 3: Connect Your Node.js App

### **3.1 Update Node.js Environment**

Add to your Node.js app environment variables:

```bash
ML_SERVICE_URL=https://yinizai-ml-service.onrender.com
```

### **3.2 Update Node.js Code**

```javascript
// config/ml-service.js
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || "http://localhost:8000";

export const mlService = {
  async analyzeQuestion(questionData) {
    try {
      const response = await fetch(`${ML_SERVICE_URL}/analyze/question`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(questionData),
      });

      if (!response.ok) {
        throw new Error(`ML Service error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("ML Service unavailable:", error);
      // Return fallback response
      return {
        difficulty_prediction: {
          predicted_difficulty: "medium",
          confidence: 0.5,
        },
        fallback: true,
      };
    }
  },
};
```

## 📊 Step 4: Initialize Database with Sample Data

### **4.1 Run Database Setup**

After deployment, trigger initial data setup:

```bash
# Option 1: Via API call to your deployed service
curl -X POST https://yinizai-ml-service.onrender.com/setup/initialize

# Option 2: Run script manually via Render shell
python generate_sample_data.py
```

### **4.2 Train Initial Models**

```bash
# Train all models
curl -X POST https://yinizai-ml-service.onrender.com/train/difficulty -H "Content-Type: application/json" -d '{"model_type":"difficulty","min_samples":10}'

curl -X POST https://yinizai-ml-service.onrender.com/train/score -H "Content-Type: application/json" -d '{"model_type":"score","min_samples":10}'

curl -X POST https://yinizai-ml-service.onrender.com/train/comprehension -H "Content-Type: application/json" -d '{"model_type":"comprehension","min_samples":10}'
```

## 🔧 Step 5: Production Configuration

### **5.1 Health Monitoring**

Render automatically monitors your service health via:

- `GET /health` endpoint
- Process monitoring
- Automatic restarts

### **5.2 Scaling Configuration**

```yaml
# render.yaml (optional - for advanced config)
services:
  - type: web
    name: yinizai-ml-service
    env: python
    buildCommand: bash build.sh
    startCommand: bash start_production.sh
    plan: starter # Free tier
    numInstances: 1
    healthCheckPath: /health
    envVars:
      - key: ENVIRONMENT
        value: production
```

### **5.3 Logging Setup**

Monitor logs via Render dashboard or configure external logging:

```python
# In main.py - already configured
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🎯 Step 6: Testing Your Deployment

### **6.1 Health Check**

```bash
curl https://yinizai-ml-service.onrender.com/health
# Should return: {"status":"healthy","timestamp":"..."}
```

### **6.2 API Test**

```bash
curl -X POST https://yinizai-ml-service.onrender.com/analyze/question \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "What is the capital of France?",
    "subject": "Geography"
  }'
```

### **6.3 Node.js Integration Test**

```javascript
// Test from your Node.js app
const testML = async () => {
  const result = await mlService.analyzeQuestion({
    question_text: "Test question",
    subject: "Test",
  });
  console.log("ML Service response:", result);
};
```

## 💰 Cost Breakdown

### **Free Tier Usage:**

- **Render Web Service**: Free (750 hours/month)
- **Aiven MySQL**: Free (1 month, then ~$10/month for hobby)
- **Total**: Free to start, ~$10/month for database

### **Scaling Options:**

- **Render Starter**: $7/month (more resources)
- **Aiven Business**: $40/month (production MySQL)
- **Render Pro**: $25/month (auto-scaling, custom domains)

## 🚨 Troubleshooting

### **Common Issues:**

**1. Build Fails**

```bash
# Check build.sh permissions
chmod +x build.sh start_production.sh
```

**2. Database Connection Error**

```bash
# Verify environment variables
echo $DB_HOST $DB_PORT $DB_USER
```

**3. spaCy Model Download Fails**

```bash
# Add to build.sh
python -m spacy download en_core_web_sm --user
```

**4. CORS Issues**

```python
# Update ALLOWED_ORIGINS in environment variables
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

**5. Memory Issues**

```python
# Reduce model complexity in production
# Use smaller spaCy model: en_core_web_sm instead of en_core_web_lg
```

## 📈 Monitoring & Maintenance

### **Performance Monitoring:**

1. **Render Dashboard**: CPU, memory, response times
2. **Aiven Console**: Database performance, storage usage
3. **Custom Metrics**: Add to your ML endpoints

### **Maintenance Tasks:**

```python
# Weekly model retraining (add to cron or scheduled job)
POST /train/difficulty {"retrain": true}

# Monthly analytics cleanup
DELETE FROM ml_training_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH)
```

## ✅ Production Checklist

- [ ] Database schema deployed to Aiven
- [ ] Environment variables configured in Render
- [ ] CORS origins set to your Node.js domain
- [ ] SSL certificates configured
- [ ] Health checks passing
- [ ] Sample data loaded and models trained
- [ ] Node.js app successfully calling ML service
- [ ] Error handling and fallbacks implemented
- [ ] Monitoring and logging configured

## 🎉 You're Live!

Your ML service is now running on:

- **API**: `https://your-service-name.onrender.com`
- **Docs**: `https://your-service-name.onrender.com/docs`
- **Health**: `https://your-service-name.onrender.com/health`

Your Node.js app can now make ML predictions in real-time! 🚀
