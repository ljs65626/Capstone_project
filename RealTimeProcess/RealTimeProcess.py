import os
import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
from PIL import Image
from datetime import timedelta
import time
from google.generativeai import GenerativeModel
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from openpyxl import Workbook, load_workbook

# Gemini API 키 설정
os.environ["GOOGLE_API_KEY"] = "여기에_API_키를_입력하세요"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# 모델 로드
container_model = YOLO('WandaVisionYOLO.pt')

# 비디오 파일 경로
video_folder = './videos/'
image_folder = './images/'
excel_path = './container_logs.xlsx'

# 이미지 폴더가 없다면 생성
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

# 엑셀 파일 확인 및 생성
def prepare_excel_file():
    if os.path.exists(excel_path):
        try:
            # 기존 파일 로드
            df = pd.read_excel(excel_path)
        except Exception as e:
            print(f"엑셀 파일을 읽는 중 오류가 발생했습니다: {e}")
            # 새로운 파일 생성
            df = pd.DataFrame(columns=["시간", "트럭번호"])
    else:
        # 새로운 파일 생성
        df = pd.DataFrame(columns=["시간", "트럭번호"])
    
    return df

# 컨테이너 번호 인식 함수
def recognize_container_number(image_path):
    try:
        # 이미지를 base64로 인코딩
        with open(image_path, "rb") as img_file:
            import base64
            image_bytes = img_file.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Gemini AI 모델 설정
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-thinking-exp",
            temperature=0.0,
            convert_system_message_to_human=True
        )
        
        # 시스템 프롬프트 설정
        system_prompt = """
        이 이미지는 트럭 컨테이너 사진입니다. 컨테이너의 오른쪽 위 부분에 있는 번호를 정확히 추출해주세요.
        번호는 대문자 4개와 숫자 6자리로 구성되어 있습니다 (예: 'TCNU 897179', 'BMOU 491266', 'FFAU 344955').
        번호만 정확히 추출하여 응답해주세요. 확실하지 않은 경우 'UNKNOWN'이라고 답변해주세요.
        """
        
        # 이미지와 프롬프트로 질의
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": "이 트럭 컨테이너 이미지에서 컨테이너 번호를 추출해주세요."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]}
        ])
        
        # 응답 처리
        container_number = response.content.strip()
        
        # 형식 검증 (4글자 대문자 + 공백 + 6자리 숫자)
        import re
        if re.match(r'^[A-Z]{4}\s\d{6}$', container_number):
            return container_number
        else:
            return "UNKNOWN"
            
    except Exception as e:
        print(f"컨테이너 번호 인식 중 오류 발생: {e}")
        return "ERROR"

# 마지막 캡처 시간 저장 변수
last_capture_time = {}

# 엑셀 파일 준비
container_df = prepare_excel_file()

# 비디오 폴더 내의 모든 파일 순회
for filename in os.listdir(video_folder):
    if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):  # 비디오 파일 형식 필터링
        video_path = os.path.join(video_folder, filename)
        print(f"처리 중인 비디오: {video_path}")

        # 비디오 캡처 객체 생성
        cap = cv2.VideoCapture(video_path)
        
        # 비디오 FPS 가져오기
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frames_to_skip = fps  # 1초당 한 프레임만 처리
        print(f"비디오 FPS: {fps}, {frames_to_skip}프레임마다 처리 (1초 간격)")
        
        # 원본 비디오 크기 가져오기
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 디스플레이 크기 계산 (원본의 50%)
        display_width = int(original_width * 0.5)
        display_height = int(original_height * 0.5)
        
        # 창 크기 설정
        cv2.namedWindow('Container Detection', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Container Detection', display_width, display_height)

        frame_count = 0
        frame_number = 0
        
        # 동일한 컨테이너 중복 캡처 방지를 위한 시간 간격 (초)
        capture_interval = 10  

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_number += 1
            
            # 1초마다 한 프레임만 처리
            if frame_number % frames_to_skip != 0:
                continue

            frame_count += 1
            
            # 현재 프레임의 시간 계산 (비디오 시작부터 경과 시간)
            current_time_seconds = frame_number / fps
            current_time = str(timedelta(seconds=int(current_time_seconds)))
            
            # YOLO 모델로 컨테이너 감지
            results = container_model.predict(frame, stream=True)
            for result in results:
                if result.boxes is None or len(result.boxes) == 0:
                    continue

                frame_height, frame_width, _ = frame.shape
                frame_area = frame_height * frame_width
                
                # 결과를 표시할 프레임 복사
                display_frame = frame.copy()

                for box in result.boxes:
                    cls = int(box.cls[0])
                    class_name = result.names[cls]
                    conf = float(box.conf[0])
                    
                    if class_name == 'container':  # 컨테이너 클래스 이름이 'container'라고 가정
                        # 바운딩 박스 좌표 추출 및 면적 계산
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        container_area = (x2 - x1) * (y2 - y1)
                        area_ratio = container_area / frame_area

                        # 바운딩 박스와 정보 표시
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        label = f'Container {conf:.2f} Area: {area_ratio:.2%}'
                        cv2.putText(display_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                        # 디버그 정보 출력
                        print(f"프레임 {frame_count} (비디오 프레임 {frame_number}): 컨테이너 감지 - 면적 비율: {area_ratio:.2%}")

                        # 컨테이너가 프레임의 20% 이상을 차지하는지 확인
                        if area_ratio > 0.2:
                            # 마지막 캡처 이후 충분한 시간이 지났는지 확인
                            current_key = f"{x1}_{y1}_{x2}_{y2}"
                            if current_key not in last_capture_time or \
                               (current_time_seconds - last_capture_time[current_key]) > capture_interval:
                                
                                # 바운딩 박스 영역 크롭
                                container_image = frame[y1:y2, x1:x2]
                                
                                # 이미지 파일 이름 생성
                                base_filename = os.path.splitext(filename)[0]
                                image_name = f"{base_filename}_container_{frame_count:04d}.jpg"
                                image_path = os.path.join(image_folder, image_name)

                                # OpenCV를 사용하여 크롭된 이미지 저장
                                success = cv2.imwrite(image_path, container_image)
                                if success:
                                    print(f"  컨테이너 이미지 저장 성공: {image_path}")
                                    
                                    # 캡처 시간 업데이트
                                    last_capture_time[current_key] = current_time_seconds
                                    
                                    # 크롭된 영역 표시를 위해 빨간색으로 바운딩 박스 변경
                                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                                    
                                    # 컨테이너 번호 인식
                                    container_number = recognize_container_number(image_path)
                                    print(f"  인식된 컨테이너 번호: {container_number}")
                                    
                                    # 엑셀에 기록
                                    if container_number != "UNKNOWN" and container_number != "ERROR":
                                        # 새 행 추가
                                        new_row = pd.DataFrame({
                                            "시간": [current_time], 
                                            "트럭번호": [container_number]
                                        })
                                        container_df = pd.concat([container_df, new_row], ignore_index=True)
                                        
                                        # 엑셀 파일 저장
                                        container_df.to_excel(excel_path, index=False)
                                        print(f"  엑셀에 기록: 시간 {current_time}, 컨테이너 번호 {container_number}")
                                else:
                                    print(f"  컨테이너 이미지 저장 실패: {image_path}")
                
                # 프레임 표시
                cv2.imshow('Container Detection', display_frame)
                
                # 'q' 키를 누르면 종료
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        # 비디오 캡처 객체 해제 및 창 닫기
        cap.release()
        cv2.destroyAllWindows()

print("모든 비디오 처리 완료!")
