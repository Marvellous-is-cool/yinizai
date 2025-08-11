"""
Initial database setup and sample data creation script
Run this after setting up your environment to create sample data for testing
"""

import os
import sys
from datetime import datetime, timedelta
import random
from faker import Faker

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import engine, SessionLocal, Base, Question, StudentAnswer
from sqlalchemy.orm import Session

fake = Faker()

def create_sample_questions():
    """Create sample questions for testing - WITHOUT pre-labeled difficulty"""
    sample_questions = [
        {
            "question_text": "What is the capital of France?",
            "question_type": "short_answer",
            "subject": "Geography",
            "correct_answer": "Paris",
            "points": 10
        },
        {
            "question_text": "Explain the process of photosynthesis and its importance in the ecosystem.",
            "question_type": "essay",
            "subject": "Biology",
            "correct_answer": "Photosynthesis is the process by which plants convert light energy into chemical energy...",
            "points": 25
        },
        {
            "question_text": "Solve for x: 2x + 5 = 13",
            "question_type": "short_answer",
            "subject": "Mathematics",
            "correct_answer": "x = 4",
            "points": 15
        },
        {
            "question_text": "What programming language is primarily used for data science?",
            "question_type": "multiple_choice",
            "subject": "Computer Science",
            "correct_answer": "Python",
            "points": 10
        },
        {
            "question_text": "Describe Newton's first law of motion",
            "question_type": "essay", 
            "subject": "Physics",
            "correct_answer": "An object at rest stays at rest and an object in motion stays in motion...",
            "points": 20
        }
    ]
    
    return sample_questions

def create_sample_answers(db: Session, questions_data):
    """Create realistic sample answers for each question"""
    
    # Sample correct and incorrect responses
    sample_responses = {
        "correct": [
            "Paris", "1945", "CO2 (carbon dioxide)", "x = 4", "True",
            "Photosynthesis is the process by which plants use sunlight to convert carbon dioxide and water into glucose and oxygen.",
            "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
            "Hamlet is a tragedy by William Shakespeare about a Danish prince seeking revenge for his father's murder.",
            "Newton's first law states that an object at rest stays at rest and an object in motion stays in motion unless acted upon by an external force.",
            "Python"
        ],
        "incorrect": [
            "London", "1944", "CO2", "x = 3", "False",
            "Photosynthesis is when plants breathe oxygen and make carbon dioxide.",
            "def factorial(n):\n    return n * n",
            "Hamlet is a comedy by Shakespeare about a happy prince who gets married.",
            "Newton's laws are about gravity. Everything falls down because of gravity.",
            "Java"
        ]
    }
    
    for i, question_data in enumerate(questions_data):
        question = db.query(Question).filter(Question.id == question_data["id"]).first()
        if not question:
            continue
            
        # Create 20-30 sample answers per question
        num_answers = random.randint(20, 30)
        
        for j in range(num_answers):
            # 70% correct, 30% incorrect for realistic data
            is_correct = random.random() < 0.7
            
            if is_correct and i < len(sample_responses["correct"]):
                answer_text = sample_responses["correct"][i]
                score_ratio = random.uniform(0.8, 1.0)  # High score for correct
            elif i < len(sample_responses["incorrect"]):
                answer_text = sample_responses["incorrect"][i]
                score_ratio = random.uniform(0.0, 0.4)  # Low score for incorrect
            else:
                # Generate random answer
                answer_text = f"Sample answer {j} for question {i}"
                score_ratio = random.uniform(0.2, 0.9)
            
            # Calculate actual score
            max_score = float(question_data["points"])
            actual_score = score_ratio * max_score
            
            # Realistic time taken (30 seconds to 10 minutes based on question type)
            if question_data["question_type"] == "essay":
                time_taken = random.randint(180, 600)  # 3-10 minutes
            elif question_data["question_type"] == "multiple_choice":
                time_taken = random.randint(15, 120)   # 15 seconds - 2 minutes
            else:
                time_taken = random.randint(30, 300)   # 30 seconds - 5 minutes
            
            # Create answer
            answer = StudentAnswer(
                student_id=random.randint(1, 100),  # 100 different students
                question_id=question_data["id"],
                answer_text=answer_text,
                score=actual_score,
                max_score=max_score,
                time_taken=time_taken,
                attempt_number=1,
                created_at=fake.date_time_between(start_date='-30d', end_date='now')
            )
            
            db.add(answer)
    
    db.commit()
    print(f"Created sample answers for {len(questions_data)} questions")

def setup_database():
    """Set up the database with sample data"""
    print("Setting up database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created")
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if we already have data
        existing_questions = db.query(Question).count()
        if existing_questions > 0:
            print(f"Database already has {existing_questions} questions")
            response = input("Do you want to add more sample data? (y/n): ")
            if response.lower() != 'y':
                return
        
        # Create sample questions
        sample_questions = create_sample_questions()
        question_objects = []
        
        for q_data in sample_questions:
            question = Question(
                question_text=q_data["question_text"],
                question_type=q_data["question_type"],
                subject=q_data["subject"],
                correct_answer=q_data["correct_answer"],
                points=q_data["points"],
                created_at=fake.date_time_between(start_date='-60d', end_date='-30d')
            )
            db.add(question)
            question_objects.append(question)
        
        db.commit()
        
        # Get the created question IDs
        for i, question in enumerate(question_objects):
            sample_questions[i]["id"] = question.id
        
        print(f"Created {len(sample_questions)} sample questions")
        
        # Create sample answers
        create_sample_answers(db, sample_questions)
        
        print("Database setup completed successfully!")
        print(f"Total questions: {db.query(Question).count()}")
        print(f"Total answers: {db.query(StudentAnswer).count()}")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_database()
