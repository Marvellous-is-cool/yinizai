# Question Difficulty Analysis API

This API provides ML-powered analysis of question difficulty based on student performance data.

## Endpoints

### 1. Comprehensive Question Difficulty Analysis

**POST** `/analytics/questions/difficulty`

Analyzes all questions to determine difficulty based on student performance using multiple ML factors.

#### Request Body:
```json
{
  "subject_filter": "Mathematics",          // Optional: filter by subject
  "min_attempts": 5,                       // Optional: minimum student attempts (default: 5)
  "include_recent_only": false,            // Optional: only recent data (default: false)
  "days_back": 30                          // Optional: days to look back if recent only (default: 30)
}
```

#### Response:
```json
{
  "total_questions_analyzed": 25,
  "analysis_summary": {
    "easy": 8,
    "medium": 12,
    "hard": 5
  },
  "questions": [
    {
      "question_id": 1,
      "question_text": "What is 2 + 2?",
      "subject": "Mathematics",
      "calculated_difficulty": "easy",
      "difficulty_score": 0.15,
      "confidence": 0.92,
      "performance_metrics": {
        "avg_score": 0.89,
        "pass_rate": 0.89,
        "score_std": 0.12,
        "avg_time_minutes": 2.5,
        "completion_efficiency": 0.85,
        "struggle_rate": 0.05,
        "consistency": 0.88
      },
      "student_statistics": {
        "total_attempts": 20,
        "unique_students": 18,
        "high_performers": 17,
        "struggling_students": 1
      },
      "recommendations": [
        "Consider increasing question complexity",
        "Add follow-up challenging questions"
      ]
    }
  ],
  "overall_insights": [
    "Good balance of moderate difficulty questions",
    "Mathematics appears to be a challenging subject area"
  ],
  "analysis_timestamp": "2025-08-15T10:30:00Z"
}
```

### 2. Quick Difficulty Summary

**GET** `/analytics/questions/difficulty/summary?subject=Mathematics&min_attempts=3`

Provides a quick overview of question difficulty by subject.

#### Query Parameters:
- `subject` (optional): Filter by specific subject
- `min_attempts` (optional): Minimum attempts required (default: 3)

#### Response:
```json
{
  "summary": {
    "Mathematics": {
      "total_questions": 15,
      "estimated_difficulty": "medium",
      "avg_performance": 0.65
    },
    "Science": {
      "total_questions": 10,
      "estimated_difficulty": "hard",
      "avg_performance": 0.45
    }
  },
  "total_subjects": 2,
  "analysis_note": "Quick summary based on average student performance",
  "for_detailed_analysis": "Use POST /analytics/questions/difficulty"
}
```

## How the ML Analysis Works

### Difficulty Calculation Factors:

1. **Average Performance (40% weight)**
   - 80%+ success rate → Easy
   - 60-80% success rate → Medium-Easy  
   - 40-60% success rate → Medium-Hard
   - <40% success rate → Hard

2. **Consistency (20% weight)**
   - High score variance suggests confusing/ambiguous questions
   - Increases difficulty rating

3. **Struggle Rate (20% weight)**
   - Percentage of students scoring below 50%
   - Higher struggle rate increases difficulty

4. **Time Factor (20% weight)**
   - Questions taking >5 minutes suggest complexity
   - Increases difficulty rating

### Difficulty Categories:

- **Easy** (0.0-0.3): High success rate, consistent performance
- **Medium** (0.3-0.7): Moderate challenge, good learning opportunity  
- **Hard** (0.7-1.0): Low success rate, may need curriculum review

### Recommendations:

The system provides actionable insights:
- **Hard questions**: Review clarity, provide study materials
- **Easy questions**: Increase complexity, add follow-ups
- **High variance**: Check for ambiguous wording
- **Time-consuming**: Consider breaking into parts

## Node.js Integration Example

```javascript
// Analyze all questions
const analyzeQuestions = async () => {
  try {
    const response = await fetch('http://your-api-url/analytics/questions/difficulty', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        subject_filter: 'Mathematics',
        min_attempts: 5
      })
    });
    
    const analysis = await response.json();
    console.log('Difficulty Analysis:', analysis);
    
    // Process results
    analysis.questions.forEach(question => {
      console.log(`Question ${question.question_id}: ${question.calculated_difficulty}`);
      console.log(`Recommendations: ${question.recommendations.join(', ')}`);
    });
    
  } catch (error) {
    console.error('Error analyzing questions:', error);
  }
};

// Quick summary
const getQuickSummary = async () => {
  try {
    const response = await fetch('http://your-api-url/analytics/questions/difficulty/summary');
    const summary = await response.json();
    console.log('Quick Summary:', summary);
    
  } catch (error) {
    console.error('Error getting summary:', error);
  }
};
```

## Use Cases

1. **Curriculum Review**: Identify questions that are too easy/hard
2. **Student Support**: Find questions causing widespread difficulty
3. **Content Balance**: Ensure good distribution of difficulty levels
4. **Performance Tracking**: Monitor how question difficulty affects learning
5. **Adaptive Learning**: Adjust question selection based on difficulty analysis

## Performance Notes

- **Comprehensive Analysis**: More detailed but slower (use for in-depth reviews)
- **Quick Summary**: Faster overview (use for dashboards/quick checks)
- **Minimum Attempts**: Higher values give more reliable difficulty assessments
- **Subject Filtering**: Improves analysis accuracy for specific domains
