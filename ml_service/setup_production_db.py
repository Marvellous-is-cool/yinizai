#!/usr/bin/env python3
"""
Production Database Setup Script
Run this once after deploying to initialize your production database
"""

import os
import sys
import mysql.connector
from urllib.parse import urlparse

def setup_production_database():
    """Set up production database with proper schema and initial data"""
    
    print("🗄️  Setting up production database...")
    
    # Get database connection details from environment
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME', 'yinizai_ml')
    }
    
    # Validate required environment variables
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your Render dashboard under Environment Variables")
        return False
    
    try:
        print(f"🔗 Connecting to {db_config['host']}:{db_config['port']}...")
        
        # Connect to MySQL
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print("✅ Database connection successful!")
        
        # Check if tables exist
        cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        if not existing_tables:
            print("📋 Creating database schema...")
            
            # Read and execute schema from DATABASE_SCHEMA.sql
            schema_file = os.path.join(os.path.dirname(__file__), '..', 'DATABASE_SCHEMA.sql')
            
            if os.path.exists(schema_file):
                with open(schema_file, 'r') as f:
                    schema_sql = f.read()
                
                # Split by statements and execute
                statements = schema_sql.split(';')
                for statement in statements:
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            cursor.execute(statement)
                        except mysql.connector.Error as e:
                            if "already exists" not in str(e):
                                print(f"⚠️  Schema warning: {e}")
                
                conn.commit()
                print("✅ Database schema created successfully!")
            else:
                print("⚠️  DATABASE_SCHEMA.sql not found, creating basic tables...")
                # Create basic tables if schema file is missing
                create_basic_tables(cursor)
                conn.commit()
        else:
            print(f"✅ Database already initialized with tables: {', '.join(existing_tables)}")
        
        # Check for sample data
        cursor.execute("SELECT COUNT(*) FROM questions")
        question_count = cursor.fetchone()[0]
        
        if question_count == 0:
            print("📊 No sample data found. To add sample data, run:")
            print("   curl -X POST https://your-service.onrender.com/setup/initialize")
        else:
            print(f"✅ Database has {question_count} questions ready for ML training")
        
        cursor.close()
        conn.close()
        
        print("🎉 Production database setup completed!")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("  1. Check your Aiven MySQL service is running")
        print("  2. Verify connection details in environment variables")
        print("  3. Ensure your IP is whitelisted in Aiven (or use 0.0.0.0/0)")
        print("  4. Check SSL requirements in Aiven settings")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_basic_tables(cursor):
    """Create basic tables if schema file is not available"""
    
    basic_schema = """
    CREATE TABLE IF NOT EXISTS questions (
        id INT PRIMARY KEY AUTO_INCREMENT,
        question_text TEXT NOT NULL,
        question_type ENUM('multiple_choice', 'short_answer', 'essay') NOT NULL,
        subject VARCHAR(100),
        correct_answer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS student_answers (
        id INT PRIMARY KEY AUTO_INCREMENT,
        question_id INT NOT NULL,
        student_id VARCHAR(100) NOT NULL,
        answer_text TEXT NOT NULL,
        score FLOAT NOT NULL,
        max_score FLOAT NOT NULL,
        time_taken INT DEFAULT 0,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
    );
    
    CREATE TABLE IF NOT EXISTS question_analytics (
        id INT PRIMARY KEY AUTO_INCREMENT,
        question_id INT NOT NULL UNIQUE,
        avg_score FLOAT,
        total_attempts INT DEFAULT 0,
        avg_time_taken FLOAT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
    );
    """
    
    statements = basic_schema.split(';')
    for statement in statements:
        statement = statement.strip()
        if statement:
            cursor.execute(statement)

if __name__ == "__main__":
    print("🚀 Production Database Setup")
    print("=" * 40)
    
    success = setup_production_database()
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("\n📋 Next steps:")
        print("  1. Deploy your service to Render")  
        print("  2. Initialize sample data via API")
        print("  3. Train ML models")
        print("  4. Start using the service!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1)
