import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

class PerformanceBasedDifficultyAnalyzer:
    """
    Analyzes student performance data to determine question difficulty dynamically
    This replaces pre-labeled difficulty with actual performance metrics
    """
    
    def __init__(self):
        self.difficulty_thresholds = {
            'score_thresholds': {
                'easy': 0.8,    # 80%+ average score = easy
                'medium_high': 0.65,  # 65-80% = medium-high  
                'medium': 0.5,  # 50-65% = medium
                'medium_low': 0.35,   # 35-50% = medium-low
                'hard': 0.35   # <35% = hard
            },
            'variance_thresholds': {
                'low': 0.15,    # Low variance in scores
                'medium': 0.25, # Medium variance
                'high': 0.35    # High variance (confusing question)
            },
            'time_thresholds': {
                'quick': 60,    # <1 minute = very easy
                'normal': 180,  # 1-3 minutes = normal
                'slow': 300,    # 3-5 minutes = complex
                'very_slow': 600 # >5 minutes = very complex
            }
        }
    
    def calculate_question_difficulty(self, performance_data: Dict) -> Dict[str, Any]:
        """
        Calculate difficulty based on actual student performance
        
        Args:
            performance_data: Dict containing:
                - avg_score_ratio: Average score (0-1)
                - score_std: Standard deviation of scores
                - avg_time: Average completion time (seconds)
                - time_std: Standard deviation of completion time
                - total_attempts: Number of attempts
                - unique_students: Number of unique students
                - pass_rate: Percentage who got >60% correct
        
        Returns:
            Dict with difficulty analysis
        """
        avg_score = performance_data.get('avg_score_ratio', 0)
        score_std = performance_data.get('score_std', 0)
        avg_time = performance_data.get('avg_time', 0)
        time_std = performance_data.get('time_std', 0)
        total_attempts = performance_data.get('total_attempts', 0)
        pass_rate = performance_data.get('pass_rate', 0)
        
        # Primary difficulty based on average score
        if avg_score >= self.difficulty_thresholds['score_thresholds']['easy']:
            base_difficulty = 'easy'
            difficulty_score = 1.0
        elif avg_score >= self.difficulty_thresholds['score_thresholds']['medium_high']:
            base_difficulty = 'medium'
            difficulty_score = 2.0
        elif avg_score >= self.difficulty_thresholds['score_thresholds']['medium']:
            base_difficulty = 'medium'
            difficulty_score = 3.0
        elif avg_score >= self.difficulty_thresholds['score_thresholds']['medium_low']:
            base_difficulty = 'hard'
            difficulty_score = 4.0
        else:
            base_difficulty = 'hard'
            difficulty_score = 5.0
        
        # Adjust based on score variance (high variance = confusing/inconsistent)
        variance_penalty = 0
        if score_std > self.difficulty_thresholds['variance_thresholds']['high']:
            variance_penalty = 0.5  # High variance makes it effectively harder
        elif score_std > self.difficulty_thresholds['variance_thresholds']['medium']:
            variance_penalty = 0.25
        
        # Adjust based on completion time
        time_penalty = 0
        if avg_time > self.difficulty_thresholds['time_thresholds']['very_slow']:
            time_penalty = 0.75  # Very slow = much harder
        elif avg_time > self.difficulty_thresholds['time_thresholds']['slow']:
            time_penalty = 0.5   # Slow = harder
        elif avg_time > self.difficulty_thresholds['time_thresholds']['normal']:
            time_penalty = 0.25  # Above normal = slightly harder
        
        # Calculate final difficulty score (1=easiest, 5=hardest)
        final_score = difficulty_score + variance_penalty + time_penalty
        final_score = min(5.0, max(1.0, final_score))  # Clamp to 1-5 range
        
        # Convert back to categorical
        if final_score <= 1.5:
            final_difficulty = 'easy'
        elif final_score <= 2.5:
            final_difficulty = 'medium_easy'
        elif final_score <= 3.5:
            final_difficulty = 'medium'
        elif final_score <= 4.5:
            final_difficulty = 'medium_hard'
        else:
            final_difficulty = 'hard'
        
        # Calculate confidence based on sample size
        confidence = min(1.0, total_attempts / 50.0)  # Full confidence at 50+ attempts
        
        # Generate insights
        insights = self._generate_difficulty_insights(
            avg_score, score_std, avg_time, time_std, total_attempts, pass_rate
        )
        
        return {
            'calculated_difficulty': final_difficulty,
            'difficulty_score': final_score,
            'confidence': confidence,
            'base_difficulty': base_difficulty,
            'performance_metrics': {
                'avg_score': avg_score,
                'score_variance': score_std,
                'avg_completion_time': avg_time,
                'time_variance': time_std,
                'pass_rate': pass_rate,
                'sample_size': total_attempts
            },
            'difficulty_factors': {
                'score_based': base_difficulty,
                'variance_penalty': variance_penalty,
                'time_penalty': time_penalty
            },
            'insights': insights
        }
    
    def _generate_difficulty_insights(self, avg_score: float, score_std: float, 
                                    avg_time: float, time_std: float, 
                                    total_attempts: int, pass_rate: float) -> List[str]:
        """Generate human-readable insights about question difficulty"""
        insights = []
        
        # Score-based insights
        if avg_score >= 0.9:
            insights.append("Question appears too easy - consider increasing complexity")
        elif avg_score <= 0.3:
            insights.append("Question appears very difficult - may need clarification")
        elif 0.4 <= avg_score <= 0.6:
            insights.append("Good difficulty level - appropriately challenging")
        
        # Variance insights
        if score_std > 0.3:
            insights.append("High score variance suggests question may be ambiguous or confusing")
        elif score_std < 0.1:
            insights.append("Low score variance - students consistently understand or don't understand")
        
        # Time-based insights
        if avg_time > 600:  # 10+ minutes
            insights.append("Long completion time - question may be too complex or unclear")
        elif avg_time < 30:  # <30 seconds
            insights.append("Very quick completion - question might be too simple")
        
        if time_std > avg_time * 0.8:  # High relative time variance
            insights.append("High time variance - some students struggle while others don't")
        
        # Pass rate insights
        if pass_rate < 0.3:
            insights.append("Low pass rate - consider providing additional learning resources")
        elif pass_rate > 0.95:
            insights.append("Very high pass rate - question effectiveness is limited")
        
        # Sample size insights
        if total_attempts < 10:
            insights.append("Small sample size - difficulty assessment may be unreliable")
        elif total_attempts > 100:
            insights.append("Large sample size - difficulty assessment is highly reliable")
        
        return insights
    
    def batch_analyze_questions(self, questions_data: List[Dict]) -> pd.DataFrame:
        """
        Analyze difficulty for multiple questions
        
        Args:
            questions_data: List of dicts with performance data for each question
            
        Returns:
            DataFrame with difficulty analysis for all questions
        """
        results = []
        
        for q_data in questions_data:
            analysis = self.calculate_question_difficulty(q_data)
            result = {
                'question_id': q_data.get('question_id'),
                'question_text': q_data.get('question_text', '')[:50] + '...',
                **analysis
            }
            results.append(result)
        
        return pd.DataFrame(results)
    
    def get_difficulty_distribution(self, questions_analysis: List[Dict]) -> Dict[str, int]:
        """Get distribution of difficulties across questions"""
        difficulties = [q['calculated_difficulty'] for q in questions_analysis]
        distribution = {}
        
        for difficulty in ['easy', 'medium_easy', 'medium', 'medium_hard', 'hard']:
            distribution[difficulty] = difficulties.count(difficulty)
        
        return distribution
    
    def identify_problematic_questions(self, questions_analysis: List[Dict], 
                                     threshold_confidence: float = 0.7) -> List[Dict]:
        """
        Identify questions that may need review based on performance patterns
        """
        problematic = []
        
        for q in questions_analysis:
            issues = []
            
            # Check for reliability issues
            if q['confidence'] < threshold_confidence:
                issues.append(f"Low confidence ({q['confidence']:.2f}) - need more data")
            
            # Check for extreme difficulties
            if q['calculated_difficulty'] == 'hard' and q['performance_metrics']['avg_score'] < 0.2:
                issues.append("Extremely low performance - question may be flawed")
            
            if q['calculated_difficulty'] == 'easy' and q['performance_metrics']['avg_score'] > 0.95:
                issues.append("Almost perfect scores - question too easy")
            
            # Check for inconsistency (high variance)
            if q['performance_metrics']['score_variance'] > 0.35:
                issues.append("High score variance - question may be ambiguous")
            
            if issues:
                problematic.append({
                    'question_id': q.get('question_id'),
                    'calculated_difficulty': q['calculated_difficulty'],
                    'issues': issues,
                    'performance_summary': q['performance_metrics']
                })
        
        return problematic
