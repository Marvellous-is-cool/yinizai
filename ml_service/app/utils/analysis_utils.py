import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import io
import base64
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class VisualizationUtils:
    """Utilities for creating visualizations and insights"""
    
    @staticmethod
    def create_score_distribution_plot(scores: List[float], title: str = "Score Distribution") -> str:
        """Create a histogram of score distribution and return as base64 string"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(scores, bins=20, edgecolor='black', alpha=0.7)
            ax.set_xlabel('Score')
            ax.set_ylabel('Frequency')
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(fig)
            
            return image_base64
        except Exception as e:
            logger.error(f"Error creating score distribution plot: {str(e)}")
            return ""
    
    @staticmethod
    def create_difficulty_distribution_plot(difficulties: List[str], title: str = "Difficulty Distribution") -> str:
        """Create a bar plot of difficulty distribution"""
        try:
            difficulty_counts = pd.Series(difficulties).value_counts()
            
            fig, ax = plt.subplots(figsize=(8, 6))
            difficulty_counts.plot(kind='bar', ax=ax, color=['green', 'orange', 'red'])
            ax.set_xlabel('Difficulty Level')
            ax.set_ylabel('Number of Questions')
            ax.set_title(title)
            ax.tick_params(axis='x', rotation=45)
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(fig)
            
            return image_base64
        except Exception as e:
            logger.error(f"Error creating difficulty distribution plot: {str(e)}")
            return ""
    
    @staticmethod
    def create_performance_heatmap(performance_data: Dict[str, Dict[str, float]]) -> str:
        """Create a heatmap of performance across subjects/topics"""
        try:
            df = pd.DataFrame(performance_data).T
            
            fig, ax = plt.subplots(figsize=(12, 8))
            sns.heatmap(df, annot=True, cmap='RdYlGn', ax=ax, fmt='.2f')
            ax.set_title('Performance Heatmap')
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(fig)
            
            return image_base64
        except Exception as e:
            logger.error(f"Error creating performance heatmap: {str(e)}")
            return ""
    
    @staticmethod
    def create_word_cloud(texts: List[str], title: str = "Common Words") -> str:
        """Create a word cloud from text data"""
        try:
            combined_text = ' '.join(texts)
            
            wordcloud = WordCloud(
                width=800, 
                height=400, 
                background_color='white',
                max_words=100,
                colormap='viridis'
            ).generate(combined_text)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            ax.set_title(title)
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(fig)
            
            return image_base64
        except Exception as e:
            logger.error(f"Error creating word cloud: {str(e)}")
            return ""

class DataValidationUtils:
    """Utilities for data validation and cleaning"""
    
    @staticmethod
    def validate_question_data(question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean question data"""
        cleaned_data = question_data.copy()
        
        # Required fields
        required_fields = ['question_text']
        for field in required_fields:
            if field not in cleaned_data or not cleaned_data[field]:
                raise ValueError(f"Required field missing: {field}")
        
        # Clean text fields
        text_fields = ['question_text', 'correct_answer', 'subject']
        for field in text_fields:
            if field in cleaned_data and cleaned_data[field]:
                cleaned_data[field] = str(cleaned_data[field]).strip()
        
        # Validate question type
        valid_types = ['multiple_choice', 'short_answer', 'essay', 'true_false']
        if 'question_type' in cleaned_data:
            if cleaned_data['question_type'] not in valid_types:
                logger.warning(f"Unknown question type: {cleaned_data['question_type']}")
        
        return cleaned_data
    
    @staticmethod
    def validate_answer_data(answer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean answer data"""
        cleaned_data = answer_data.copy()
        
        # Required fields
        required_fields = ['answer_text', 'question_text']
        for field in required_fields:
            if field not in cleaned_data or not cleaned_data[field]:
                raise ValueError(f"Required field missing: {field}")
        
        # Clean text fields
        text_fields = ['answer_text', 'question_text', 'correct_answer']
        for field in text_fields:
            if field in cleaned_data and cleaned_data[field]:
                cleaned_data[field] = str(cleaned_data[field]).strip()
        
        # Validate numeric fields
        numeric_fields = ['score', 'max_score', 'time_taken']
        for field in numeric_fields:
            if field in cleaned_data:
                try:
                    cleaned_data[field] = float(cleaned_data[field])
                    if field in ['score', 'max_score'] and cleaned_data[field] < 0:
                        cleaned_data[field] = 0
                except (ValueError, TypeError):
                    logger.warning(f"Invalid numeric value for {field}: {cleaned_data[field]}")
                    cleaned_data[field] = 0
        
        return cleaned_data

class PerformanceUtils:
    """Utilities for performance analysis and insights"""
    
    @staticmethod
    def calculate_difficulty_metrics(scores: List[float]) -> Dict[str, float]:
        """Calculate various difficulty metrics from scores"""
        if not scores:
            return {}
        
        scores_array = np.array(scores)
        
        return {
            'mean_score': float(np.mean(scores_array)),
            'median_score': float(np.median(scores_array)),
            'std_score': float(np.std(scores_array)),
            'min_score': float(np.min(scores_array)),
            'max_score': float(np.max(scores_array)),
            'pass_rate': float(np.sum(scores_array >= 0.6) / len(scores_array)),
            'difficulty_index': float(1 - np.mean(scores_array)),  # Higher = more difficult
            'discrimination_index': float(np.std(scores_array))  # Higher = better discrimination
        }
    
    @staticmethod
    def identify_outliers(scores: List[float], method: str = 'iqr') -> List[int]:
        """Identify outlier indices in score data"""
        if not scores:
            return []
        
        scores_array = np.array(scores)
        
        if method == 'iqr':
            Q1 = np.percentile(scores_array, 25)
            Q3 = np.percentile(scores_array, 75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = np.where((scores_array < lower_bound) | (scores_array > upper_bound))[0]
        
        elif method == 'zscore':
            z_scores = np.abs((scores_array - np.mean(scores_array)) / np.std(scores_array))
            outliers = np.where(z_scores > 3)[0]
        
        else:
            outliers = np.array([])
        
        return outliers.tolist()
    
    @staticmethod
    def generate_performance_insights(performance_data: Dict[str, float]) -> List[str]:
        """Generate human-readable insights from performance data"""
        insights = []
        
        avg_score = performance_data.get('avg_score', 0)
        pass_rate = performance_data.get('pass_rate', 0)
        std_score = performance_data.get('std_score', 0)
        
        # Score-based insights
        if avg_score < 0.4:
            insights.append("Very low average score - consider reviewing question clarity or difficulty")
        elif avg_score < 0.6:
            insights.append("Below average performance - additional support may be needed")
        elif avg_score > 0.9:
            insights.append("Excellent performance - question may be too easy")
        
        # Pass rate insights
        if pass_rate < 0.3:
            insights.append("Low pass rate indicates significant comprehension issues")
        elif pass_rate > 0.95:
            insights.append("Very high pass rate - consider increasing difficulty")
        
        # Variability insights
        if std_score < 0.1:
            insights.append("Low score variability - all students performed similarly")
        elif std_score > 0.3:
            insights.append("High score variability - wide range of student understanding")
        
        # Time-based insights
        avg_time = performance_data.get('avg_time', 0)
        if avg_time > 300:  # 5 minutes
            insights.append("High completion time - question may be complex or unclear")
        elif avg_time < 30:  # 30 seconds
            insights.append("Very fast completion - question may be too simple")
        
        return insights
    
    @staticmethod
    def calculate_learning_progress(student_scores: List[Dict[str, Any]]) -> Dict[str, Union[float, int]]:
        """Calculate learning progress metrics for a student"""
        if not student_scores:
            return {}
        
        # Sort by timestamp or attempt number
        sorted_scores = sorted(student_scores, key=lambda x: x.get('created_at', x.get('attempt_number', 0)))
        
        scores = [s['score'] / s['max_score'] for s in sorted_scores if s['max_score'] > 0]
        
        if len(scores) < 2:
            return {'progress': 0.0, 'trend': 0.0}  # Return float for trend as well
        
        # Calculate trend
        x = np.arange(len(scores))
        slope, _ = np.polyfit(x, scores, 1)
        
        # Calculate progress metrics
        first_half_avg = np.mean(scores[:len(scores)//2])
        second_half_avg = np.mean(scores[len(scores)//2:])
        
        progress = {
            'slope': float(slope),
            'improvement': float(second_half_avg - first_half_avg),
            'consistency': float(1 - np.std(scores)),
            'current_level': float(scores[-1]),
            'best_performance': float(max(scores)),
            'attempts': len(scores)
        }
        
        # Determine trend
        if slope > 0.1:
            progress['trend'] = 'improving'
        elif slope < -0.1:
            progress['trend'] = 'declining'
        else:
            progress['trend'] = 'stable'
        
        return progress

class RecommendationEngine:
    """Generate recommendations based on analysis results"""
    
    @staticmethod
    def generate_question_recommendations(analysis_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations for question improvement"""
        recommendations = []
        
        difficulty = analysis_results.get('predicted_difficulty', '').lower()
        confidence = analysis_results.get('confidence', 1.0)
        
        if confidence < 0.7:
            recommendations.append("Low prediction confidence - consider reviewing question structure")
        
        if difficulty == 'hard':
            recommendations.append("Question predicted as difficult - ensure adequate preparation material is available")
            recommendations.append("Consider providing hints or scaffolding for struggling students")
        
        elif difficulty == 'easy':
            recommendations.append("Question may be too simple - consider adding complexity or depth")
        
        # Feature-based recommendations
        features = analysis_results.get('features_extracted', {})
        
        if features.get('word_count', 0) > 100:
            recommendations.append("Long question text - consider simplifying language")
        
        if features.get('flesch_reading_ease', 50) < 30:
            recommendations.append("Text may be difficult to read - simplify vocabulary and sentence structure")
        
        if features.get('question_word_count', 0) == 0:
            recommendations.append("No clear question words detected - ensure question is clearly stated")
        
        return recommendations
    
    @staticmethod
    def generate_student_recommendations(analysis_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations for student support"""
        recommendations = []
        
        predicted_score = analysis_results.get('predicted_score', 1.0)
        comprehension_cluster = analysis_results.get('comprehension_cluster', 0)
        
        if predicted_score < 0.5:
            recommendations.append("Student may struggle with this question - provide additional support")
            recommendations.append("Consider one-on-one tutoring or additional practice materials")
        
        elif predicted_score < 0.7:
            recommendations.append("Student performance may be below average - monitor progress closely")
        
        # Cluster-based recommendations
        if comprehension_cluster == 0:  # Assuming cluster 0 is low performers
            recommendations.append("Student shows patterns of low comprehension - fundamental review needed")
        elif comprehension_cluster == 1:  # Average performers
            recommendations.append("Student shows average comprehension - encourage continued practice")
        
        return recommendations
