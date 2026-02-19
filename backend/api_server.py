# ==========================================================
# server.py
# FastAPI 기반 집중도 분석 백엔드 서버
# - 실시간 학습 세션 실행
# - 집중도 기록 저장
# - 일일 리포트 및 자격증 기간 누적 피드백 생성
# ==========================================================

from fastapi import FastAPI
from pydantic import BaseModel
import pymysql
import requests
from typing import Optional
import subprocess
import sys
import uvicorn
import time

app = FastAPI()

# ==========================================================
# 1. 환경 설정 및 데이터베이스 구성
# ==========================================================

# Google Gemini API Key (환경 변수 사용 권장)
GEMINI_API_KEY = ""

# MySQL 연결 설정
# - DictCursor 사용으로 컬럼명을 key로 접근
# - autocommit=True로 트랜잭션 누락 방지
# - connect_timeout 설정으로 네트워크 지연 대비
DB_CONFIG = {
    "host": "project-db-cgi.smhrd.com",
    "port": 3307,
    "user": "2nd_pjt",
    "password": "1234",
    "db": "2nd_pjt",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
    "connect_timeout": 5
}

# ==========================================================
# 2. 요청 데이터 모델 (DTO)
# ==========================================================

class StartLearningReq(BaseModel):
    """
    학습 세션 시작 요청 모델
    - user_no: 사용자 식별 번호
    - licence_kind: 선택적 자격증 종류
    """
    user_no: int
    licence_kind: Optional[str] = None


class RecordModel(BaseModel):
    """
    집중도 기록 저장 및 리포트 생성 요청 모델
    """
    user_no: int
    focus_score: int
    stress_score: int = 0


# ==========================================================
# 3. Gemini API 호출 로직
# ==========================================================

def call_gemini(prompt, timeout=10):
    """
    Gemini API 호출 함수
    
    - 모델 장애 또는 과부하 대비 다중 모델 fallback 구조
    - 404, 429 발생 시 즉시 다음 모델로 전환
    - 503 발생 시 재시도 후 실패 시 모델 교체
    """

    if not GEMINI_API_KEY:
        return "오늘도 고생하셨습니다."

    candidate_models = [
        "gemini-2.0-flash",
        "gemini-flash-latest",
        "gemini-pro"
    ]

    for model_name in candidate_models:

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={GEMINI_API_KEY}"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        for attempt in range(2):
            try:
                res = requests.post(url, json=payload, timeout=timeout)

                if res.status_code == 200:
                    return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()

                elif res.status_code in [404, 429]:
                    # 모델 사용 불가 또는 요청 제한 시 즉시 모델 전환
                    break

                elif res.status_code == 503:
                    # 일시적 서버 오류 → 재시도
                    time.sleep(2)
                    continue

            except Exception:
                continue

    return "학습 데이터 기반 자동 피드백이 생성되었습니다."


# ==========================================================
# 4. 학습 세션 실행 API
# ==========================================================

@app.post("/start-learning")
async def start_learning(data: StartLearningReq):
    """
    클라이언트 요청 시 학습 분석 프로세스를 서브프로세스로 실행
    
    - sys.executable 사용으로 Python 환경 일관성 유지
    - licence_kind 인자 선택적 전달
    """
    try:
        args = [sys.executable, "main.py", str(data.user_no)]

        if data.licence_kind:
            args.append(data.licence_kind)

        subprocess.Popen(args)

        return {"status": "ok"}

    except Exception:
        return {"status": "error"}


# ==========================================================
# 5. 실시간 집중도 기록 저장 API
# ==========================================================

@app.post("/record")
def save_record(data: RecordModel):
    """
    분석 모듈에서 전달된 집중도 데이터를 DB에 저장
    
    - 5초 단위 기록 구조
    - start_time / end_time 자동 생성
    """
    conn = None

    try:
        conn = pymysql.connect(**DB_CONFIG)

        with conn.cursor() as cur:
            sql = """
                INSERT INTO study_record
                (user_no, start_time, end_time, focus_score, stress_score)
                VALUES (%s, NOW(), DATE_ADD(NOW(), INTERVAL 5 SECOND), %s, %s)
            """
            cur.execute(sql, (data.user_no, data.focus_score, data.stress_score))

        return {"msg": "saved"}

    except Exception:
        return {"msg": "db_error"}

    finally:
        if conn:
            conn.close()


# ==========================================================
# 6. 일일 리포트 및 자격증 기간 누적 피드백 API
# ==========================================================

@app.post("/report/daily")
def create_daily_report(data: RecordModel):
    """
    1) 오늘 평균 집중도/스트레스 계산
    2) Gemini 기반 일일 피드백 생성
    3) 자격증 준비 기간 누적 평균 계산
    4) 누적 AI 피드백 갱신
    """

    conn = None

    try:
        conn = pymysql.connect(**DB_CONFIG)

        with conn.cursor() as cur:

            # 1. 오늘 평균 계산
            sql_today = """
                SELECT AVG(focus_score) as af,
                       AVG(stress_score) as as_
                FROM study_record
                WHERE user_no=%s AND DATE(start_time)=CURDATE()
            """
            cur.execute(sql_today, (data.user_no,))
            stats = cur.fetchone()

            af = round(float(stats['af']), 2) if stats and stats['af'] else float(data.focus_score)
            as_ = round(float(stats['as_']), 2) if stats and stats['as_'] else 0.0

            # 2. 일일 AI 피드백 생성
            daily_prompt = f"평균집중도 {af}, 스트레스 {as_}. 격려 50자 이내."
            daily_comment = call_gemini(daily_prompt)

            # 3. daily_reports 테이블 upsert
            sql_save_daily = """
                INSERT INTO daily_reports
                (user_no, report_date, avg_focus_score, avg_stress_score, feedback_comment)
                VALUES (%s, CURDATE(), %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    avg_focus_score=VALUES(avg_focus_score),
                    avg_stress_score=VALUES(avg_stress_score),
                    feedback_comment=VALUES(feedback_comment)
            """
            cur.execute(sql_save_daily, (data.user_no, af, as_, daily_comment))

            # 4. 자격증 준비 기간 누적 평균 계산
            sql_lic = """
                SELECT prepare_no, licence_kind, licence_start, licence_end
                FROM licence_prep
                WHERE user_no=%s
                LIMIT 1
            """
            cur.execute(sql_lic, (data.user_no,))
            licence = cur.fetchone()

            if licence:
                start_date = licence['licence_start']
                end_date = licence['licence_end'] or "9999-12-31"

                sql_period_avg = """
                    SELECT AVG(avg_focus_score) p_f,
                           AVG(avg_stress_score) p_s
                    FROM daily_reports
                    WHERE user_no=%s
                    AND report_date BETWEEN %s AND %s
                """
                cur.execute(sql_period_avg, (data.user_no, start_date, end_date))
                p_stats = cur.fetchone()

                pf = round(float(p_stats['p_f']), 2) if p_stats and p_stats['p_f'] else 0.0
                ps = round(float(p_stats['p_s']), 2) if p_stats and p_stats['p_s'] else 0.0

                l_prompt = (
                    f"자격증 {licence['licence_kind']} 준비."
                    f" 누적집중도 {pf}, 스트레스 {ps}. 격려 80자 이내."
                )

                l_feedback = call_gemini(l_prompt)

                sql_up_lic = """
                    UPDATE licence_prep
                    SET licence_feedback=%s
                    WHERE prepare_no=%s
                """
                cur.execute(sql_up_lic, (l_feedback, licence['prepare_no']))

            conn.commit()

        return {"msg": "success", "ai_feedback": daily_comment}

    except Exception:
        return {"msg": "error"}

    finally:
        if conn:
            conn.close()


# ==========================================================
# 7. 서버 실행 진입점
# ==========================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
