# ==========================================================
# main.py
# Eye Landmark 기반 집중도 분석 엔진
# ----------------------------------------------------------
# - MediaPipe Face Mesh 기반 눈 랜드마크 추출
# - 눈 개폐 정도를 활용한 집중도 추정
# - 일정 구간 평균값을 FastAPI 서버로 전송
# ==========================================================

import sys
import io
import time
import requests
import cv2
import signal
import os
from collections import deque
import mediapipe as mp


# ==========================================================
# 1. 실행 경로 및 환경 설정
# ==========================================================

# 현재 파일 기준 절대 경로 (서버 실행 위치와 무관하게 동작하도록 구성)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# MediaPipe Protobuf 충돌 방지 (Python 3.10+ 환경 대응)
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# 표준 출력 UTF-8 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 서버 주소 (환경 변수 우선 → 기본 localhost)
SERVER_URL = os.getenv("SERVER_URL", "http://127.0.0.1:8000")

WINDOW_SECONDS = 30   # 집중도 평균 산출 구간 (초)


# ==========================================================
# 2. 종료 신호 처리
# ==========================================================

should_exit = False

def signal_handler(sig, frame):
    """Ctrl+C 입력 시 분석 루프 안전 종료"""
    global should_exit
    should_exit = True

signal.signal(signal.SIGINT, signal_handler)


# ==========================================================
# 3. 카메라 초기화
# ==========================================================

def open_camera(camera_index=0):
    """
    다양한 OpenCV 백엔드를 순차 시도하여
    환경별 카메라 호환성 문제를 최소화한다.
    """

    backends = [
        cv2.CAP_MSMF,
        cv2.CAP_DSHOW,
        cv2.CAP_ANY,
    ]

    for backend in backends:
        cap = cv2.VideoCapture(camera_index, backend)

        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                return cap
            cap.release()

    return None


# ==========================================================
# 4. 실행 인자 처리
# ==========================================================

def get_args():
    """
    실행 인자:
    argv[1] → user_no
    argv[2] → (선택) licence_kind
    argv[3] → camera_index
    """

    user_no = 1
    camera_index = 0

    if len(sys.argv) > 1:
        try:
            user_no = int(sys.argv[1])
        except ValueError:
            pass

    if len(sys.argv) > 3:
        try:
            camera_index = int(sys.argv[3])
        except ValueError:
            pass

    return user_no, camera_index


# ==========================================================
# 5. 서버 전송 로직
# ==========================================================

def send_record(user_no, buffer, all_scores):
    """
    구간 평균 집중도를 계산하여 서버에 전송.
    네트워크 오류 발생 시에도 로컬 통계는 유지.
    """

    if not buffer:
        return

    avg_focus = int(sum(buffer) / len(buffer))

    try:
        payload = {
            "user_no": user_no,
            "focus_score": avg_focus,
            "stress_score": 0
        }

        requests.post(
            f"{SERVER_URL}/record",
            json=payload,
            timeout=5
        )

    except Exception:
        pass

    all_scores.append(avg_focus)
    buffer.clear()


# ==========================================================
# 6. 핵심 분석 루프
# ==========================================================

def main():
    """
    실행 흐름:
    1) 카메라 초기화
    2) MediaPipe Face Mesh 분석
    3) 눈 개폐 기반 집중도 점수화
    4) 일정 구간 평균 서버 전송
    """

    global should_exit

    user_no, camera_index = get_args()

    cap = open_camera(camera_index)
    if cap is None:
        return

    mp_face_mesh = mp.solutions.face_mesh

    try:
        face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    except Exception:
        return

    focus_buffer = deque(maxlen=WINDOW_SECONDS)
    all_scores = []
    last_save_time = time.time()
    error_count = 0

    try:
        while cap.isOpened() and not should_exit:

            ret, frame = cap.read()

            if not ret:
                error_count += 1
                if error_count >= 10:
                    break
                time.sleep(0.1)
                continue

            error_count = 0

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = face_mesh.process(frame_rgb)

            focus_score = 0

            if result.multi_face_landmarks:
                landmarks = result.multi_face_landmarks[0].landmark

                # 눈 상하 랜드마크 Y좌표 차이 → 개폐 정도 추정
                eye_diff = abs(landmarks[33].y - landmarks[263].y)

                if eye_diff < 0.005:
                    focus_score = 90
                elif eye_diff < 0.015:
                    focus_score = 70
                else:
                    focus_score = 40

            # 1초 단위 데이터 적립
            now = time.time()
            if now - last_save_time >= 1:
                focus_buffer.append(focus_score)
                last_save_time = now

            # 30초 구간 도달 시 서버 전송
            if len(focus_buffer) == WINDOW_SECONDS:
                send_record(user_no, focus_buffer, all_scores)

            cv2.imshow("Eye Focus Analysis", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        if "face_mesh" in locals():
            face_mesh.close()

        cap.release()
        cv2.destroyAllWindows()

        if focus_buffer:
            send_record(user_no, focus_buffer, all_scores)

        final_avg = int(sum(all_scores) / len(all_scores)) if all_scores else 0

        # 세션 종료 후 일일 리포트 요청
        try:
            requests.post(
                f"{SERVER_URL}/report/daily",
                json={
                    "user_no": user_no,
                    "focus_score": final_avg
                },
                timeout=120
            )
        except Exception:
            pass


# ==========================================================
# 7. 진입점
# ==========================================================

if __name__ == "__main__":
    main()
