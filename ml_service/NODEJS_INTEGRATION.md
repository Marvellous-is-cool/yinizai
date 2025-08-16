# Node.js Integration for ML Question Difficulty Analysis

## Overview

This guide shows how to integrate your Node.js application with the ML service to analyze question difficulty based on real student performance data.

## Step 1: Send Student Data to ML Service

First, your Node.js app needs to send the actual student test results to the ML service for training.

### Endpoint: POST `/train/with-student-data`

```javascript
const trainMLWithStudentData = async (studentPerformances) => {
  try {
    const response = await fetch('https://your-ml-service.onrender.com/train/with-student-data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        student_performances: studentPerformances,
        retrain_existing: false  // Set to true to clear existing data
      })
    });
    
    const result = await response.json();
    console.log('Training started:', result.message);
    return result;
    
  } catch (error) {
    console.error('Error training ML models:', error);
    throw error;
  }
};

// Example usage - send your real student data
const studentData = [
  {
    student_id: 1,
    question_id: 101,
    question_text: "What is the capital of France?",
    question_type: "multiple_choice",
    subject: "Geography", 
    correct_answer: "Paris",
    student_answer: "Paris",
    score: 10,
    max_score: 10,
    time_taken: 15  // seconds
  },
  {
    student_id: 2,
    question_id: 101,
    question_text: "What is the capital of France?",
    question_type: "multiple_choice", 
    subject: "Geography",
    correct_answer: "Paris",
    student_answer: "London",
    score: 0,
    max_score: 10,
    time_taken: 25
  },
  // ... more student performance records
];

// Train the ML models with your real data
trainMLWithStudentData(studentData);
```

## Step 2: Analyze Question Difficulty

After training, you can analyze question difficulty based on all student performance data.

### Endpoint: POST `/analytics/questions/difficulty`

```javascript
const analyzeQuestionDifficulty = async (options = {}) => {
  try {
    const response = await fetch('https://your-ml-service.onrender.com/analytics/questions/difficulty', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        subject_filter: options.subject || null,
        min_attempts: options.minAttempts || 5,
        include_recent_only: options.recentOnly || false,
        days_back: options.daysBack || 30
      })
    });
    
    const analysis = await response.json();
    
    // Process the results
    console.log(`Analyzed ${analysis.total_questions_analyzed} questions`);
    console.log('Difficulty Distribution:', analysis.analysis_summary);
    
    // Get questions that need attention
    const hardQuestions = analysis.questions.filter(q => 
      q.calculated_difficulty === 'hard' && 
      q.performance_metrics.avg_score < 0.4
    );
    
    console.log(`Found ${hardQuestions.length} questions that may need review`);
    
    return analysis;
    
  } catch (error) {
    console.error('Error analyzing question difficulty:', error);
    throw error;
  }
};

// Example usage
analyzeQuestionDifficulty({ 
  subject: 'Mathematics', 
  minAttempts: 3 
});
```

## Complete Integration Example

```javascript
class MLQuestionAnalyzer {
  constructor(mlServiceUrl) {
    this.baseUrl = mlServiceUrl;
  }
  
  // Step 1: Train with your student data
  async trainWithStudentData(studentPerformances, retrain = false) {
    const response = await fetch(`${this.baseUrl}/train/with-student-data`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_performances: studentPerformances,
        retrain_existing: retrain
      })
    });
    
    if (!response.ok) {
      throw new Error(`Training failed: ${response.status}`);
    }
    
    return await response.json();
  }
  
  // Step 2: Analyze question difficulty
  async analyzeDifficulty(options = {}) {
    const response = await fetch(`${this.baseUrl}/analytics/questions/difficulty`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options)
    });
    
    if (!response.ok) {
      throw new Error(`Analysis failed: ${response.status}`);
    }
    
    return await response.json();
  }
  
  // Helper: Convert your database data to the required format
  formatStudentData(students, questions, answers) {
    const performances = [];
    
    answers.forEach(answer => {
      const student = students.find(s => s.id === answer.student_id);
      const question = questions.find(q => q.id === answer.question_id);
      
      if (student && question) {
        performances.push({
          student_id: student.id,
          question_id: question.id,
          question_text: question.text,
          question_type: question.type || 'short_answer',
          subject: question.subject,
          correct_answer: question.correct_answer,
          student_answer: answer.answer_text,
          score: answer.score,
          max_score: answer.max_score || question.points,
          time_taken: answer.time_taken,
          attempt_number: answer.attempt_number || 1
        });
      }
    });
    
    return performances;
  }
  
  // Helper: Get questions that need attention
  getProblematicQuestions(analysis) {
    return analysis.questions.filter(question => {
      const metrics = question.performance_metrics;
      return (
        question.calculated_difficulty === 'hard' ||
        metrics.avg_score < 0.5 ||
        metrics.struggle_rate > 0.4 ||
        metrics.score_std > 0.4  // High variance = confusing
      );
    });
  }
}

// Usage example
const analyzer = new MLQuestionAnalyzer('https://your-ml-service.onrender.com');

// Initialize with your student data
async function initializeMLAnalysis() {
  try {
    // Get your real data from database
    const students = await getStudentsFromDB();
    const questions = await getQuestionsFromDB();
    const answers = await getAnswersFromDB();
    
    // Format for ML service
    const studentPerformances = analyzer.formatStudentData(students, questions, answers);
    
    // Train the models
    console.log('Training ML models with real student data...');
    const trainResult = await analyzer.trainWithStudentData(studentPerformances);
    console.log('Training initiated:', trainResult.message);
    
    // Wait a bit for training to complete (it runs in background)
    setTimeout(async () => {
      // Analyze question difficulty
      console.log('Analyzing question difficulty...');
      const analysis = await analyzer.analyzeDifficulty();
      
      // Get questions that need attention
      const problematic = analyzer.getProblematicQuestions(analysis);
      console.log(`Found ${problematic.length} questions that may need review`);
      
      // Update your database with insights
      await updateQuestionInsights(analysis);
      
    }, 30000); // Wait 30 seconds for training
    
  } catch (error) {
    console.error('ML Analysis failed:', error);
  }
}

// Run the analysis
initializeMLAnalysis();
```

## What the Analysis Provides

The ML service analyzes your real student data and provides:

1. **Difficulty Classification**: Easy, Medium, Hard based on actual performance
2. **Performance Metrics**: Average scores, pass rates, time taken
3. **Student Statistics**: How many students attempted, struggled, etc.
4. **Recommendations**: Actionable suggestions for each question
5. **Overall Insights**: System-wide patterns and suggestions

## Benefits for Your Application

- **Data-Driven Decisions**: Base difficulty on actual student performance, not assumptions
- **Identify Problem Questions**: Find questions that consistently cause issues
- **Curriculum Optimization**: Balance easy/medium/hard questions appropriately  
- **Student Support**: Understand where students struggle most
- **Content Quality**: Improve questions based on performance patterns

This integration gives you ML-powered insights into your actual educational content effectiveness!
