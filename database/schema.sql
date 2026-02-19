-- user_info table 구성 및 제약조건
CREATE TABLE user_info(
			user_no INT AUTO_INCREMENT PRIMARY KEY,
			login_id VARCHAR(20) NOT NULL,
			user_pwd VARCHAR(15) NOT NULL,
            user_name VARCHAR(20) NOT NULL,
            email VARCHAR(30) NOT NULL,
            gender ENUM('M', 'F'),
            age INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE user_info ADD CONSTRAINT user_info_login_id_uk UNIQUE KEY(login_id);
ALTER TABLE user_info ADD CONSTRAINT user_info_email_uk UNIQUE KEY(email);

-- study_record table 구성 및 제약조건
CREATE TABLE study_record(
	session_no INT AUTO_INCREMENT PRIMARY KEY,
    user_no INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME DEFAULT NULL,
	focus_score TINYINT CHECK (focus_score BETWEEN 0 AND 100),
    stress_score TINYINT CHECK (stress_score BETWEEN 0 AND 100)
);

ALTER TABLE study_record ADD CONSTRAINT study_record_user_no_fk FOREIGN KEY(user_no)
REFERENCES user_info(user_no);

-- daily_reports table 구성 및 제약조건
CREATE TABLE daily_reports (
    report_no INT AUTO_INCREMENT PRIMARY KEY,
    user_no INT NOT NULL,
    report_date DATE NOT NULL,
    avg_focus_score DECIMAL(5,2),
    avg_stress_score DECIMAL(5,2),
    feedback_comment TEXT,
    star_rating TINYINT CHECK (star_rating BETWEEN 1 AND 5),
    content TEXT
);

ALTER TABLE daily_reports ADD CONSTRAINT daily_reports_user_no_fk FOREIGN KEY(user_no)
REFERENCES user_info(user_no);

-- licence_prep table 구성 및 제약조건
CREATE TABLE licence_prep (
    prepare_no INT AUTO_INCREMENT PRIMARY KEY,
    user_no INT NOT NULL,
    licence_kind VARCHAR(30) NOT NULL,
    licence_start DATETIME NOT NULL,
    licence_end DATETIME DEFAULT NULL,
    licence_feedback TEXT
);

ALTER TABLE licence_prep ADD CONSTRAINT licence_prep_user_no_fk FOREIGN KEY(user_no)
REFERENCES user_info(user_no);







-- 개선 스키마

-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS eye_focus_db;
USE eye_focus_db;

-- =========================================
-- user_info 테이블
-- =========================================
CREATE TABLE user_info (
    user_no INT AUTO_INCREMENT PRIMARY KEY,
    login_id VARCHAR(20) NOT NULL,
    user_pwd VARCHAR(100) NOT NULL, -- 해시 저장 대비
    user_name VARCHAR(20) NOT NULL,
    email VARCHAR(50) NOT NULL,
    gender ENUM('M', 'F'),
    age INT UNSIGNED NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY user_info_login_id_uk (login_id),
    UNIQUE KEY user_info_email_uk (email)
);

-- =========================================
-- study_record 테이블
-- =========================================
CREATE TABLE study_record (
    session_no INT AUTO_INCREMENT PRIMARY KEY,
    user_no INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME DEFAULT NULL,
    focus_score TINYINT UNSIGNED,
    stress_score TINYINT UNSIGNED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT study_record_user_no_fk 
        FOREIGN KEY (user_no)
        REFERENCES user_info(user_no)
        ON DELETE CASCADE
);

-- 인덱스 (조회 성능 향상)
CREATE INDEX idx_study_record_user_no ON study_record(user_no);

-- =========================================
-- daily_reports 테이블
-- =========================================
CREATE TABLE daily_reports (
    report_no INT AUTO_INCREMENT PRIMARY KEY,
    user_no INT NOT NULL,
    report_date DATE NOT NULL,
    avg_focus_score DECIMAL(5,2),
    avg_stress_score DECIMAL(5,2),
    feedback_comment TEXT,
    star_rating TINYINT UNSIGNED,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT daily_reports_user_no_fk 
        FOREIGN KEY (user_no)
        REFERENCES user_info(user_no)
        ON DELETE CASCADE,

    UNIQUE KEY daily_user_date_uk (user_no, report_date)
);

CREATE INDEX idx_daily_reports_user_no ON daily_reports(user_no);

-- =========================================
-- licence_prep 테이블
-- =========================================
CREATE TABLE licence_prep (
    prepare_no INT AUTO_INCREMENT PRIMARY KEY,
    user_no INT NOT NULL,
    licence_kind VARCHAR(30) NOT NULL,
    licence_start DATETIME NOT NULL,
    licence_end DATETIME DEFAULT NULL,
    licence_feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT licence_prep_user_no_fk 
        FOREIGN KEY (user_no)
        REFERENCES user_info(user_no)
        ON DELETE CASCADE
);

CREATE INDEX idx_licence_prep_user_no ON licence_prep(user_no);
