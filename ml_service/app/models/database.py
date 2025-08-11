from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class StudentAnswer(Base):
    __tablename__ = 'student_answers'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer)
    question_id = Column(Integer)
    answer_text = Column(Text)
    score = Column(Float)
    max_score = Column(Float)
    time_taken = Column(Integer)  # in seconds
    attempt_number = Column(Integer)
    created_at = Column(DateTime)

class Question(Base):
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    question_text = Column(Text)
    question_type = Column(String(50))  # multiple_choice, short_answer, essay
    subject = Column(String(100))
    correct_answer = Column(Text)
    points = Column(Integer)
    created_at = Column(DateTime)
    
    # Optional: Store externally labeled difficulty for comparison
    external_difficulty_label = Column(String(20))  # If you have teacher-assigned difficulty

class QuestionAnalytics(Base):
    __tablename__ = 'question_analytics'
    
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer)
    predicted_difficulty = Column(String(20))
    calculated_difficulty = Column(String(20))  # Based on student performance
    avg_score = Column(Float)
    completion_rate = Column(Float)
    score_std_dev = Column(Float)
    avg_completion_time = Column(Float)
    time_std_dev = Column(Float)
    total_attempts = Column(Integer)
    unique_students = Column(Integer)
    common_mistakes = Column(Text)
    comprehension_issues = Column(Text)
    updated_at = Column(DateTime)

# Database connection
DATABASE_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
