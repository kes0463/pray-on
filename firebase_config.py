# ====================================================
# firebase_config.py - Firebase 초기화 모듈
# ====================================================
# 이 파일은 Firebase Admin SDK를 초기화하고,
# Firestore 데이터베이스 클라이언트를 반환하는 함수를 제공합니다.
# 다른 파일에서 "from firebase_config import get_db" 형태로 불러와 사용합니다.
# ====================================================

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 불러옵니다.
load_dotenv()


def initialize_firebase():
    """
    Firebase Admin SDK를 초기화하는 함수.
    이미 초기화되어 있으면 새로 초기화하지 않습니다 (중복 방지).
    """
    # firebase_admin.get_app()으로 이미 초기화됐는지 확인합니다.
    # 초기화되지 않았으면 ValueError가 발생하므로 try/except로 처리합니다.
    try:
        firebase_admin.get_app()
        # 앱이 이미 있으면 아무것도 하지 않습니다.
    except ValueError:
        # 처음 실행 시 Firebase를 초기화합니다.
        
        # 1. 환경 변수에서 JSON 문자열을 직접 읽어오기 시도 (Railway 배포용)
        service_account_json = os.getenv("SERVICE_ACCOUNT_KEY")
        
        if service_account_json:
            try:
                # 문자열을 파이썬 딕셔너리로 변환
                cred_dict = json.loads(service_account_json)
                cred = credentials.Certificate(cred_dict)
                print("✅ 환경변수에서 Firebase 인증 정보를 불러왔습니다.")
            except json.JSONDecodeError as e:
                raise ValueError(f"SERVICE_ACCOUNT_KEY 환경변수의 JSON 형식이 잘못되었습니다: {e}")
        else:
            # 2. 로컬 파일에서 읽기 시도 (로컬 개발용)
            credential_path = os.getenv("FIREBASE_CREDENTIAL_PATH", "serviceAccountKey.json")
            if not os.path.exists(credential_path):
                raise FileNotFoundError(
                    "❌ Firebase 인증 정보가 없습니다.\n"
                    "Railway 배포 시: SERVICE_ACCOUNT_KEY 환경변수에 JSON 전체 내용을 복사하세요.\n"
                    f"로컬 개발 시: '{credential_path}' 파일이 필요합니다."
                )
            
            cred = credentials.Certificate(credential_path)
            print(f"✅ 로컬 파일({credential_path})에서 Firebase 인증 정보를 불러왔습니다.")

        # Firebase 앱을 초기화합니다.
        firebase_admin.initialize_app(cred)
        print("✅ Firebase 초기화 완료!")


def get_db():
    """
    Firestore 데이터베이스 클라이언트를 반환하는 함수.
    이 함수를 호출하면 데이터베이스에 접근할 수 있는 객체(db)를 받습니다.
    
    사용 예시:
        db = get_db()
        db.collection("prayers").add({"text": "오늘의 기도문..."})
    """
    # Firebase가 초기화되어 있는지 확인하고 없으면 초기화합니다.
    initialize_firebase()

    # Firestore 클라이언트를 반환합니다.
    return firestore.client()
