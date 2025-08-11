# 🧪 Testing Guide for Yinizai ML Service

## 📋 **How It Works - Step by Step**

### **1. Data Flow**

```
1. Student submits answer → Node.js receives it
2. Node.js sends question + answer → ML Service API
3. ML Service extracts 40+ features from text
4. Features fed into trained ML models
5. Models return predictions (difficulty, score, comprehension)
6. Results sent back to Node.js → stored in database → shown to user
```

### **2. ML Models Process**

```
Input Text → Feature Engineering → Model Prediction → Insights
    ↓              ↓                    ↓              ↓
"What is        40+ features      Easy/Medium/Hard   Recommendations
the capital     (readability,     + confidence       for teachers
of France?"     complexity,       scores             and students
                grammar, etc.)
```

## 🚀 **Testing the System**

### **Phase 1: Basic Setup Test**

#### **Step 1: Start the Service**

```bash
cd /Users/mac/Documents/My\ Projects/yinizai/ml_service
./start.sh
```

#### **Step 2: Check if Service is Running**

Open your browser and go to: `http://localhost:8000`
You should see:

```json
{
  "service": "Yinizai ML Analysis Service",
  "status": "running",
  "version": "1.0.0",
  "timestamp": "2025-08-10T..."
}
```

#### **Step 3: Check API Documentation**

Visit: `http://localhost:8000/docs`
This shows interactive API documentation where you can test all endpoints.

### **Phase 2: Database Setup Test**

#### **Step 1: Configure Database**

```bash
# Copy environment template
cp .env.example .env

# Edit with your database details
nano .env
```

#### **Step 2: Create Sample Data**

```bash
python setup_database.py
```

#### **Step 3: Verify Database Connection**

```bash
curl http://localhost:8000/status
```

Expected response:

```json
{
  "service_status": "running",
  "database_connected": true,
  "total_questions_analyzed": 10,
  "total_answers_processed": 87
}
```

### **Phase 3: API Testing**

#### **Test 1: Analyze Question Difficulty**

```bash
curl -X POST "http://localhost:8000/analyze/question" \
     -H "Content-Type: application/json" \
     -d '{
       "question_text": "Explain the process of photosynthesis in detail",
       "question_type": "essay",
       "subject": "Biology"
     }'
```

Expected response:

```json
{
  "difficulty_prediction": {
    "predicted_difficulty": "medium",
    "confidence": 0.85,
    "probabilities": {
      "easy": 0.15,
      "medium": 0.7,
      "hard": 0.15
    }
  },
  "features_extracted": {
    "word_count": 8,
    "flesch_reading_ease": 45.2,
    "sentence_count": 1
    // ... 37+ more features
  }
}
```

#### **Test 2: Analyze Student Answer**

```bash
curl -X POST "http://localhost:8000/analyze/answer" \
     -H "Content-Type: application/json" \
     -d '{
       "question_text": "What is the capital of France?",
       "answer_text": "Paris is the capital city of France and it is located in the north-central part of the country.",
       "question_type": "short_answer",
       "correct_answer": "Paris"
     }'
```

Expected response:

```json
{
  "score_prediction": {
    "predicted_score": 0.95
  },
  "comprehension_analysis": {
    "comprehension_cluster": 2,
    "cluster_confidence": 0.88,
    "issues_identified": [],
    "recommendations": ["Student shows good understanding"]
  },
  "features_extracted": {
    "correct_answer_similarity": 0.75,
    "sentiment_positive": 0.1
    // ... more features
  }
}
```

#### **Test 3: Get Question Performance**

```bash
# First, get a question ID from the database
curl http://localhost:8000/status

# Then analyze performance (replace 1 with actual question ID)
curl "http://localhost:8000/analyze/question/1/performance"
```

### **Phase 4: Node.js Integration Test**

#### **Test 1: Install Node.js Dependencies**

```bash
cd /Users/mac/Documents/My\ Projects/yinizai
npm install axios  # If not already installed
```

#### **Test 2: Create Test Script**

Create `test-ml-integration.js`:

```javascript
const YinizaiMLClient = require("./nodejs-integration-example");

async function testMLService() {
  const mlClient = new YinizaiMLClient("http://localhost:8000");

  console.log("🧪 Testing ML Service Integration...\n");

  try {
    // Test 1: Health Check
    console.log("1. Checking service health...");
    const isHealthy = await mlClient.checkHealth();
    console.log(
      `   Health Status: ${isHealthy ? "✅ Healthy" : "❌ Unhealthy"}\n`
    );

    // Test 2: System Status
    console.log("2. Getting system status...");
    const status = await mlClient.getSystemStatus();
    console.log(`   Service Status: ${status.service_status}`);
    console.log(`   Database Connected: ${status.database_connected}`);
    console.log(`   Questions in DB: ${status.total_questions_analyzed}\n`);

    // Test 3: Question Analysis
    console.log("3. Testing question analysis...");
    const questionResult = await mlClient.analyzeQuestion({
      question_text: "What are the main causes of climate change?",
      question_type: "essay",
      subject: "Environmental Science",
    });
    console.log(
      `   Predicted Difficulty: ${questionResult.difficulty_prediction.predicted_difficulty}`
    );
    console.log(
      `   Confidence: ${questionResult.difficulty_prediction.confidence.toFixed(
        2
      )}\n`
    );

    // Test 4: Answer Analysis
    console.log("4. Testing answer analysis...");
    const answerResult = await mlClient.analyzeAnswer({
      question_text: "What is the capital of France?",
      answer_text: "Paris is the beautiful capital city of France",
      question_type: "short_answer",
      correct_answer: "Paris",
    });
    console.log(
      `   Predicted Score: ${answerResult.score_prediction.predicted_score.toFixed(
        2
      )}`
    );
    console.log(
      `   Comprehension Cluster: ${answerResult.comprehension_analysis.comprehension_cluster}\n`
    );

    // Test 5: Batch Processing
    console.log("5. Testing batch question analysis...");
    const batchResult = await mlClient.batchAnalyzeQuestions([
      {
        question_text: "What is 2 + 2?",
        question_type: "short_answer",
        subject: "Mathematics",
      },
      {
        question_text: "Explain the theory of relativity",
        question_type: "essay",
        subject: "Physics",
      },
    ]);
    console.log(
      `   Processed: ${batchResult.processed_questions}/${batchResult.total_questions} questions`
    );
    console.log(
      `   Processing Time: ${batchResult.processing_time.toFixed(2)}s\n`
    );

    console.log("🎉 All tests completed successfully!");
  } catch (error) {
    console.error("❌ Test failed:", error.message);
  }
}

testMLService();
```

#### **Test 3: Run Integration Test**

```bash
node test-ml-integration.js
```

### **Phase 5: Model Training Test**

#### **Test 1: Train Difficulty Prediction Model**

```bash
curl -X POST "http://localhost:8000/train/difficulty" \
     -H "Content-Type: application/json" \
     -d '{
       "model_type": "difficulty",
       "min_samples": 10
     }'
```

#### **Test 2: Train Score Prediction Model**

```bash
curl -X POST "http://localhost:8000/train/score" \
     -H "Content-Type: application/json" \
     -d '{
       "model_type": "score",
       "min_samples": 20
     }'
```

#### **Test 3: Check Model Files**

```bash
ls -la trained_models/
```

You should see `.joblib` files for each trained model.

## 🔍 **Expected Results & Troubleshooting**

### **✅ Success Indicators**

- Service starts on `http://localhost:8000`
- API documentation loads at `/docs`
- Database connection successful
- Models return predictions within 1-2 seconds
- Confidence scores between 0.0-1.0
- Feature extraction returns 40+ features

### **❌ Common Issues & Solutions**

#### **Issue 1: Service Won't Start**

```bash
# Check Python version (needs 3.8+)
python --version

# Check if port 8000 is available
lsof -i :8000

# Check dependencies
pip install -r requirements.txt
```

#### **Issue 2: Database Connection Failed**

```bash
# Verify MySQL is running
brew services start mysql

# Test connection manually
mysql -u your_username -p your_database

# Check .env file configuration
cat .env
```

#### **Issue 3: Models Not Trained**

```bash
# Check if enough sample data exists
curl http://localhost:8000/status

# Manually trigger training
curl -X POST http://localhost:8000/train/difficulty
```

#### **Issue 4: Slow Predictions**

- First prediction is slower (model loading)
- Subsequent predictions should be <500ms
- Check server resources (RAM, CPU)

## 📊 **Performance Benchmarks**

### **Expected Response Times**

- Health check: <50ms
- Question analysis: <200ms
- Answer analysis: <500ms
- Batch processing (10 items): <3s
- Model training: 1-10 minutes

### **Expected Accuracy**

- Difficulty prediction: 75-85%
- Score prediction: R² > 0.7
- Response time consistency: 95%

## 🎯 **Integration with Your Node.js App**

### **Example Route Integration**

```javascript
// In your existing Node.js routes
app.post("/api/submit-answer", async (req, res) => {
  const { questionId, studentId, answerText } = req.body;

  // Get question details
  const question = await Question.findById(questionId);

  // Analyze with ML service
  const mlClient = new YinizaiMLClient();
  const analysis = await mlClient.analyzeAnswer({
    question_text: question.text,
    answer_text: answerText,
    question_type: question.type,
    correct_answer: question.correctAnswer,
  });

  // Save answer with ML insights
  const answer = await Answer.create({
    questionId,
    studentId,
    text: answerText,
    predictedScore: analysis.score_prediction.predicted_score,
    comprehensionCluster: analysis.comprehension_analysis.comprehension_cluster,
    mlAnalysis: analysis,
  });

  // Return results with insights
  res.json({
    answer,
    insights: {
      predictedScore: analysis.score_prediction.predicted_score,
      recommendations: analysis.comprehension_analysis.recommendations,
    },
  });
});
```

Ready to test? Start with Phase 1 and let me know what results you get! 🚀
