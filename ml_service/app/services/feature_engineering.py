import pandas as pd
import numpy as np
import nltk
import spacy
import textstat
import re
from typing import List, Dict, Any, Optional
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from textblob import TextBlob

class FeatureEngineer:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
            
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon', quiet=True)
        
        # Use lazy loading for spaCy model to save memory
        self._nlp = None
        
        # Initialize NLTK components
        from nltk.corpus import stopwords
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        
        self.stop_words = set(stopwords.words('english'))
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
    
    @property
    def nlp(self):
        """Lazy load spaCy model"""
        if self._nlp is None:
            try:
                # Try smaller model first for memory efficiency
                import spacy
                self._nlp = spacy.load("en_core_web_sm", disable=["parser", "ner", "textcat"])
            except (OSError, ImportError) as e:
                # Fallback to basic English model
                try:
                    import spacy.lang.en
                    self._nlp = spacy.lang.en.English()
                except (ImportError, Exception):
                    # If spaCy completely fails, disable NLP features
                    self._nlp = False  # Use False to indicate failed loading
        return self._nlp if self._nlp is not False else None
    
    def extract_text_features(self, text: str) -> Dict[str, float]:
        """Extract various text features from a given text"""
        if not text or text.strip() == "":
            return self._get_empty_features()
        
        features = {}
        
        # Basic text statistics
        features['char_count'] = len(text)
        features['word_count'] = len(text.split())
        features['sentence_count'] = len(nltk.sent_tokenize(text))
        features['paragraph_count'] = len([p for p in text.split('\n\n') if p.strip()])
        
        # Average lengths
        words = text.split()
        features['avg_word_length'] = np.mean([len(word) for word in words]) if words else 0
        sentences = nltk.sent_tokenize(text)
        features['avg_sentence_length'] = np.mean([len(sent.split()) for sent in sentences]) if sentences else 0
        
        # Readability scores
        features['flesch_reading_ease'] = textstat.flesch_reading_ease(text)
        features['flesch_kincaid_grade'] = textstat.flesch_kincaid_grade(text)
        features['gunning_fog'] = textstat.gunning_fog(text)
        features['automated_readability_index'] = textstat.automated_readability_index(text)
        
        # Linguistic complexity
        features['syllable_count'] = textstat.syllable_count(text)
        features['polysyllable_count'] = textstat.polysyllabcount(text)
        features['difficult_words'] = textstat.difficult_words(text)
        
        # Vocabulary diversity
        unique_words = set(word.lower() for word in words if word.isalpha())
        features['unique_word_ratio'] = len(unique_words) / len(words) if words else 0
        
        # Punctuation and formatting
        features['punctuation_count'] = len([c for c in text if c in '.,;:!?'])
        features['uppercase_ratio'] = len([c for c in text if c.isupper()]) / len(text) if text else 0
        features['digit_count'] = len([c for c in text if c.isdigit()])
        
        # Sentiment analysis
        sentiment_scores = self.sentiment_analyzer.polarity_scores(text)
        features['sentiment_positive'] = sentiment_scores['pos']
        features['sentiment_negative'] = sentiment_scores['neg']
        features['sentiment_neutral'] = sentiment_scores['neu']
        features['sentiment_compound'] = sentiment_scores['compound']
        
        # spaCy features (if available)
        try:
            nlp_model = self.nlp
            if nlp_model is not None:
                doc = nlp_model(text)  # type: ignore
                features['noun_count'] = len([token for token in doc if token.pos_ == 'NOUN'])
                features['verb_count'] = len([token for token in doc if token.pos_ == 'VERB'])
                features['adj_count'] = len([token for token in doc if token.pos_ == 'ADJ'])
                features['adv_count'] = len([token for token in doc if token.pos_ == 'ADV'])
                features['entity_count'] = len(doc.ents)
            else:
                # Fallback values when spaCy is not available
                features['noun_count'] = 0
                features['verb_count'] = 0
                features['adj_count'] = 0
                features['adv_count'] = 0
                features['entity_count'] = 0
        except Exception as e:
            # Safe fallback if spaCy fails
            features['noun_count'] = 0
            features['verb_count'] = 0
            features['adj_count'] = 0
            features['adv_count'] = 0
            features['entity_count'] = 0
        
        return features
    
    def extract_question_features(self, question_text: str, question_type: Optional[str] = None) -> Dict[str, float]:
        """Extract features specific to questions"""
        features = self.extract_text_features(question_text)
        
        # Question-specific features
        question_words = ['what', 'when', 'where', 'who', 'why', 'how', 'which', 'whom', 'whose']
        features['question_word_count'] = sum(1 for word in question_words if word in question_text.lower())
        features['has_question_mark'] = 1 if '?' in question_text else 0
        
        # Question type encoding
        if question_type:
            features['is_multiple_choice'] = 1 if question_type == 'multiple_choice' else 0
            features['is_short_answer'] = 1 if question_type == 'short_answer' else 0
            features['is_essay'] = 1 if question_type == 'essay' else 0
        
        return features
    
    def extract_answer_features(self, answer_text: str, question_text: Optional[str] = None, correct_answer: Optional[str] = None) -> Dict[str, float]:
        """Extract features specific to student answers"""
        features = self.extract_text_features(answer_text)
        
        # Answer-specific features
        if question_text:
            # Semantic similarity (simple word overlap)
            answer_words = set(answer_text.lower().split())
            question_words = set(question_text.lower().split())
            features['answer_question_overlap'] = len(answer_words.intersection(question_words)) / len(answer_words.union(question_words)) if answer_words.union(question_words) else 0
        
        if correct_answer:
            # Similarity to correct answer
            answer_words = set(answer_text.lower().split())
            correct_words = set(correct_answer.lower().split())
            features['correct_answer_similarity'] = len(answer_words.intersection(correct_words)) / len(answer_words.union(correct_words)) if answer_words.union(correct_words) else 0
        
        # Answer completeness indicators
        features['starts_with_capital'] = 1 if answer_text and answer_text[0].isupper() else 0
        features['ends_with_period'] = 1 if answer_text.endswith('.') else 0
        features['contains_numbers'] = 1 if any(char.isdigit() for char in answer_text) else 0
        
        return features
    
    def extract_performance_features(self, student_answers: List[Dict]) -> Dict[str, float]:
        """Extract features from a collection of student answers for a question"""
        if not student_answers:
            return {}
        
        scores = [answer['score'] / answer['max_score'] for answer in student_answers if answer['max_score'] > 0]
        times = [answer['time_taken'] for answer in student_answers if answer['time_taken'] > 0]
        
        features = {}
        
        if scores:
            features['avg_score'] = np.mean(scores)
            features['median_score'] = np.median(scores)
            features['std_score'] = np.std(scores)
            features['min_score'] = np.min(scores)
            features['max_score'] = np.max(scores)
            features['pass_rate'] = sum(1 for score in scores if score >= 0.6) / len(scores)  # Assuming 60% is passing
        
        if times:
            features['avg_time'] = np.mean(times)
            features['median_time'] = np.median(times)
            features['std_time'] = np.std(times)
        
        features['total_attempts'] = len(student_answers)
        features['unique_students'] = len(set(answer['student_id'] for answer in student_answers))
        
        return features
    
    def _get_empty_features(self) -> Dict[str, float]:
        """Return default feature values for empty text"""
        return {key: 0.0 for key in [
            'char_count', 'word_count', 'sentence_count', 'paragraph_count',
            'avg_word_length', 'avg_sentence_length', 'flesch_reading_ease',
            'flesch_kincaid_grade', 'gunning_fog', 'automated_readability_index',
            'syllable_count', 'polysyllable_count', 'difficult_words',
            'unique_word_ratio', 'punctuation_count', 'uppercase_ratio',
            'digit_count', 'sentiment_positive', 'sentiment_negative',
            'sentiment_neutral', 'sentiment_compound'
        ]}
    
    def create_feature_matrix(self, data: List[Dict]) -> pd.DataFrame:
        """Create a feature matrix from a list of text data"""
        features_list = []
        
        for item in data:
            if 'question_text' in item and 'answer_text' in item:
                # This is for answer analysis
                question_features = self.extract_question_features(
                    item['question_text'], 
                    item.get('question_type')
                )
                answer_features = self.extract_answer_features(
                    item['answer_text'],
                    item['question_text'],
                    item.get('correct_answer')
                )
                
                # Combine features
                combined_features = {**question_features, **answer_features}
                combined_features['score_ratio'] = item.get('score', 0) / item.get('max_score', 1)
                combined_features['time_taken'] = item.get('time_taken', 0)
                
                features_list.append(combined_features)
            
            elif 'question_text' in item:
                # This is for question difficulty prediction
                features = self.extract_question_features(
                    item['question_text'], 
                    item.get('question_type')
                )
                features_list.append(features)
        
        return pd.DataFrame(features_list).fillna(0)
