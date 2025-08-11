import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.database import StudentAnswer, Question, QuestionAnalytics
from app.services.feature_engineering import FeatureEngineer
from datetime import datetime, timedelta

class DataProcessor:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.feature_engineer = FeatureEngineer()
    
    def get_training_data_for_difficulty_prediction(self, min_samples: int = 10) -> pd.DataFrame:
        """
        Get training data for question difficulty prediction based on actual student performance
        """
        # Query questions with enough student responses to calculate reliable difficulty
        questions_with_stats = self.db.query(
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
            func.count(func.distinct(StudentAnswer.student_id)).label('unique_students')
        ).join(StudentAnswer, Question.id == StudentAnswer.question_id)\
         .group_by(Question.id)\
         .having(func.count(StudentAnswer.id) >= min_samples)\
         .all()
        
        if not questions_with_stats:
            return pd.DataFrame()
        
        # Convert to list of dictionaries for feature extraction
        question_data = []
        for q in questions_with_stats:
            # Calculate difficulty based on performance metrics
            avg_score = float(q.avg_score_ratio) if q.avg_score_ratio else 0
            score_std = float(q.score_std) if q.score_std else 0
            
            # Determine difficulty based on student performance
            if avg_score >= 0.8:  # 80%+ success rate
                calculated_difficulty = 'easy'
            elif avg_score >= 0.5:  # 50-80% success rate  
                calculated_difficulty = 'medium'
            else:  # <50% success rate
                calculated_difficulty = 'hard'
            
            # Add additional context based on time and variance
            if score_std > 0.3:  # High variance suggests confusing question
                if calculated_difficulty == 'easy':
                    calculated_difficulty = 'medium'  # Bump up difficulty
            
            question_data.append({
                'id': q.id,
                'question_text': q.question_text,
                'question_type': q.question_type,
                'subject': q.subject,
                'correct_answer': q.correct_answer,
                'points': q.points,
                'total_attempts': q.total_attempts,
                'avg_score_ratio': avg_score,
                'score_std': score_std,
                'avg_time': float(q.avg_time) if q.avg_time else 0,
                'time_std': float(q.time_std) if q.time_std else 0,
                'unique_students': q.unique_students,
                'calculated_difficulty': calculated_difficulty
            })
        
        # Extract text features
        features_df = self.feature_engineer.create_feature_matrix(question_data)
        
        # Add performance-based features and target
        for i, q_data in enumerate(question_data):
            features_df.loc[i, 'difficulty_level'] = q_data['calculated_difficulty']
            features_df.loc[i, 'question_id'] = q_data['id']
            features_df.loc[i, 'subject'] = q_data['subject']
            
            # Add performance metrics as features
            features_df.loc[i, 'performance_avg_score'] = q_data['avg_score_ratio']
            features_df.loc[i, 'performance_score_std'] = q_data['score_std']
            features_df.loc[i, 'performance_avg_time'] = q_data['avg_time']
            features_df.loc[i, 'performance_time_std'] = q_data['time_std']
            features_df.loc[i, 'performance_total_attempts'] = q_data['total_attempts']
            features_df.loc[i, 'performance_unique_students'] = q_data['unique_students']
        
        return features_df
    
    def get_training_data_for_score_prediction(self, limit: int = 1000) -> pd.DataFrame:
        """
        Get training data for score prediction
        """
        # Query student answers with question data
        query = self.db.query(
            StudentAnswer.id,
            StudentAnswer.student_id,
            StudentAnswer.question_id,
            StudentAnswer.answer_text,
            StudentAnswer.score,
            StudentAnswer.max_score,
            StudentAnswer.time_taken,
            StudentAnswer.attempt_number,
            Question.question_text,
            Question.question_type,
            Question.correct_answer,
            Question.subject
        ).join(Question, StudentAnswer.question_id == Question.id)\
         .filter(StudentAnswer.answer_text.isnot(None))\
         .filter(StudentAnswer.score.isnot(None))\
         .limit(limit)
        
        answers = query.all()
        
        if not answers:
            return pd.DataFrame()
        
        # Convert to list of dictionaries for feature extraction
        answer_data = []
        for a in answers:
            answer_data.append({
                'id': a.id,
                'student_id': a.student_id,
                'question_id': a.question_id,
                'question_text': a.question_text,
                'question_type': a.question_type,
                'answer_text': a.answer_text,
                'correct_answer': a.correct_answer,
                'score': a.score,
                'max_score': a.max_score,
                'time_taken': a.time_taken,
                'attempt_number': a.attempt_number,
                'subject': a.subject
            })
        
        # Extract features
        features_df = self.feature_engineer.create_feature_matrix(answer_data)
        
        return features_df
    
    def get_question_performance_data(self, question_id: int) -> Dict[str, Any]:
        """
        Get performance data for a specific question
        """
        # Get all answers for this question
        answers = self.db.query(StudentAnswer).filter(
            StudentAnswer.question_id == question_id
        ).all()
        
        if not answers:
            return {}
        
        # Get question details
        question = self.db.query(Question).filter(Question.id == question_id).first()
        
        if not question:
            return {}
        
        # Convert to format for feature extraction
        answer_data = []
        for a in answers:
            answer_data.append({
                'student_id': a.student_id,
                'score': a.score,
                'max_score': a.max_score,
                'time_taken': a.time_taken,
                'attempt_number': a.attempt_number
            })
        
        # Extract performance features
        performance_features = self.feature_engineer.extract_performance_features(answer_data)
        
        # Return just the numeric features for now
        # TODO: Add metadata handling in a separate method
        return performance_features
    
    def analyze_common_mistakes(self, question_id: int, min_frequency: int = 3) -> List[Dict[str, Any]]:
        """
        Analyze common mistakes for a question
        """
        # Get incorrect answers
        incorrect_answers = self.db.query(StudentAnswer).filter(
            StudentAnswer.question_id == question_id,
            StudentAnswer.score < StudentAnswer.max_score * 0.5  # Less than 50% correct
        ).all()
        
        if not incorrect_answers:
            return []
        
        # Group similar answers (simple approach using exact matches)
        answer_groups = {}
        for answer in incorrect_answers:
            answer_text = (answer.answer_text or "").strip().lower()
            
            if answer_text in answer_groups:
                answer_groups[answer_text]['count'] += 1
                answer_groups[answer_text]['scores'].append(answer.score / answer.max_score)
            else:
                answer_groups[answer_text] = {
                    'count': 1,
                    'scores': [answer.score / answer.max_score],
                    'original_text': answer.answer_text
                }
        
        # Filter by frequency and format results
        common_mistakes = []
        for answer_text, data in answer_groups.items():
            if data['count'] >= min_frequency:
                common_mistakes.append({
                    'mistake_text': data['original_text'],
                    'frequency': data['count'],
                    'avg_score': np.mean(data['scores']),
                    'student_count': data['count']
                })
        
        # Sort by frequency
        common_mistakes.sort(key=lambda x: x['frequency'], reverse=True)
        
        return common_mistakes
    
    def identify_comprehension_issues(self, question_id: int) -> List[str]:
        """
        Identify potential comprehension issues based on answer patterns
        """
        issues = []
        
        # Get performance data
        performance = self.get_question_performance_data(question_id)
        
        if not performance:
            return issues
        
        # Check various indicators
        if performance.get('avg_score', 1) < 0.4:
            issues.append("Low average score indicates fundamental comprehension issues")
        
        if performance.get('pass_rate', 1) < 0.3:
            issues.append("Low pass rate suggests question may be too difficult or unclear")
        
        if performance.get('std_time', 0) > performance.get('avg_time', 1) * 0.8:
            issues.append("High time variance suggests some students struggle with question interpretation")
        
        if performance.get('avg_time', 0) > 300:  # 5 minutes
            issues.append("High average completion time may indicate complexity issues")
        
        # Analyze common mistakes
        common_mistakes = self.analyze_common_mistakes(question_id)
        if len(common_mistakes) > 0:
            mistake_rate = sum(m['frequency'] for m in common_mistakes) / performance.get('total_attempts', 1)
            if mistake_rate > 0.3:
                issues.append(f"High rate of common mistakes ({mistake_rate:.1%}) suggests specific misconceptions")
        
        return issues
    
    def prepare_prediction_data(self, question_text: str, question_type: Optional[str] = None,
                              answer_text: Optional[str] = None, correct_answer: Optional[str] = None) -> pd.DataFrame:
        """
        Prepare data for making predictions on new questions/answers
        """
        data = [{
            'question_text': question_text,
            'question_type': question_type,
            'answer_text': answer_text,
            'correct_answer': correct_answer
        }]
        
        # Remove None values
        data[0] = {k: v for k, v in data[0].items() if v is not None}
        
        return self.feature_engineer.create_feature_matrix(data)
    
    def update_question_analytics(self, question_id: int, predictions: Dict[str, Any]):
        """
        Update or create analytics record for a question
        """
        # Check if analytics record exists
        analytics = self.db.query(QuestionAnalytics).filter(
            QuestionAnalytics.question_id == question_id
        ).first()
        
        performance_data = self.get_question_performance_data(question_id)
        comprehension_issues = self.identify_comprehension_issues(question_id)
        common_mistakes = self.analyze_common_mistakes(question_id)
        
        analytics_data = {
            'question_id': question_id,
            'predicted_difficulty': predictions.get('predicted_difficulty'),
            'avg_score': performance_data.get('avg_score'),
            'completion_rate': performance_data.get('pass_rate'),
            'comprehension_issues': '; '.join(comprehension_issues),
            'common_mistakes': str(common_mistakes[:3]),  # Top 3 mistakes
            'updated_at': datetime.utcnow()
        }
        
        if analytics:
            # Update existing record
            for key, value in analytics_data.items():
                if key != 'question_id':  # Don't update the ID
                    setattr(analytics, key, value)
        else:
            # Create new record
            analytics = QuestionAnalytics(**analytics_data)
            self.db.add(analytics)
        
        self.db.commit()
        return analytics
    
    def get_subject_performance_summary(self, subject: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance summary by subject
        """
        query = self.db.query(
            Question.subject,
            func.count(StudentAnswer.id).label('total_answers'),
            func.avg(StudentAnswer.score / StudentAnswer.max_score).label('avg_score'),
            func.count(func.distinct(Question.id)).label('question_count'),
            func.count(func.distinct(StudentAnswer.student_id)).label('student_count')
        ).join(StudentAnswer, Question.id == StudentAnswer.question_id)
        
        if subject:
            query = query.filter(Question.subject == subject)
        
        query = query.group_by(Question.subject)
        
        results = query.all()
        
        summary = {}
        for result in results:
            summary[result.subject] = {
                'total_answers': result.total_answers,
                'avg_score': float(result.avg_score) if result.avg_score else 0,
                'question_count': result.question_count,
                'student_count': result.student_count
            }
        
        return summary
