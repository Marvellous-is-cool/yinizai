from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
import logging
import os

from app.models.database import get_db, Base, engine
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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/status", response_model=SystemStatusResponse)
async def get_system_status(db: Session = Depends(get_db)):
    """Get system status and model information"""
    try:
        # Get model information
        model_info = ml_models.get_model_info()
        
        # Count questions and answers in database
        from app.models.database import Question, StudentAnswer
        question_count = db.query(Question).count()
        answer_count = db.query(StudentAnswer).count()
        
        loaded_models = []
        for model_name in model_info['loaded_models']:
            loaded_models.append(ModelInfo(
                model_name=model_name,
                model_type=model_name.replace('_predictor', '').replace('_analyzer', ''),
                performance_metrics={},
                feature_count=0,
                is_loaded=True
            ))
        
        return SystemStatusResponse(
            service_status="running",
            loaded_models=loaded_models,
            database_connected=True,
            total_questions_analyzed=question_count,
            total_answers_processed=answer_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system status: {str(e)}")

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
