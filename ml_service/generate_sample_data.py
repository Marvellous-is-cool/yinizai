#!/usr/bin/env python3
"""
Sample Data Generator for Yinizai ML Service
This script generates realistic student test data to train the ML models.
"""

import random
import mysql.connector
from datetime import datetime, timedelta
from faker import Faker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

fake = Faker()

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'yinizai_user'),
        password=os.getenv('DB_PASSWORD', 'yinizai_password'),
        database=os.getenv('DB_NAME', 'yinizai_db')
    )

# Sample questions with different difficulty levels
SAMPLE_QUESTIONS = [
    # Easy Questions
    ("What is 2 + 2?", "multiple_choice", "Mathematics", "4", "easy"),
    ("What color is the sky?", "short_answer", "Science", "Blue", "easy"),
    ("How many days are in a week?", "short_answer", "General", "7", "easy"),
    ("What is the capital of the USA?", "multiple_choice", "Geography", "Washington D.C.", "easy"),
    ("What sound does a dog make?", "short_answer", "General", "Bark", "easy"),
    
    # Medium Questions  
    ("Explain the water cycle in 2-3 sentences.", "short_answer", "Science", "Water evaporates from oceans, condenses into clouds, and falls as precipitation.", "medium"),
    ("What is 15 × 12?", "short_answer", "Mathematics", "180", "medium"),
    ("Name three countries in Europe.", "short_answer", "Geography", "France, Germany, Italy", "medium"),
    ("What is photosynthesis?", "short_answer", "Biology", "The process plants use to make food from sunlight", "medium"),
    ("Who wrote Romeo and Juliet?", "short_answer", "Literature", "William Shakespeare", "medium"),
    
    # Hard Questions
    ("Derive the quadratic formula and explain each step.", "essay", "Mathematics", "x = (-b ± √(b²-4ac))/(2a), derived from completing the square...", "hard"),
    ("Analyze the causes and effects of World War I.", "essay", "History", "Multiple causes including imperialism, alliances, and nationalism led to...", "hard"),
    ("Explain quantum entanglement in detail.", "essay", "Physics", "Quantum entanglement is a phenomenon where particles become correlated...", "hard"),
    ("Compare and contrast capitalism and socialism.", "essay", "Economics", "Capitalism emphasizes private ownership while socialism emphasizes collective ownership...", "hard"),
    ("Discuss the impact of climate change on biodiversity.", "essay", "Environmental Science", "Climate change affects biodiversity through habitat loss, species migration...", "hard"),
]

def generate_student_answer(question_text, correct_answer, difficulty):
    """Generate realistic student answers based on question difficulty"""
    
    if difficulty == "easy":
        # Easy questions - mostly correct answers
        if random.random() < 0.8:  # 80% correct
            variations = [
                correct_answer,
                correct_answer.lower(),
                f"The answer is {correct_answer}",
                f"I think it's {correct_answer}",
            ]
            return random.choice(variations), random.randint(80, 100)
        else:
            # Wrong answers for easy questions
            wrong_answers = ["I don't know", "Not sure", "Maybe something else"]
            return random.choice(wrong_answers), random.randint(0, 40)
    
    elif difficulty == "medium":
        # Medium questions - mixed quality answers
        if random.random() < 0.6:  # 60% decent answers
            if random.random() < 0.7:  # 70% of decent answers are correct
                variations = [
                    correct_answer,
                    f"{correct_answer}. This is because...",
                    f"I believe {correct_answer} is the correct answer.",
                ]
                return random.choice(variations), random.randint(70, 95)
            else:
                # Partially correct
                partial_answers = [
                    f"Something related to {correct_answer.split()[0]}",
                    f"I think it involves {correct_answer.split()[-1]}",
                    "I'm not entirely sure but..."
                ]
                return random.choice(partial_answers), random.randint(40, 70)
        else:
            # Poor answers
            poor_answers = ["I don't know", "This is confusing", "Need more time"]
            return random.choice(poor_answers), random.randint(0, 30)
    
    else:  # hard
        # Hard questions - varied answer quality
        if random.random() < 0.3:  # 30% good answers
            good_answers = [
                f"{correct_answer} Additionally, this concept involves multiple factors...",
                f"This is a complex topic. {correct_answer} Furthermore...",
                f"From my understanding, {correct_answer} The reasoning behind this..."
            ]
            return random.choice(good_answers), random.randint(75, 100)
        elif random.random() < 0.5:  # 50% partial answers
            partial_answers = [
                f"I think {correct_answer.split('.')[0]} but I'm not completely sure about the details.",
                "This is partially related to what we studied in class...",
                "I remember something about this but need to think more..."
            ]
            return random.choice(partial_answers), random.randint(40, 75)
        else:  # Poor answers
            poor_answers = [
                "This question is too difficult for me",
                "I need more study time for this topic",
                "Can we review this in class?"
            ]
            return random.choice(poor_answers), random.randint(0, 40)

def generate_sample_data():
    """Generate and insert sample data into database"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🎯 Generating sample student test data...")
    
    # Insert questions
    question_ids = []
    for question_text, question_type, subject, correct_answer, difficulty in SAMPLE_QUESTIONS:
        cursor.execute("""
            INSERT INTO questions (question_text, question_type, subject, correct_answer, difficulty_level, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (question_text, question_type, subject, correct_answer, difficulty, datetime.now()))
        question_ids.append(cursor.lastrowid)
    
    print(f"📝 Added {len(SAMPLE_QUESTIONS)} questions")
    
    # Generate student answers (multiple students per question)
    students_per_question = random.randint(8, 15)  # 8-15 students per question
    total_answers = 0
    
    for question_id, (question_text, question_type, subject, correct_answer, difficulty) in zip(question_ids, SAMPLE_QUESTIONS):
        
        for student_num in range(students_per_question):
            student_id = f"student_{random.randint(1000, 9999)}"
            
            # Generate student answer
            answer_text, score = generate_student_answer(question_text, correct_answer, difficulty)
            max_score = 100
            
            # Generate realistic time taken based on difficulty
            if difficulty == "easy":
                time_taken = random.randint(30, 120)  # 30 seconds to 2 minutes
            elif difficulty == "medium":
                time_taken = random.randint(120, 300)  # 2 to 5 minutes  
            else:
                time_taken = random.randint(300, 900)  # 5 to 15 minutes
            
            # Insert answer
            cursor.execute("""
                INSERT INTO student_answers 
                (question_id, student_id, answer_text, score, max_score, time_taken, submitted_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                question_id, student_id, answer_text, score, max_score, 
                time_taken, datetime.now() - timedelta(days=random.randint(1, 30))
            ))
            
            total_answers += 1
    
    # Update question analytics
    for question_id in question_ids:
        cursor.execute("""
            SELECT AVG(score), COUNT(*), AVG(time_taken)
            FROM student_answers 
            WHERE question_id = %s
        """, (question_id,))
        
        avg_score, total_attempts, avg_time = cursor.fetchone()
        
        cursor.execute("""
            INSERT INTO question_analytics 
            (question_id, avg_score, total_attempts, avg_time_taken, last_updated)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                avg_score = VALUES(avg_score),
                total_attempts = VALUES(total_attempts),
                avg_time_taken = VALUES(avg_time_taken),
                last_updated = VALUES(last_updated)
        """, (question_id, avg_score or 0, total_attempts or 0, avg_time or 0, datetime.now()))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"👥 Generated {total_answers} student answers")
    print(f"📊 Updated analytics for {len(question_ids)} questions")
    print("✅ Sample data generation complete!")
    
    return len(question_ids), total_answers

def main():
    """Main function"""
    print("🚀 Yinizai ML Service - Sample Data Generator")
    print("=" * 50)
    
    try:
        questions_count, answers_count = generate_sample_data()
        
        print("\n🎉 SUCCESS! Sample data generated:")
        print(f"   • {questions_count} questions added")
        print(f"   • {answers_count} student answers generated") 
        print(f"   • Ready to train ML models")
        print("\n💡 Next steps:")
        print("   1. Run: curl -X POST http://localhost:8000/train/difficulty")
        print("   2. Run: curl -X POST http://localhost:8000/train/score") 
        print("   3. Run: curl -X POST http://localhost:8000/train/comprehension")
        print("   4. Test the API endpoints!")
        
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        print("💡 Make sure MySQL is running and database credentials are correct")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
