#!/usr/bin/env python3
"""
Test Script for Yinizai ML Service API
Tests all endpoints and validates responses match documentation
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_status():
    """Test system status endpoint"""
    print("\n📊 Testing system status...")
    try:
        response = requests.get(f"{BASE_URL}/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service Status: {data['service_status']}")
            print(f"✅ Database Connected: {data['database_connected']}")
            print(f"✅ Total Questions: {data['total_questions_analyzed']}")
            print(f"✅ Models Loaded: {len(data['loaded_models'])}")
            return True
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return False

def test_question_analysis():
    """Test question difficulty analysis"""
    print("\n🤔 Testing question analysis...")
    
    test_request = {
        "question_text": "What is the capital of France?",
        "question_type": "short_answer",
        "subject": "Geography"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze/question",
            headers={"Content-Type": "application/json"},
            json=test_request
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Question Analysis Success!")
            print(f"   Difficulty: {data['difficulty_prediction']['predicted_difficulty']}")
            print(f"   Confidence: {data['difficulty_prediction']['confidence']:.2f}")
            return True
        else:
            print(f"❌ Question analysis failed: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Question analysis error: {e}")
        return False

def test_answer_analysis():
    """Test answer analysis"""
    print("\n✍️ Testing answer analysis...")
    
    test_request = {
        "question_text": "What is the capital of France?",
        "answer_text": "Paris is the capital city of France.",
        "correct_answer": "Paris",
        "time_taken": 45
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze/answer",
            headers={"Content-Type": "application/json"},
            json=test_request
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Answer Analysis Success!")
            print(f"   Predicted Score: {data['score_prediction']['predicted_score']:.1f}")
            print(f"   Comprehension Level: {data['comprehension_analysis']['comprehension_cluster']}")
            return True
        else:
            print(f"❌ Answer analysis failed: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Answer analysis error: {e}")
        return False

def train_models():
    """Train all ML models"""
    print("\n🧠 Training ML models...")
    
    models = ["difficulty", "score", "comprehension"]
    trained = 0
    
    for model_type in models:
        print(f"   Training {model_type} model...")
        try:
            response = requests.post(
                f"{BASE_URL}/train/{model_type}",
                headers={"Content-Type": "application/json"},
                json={
                    "model_type": model_type,
                    "min_samples": 10,
                    "retrain": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["training_success"]:
                    print(f"   ✅ {model_type} model trained successfully")
                    trained += 1
                else:
                    print(f"   ⚠️  {model_type} model training: {data['message']}")
            else:
                print(f"   ❌ {model_type} training failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {model_type} training error: {e}")
    
    return trained

def main():
    """Main test function"""
    print("🚀 Yinizai ML Service API Test Suite")
    print("=" * 50)
    
    # Test basic endpoints
    if not test_health():
        print("❌ Service is not running. Please start it first.")
        return
    
    test_status()
    
    # Try to train models first
    print("\n🎯 Attempting to train models...")
    trained_count = train_models()
    
    if trained_count > 0:
        print(f"\n✅ {trained_count} models trained successfully!")
        print("   Waiting 2 seconds for models to load...")
        time.sleep(2)
        
        # Test analysis endpoints
        test_question_analysis()
        test_answer_analysis()
    else:
        print("\n⚠️  No models were trained. Trying analysis anyway...")
        test_question_analysis()
        test_answer_analysis()
    
    print("\n🎉 Test suite completed!")
    print("\n💡 To view interactive API docs: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
