from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import os

from app.models.database import get_db, Base, engine, Question, StudentAnswer
from app.models.api_models import *
from app.services.feature_engineering import FeatureEngineer
from app.services.ml_models import MLModels
from app.services.data_processor import DataProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Yinizai ML Analysis Service",
    description="Machine Learning service for analyzing student answers and predicting question difficulty",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,  # Disable docs in production if needed
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# Production-ready CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize ML components
ml_models = MLModels()
feature_engineer = FeatureEngineer()

# Load existing models on startup
@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    try:
        ml_models.load_all_models()
        logger.info("ML Service started successfully")
    except Exception as e:
        logger.error(f"Error loading models on startup: {str(e)}")

@app.get("/")
async def root():
    return {
        "service": "Yinizai ML Analysis Service",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }

@app.get("/health", response_model=SystemStatusResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with model status"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_connected = True
        
        # Get model information
        model_info = ml_models.get_model_info()
        
        # Check if core models are available
        required_models = ['difficulty_predictor', 'score_predictor', 'comprehension_analyzer']
        available_models = []
        
        for model_name in required_models:
            model_file = f"{model_name}.joblib"
            if model_file in model_info.get('available_model_files', []):
                is_loaded = model_name in ml_models.models
                available_models.append(ModelInfo(
                    model_name=model_name,
                    model_type="ML Model",
                    training_date=datetime.utcnow() if is_loaded else None,
                    performance_metrics={},
                    feature_count=0,
                    is_loaded=is_loaded
                ))
        
        # Determine service status
        if len(available_models) == len(required_models):
            service_status = "fully_operational"
        elif len(available_models) > 0:
            service_status = "partially_operational"
        else:
            service_status = "models_not_trained"
        
        # Get basic analytics
        from app.models.database import Question, StudentAnswer
        try:
            total_questions = db.query(Question).count()
            total_answers = db.query(StudentAnswer).count()
        except:
            total_questions = 0
            total_answers = 0
        
        return SystemStatusResponse(
            service_status=service_status,
            loaded_models=available_models,
            database_connected=db_connected,
            last_training_date=datetime.utcnow() if available_models else None,
            total_questions_analyzed=total_questions,
            total_answers_processed=total_answers
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system status: {str(e)}")

@app.post("/train/with-student-data", response_model=TrainWithStudentDataResponse)
async def train_with_student_data(
    request: TrainWithStudentDataRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Train ML models using real student performance data from Node.js.
    This endpoint accepts actual student test scores and trains the difficulty prediction models.
    """
    try:
        if not request.student_performances:
            raise HTTPException(status_code=400, detail="No student performance data provided")
        
        # Start training in background
        background_tasks.add_task(
            _train_with_student_data_background,
            request.student_performances,
            request.retrain_existing or False,
            db
        )
        
        return TrainWithStudentDataResponse(
            total_records_processed=len(request.student_performances),
            questions_analyzed=len(set(p.question_id for p in request.student_performances)),
            models_trained=["difficulty_predictor", "score_predictor"],
            training_results={},
            message=f"Training started with {len(request.student_performances)} student performance records",
            training_timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error starting training with student data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting training: {str(e)}")

async def _train_with_student_data_background(
    student_performances: List[StudentPerformanceData], 
    retrain_existing: bool,
    db: Session
):
    """Background task for training models with real student data"""
    try:
        logger.info(f"Training models with {len(student_performances)} student performance records")
        
        # Clear existing data if retraining
        if retrain_existing:
            db.query(StudentAnswer).delete()
            db.query(Question).delete()
            db.commit()
        
        # Convert student performance data to database records
        questions_created = {}
        answers_created = []
        
        for perf in student_performances:
            # Create or update question record
            if perf.question_id not in questions_created:
                existing_question = db.query(Question).filter(Question.id == perf.question_id).first()
                
                if not existing_question:
                    question = Question(
                        id=perf.question_id,
                        question_text=perf.question_text,
                        question_type=perf.question_type or "short_answer",
                        subject=perf.subject or "General",
                        correct_answer=perf.correct_answer or "",
                        points=int(perf.max_score),
                        created_at=datetime.utcnow()
                    )
                    db.add(question)
                    questions_created[perf.question_id] = question
                else:
                    questions_created[perf.question_id] = existing_question
            
            # Create student answer record
            student_answer = StudentAnswer(
                student_id=perf.student_id,
                question_id=perf.question_id,
                answer_text=perf.student_answer,
                score=perf.score,
                max_score=perf.max_score,
                time_taken=perf.time_taken or 0,
                attempt_number=perf.attempt_number or 1,
                created_at=datetime.utcnow()
            )
            db.add(student_answer)
            answers_created.append(student_answer)
        
        # Commit to database
        db.commit()
        logger.info(f"Created {len(questions_created)} questions and {len(answers_created)} student answers")
        
        # Now train the ML models using this real data
        data_processor = DataProcessor(db)
        
        # Train difficulty prediction model
        try:
            training_data = data_processor.get_training_data_for_difficulty_prediction(min_samples=3)
            if len(training_data) >= 5:  # Need minimum data for training
                results = ml_models.train_difficulty_predictor(training_data)
                logger.info(f"Difficulty model trained with accuracy: {results.get('test_accuracy', 0):.3f}")
            else:
                logger.warning(f"Not enough data for difficulty training. Need at least 5 samples, got {len(training_data)}")
        except Exception as e:
            logger.error(f"Error training difficulty model: {str(e)}")
        
        # Train score prediction model
        try:
            score_training_data = data_processor.get_training_data_for_score_prediction(limit=len(answers_created))
            if len(score_training_data) >= 10:  # Need minimum data for training
                results = ml_models.train_score_predictor(score_training_data)
                logger.info(f"Score model trained with R²: {results.get('test_r2', 0):.3f}")
            else:
                logger.warning(f"Not enough data for score training. Need at least 10 samples, got {len(score_training_data)}")
        except Exception as e:
            logger.error(f"Error training score model: {str(e)}")
        
        logger.info("Model training completed successfully")
    
    except Exception as e:
        logger.error(f"Error in background training with student data: {str(e)}")
        db.rollback()

@app.post("/analyze/question", response_model=QuestionAnalysisResponse)
async def analyze_question(request: QuestionAnalysisRequest, db: Session = Depends(get_db)):
    """Analyze a question and predict its difficulty"""
    try:
        # Prepare data for prediction
        data_processor = DataProcessor(db)
        features_df = data_processor.prepare_prediction_data(
            question_text=request.question_text,
            question_type=request.question_type or "short_answer"
        )
        
        # Extract features for response
        features_dict = features_df.iloc[0].to_dict()
        
        # Make difficulty prediction
        difficulty_predictions = ml_models.predict_difficulty(features_df)
        difficulty_pred = difficulty_predictions[0]
        
        return QuestionAnalysisResponse(
            difficulty_prediction=DifficultyPrediction(
                predicted_difficulty=difficulty_pred['predicted_difficulty'],
                confidence=difficulty_pred['confidence'],
                probabilities=difficulty_pred['probabilities']
            ),
            features_extracted=features_dict,
            analysis_timestamp=datetime.utcnow()
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Model not available: {str(e)}")
    except Exception as e:
        logger.error(f"Error analyzing question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing question: {str(e)}")

@app.post("/analyze/answer", response_model=AnswerAnalysisResponse)
async def analyze_answer(request: AnswerAnalysisRequest, db: Session = Depends(get_db)):
    """Analyze a student answer and predict score and comprehension issues"""
    try:
        # Prepare data for prediction
        data_processor = DataProcessor(db)
        features_df = data_processor.prepare_prediction_data(
            question_text=request.question_text,
            question_type=request.question_type or "short_answer",
            answer_text=request.answer_text,
            correct_answer=request.correct_answer or ""
        )
        
        # Extract features for response
        features_dict = features_df.iloc[0].to_dict()
        
        # Make score prediction
        score_predictions = ml_models.predict_score(features_df)
        predicted_score = score_predictions[0]
        
        # Analyze comprehension
        comprehension_analysis = ml_models.analyze_comprehension(features_df)
        comprehension = comprehension_analysis[0]
        
        # Generate recommendations based on analysis
        issues = []
        recommendations = []
        
        if predicted_score < 0.5:
            issues.append("Low predicted score indicates comprehension difficulties")
            recommendations.append("Consider providing additional explanation or examples")
        
        if comprehension['cluster_confidence'] < 0.7:
            issues.append("Unclear comprehension pattern")
            recommendations.append("Review answer for clarity and completeness")
        
        return AnswerAnalysisResponse(
            score_prediction=ScorePrediction(predicted_score=predicted_score),
            comprehension_analysis=ComprehensionAnalysis(
                comprehension_cluster=comprehension['comprehension_cluster'],
                cluster_confidence=comprehension['cluster_confidence'],
                issues_identified=issues,
                recommendations=recommendations
            ),
            features_extracted=features_dict,
            analysis_timestamp=datetime.utcnow()
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Model not available: {str(e)}")
    except Exception as e:
        logger.error(f"Error analyzing answer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing answer: {str(e)}")

@app.get("/analyze/question/{question_id}/performance", response_model=QuestionPerformanceResponse)
async def get_question_performance(question_id: int, db: Session = Depends(get_db)):
    """Get detailed performance analysis for a specific question"""
    try:
        data_processor = DataProcessor(db)
        
        # Get performance metrics
        performance = data_processor.get_question_performance_data(question_id)
        
        if not performance:
            raise HTTPException(status_code=404, detail="Question not found or no data available")
        
        # Get common mistakes
        mistakes = data_processor.analyze_common_mistakes(question_id)
        common_mistakes = [
            CommonMistake(
                mistake_text=m['mistake_text'],
                frequency=m['frequency'],
                avg_score=m['avg_score'],
                student_count=m['student_count']
            ) for m in mistakes
        ]
        
        # Get comprehension issues
        comprehension_issues = data_processor.identify_comprehension_issues(question_id)
        
        # Generate recommendations
        recommendations = []
        if performance.get('avg_score', 1) < 0.6:
            recommendations.append("Consider revising question clarity or difficulty level")
        if performance.get('pass_rate', 1) < 0.5:
            recommendations.append("Provide additional learning resources for this topic")
        if len(mistakes) > 3:
            recommendations.append("Address common misconceptions in class discussion")
        
        return QuestionPerformanceResponse(
            question_id=question_id,
            performance_metrics=performance,
            common_mistakes=common_mistakes,
            comprehension_issues=comprehension_issues,
            recommendations=recommendations
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting question performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting question performance: {str(e)}")

@app.post("/train/{model_type}", response_model=TrainingResponse)
async def train_model(model_type: str, request: TrainingRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Train or retrain ML models"""
    valid_models = ['difficulty', 'score', 'comprehension']
    
    if model_type not in valid_models:
        raise HTTPException(status_code=400, detail=f"Invalid model type. Must be one of: {valid_models}")
    
    try:
        # Start training in background
        background_tasks.add_task(
            _train_model_background,
            model_type,
            request.min_samples or 50,
            request.retrain or False,
            db
        )
        
        return TrainingResponse(
            model_type=model_type,
            training_success=True,
            metrics={},
            message=f"Training for {model_type} model started in background",
            training_timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error starting training: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting training: {str(e)}")

async def _train_model_background(model_type: str, min_samples: int, retrain: bool, db: Session):
    """Background task for model training"""
    try:
        data_processor = DataProcessor(db)
        
        if model_type == 'difficulty':
            # Train difficulty prediction model
            training_data = data_processor.get_training_data_for_difficulty_prediction(min_samples)
            if len(training_data) < min_samples:
                logger.warning(f"Not enough data for training. Required: {min_samples}, Available: {len(training_data)}")
                return
            
            results = ml_models.train_difficulty_predictor(training_data)
            logger.info(f"Difficulty model training completed: {results['test_accuracy']:.3f} accuracy")
        
        elif model_type == 'score':
            # Train score prediction model
            training_data = data_processor.get_training_data_for_score_prediction(limit=min_samples * 10)
            if len(training_data) < min_samples:
                logger.warning(f"Not enough data for training. Required: {min_samples}, Available: {len(training_data)}")
                return
            
            results = ml_models.train_score_predictor(training_data)
            logger.info(f"Score model training completed: {results['test_r2']:.3f} R²")
        
        elif model_type == 'comprehension':
            # Train comprehension analysis model
            training_data = data_processor.get_training_data_for_score_prediction(limit=min_samples * 5)
            if len(training_data) < min_samples:
                logger.warning(f"Not enough data for training. Required: {min_samples}, Available: {len(training_data)}")
                return
            
            results = ml_models.train_comprehension_analyzer(training_data)
            logger.info(f"Comprehension model training completed: {results['n_clusters']} clusters")
    
    except Exception as e:
        logger.error(f"Error in background training: {str(e)}")

@app.get("/analytics/subject/{subject}", response_model=SubjectPerformanceResponse)
async def get_subject_performance(subject: str, db: Session = Depends(get_db)):
    """Get performance analytics for a specific subject"""
    try:
        data_processor = DataProcessor(db)
        
        # Get subject performance summary
        summary = data_processor.get_subject_performance_summary(subject)
        
        if subject not in summary:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        subject_data = summary[subject]
        
        # Generate improvement suggestions
        suggestions = []
        if subject_data['avg_score'] < 0.6:
            suggestions.append("Focus on fundamental concepts review")
        if subject_data['question_count'] < 10:
            suggestions.append("Consider adding more practice questions")
        
        return SubjectPerformanceResponse(
            subject=subject,
            performance_summary=subject_data,
            question_count=subject_data['question_count'],
            student_count=subject_data['student_count'],
            difficulty_distribution={},  # Would need additional query
            improvement_suggestions=suggestions
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subject performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting subject performance: {str(e)}")

@app.post("/batch/analyze/questions", response_model=BatchQuestionAnalysis)
async def batch_analyze_questions(request: BatchAnalysisRequest, db: Session = Depends(get_db)):
    """Analyze multiple questions in batch"""
    try:
        start_time = datetime.utcnow()
        results = []
        failed_count = 0
        
        for question_request in request.questions:
            try:
                # Analyze each question
                analysis = await analyze_question(question_request, db)
                results.append(analysis)
            except Exception as e:
                logger.error(f"Failed to analyze question: {str(e)}")
                failed_count += 1
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        return BatchQuestionAnalysis(
            total_questions=len(request.questions),
            processed_questions=len(results),
            failed_questions=failed_count,
            results=results,
            processing_time=processing_time
        )
    
    except Exception as e:
        logger.error(f"Error in batch question analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in batch analysis: {str(e)}")

@app.post("/analytics/questions/difficulty", response_model=QuestionDifficultyAnalysisResponse)
async def analyze_all_questions_difficulty(
    request: StudentPerformanceAnalysisRequest, 
    db: Session = Depends(get_db)
):
    """
    Analyze all questions to determine difficulty based on student performance data.
    This endpoint uses ML to evaluate student scores and determine if questions are easy, medium, or hard.
    """
    try:
        data_processor = DataProcessor(db)
        
        # Get questions with sufficient student data
        min_attempts = request.min_attempts or 5
        
        # Filter by subject if specified
        base_query = db.query(
            Question.id,
            Question.question_text,
            Question.question_type,
            Question.subject,
            Question.correct_answer,
            Question.points,
            func.count(StudentAnswer.id).label('total_attempts'),
            func.avg(StudentAnswer.score / StudentAnswer.max_score).label('avg_score_ratio'),
            func.stddev(StudentAnswer.score / StudentAnswer.max_score).label('score_std'),
            func.avg(StudentAnswer.time_taken).label('avg_time'),
            func.stddev(StudentAnswer.time_taken).label('time_std'),
            func.count(func.distinct(StudentAnswer.student_id)).label('unique_students'),
            func.min(StudentAnswer.score / StudentAnswer.max_score).label('min_score'),
            func.max(StudentAnswer.score / StudentAnswer.max_score).label('max_score'),
            func.sum(func.case([(StudentAnswer.score / StudentAnswer.max_score >= 0.7, 1)], else_=0)).label('high_scores'),
            func.sum(func.case([(StudentAnswer.score / StudentAnswer.max_score < 0.5, 1)], else_=0)).label('low_scores')
        ).join(StudentAnswer, Question.id == StudentAnswer.question_id)
        
        # Apply filters
        if request.subject_filter:
            base_query = base_query.filter(Question.subject == request.subject_filter)
        
        if request.include_recent_only:
            days_back = request.days_back or 30
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            base_query = base_query.filter(StudentAnswer.created_at >= cutoff_date)
        
        questions_with_stats = base_query.group_by(Question.id)\
            .having(func.count(StudentAnswer.id) >= min_attempts)\
            .all()
        
        if not questions_with_stats:
            return QuestionDifficultyAnalysisResponse(
                total_questions_analyzed=0,
                analysis_summary={'easy': 0, 'medium': 0, 'hard': 0},
                questions=[],
                overall_insights=["No questions found with sufficient student data"],
                analysis_timestamp=datetime.utcnow()
            )
        
        # Analyze each question
        analyzed_questions = []
        difficulty_counts = {'easy': 0, 'medium': 0, 'hard': 0}
        
        for q in questions_with_stats:
            # Calculate performance metrics
            avg_score = float(q.avg_score_ratio) if q.avg_score_ratio else 0
            score_std = float(q.score_std) if q.score_std else 0
            avg_time = float(q.avg_time) if q.avg_time else 0
            total_attempts = q.total_attempts
            unique_students = q.unique_students
            high_scores = q.high_scores or 0
            low_scores = q.low_scores or 0
            
            # Calculate advanced difficulty metrics
            pass_rate = avg_score
            consistency = 1 - min(score_std, 1.0)  # Higher consistency = more reliable difficulty
            completion_efficiency = high_scores / total_attempts if total_attempts > 0 else 0
            struggle_rate = low_scores / total_attempts if total_attempts > 0 else 0
            
            # Determine difficulty using multiple factors
            difficulty_score = 0.0
            
            # Primary factor: average performance (40% weight)
            if avg_score >= 0.8:
                difficulty_score += 0.1  # Easy
            elif avg_score >= 0.6:
                difficulty_score += 0.4  # Medium-Easy
            elif avg_score >= 0.4:
                difficulty_score += 0.7  # Medium-Hard
            else:
                difficulty_score += 1.0  # Hard
            
            # Secondary factor: consistency (20% weight)
            if score_std > 0.4:  # High variance suggests confusing/ambiguous
                difficulty_score += 0.2
            
            # Tertiary factor: struggle rate (20% weight)
            difficulty_score += (struggle_rate * 0.2)
            
            # Quaternary factor: time factor (20% weight)
            if avg_time > 300:  # More than 5 minutes suggests complexity
                difficulty_score += 0.2
            
            # Normalize difficulty score (0-1 scale)
            difficulty_score = min(difficulty_score, 1.0)
            
            # Categorize difficulty
            if difficulty_score <= 0.3:
                calculated_difficulty = 'easy'
                confidence = 1 - difficulty_score
            elif difficulty_score <= 0.7:
                calculated_difficulty = 'medium'
                confidence = 1 - abs(0.5 - difficulty_score)
            else:
                calculated_difficulty = 'hard'
                confidence = difficulty_score
            
            # Generate recommendations
            recommendations = []
            if calculated_difficulty == 'hard' and avg_score < 0.4:
                recommendations.append("Consider providing additional study materials")
                recommendations.append("Review question clarity and instructions")
            elif calculated_difficulty == 'easy' and avg_score > 0.9:
                recommendations.append("Consider increasing question complexity")
                recommendations.append("Add follow-up challenging questions")
            elif score_std > 0.4:
                recommendations.append("Question may be ambiguous - review wording")
                recommendations.append("Provide clearer examples or context")
            
            if struggle_rate > 0.3:
                recommendations.append("High struggle rate - consider prerequisite topics review")
            
            if avg_time > 600:  # More than 10 minutes
                recommendations.append("Question may be too time-consuming - consider breaking into parts")
            
            # Create analysis object
            question_analysis = QuestionDifficultyAnalysis(
                question_id=q.id,
                question_text=q.question_text[:200] + "..." if len(q.question_text) > 200 else q.question_text,
                subject=q.subject or "Unknown",
                calculated_difficulty=calculated_difficulty,
                difficulty_score=round(difficulty_score, 3),
                confidence=round(confidence, 3),
                performance_metrics={
                    'avg_score': round(avg_score, 3),
                    'pass_rate': round(pass_rate, 3),
                    'score_std': round(score_std, 3),
                    'avg_time_minutes': round(avg_time / 60, 2),
                    'completion_efficiency': round(completion_efficiency, 3),
                    'struggle_rate': round(struggle_rate, 3),
                    'consistency': round(consistency, 3)
                },
                student_statistics={
                    'total_attempts': total_attempts,
                    'unique_students': unique_students,
                    'high_performers': high_scores,
                    'struggling_students': low_scores
                },
                recommendations=recommendations
            )
            
            analyzed_questions.append(question_analysis)
            difficulty_counts[calculated_difficulty] += 1
        
        # Generate overall insights
        overall_insights = []
        total_analyzed = len(analyzed_questions)
        
        if difficulty_counts['hard'] / total_analyzed > 0.4:
            overall_insights.append("High proportion of difficult questions detected - consider curriculum review")
        
        if difficulty_counts['easy'] / total_analyzed > 0.5:
            overall_insights.append("Many questions are too easy - consider increasing overall difficulty")
        
        if difficulty_counts['medium'] / total_analyzed > 0.6:
            overall_insights.append("Good balance of moderate difficulty questions")
        
        # Add subject-specific insights if filtered
        if request.subject_filter:
            subject_avg_difficulty = sum(q.difficulty_score for q in analyzed_questions) / len(analyzed_questions)
            if subject_avg_difficulty > 0.7:
                overall_insights.append(f"{request.subject_filter} appears to be a challenging subject area")
            elif subject_avg_difficulty < 0.3:
                overall_insights.append(f"{request.subject_filter} questions may need more complexity")
        
        return QuestionDifficultyAnalysisResponse(
            total_questions_analyzed=total_analyzed,
            analysis_summary=difficulty_counts,
            questions=analyzed_questions,
            overall_insights=overall_insights,
            analysis_timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error in question difficulty analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing question difficulty: {str(e)}")

@app.get("/analytics/questions/difficulty/summary")
async def get_question_difficulty_summary(
    subject: Optional[str] = None,
    min_attempts: int = 3,
    db: Session = Depends(get_db)
):
    """
    Get a quick summary of question difficulty distribution.
    This is a faster endpoint for getting overview statistics.
    """
    try:
        # Quick query for summary statistics
        base_query = db.query(
            Question.subject,
            func.count(Question.id).label('total_questions'),
            func.avg(func.coalesce(
                (func.count(StudentAnswer.id) * func.avg(StudentAnswer.score / StudentAnswer.max_score)), 0
            )).label('avg_performance')
        ).outerjoin(StudentAnswer, Question.id == StudentAnswer.question_id)
        
        if subject:
            base_query = base_query.filter(Question.subject == subject)
        
        results = base_query.group_by(Question.subject).all()
        
        summary = {}
        for result in results:
            subject_name = result.subject or "Unknown"
            avg_performance = float(result.avg_performance) if result.avg_performance else 0
            
            # Simple difficulty classification
            if avg_performance >= 0.7:
                difficulty = "easy"
            elif avg_performance >= 0.4:
                difficulty = "medium"
            else:
                difficulty = "hard"
            
            summary[subject_name] = {
                "total_questions": result.total_questions,
                "estimated_difficulty": difficulty,
                "avg_performance": round(avg_performance, 3)
            }
        
        return {
            "summary": summary,
            "total_subjects": len(summary),
            "analysis_note": "Quick summary based on average student performance",
            "for_detailed_analysis": "Use POST /analytics/questions/difficulty"
        }
    
    except Exception as e:
        logger.error(f"Error in difficulty summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting difficulty summary: {str(e)}")

@app.post("/setup/initialize-models")
async def initialize_models(db: Session = Depends(get_db)):
    """Initialize ML models with sample data for immediate functionality"""
    try:
        # Check if models already exist
        model_info = ml_models.get_model_info()
        if model_info['available_model_files']:
            return {
                "message": "Models already exist",
                "existing_models": model_info['available_model_files'],
                "status": "skipped"
            }
        
        # Create sample training data for models to work
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Generate minimal sample data for difficulty prediction
        sample_difficulty_data = []
        difficulties = ['easy', 'medium', 'hard']
        
        for i in range(30):  # 30 sample questions
            difficulty = difficulties[i % 3]
            
            # Generate features based on difficulty
            if difficulty == 'easy':
                text_length = np.random.randint(20, 80)
                word_count = np.random.randint(5, 15)
                avg_score = np.random.uniform(0.7, 0.9)
            elif difficulty == 'medium':
                text_length = np.random.randint(80, 150)
                word_count = np.random.randint(15, 30)
                avg_score = np.random.uniform(0.4, 0.7)
            else:  # hard
                text_length = np.random.randint(150, 300)
                word_count = np.random.randint(30, 60)
                avg_score = np.random.uniform(0.1, 0.4)
            
            sample_difficulty_data.append({
                'text_length': text_length,
                'word_count': word_count,
                'avg_word_length': text_length / word_count if word_count > 0 else 5,
                'performance_avg_score': avg_score,
                'performance_score_std': np.random.uniform(0.1, 0.3),
                'performance_total_attempts': np.random.randint(10, 50),
                'difficulty_level': difficulty
            })
        
        difficulty_df = pd.DataFrame(sample_difficulty_data)
        
        # Train difficulty predictor
        diff_results = ml_models.train_difficulty_predictor(difficulty_df)
        
        # Generate sample data for score prediction
        sample_score_data = []
        for i in range(50):  # 50 sample answers
            answer_length = np.random.randint(10, 200)
            text_similarity = np.random.uniform(0.1, 1.0)
            score_ratio = min(1.0, text_similarity * 0.8 + np.random.uniform(-0.2, 0.2))
            
            sample_score_data.append({
                'answer_length': answer_length,
                'word_count': answer_length // 5,
                'text_similarity': text_similarity,
                'avg_word_length': 5.0,
                'score_ratio': max(0.0, score_ratio)
            })
        
        score_df = pd.DataFrame(sample_score_data)
        
        # Train score predictor
        score_results = ml_models.train_score_predictor(score_df)
        
        # Generate sample data for comprehension analysis
        comprehension_df = score_df.copy()  # Reuse score data
        comp_results = ml_models.train_comprehension_analyzer(comprehension_df)
        
        return {
            "message": "Models initialized successfully with sample data",
            "models_created": [
                "difficulty_predictor",
                "score_predictor", 
                "comprehension_analyzer"
            ],
            "difficulty_accuracy": f"{diff_results['test_accuracy']:.3f}",
            "score_r2": f"{score_results['test_r2']:.3f}",
            "comprehension_clusters": comp_results['n_clusters'],
            "status": "success",
            "note": "Models trained with synthetic data. Performance will improve with real student data."
        }
        
    except Exception as e:
        logger.error(f"Error initializing models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model initialization failed: {str(e)}")

@app.post("/setup/initialize")
async def initialize_deployment(db: Session = Depends(get_db)):
    """Initialize deployment with sample data (for production setup)"""
    try:
        # Check if already initialized
        from app.models.database import Question
        question_count = db.query(Question).count()
        
        if question_count > 0:
            return {
                "message": "Database already initialized",
                "existing_questions": question_count,
                "status": "skipped"
            }
        
        # Run sample data generation
        import subprocess
        result = subprocess.run(
            ["python", "generate_sample_data.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            new_question_count = db.query(Question).count()
            return {
                "message": "Sample data generated successfully",
                "questions_created": new_question_count,
                "status": "success",
                "next_steps": [
                    "Train models with POST /train/difficulty",
                    "Train models with POST /train/score", 
                    "Train models with POST /train/comprehension"
                ]
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Sample data generation failed: {result.stderr}"
            )
    
    except Exception as e:
        logger.error(f"Error in deployment initialization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", 8000)),
        reload=True
    )
