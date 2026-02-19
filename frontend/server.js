// ==========================================================
// Eye Focus Analysis - Backend Server
// Node.js + Express + MySQL
// ----------------------------------------------------------
// 1. 사용자 인증 (회원가입 / 로그인)
// 2. 학습 세션 시작 → Python 분석 엔진 실행
// 3. 학습 종료 처리
// 4. 자격증 학습 피드백 DB 저장
// ==========================================================

/* ================================
   1. Module Imports
================================ */

const express = require('express');         // Web framework
const mysql = require('mysql2');            // MySQL driver
const cors = require('cors');               // Cross-Origin 설정
const bodyParser = require('body-parser');  // JSON parsing
const path = require('path');               // Path handling
const { spawn } = require('child_process'); // Python process 실행

const app = express();
const PORT = 3000;

app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public')));


/* ================================
   2. Python Engine Path Config
================================ */

// Conda Python 환경
const pythonEnvPath = 'C:/Users/smhrd/.conda/envs/mp_fix/python.exe';

// AI 분석 엔진 디렉토리
const aiServerDir = path.join(__dirname, '../ai_server');

// 실행할 Python 메인 파일
const mainPyPath = path.join(aiServerDir, 'main.py');


/* ================================
   3. Database Connection (Pool)
================================ */

const db = mysql.createPool({
    host: 'project-db-cgi.smhrd.com',
    port: 3307,
    user: '2nd_pjt',
    password: '1234',
    database: '2nd_pjt',
    waitForConnections: true,
    connectionLimit: 10,
    charset: 'utf8mb4'
});


/* ================================
   4. User Registration API
================================ */

app.post('/signup', (req, res) => {
    const { login_id, user_pwd, user_name, email, gender, age } = req.body;

    const sql = `
        INSERT INTO user_info 
        (login_id, user_pwd, user_name, email, gender, age)
        VALUES (?, ?, ?, ?, ?, ?)
    `;

    db.query(sql, [login_id, user_pwd, user_name, email, gender, age], (err) => {
        if (err) {
            return res.status(500).json({ status: 'error', msg: err.message });
        }
        res.json({ status: 'success' });
    });
});


/* ================================
   5. User Login API
================================ */

app.post('/login', (req, res) => {
    const { login_id, user_pwd } = req.body;

    const sql = `
        SELECT user_no, user_name 
        FROM user_info 
        WHERE login_id = ? AND user_pwd = ?
    `;

    db.query(sql, [login_id, user_pwd], (err, results) => {
        if (err) {
            return res.status(500).json({ status: 'error', msg: err.message });
        }

        if (results.length > 0) {
            res.json({
                status: 'success',
                user_no: results[0].user_no,
                name: results[0].user_name
            });
        } else {
            res.json({
                status: 'fail',
                msg: 'Invalid ID or password.'
            });
        }
    });
});


/* ==========================================================
   6. Learning Session Start
   - Python 분석 엔진 실행
   - 학습 종료 시 AI 피드백 반환
========================================================== */

let currentPyProcess = null;

app.post('/start-learning', (req, res) => {

    const { user_no, licence_kind } = req.body;

    console.log(`[Node] Start Learning - User: ${user_no}`);

    // Python 실행 인자 구성
    const args = [mainPyPath, String(user_no)];

    if (licence_kind) {
        args.push(licence_kind);
    }

    // Python 프로세스 실행
    const pyProc = spawn(pythonEnvPath, args, {
        cwd: aiServerDir,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    });

    currentPyProcess = pyProc;

    let aiFeedbackText = "";

    // Python 표준 출력 감시
    pyProc.stdout.on('data', (data) => {
        const msg = data.toString().trim();
        console.log(`[Python] ${msg}`);

        if (msg.includes("AI_MSG:")) {
            const parts = msg.split("AI_MSG:");
            if (parts.length > 1) {
                aiFeedbackText = parts[1].trim();
            }
        }
    });

    // Python 오류 출력
    pyProc.stderr.on('data', (data) => {
        console.error(`[Python Error] ${data.toString().trim()}`);
    });

    // Python 종료 시 응답 반환
    pyProc.on('close', (code) => {

        console.log(`[Node] Python Exit Code: ${code}`);

        if (!aiFeedbackText) {
            aiFeedbackText = "Analysis completed.";
        }

        res.json({
            status: 'finished',
            message: aiFeedbackText
        });
    });
});


/* ================================
   7. Learning Session Stop
================================ */

app.post('/stop-learning', (req, res) => {

    if (currentPyProcess) {
        currentPyProcess.kill('SIGINT');
        currentPyProcess = null;
        res.json({ status: 'stopped' });
    } else {
        res.status(400).json({ error: 'No active session.' });
    }
});


/* ==========================================================
   8. Licence Feedback Save API
   - Python / FastAPI → Node → MySQL
========================================================== */

app.post('/licence/feedback', (req, res) => {

    const { user_no, licence_kind, feedback } = req.body;

    const sql = `
        INSERT INTO licence_prep
        (user_no, licence_kind, licence_start, licence_end, licence_feedback)
        VALUES (?, ?, NOW(), NOW(), ?)
    `;

    db.query(sql, [user_no, licence_kind, feedback], (err, result) => {
        if (err) {
            return res.status(500).json({ msg: 'db error', error: err.message });
        }

        res.json({
            msg: 'success',
            feedback: feedback
        });
    });
});


/* ================================
   9. Server Start
================================ */

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
