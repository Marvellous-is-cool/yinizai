-- ==========================================
-- Yinizai ML Service - MySQL Database Schema
-- ==========================================
-- This schema supports the performance-based difficulty analysis system
-- No pre-labeled difficulties - everything is calculated from real student data!

-- Create the database and user (run as MySQL root)
CREATE DATABASE IF NOT EXISTS yinizai_db;
CREATE USER IF NOT EXISTS 'yinizai_user'@'localhost' IDENTIFIED BY 'yinizai_password';
GRANT ALL PRIVILEGES ON yinizai_db.* TO 'yinizai_user'@'localhost';
FLUSH PRIVILEGES;

USE yinizai_db;

-- ==========================================
-- 1. QUESTIONS TABLE
-- ==========================================
-- Stores all questions WITHOUT pre-assigned difficulty levels
-- Difficulty will be calculated based on student performance data

CREATE TABLE questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    question_text TEXT NOT NULL,
    question_type ENUM('multiple_choice', 'short_answer', 'essay') NOT NULL,
    subject VARCHAR(100),
    correct_answer TEXT,
    points INT DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Optional: For comparison with external difficulty labels
    external_difficulty_label ENUM('easy', 'medium', 'hard') NULL COMMENT 'Teacher-assigned difficulty (for comparison only)',
    
    -- Indexes for better query performance
    INDEX idx_subject (subject),
    INDEX idx_question_type (question_type),
    INDEX idx_created_at (created_at)
);

-- ==========================================
-- 2. STUDENT ANSWERS TABLE  
-- ==========================================
-- Stores all student responses - this is the core data for ML training
-- Each row represents one student's attempt at answering one question

CREATE TABLE student_answers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    question_id INT NOT NULL,
    student_id VARCHAR(100) NOT NULL COMMENT 'Student identifier (can be numeric or string)',
    answer_text TEXT NOT NULL,
    score FLOAT NOT NULL COMMENT 'Points earned (0 to max_score)',
    max_score FLOAT NOT NULL COMMENT 'Maximum possible points',
    time_taken INT DEFAULT 0 COMMENT 'Time spent in seconds',
    attempt_number INT DEFAULT 1 COMMENT 'Multiple attempts allowed',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    
    -- Indexes for ML queries
    INDEX idx_question_id (question_id),
    INDEX idx_student_id (student_id),
    INDEX idx_score (score),
    INDEX idx_time_taken (time_taken),
    INDEX idx_submitted_at (submitted_at),
    
    -- Composite indexes for common ML queries
    INDEX idx_question_score (question_id, score),
    INDEX idx_question_time (question_id, time_taken),
    INDEX idx_student_question (student_id, question_id)
);

-- ==========================================
-- 3. QUESTION ANALYTICS TABLE
-- ==========================================
-- Stores calculated difficulty and performance metrics
-- Updated automatically as more student data comes in

CREATE TABLE question_analytics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    question_id INT NOT NULL UNIQUE,
    
    -- ML Predictions vs Reality
    predicted_difficulty ENUM('easy', 'medium', 'hard') COMMENT 'ML prediction based on text analysis',
    calculated_difficulty ENUM('easy', 'medium', 'hard') COMMENT 'Calculated from student performance',
    prediction_confidence FLOAT COMMENT 'Confidence score (0-1) for predicted_difficulty',
    calculation_confidence FLOAT COMMENT 'Confidence based on sample size',
    
    -- Performance Metrics
    avg_score FLOAT COMMENT 'Average score ratio (score/max_score)',
    median_score FLOAT COMMENT 'Median score ratio',
    score_std_dev FLOAT COMMENT 'Standard deviation of scores',
    pass_rate FLOAT COMMENT 'Percentage of students scoring >= 60%',
    
    -- Time Analysis
    avg_time_taken FLOAT COMMENT 'Average time in seconds',
    median_time_taken FLOAT COMMENT 'Median time in seconds', 
    time_std_dev FLOAT COMMENT 'Time standard deviation',
    
    -- Attempt Statistics
    total_attempts INT DEFAULT 0,
    unique_students INT DEFAULT 0,
    completion_rate FLOAT COMMENT 'Percentage who submitted vs started',
    
    -- Text Analysis Results
    common_mistakes JSON COMMENT 'Array of common wrong answers with frequencies',
    comprehension_issues JSON COMMENT 'Array of identified learning gaps',
    recommendations JSON COMMENT 'Array of suggested improvements',
    
    -- ML Feature Data
    question_features JSON COMMENT 'Extracted text features (word count, readability, etc.)',
    
    -- Timestamps
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_predicted_difficulty (predicted_difficulty),
    INDEX idx_calculated_difficulty (calculated_difficulty),
    INDEX idx_avg_score (avg_score),
    INDEX idx_pass_rate (pass_rate),
    INDEX idx_last_updated (last_updated)
);

-- ==========================================
-- 4. STUDENT PERFORMANCE TABLE (Optional)
-- ==========================================
-- Tracks individual student progress over time
-- Useful for personalized recommendations

CREATE TABLE student_performance (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(100) NOT NULL,
    subject VARCHAR(100),
    
    -- Performance Metrics
    avg_score FLOAT,
    total_questions_attempted INT DEFAULT 0,
    questions_passed INT DEFAULT 0,
    avg_time_per_question FLOAT,
    
    -- Learning Patterns
    preferred_question_types JSON COMMENT 'Array of question types student performs well on',
    struggling_topics JSON COMMENT 'Array of subjects/topics where student needs help',
    learning_speed ENUM('fast', 'medium', 'slow') COMMENT 'Based on time-to-mastery',
    
    -- ML Insights
    comprehension_cluster INT COMMENT 'ML-assigned learning cluster',
    predicted_next_difficulty ENUM('easy', 'medium', 'hard') COMMENT 'Recommended next question difficulty',
    confidence_level FLOAT COMMENT 'Student confidence score (0-1)',
    
    -- Timestamps
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    UNIQUE KEY unique_student_subject (student_id, subject),
    INDEX idx_student_id (student_id),
    INDEX idx_subject (subject),
    INDEX idx_avg_score (avg_score),
    INDEX idx_comprehension_cluster (comprehension_cluster),
    INDEX idx_last_activity (last_activity)
);

-- ==========================================
-- 5. ML TRAINING LOGS TABLE
-- ==========================================
-- Tracks ML model training runs and performance

CREATE TABLE ml_training_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    model_type ENUM('difficulty', 'score', 'comprehension') NOT NULL,
    
    -- Training Data
    training_samples INT COMMENT 'Number of samples used for training',
    validation_samples INT COMMENT 'Number of samples used for validation',
    features_count INT COMMENT 'Number of input features',
    
    -- Model Performance
    train_accuracy FLOAT,
    validation_accuracy FLOAT,
    test_accuracy FLOAT,
    precision_score FLOAT,
    recall_score FLOAT,
    f1_score FLOAT,
    
    -- Model Configuration
    algorithm VARCHAR(100) COMMENT 'ML algorithm used (RandomForest, etc.)',
    hyperparameters JSON COMMENT 'Model hyperparameters used',
    feature_importance JSON COMMENT 'Top contributing features and their weights',
    
    -- Training Details
    training_duration_seconds INT,
    model_file_path VARCHAR(500) COMMENT 'Path to saved model file',
    
    -- Status
    status ENUM('training', 'completed', 'failed') DEFAULT 'training',
    error_message TEXT NULL,
    
    -- Timestamps
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    
    -- Indexes
    INDEX idx_model_type (model_type),
    INDEX idx_status (status),
    INDEX idx_completed_at (completed_at),
    INDEX idx_validation_accuracy (validation_accuracy)
);

-- ==========================================
-- 6. SYSTEM ALERTS TABLE
-- ==========================================
-- Stores automated alerts for teachers/admins

CREATE TABLE system_alerts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    alert_type ENUM('question_too_hard', 'question_too_easy', 'student_struggling', 'model_retrain_needed') NOT NULL,
    severity ENUM('info', 'warning', 'critical') DEFAULT 'info',
    
    -- Related Objects
    question_id INT NULL,
    student_id VARCHAR(100) NULL,
    subject VARCHAR(100) NULL,
    
    -- Alert Content
    title VARCHAR(200) NOT NULL,
    description TEXT,
    recommendation TEXT,
    data JSON COMMENT 'Supporting data (scores, metrics, etc.)',
    
    -- Status
    status ENUM('new', 'acknowledged', 'resolved') DEFAULT 'new',
    acknowledged_by VARCHAR(100) NULL,
    acknowledged_at TIMESTAMP NULL,
    resolved_at TIMESTAMP NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_alert_type (alert_type),
    INDEX idx_severity (severity),
    INDEX idx_status (status),
    INDEX idx_question_id (question_id),
    INDEX idx_student_id (student_id),
    INDEX idx_created_at (created_at)
);

-- ==========================================
-- VIEWS FOR COMMON QUERIES
-- ==========================================

-- View: Question Performance Summary
CREATE VIEW question_performance_view AS
SELECT 
    q.id,
    q.question_text,
    q.subject,
    q.question_type,
    qa.predicted_difficulty,
    qa.calculated_difficulty,
    qa.avg_score,
    qa.pass_rate,
    qa.avg_time_taken,
    qa.total_attempts,
    qa.unique_students,
    CASE 
        WHEN qa.predicted_difficulty = qa.calculated_difficulty THEN 'Match'
        WHEN qa.predicted_difficulty IS NULL OR qa.calculated_difficulty IS NULL THEN 'Incomplete'
        ELSE 'Mismatch'
    END as prediction_accuracy,
    CASE
        WHEN qa.pass_rate < 0.3 THEN 'Very Hard'
        WHEN qa.pass_rate < 0.5 THEN 'Hard' 
        WHEN qa.pass_rate > 0.95 THEN 'Too Easy'
        ELSE 'Appropriate'
    END as difficulty_assessment
FROM questions q
LEFT JOIN question_analytics qa ON q.id = qa.question_id;

-- View: Student Progress Summary  
CREATE VIEW student_progress_view AS
SELECT 
    sa.student_id,
    COUNT(DISTINCT sa.question_id) as questions_attempted,
    AVG(sa.score / sa.max_score) as avg_score_ratio,
    AVG(sa.time_taken) as avg_time_taken,
    COUNT(DISTINCT q.subject) as subjects_covered,
    SUM(CASE WHEN (sa.score / sa.max_score) >= 0.6 THEN 1 ELSE 0 END) as questions_passed,
    MAX(sa.submitted_at) as last_activity
FROM student_answers sa
JOIN questions q ON sa.question_id = q.id
GROUP BY sa.student_id;

-- ==========================================
-- STORED PROCEDURES
-- ==========================================

-- Procedure: Update Question Analytics
DELIMITER //
CREATE PROCEDURE UpdateQuestionAnalytics(IN p_question_id INT)
BEGIN
    DECLARE v_avg_score FLOAT;
    DECLARE v_median_score FLOAT; 
    DECLARE v_score_stddev FLOAT;
    DECLARE v_pass_rate FLOAT;
    DECLARE v_avg_time FLOAT;
    DECLARE v_median_time FLOAT;
    DECLARE v_time_stddev FLOAT;
    DECLARE v_total_attempts INT;
    DECLARE v_unique_students INT;
    
    -- Calculate metrics
    SELECT 
        AVG(score / max_score) as avg_score,
        STDDEV(score / max_score) as score_stddev,
        AVG(CASE WHEN (score / max_score) >= 0.6 THEN 1.0 ELSE 0.0 END) as pass_rate,
        AVG(time_taken) as avg_time,
        STDDEV(time_taken) as time_stddev,
        COUNT(*) as total_attempts,
        COUNT(DISTINCT student_id) as unique_students
    INTO v_avg_score, v_score_stddev, v_pass_rate, v_avg_time, v_time_stddev, v_total_attempts, v_unique_students
    FROM student_answers 
    WHERE question_id = p_question_id;
    
    -- Calculate difficulty based on performance
    SET @calculated_difficulty = CASE
        WHEN v_pass_rate >= 0.8 THEN 'easy'
        WHEN v_pass_rate >= 0.5 THEN 'medium' 
        ELSE 'hard'
    END;
    
    -- Update analytics table
    INSERT INTO question_analytics (
        question_id, calculated_difficulty, avg_score, score_std_dev, pass_rate,
        avg_time_taken, time_std_dev, total_attempts, unique_students, 
        calculation_confidence, last_updated
    ) VALUES (
        p_question_id, @calculated_difficulty, v_avg_score, v_score_stddev, v_pass_rate,
        v_avg_time, v_time_stddev, v_total_attempts, v_unique_students,
        LEAST(1.0, v_unique_students / 50.0), NOW()
    )
    ON DUPLICATE KEY UPDATE
        calculated_difficulty = @calculated_difficulty,
        avg_score = v_avg_score,
        score_std_dev = v_score_stddev,
        pass_rate = v_pass_rate,
        avg_time_taken = v_avg_time,
        time_std_dev = v_time_stddev,
        total_attempts = v_total_attempts,
        unique_students = v_unique_students,
        calculation_confidence = LEAST(1.0, v_unique_students / 50.0),
        last_updated = NOW();
        
END //
DELIMITER ;

-- ==========================================
-- TRIGGERS
-- ==========================================

-- Trigger: Auto-update analytics when new answer is submitted
DELIMITER //
CREATE TRIGGER after_answer_insert 
    AFTER INSERT ON student_answers
    FOR EACH ROW
BEGIN
    -- Update question analytics if we have enough samples
    SET @answer_count = (SELECT COUNT(*) FROM student_answers WHERE question_id = NEW.question_id);
    
    IF @answer_count >= 10 THEN
        CALL UpdateQuestionAnalytics(NEW.question_id);
    END IF;
    
    -- Generate alerts for struggling students
    SET @student_recent_score = (
        SELECT AVG(score / max_score) 
        FROM student_answers 
        WHERE student_id = NEW.student_id 
        ORDER BY submitted_at DESC 
        LIMIT 5
    );
    
    IF @student_recent_score < 0.4 THEN
        INSERT INTO system_alerts (
            alert_type, severity, student_id, title, description, data
        ) VALUES (
            'student_struggling', 'warning', NEW.student_id,
            'Student May Need Help',
            CONCAT('Student ', NEW.student_id, ' has low recent scores'),
            JSON_OBJECT('avg_recent_score', @student_recent_score)
        );
    END IF;
END //
DELIMITER ;

-- ==========================================
-- SAMPLE QUERIES FOR YOUR NODE.JS APP
-- ==========================================

/* 
-- Get questions that need difficulty prediction:
SELECT * FROM questions q
LEFT JOIN question_analytics qa ON q.id = qa.question_id
WHERE qa.predicted_difficulty IS NULL;

-- Get questions with enough data for training:
SELECT q.*, COUNT(sa.id) as answer_count
FROM questions q
JOIN student_answers sa ON q.id = sa.question_id
GROUP BY q.id
HAVING answer_count >= 10;

-- Get student performance for personalization:
SELECT * FROM student_progress_view 
WHERE student_id = 'student_123';

-- Get questions that are too hard/easy:
SELECT * FROM question_performance_view 
WHERE difficulty_assessment IN ('Very Hard', 'Too Easy');

-- Get latest training performance:
SELECT * FROM ml_training_logs 
WHERE status = 'completed'
ORDER BY completed_at DESC 
LIMIT 3;
*/

-- ==========================================
-- INDEXES FOR PERFORMANCE
-- ==========================================

-- Additional composite indexes for ML queries
CREATE INDEX idx_answers_question_score_time ON student_answers(question_id, score, time_taken);
CREATE INDEX idx_answers_student_submitted ON student_answers(student_id, submitted_at);
CREATE INDEX idx_analytics_difficulty_confidence ON question_analytics(calculated_difficulty, calculation_confidence);

-- ==========================================
-- CONFIGURATION NOTES
-- ==========================================

/*
IMPORTANT CONFIGURATION NOTES:

1. **Character Set**: Use utf8mb4 for full Unicode support
   ALTER DATABASE yinizai_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

2. **JSON Storage**: MySQL 5.7+ required for JSON column type
   For older versions, use TEXT and validate JSON in application

3. **Time Zones**: Set consistent timezone
   SET time_zone = '+00:00'; -- UTC recommended

4. **Performance**: 
   - Monitor slow queries with slow_query_log
   - Consider partitioning student_answers by date for large datasets
   - Use EXPLAIN to optimize query performance

5. **Backup Strategy**:
   - Regular backups of student data (GDPR compliance)
   - Separate backups for ML training data vs current operations

6. **Security**:
   - Use SSL connections in production
   - Encrypt sensitive student data
   - Implement proper access controls
*/
