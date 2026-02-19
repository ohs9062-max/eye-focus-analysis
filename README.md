# Eye Focus Analysis

AI 기반 시선 추적을 활용한 학습 집중도 분석 시스템

---

## 📌 프로젝트 소개

MediaPipe Face Mesh를 활용하여  
눈 랜드마크 좌표를 기반으로  
집중도를 계산하는 AI 프로젝트입니다.

---

## 🛠 기술 스택

- Node.js (Express)
- Python (MediaPipe, OpenCV)
- MySQL

---

## 📊 Database ERD

![ERD](database/erd.png)

---

## 🚀 실행 방법

### 1. Backend 실행

```bash
cd backend
npm install
node server.js

cd ai_server
pip install -r requirements.txt
python main.py

eye-focus-analysis/
│
├── backend/                # Node.js 서버
│   ├── server.js
│   ├── package.json
│
├── ai_server/              # Python 집중도 분석 엔진
│   ├── main.py
│   ├── requirements.txt
│
├── database/               # DB 설계 문서
│   ├── erd.png
│   └── schema.sql
│
└── README.md


---

# 🔥 핵심 기억

✔ 코드블록은 열었으면 반드시 닫는다  
✔ 트리 구조는 항상 ``` 로 감싼다  
✔ ```md 같은 건 쓰지 않는다  

---

수정 후:

```bash
git add .
git commit -m "Fix README formatting properly"
git push
