# Eye Focus Analysis

AI 기반 시선 추적을 활용한 학습 집중도 분석 시스템

---

## 📌 프로젝트 소개

MediaPipe Face Mesh를 활용하여  
눈 랜드마크 좌표를 기반으로 집중도를 계산하는 AI 프로젝트입니다.

---

## 🛠 기술 스택

### Backend
- Node.js (Express)
- FastAPI
- MySQL

### AI Engine
- Python
- MediaPipe
- OpenCV
- Google Gemini API

### Validation
- Pydantic
- MySQL Transaction

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
```

### 2. AI Server 실행

```bash
cd ai_server
pip install -r requirements.txt
python main.py
```

---

## 📂 Project Structure

```
eye-focus-analysis/
│
├── backend/                # Node.js 서버
│   ├── server.js
│   ├── package.json
│
├── ai_server/              # Python 집중도 분석 엔진 (FastAPI)
│   ├── main.py
│   ├── requirements.txt
│
├── database/               # DB 설계 문서
│   ├── erd.png
│   └── schema.sql
│
└── README.md
```

---

## 🚀 주요 기능 및 특징 (Key Features)

- **실시간 시선 추적**  
  MediaPipe Face Mesh 기반 눈 랜드마크 분석

- **집중도 계산 로직**  
  눈 종횡비(EAR) 계산 및 좌/우 눈 비율 차이 기반 집중도 판별

- **AI 피드백 생성**  
  Google Gemini API를 활용한 개인 맞춤 학습 조언 생성

- **비동기 AI 서버 구조**  
  FastAPI 비동기 처리로 AI 응답 대기 중에도 서버 블로킹 방지

- **데이터 안정성 확보**  
  Pydantic 데이터 검증 및 DB 트랜잭션 관리

---

## 🔌 시스템 아키텍처

Client  
→ Node.js Server  
→ FastAPI AI Server  
→ MySQL Database
