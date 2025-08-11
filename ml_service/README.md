# Yinizai ML Analysis Service

A comprehensive machine learning service for analyzing student answers and predicting question difficulty in educational systems.

## Features

- **Question Difficulty Prediction**: Automatically predict question difficulty levels based on text features
- **Answer Score Prediction**: Predict student scores based on answer content and question characteristics
- **Comprehension Analysis**: Identify comprehension patterns and cluster students based on performance
- **Performance Analytics**: Detailed performance metrics and insights for questions and subjects
- **Common Mistake Detection**: Identify and analyze common mistakes across student answers
- **Real-time API**: RESTful API endpoints for integration with Node.js applications

## Architecture

```
ml_service/
├── app/
│   ├── models/          # Database and API models
│   ├── services/        # Core ML and data processing services
│   ├── utils/          # Utility functions and helpers
│   └── main.py         # FastAPI application
├── data/               # Data storage and samples
├── trained_models/     # Saved ML models
└── requirements.txt    # Python dependencies
```

## Setup and Installation

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:

```
DB_HOST=your_mysql_host
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database_name
```

### 4. Database Setup

Ensure your MySQL database has the following tables (auto-created on startup):

- `questions`: Store question data
- `student_answers`: Store student response data
- `question_analytics`: Store ML analysis results

### 5. Run the Service

```bash
# Development mode
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Core Analysis Endpoints

- `POST /analyze/question` - Analyze question difficulty
- `POST /analyze/answer` - Analyze student answer
- `GET /analyze/question/{question_id}/performance` - Get question performance metrics

### Training Endpoints

- `POST /train/difficulty` - Train difficulty prediction model
- `POST /train/score` - Train score prediction model
- `POST /train/comprehension` - Train comprehension analysis model

### Analytics Endpoints

- `GET /analytics/subject/{subject}` - Get subject performance analytics
- `POST /batch/analyze/questions` - Batch question analysis

### System Endpoints

- `GET /` - Service information
- `GET /health` - Health check
- `GET /status` - System status and model information

## Usage Examples

### Analyze a Question

```python
import requests

question_data = {
    "question_text": "What is the capital of France?",
    "question_type": "short_answer",
    "subject": "geography"
}

response = requests.post("http://localhost:8000/analyze/question", json=question_data)
result = response.json()

print(f"Predicted difficulty: {result['difficulty_prediction']['predicted_difficulty']}")
print(f"Confidence: {result['difficulty_prediction']['confidence']:.2f}")
```

### Analyze a Student Answer

```python
answer_data = {
    "question_text": "What is the capital of France?",
    "answer_text": "Paris is the capital of France",
    "question_type": "short_answer",
    "correct_answer": "Paris"
}

response = requests.post("http://localhost:8000/analyze/answer", json=answer_data)
result = response.json()

print(f"Predicted score: {result['score_prediction']['predicted_score']:.2f}")
print(f"Comprehension cluster: {result['comprehension_analysis']['comprehension_cluster']}")
```

### Train Models

```python
# Train difficulty prediction model
train_request = {
    "model_type": "difficulty",
    "min_samples": 50
}

response = requests.post("http://localhost:8000/train/difficulty", json=train_request)
print(response.json()["message"])
```

## Integration with Node.js

### Example Node.js Integration

```javascript
const axios = require("axios");

const ML_SERVICE_URL = "http://localhost:8000";

class MLService {
  async analyzeQuestion(questionData) {
    try {
      const response = await axios.post(
        `${ML_SERVICE_URL}/analyze/question`,
        questionData
      );
      return response.data;
    } catch (error) {
      console.error(
        "Error analyzing question:",
        error.response?.data || error.message
      );
      throw error;
    }
  }

  async analyzeAnswer(answerData) {
    try {
      const response = await axios.post(
        `${ML_SERVICE_URL}/analyze/answer`,
        answerData
      );
      return response.data;
    } catch (error) {
      console.error(
        "Error analyzing answer:",
        error.response?.data || error.message
      );
      throw error;
    }
  }

  async getQuestionPerformance(questionId) {
    try {
      const response = await axios.get(
        `${ML_SERVICE_URL}/analyze/question/${questionId}/performance`
      );
      return response.data;
    } catch (error) {
      console.error(
        "Error getting question performance:",
        error.response?.data || error.message
      );
      throw error;
    }
  }
}

module.exports = MLService;
```

## Model Training

The service includes three main ML models:

### 1. Difficulty Prediction Model

- **Algorithm**: Random Forest Classifier
- **Features**: Text complexity, readability scores, linguistic features
- **Output**: Difficulty level (easy, medium, hard) with confidence scores

### 2. Score Prediction Model

- **Algorithm**: Random Forest Regressor
- **Features**: Answer quality, similarity to correct answer, text features
- **Output**: Predicted score (0-1 scale)

### 3. Comprehension Analysis Model

- **Algorithm**: K-Means Clustering
- **Features**: Performance patterns, answer characteristics
- **Output**: Comprehension cluster and confidence

## Features Extracted

The service extracts 40+ features from questions and answers:

### Text Features

- Character, word, sentence counts
- Average word/sentence length
- Readability scores (Flesch-Kincaid, Gunning Fog, etc.)
- Vocabulary diversity
- Punctuation patterns

### Linguistic Features

- Part-of-speech counts
- Named entity counts
- Sentiment scores
- Question word detection

### Performance Features

- Score statistics
- Completion time patterns
- Attempt patterns
- Pass rates

## Monitoring and Maintenance

### Model Performance Monitoring

- Track prediction accuracy over time
- Monitor feature drift
- Evaluate model performance on new data

### Data Quality

- Validate input data format
- Handle missing values
- Detect and handle outliers

### System Monitoring

- API response times
- Model loading status
- Database connectivity
- Error rates and logging

## Deployment

### Docker Deployment (Recommended)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

- Use environment variables for configuration
- Set up proper logging and monitoring
- Configure CORS properly for your domain
- Use SSL/TLS in production
- Set up database connection pooling
- Implement rate limiting
- Regular model retraining schedules

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details
