import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, mean_squared_error, r2_score
from sklearn.cluster import KMeans
import joblib
import os
from typing import Dict, List, Tuple, Any
from datetime import datetime

class MLModels:
    def __init__(self, model_path: str = "./trained_models/"):
        self.model_path = model_path
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self._model_cache = {}  # Lazy loading cache
        
        # Ensure model directory exists
        os.makedirs(model_path, exist_ok=True)
    
    def _get_model(self, model_name: str):
        """Lazy load models to save memory"""
        if model_name not in self._model_cache:
            model_file = os.path.join(self.model_path, f"{model_name}_model.joblib")
            if os.path.exists(model_file):
                self._model_cache[model_name] = joblib.load(model_file)
            else:
                return None
        return self._model_cache.get(model_name)
    
    def _clear_model_cache(self):
        """Clear model cache to free memory"""
        self._model_cache.clear()
    
    def train_difficulty_predictor(self, training_data: pd.DataFrame, target_column: str = 'difficulty_level') -> Dict[str, Any]:
        """
        Train a model to predict question difficulty based on question features
        """
        print(f"Training difficulty predictor with {len(training_data)} samples...")
        
        # Prepare features and target
        feature_columns = [col for col in training_data.columns if col not in [target_column, 'id', 'question_id', 'student_id']]
        X = training_data[feature_columns]
        y = training_data[target_column]
        
        # Encode target labels
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)
        self.label_encoders['difficulty'] = le
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['difficulty'] = scaler
        
        # Train Random Forest model
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        rf_model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        train_score = rf_model.score(X_train_scaled, y_train)
        test_score = rf_model.score(X_test_scaled, y_test)
        
        y_pred = rf_model.predict(X_test_scaled)
        
        # Store model
        self.models['difficulty_predictor'] = rf_model
        
        # Save models
        self._save_model('difficulty_predictor', rf_model)
        self._save_model('difficulty_scaler', scaler)
        self._save_model('difficulty_encoder', le)
        
        # Feature importance
        feature_importance = dict(zip(feature_columns, rf_model.feature_importances_))
        
        results = {
            'model_type': 'RandomForestClassifier',
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'feature_importance': feature_importance,
            'classification_report': classification_report(y_test, y_pred, target_names=le.classes_),
            'classes': le.classes_.tolist()
        }
        
        print(f"Difficulty predictor trained. Test accuracy: {test_score:.3f}")
        return results
    
    def train_score_predictor(self, training_data: pd.DataFrame, target_column: str = 'score_ratio') -> Dict[str, Any]:
        """
        Train a model to predict student score based on answer and question features
        """
        print(f"Training score predictor with {len(training_data)} samples...")
        
        # Prepare features and target
        feature_columns = [col for col in training_data.columns if col not in [target_column, 'id', 'question_id', 'student_id', 'score', 'max_score']]
        X = training_data[feature_columns]
        y = training_data[target_column]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['score'] = scaler
        
        # Train Random Forest Regressor
        rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        rf_model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        train_score = rf_model.score(X_train_scaled, y_train)
        test_score = rf_model.score(X_test_scaled, y_test)
        
        y_pred = rf_model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        
        # Store model
        self.models['score_predictor'] = rf_model
        
        # Save models
        self._save_model('score_predictor', rf_model)
        self._save_model('score_scaler', scaler)
        
        # Feature importance
        feature_importance = dict(zip(feature_columns, rf_model.feature_importances_))
        
        results = {
            'model_type': 'RandomForestRegressor',
            'train_r2': train_score,
            'test_r2': test_score,
            'rmse': rmse,
            'mse': mse,
            'feature_importance': feature_importance
        }
        
        print(f"Score predictor trained. Test R²: {test_score:.3f}, RMSE: {rmse:.3f}")
        return results
    
    def train_comprehension_analyzer(self, training_data: pd.DataFrame, n_clusters: int = 5) -> Dict[str, Any]:
        """
        Train a clustering model to identify comprehension patterns
        """
        print(f"Training comprehension analyzer with {len(training_data)} samples...")
        
        # Prepare features (exclude non-numeric columns)
        feature_columns = training_data.select_dtypes(include=[np.number]).columns
        feature_columns = [col for col in feature_columns if col not in ['id', 'question_id', 'student_id']]
        X = training_data[feature_columns]
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['comprehension'] = scaler
        
        # Train K-Means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
        
        # Store model
        self.models['comprehension_analyzer'] = kmeans
        
        # Save models
        self._save_model('comprehension_analyzer', kmeans)
        self._save_model('comprehension_scaler', scaler)
        
        # Analyze clusters
        training_data_with_clusters = training_data.copy()
        training_data_with_clusters['cluster'] = cluster_labels
        
        cluster_analysis = {}
        for i in range(n_clusters):
            cluster_data = training_data_with_clusters[training_data_with_clusters['cluster'] == i]
            
            if 'score_ratio' in cluster_data.columns:
                avg_score = cluster_data['score_ratio'].mean()
                score_std = cluster_data['score_ratio'].std()
            else:
                avg_score = score_std = 0
            
            cluster_analysis[f'cluster_{i}'] = {
                'size': len(cluster_data),
                'avg_score': avg_score,
                'score_std': score_std,
                'characteristics': self._analyze_cluster_characteristics(cluster_data, feature_columns)
            }
        
        results = {
            'model_type': 'KMeans',
            'n_clusters': n_clusters,
            'cluster_analysis': cluster_analysis,
            'inertia': kmeans.inertia_
        }
        
        print(f"Comprehension analyzer trained with {n_clusters} clusters")
        return results
    
    def predict_difficulty(self, features: pd.DataFrame) -> List[Dict[str, Any]]:
        """Predict difficulty for new questions"""
        if 'difficulty_predictor' not in self.models:
            self._load_model('difficulty_predictor')
        
        model = self.models['difficulty_predictor']
        scaler = self.scalers.get('difficulty')
        encoder = self.label_encoders.get('difficulty')
        
        if model is None or scaler is None or encoder is None:
            raise ValueError("Difficulty prediction model not trained or loaded")
        
        # Scale features
        X_scaled = scaler.transform(features)
        
        # Make predictions
        predictions = model.predict(X_scaled)
        probabilities = model.predict_proba(X_scaled)
        
        results = []
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            difficulty = encoder.inverse_transform([pred])[0]
            confidence = max(prob)
            
            results.append({
                'predicted_difficulty': difficulty,
                'confidence': confidence,
                'probabilities': dict(zip(encoder.classes_, prob))
            })
        
        return results
    
    def predict_score(self, features: pd.DataFrame) -> List[float]:
        """Predict scores for new answers"""
        if 'score_predictor' not in self.models:
            self._load_model('score_predictor')
        
        model = self.models['score_predictor']
        scaler = self.scalers.get('score')
        
        if model is None or scaler is None:
            raise ValueError("Score prediction model not trained or loaded")
        
        # Scale features
        X_scaled = scaler.transform(features)
        
        # Make predictions
        predictions = model.predict(X_scaled)
        
        # Ensure predictions are between 0 and 1
        predictions = np.clip(predictions, 0, 1)
        
        return predictions.tolist()
    
    def analyze_comprehension(self, features: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze comprehension patterns"""
        if 'comprehension_analyzer' not in self.models:
            self._load_model('comprehension_analyzer')
        
        model = self.models['comprehension_analyzer']
        scaler = self.scalers.get('comprehension')
        
        if model is None or scaler is None:
            raise ValueError("Comprehension analyzer model not trained or loaded")
        
        # Scale features
        X_scaled = scaler.transform(features)
        
        # Make predictions
        cluster_labels = model.predict(X_scaled)
        distances = model.transform(X_scaled)
        
        results = []
        for i, (cluster, dist) in enumerate(zip(cluster_labels, distances)):
            # Find distance to assigned cluster
            cluster_distance = dist[cluster]
            
            results.append({
                'comprehension_cluster': int(cluster),
                'cluster_confidence': float(1 / (1 + cluster_distance)),  # Convert distance to confidence
                'cluster_distances': dist.tolist()
            })
        
        return results
    
    def _analyze_cluster_characteristics(self, cluster_data: pd.DataFrame, feature_columns: List[str]) -> Dict[str, float]:
        """Analyze characteristics of a cluster"""
        characteristics = {}
        
        for col in feature_columns:
            if col in cluster_data.columns:
                characteristics[col] = {
                    'mean': float(cluster_data[col].mean()),
                    'std': float(cluster_data[col].std())
                }
        
        return characteristics
    
    def _save_model(self, name: str, model: Any):
        """Save a model to disk"""
        filepath = os.path.join(self.model_path, f"{name}.joblib")
        joblib.dump(model, filepath)
        print(f"Model saved: {filepath}")
    
    def _load_model(self, name: str) -> Any:
        """Load a model from disk"""
        filepath = os.path.join(self.model_path, f"{name}.joblib")
        
        if os.path.exists(filepath):
            model = joblib.load(filepath)
            
            if name.endswith('_scaler'):
                model_key = name.replace('_scaler', '')
                self.scalers[model_key] = model
            elif name.endswith('_encoder'):
                model_key = name.replace('_encoder', '')
                self.label_encoders[model_key] = model
            else:
                self.models[name] = model
            
            print(f"Model loaded: {filepath}")
            return model
        else:
            print(f"Model file not found: {filepath}")
            return None
    
    def load_all_models(self):
        """Load all available models"""
        model_files = [f for f in os.listdir(self.model_path) if f.endswith('.joblib')]
        
        for file in model_files:
            name = file.replace('.joblib', '')
            self._load_model(name)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        info = {
            'loaded_models': list(self.models.keys()),
            'loaded_scalers': list(self.scalers.keys()),
            'loaded_encoders': list(self.label_encoders.keys()),
            'model_path': self.model_path
        }
        
        # Add file information
        if os.path.exists(self.model_path):
            model_files = [f for f in os.listdir(self.model_path) if f.endswith('.joblib')]
            info['available_model_files'] = model_files
        
        return info
