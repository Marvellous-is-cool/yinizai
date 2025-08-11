#!/usr/bin/env python3
"""
Simple database initialization script for Yinizai ML Service
Creates the necessary tables for the ML analysis service
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
sys.path.insert(0, str(app_dir))

try:
    from models.database import engine, Base, Question, StudentAnswer
    from sqlalchemy import text
    
    def create_tables():
        """Create all database tables"""
        print("🔧 Creating database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Test connection and show tables
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            print(f"📊 Created tables: {', '.join(tables)}")
    
    def test_connection():
        """Test database connection"""
        print("🔌 Testing database connection...")
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 'Database connected successfully!' as status"))
                status = result.fetchone()[0]
                print(f"✅ {status}")
                
                # Show database info
                result = conn.execute(text("SELECT DATABASE() as db_name, VERSION() as version"))
                db_info = result.fetchone()
                print(f"📦 Database: {db_info[0]}")
                print(f"🔧 MySQL Version: {db_info[1]}")
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
        return True
    
    def main():
        """Main initialization function"""
        print("🚀 Yinizai ML Database Initialization")
        print("=" * 50)
        
        # Test connection first
        if not test_connection():
            print("❌ Please check your database credentials in .env file")
            return
        
        # Create tables
        create_tables()
        
        print("\n🎉 Database initialization completed!")
        print("\n📝 Next steps:")
        print("1. Your database is ready for the ML service")
        print("2. Run './start.sh' to start the ML service")
        print("3. The service will create sample data automatically when needed")
        
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure you're running this from the ml_service directory")
    print("and that all dependencies are installed.")
