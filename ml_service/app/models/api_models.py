from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Request Models
class QuestionAnalysisRequest(BaseModel):
    question_text: str
    question_type: Optional[str] = None
    subject: Optional[str] = None
    correct_answer: Optional[str] = None

class AnswerAnalysisRequest(BaseModel):
    question_text: str
    answer_text: str
    question_type: Optional[str] = None
    correct_answer: Optional[str] = None
    time_taken: Optional[int] = None

class BatchAnalysisRequest(BaseModel):
    questions: List[QuestionAnalysisRequest]

class TrainingRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_type: str = Field(..., description="'difficulty', 'score', or 'comprehension'")
    min_samples: Optional[int] = 50
    retrain: Optional[bool] = False

# Response Models
class DifficultyPrediction(BaseModel):
    predicted_difficulty: str
    confidence: float
    probabilities: Dict[str, float]

class ScorePrediction(BaseModel):
    predicted_score: float
    confidence_interval: Optional[Dict[str, float]] = None

class ComprehensionAnalysis(BaseModel):
    comprehension_cluster: int
    cluster_confidence: float
    issues_identified: List[str]
    recommendations: List[str]

class QuestionAnalysisResponse(BaseModel):
    question_id: Optional[int] = None
    difficulty_prediction: DifficultyPrediction
    features_extracted: Dict[str, float]
    analysis_timestamp: datetime

class AnswerAnalysisResponse(BaseModel):
    answer_id: Optional[int] = None
    score_prediction: ScorePrediction
    comprehension_analysis: ComprehensionAnalysis
    features_extracted: Dict[str, float]
    analysis_timestamp: datetime

class CommonMistake(BaseModel):
    mistake_text: str
    frequency: int
    avg_score: float
    student_count: int

class QuestionPerformanceResponse(BaseModel):
    question_id: int
    performance_metrics: Dict[str, float]
    common_mistakes: List[CommonMistake]
    comprehension_issues: List[str]
    recommendations: List[str]

class TrainingResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_type: str = Field(..., description="Type of model that was trained")
    training_success: bool
    metrics: Dict[str, Any]
    message: str
    training_timestamp: datetime

class ModelInfo(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_name: str = Field(..., description="Name of the model")
    model_type: str = Field(..., description="Type of the model")
    training_date: Optional[datetime] = None
    performance_metrics: Dict[str, float]
    feature_count: int
    is_loaded: bool

class SystemStatusResponse(BaseModel):
    service_status: str
    loaded_models: List[ModelInfo]
    database_connected: bool
    last_training_date: Optional[datetime] = None
    total_questions_analyzed: int
    total_answers_processed: int

class SubjectPerformanceResponse(BaseModel):
    subject: str
    performance_summary: Dict[str, float]
    question_count: int
    student_count: int
    difficulty_distribution: Dict[str, int]
    improvement_suggestions: List[str]

# Analytics Models
class QuestionAnalytics(BaseModel):
    question_id: int
    predicted_difficulty: str
    actual_difficulty: Optional[str] = None
    avg_score: float
    completion_rate: float
    common_mistakes: List[str]
    comprehension_issues: List[str]
    last_updated: datetime

class StudentPerformancePattern(BaseModel):
    student_id: int
    performance_cluster: int
    strengths: List[str]
    weaknesses: List[str]
    recommended_actions: List[str]
    confidence_score: float

# Batch Processing Models
class BatchQuestionAnalysis(BaseModel):
    total_questions: int
    processed_questions: int
    failed_questions: int
    results: List[QuestionAnalysisResponse]
    processing_time: float

class BatchAnswerAnalysis(BaseModel):
    total_answers: int
    processed_answers: int
    failed_answers: int
    results: List[AnswerAnalysisResponse]
    processing_time: float

# Error Models
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime

# Feature Analysis Models
class FeatureImportance(BaseModel):
    feature_name: str
    importance_score: float
    description: str

class ModelExplanation(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_type: str = Field(..., description="Type of model providing the explanation")
    prediction: Any
    feature_contributions: List[FeatureImportance]
    confidence: float
    explanation: str

# Student Performance Analytics Models
class StudentPerformanceData(BaseModel):
    student_id: int
    question_id: int
    question_text: str
    question_type: Optional[str] = None
    subject: Optional[str] = None
    correct_answer: Optional[str] = None
    student_answer: str
    score: float
    max_score: float
    time_taken: Optional[int] = None  # in seconds
    attempt_number: Optional[int] = 1

class TrainWithStudentDataRequest(BaseModel):
    student_performances: List[StudentPerformanceData]
    retrain_existing: Optional[bool] = False

class TrainWithStudentDataResponse(BaseModel):
    total_records_processed: int
    questions_analyzed: int
    models_trained: List[str]
    training_results: Dict[str, Any]
    message: str
    training_timestamp: datetime

class QuestionDifficultyAnalysis(BaseModel):
    question_id: int
    question_text: str
    subject: str
    calculated_difficulty: str  # easy, medium, hard
    difficulty_score: float  # 0-1 scale where 1 is hardest
    confidence: float
    performance_metrics: Dict[str, float]
    student_statistics: Dict[str, int]
    recommendations: List[str]

class StudentPerformanceAnalysisRequest(BaseModel):
    subject_filter: Optional[str] = None
    min_attempts: Optional[int] = 5
    include_recent_only: Optional[bool] = False
    days_back: Optional[int] = 30

class QuestionDifficultyAnalysisResponse(BaseModel):
    total_questions_analyzed: int
    analysis_summary: Dict[str, int]  # difficulty distribution
    questions: List[QuestionDifficultyAnalysis]
    overall_insights: List[str]
    analysis_timestamp: datetime
