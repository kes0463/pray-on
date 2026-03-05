# ====================================================
# firebase_config.py - Firebase 초기화 모듈
# ====================================================
# 이 파일은 Firebase Admin SDK를 초기화하고,
# Firestore 데이터베이스 클라이언트를 반환하는 함수를 제공합니다.
# 다른 파일에서 "from firebase_config import get_db" 형태로 불러와 사용합니다.
# ====================================================

import os
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

        # serviceAccountKey.json 파일 경로를 .env에서 읽어옵니다.
        credential_path = os.getenv(
            "FIREBASE_CREDENTIAL_PATH", "serviceAccountKey.json"
        )

        # 파일이 존재하는지 확인합니다.
        if not os.path.exists(credential_path):
            raise FileNotFoundError(
                f"Firebase 서비스 계정 키 파일을 찾을 수 없습니다: '{credential_path}'\n"
                "Firebase 콘솔 → 프로젝트 설정 → 서비스 계정 → "
                "'새 비공개 키 생성'을 클릭하여 JSON 파일을 다운로드한 뒤 "
                "프로젝트 폴더에 'serviceAccountKey.json' 이름으로 저장하세요."
            )

        # 서비스 계정 JSON 파일로 인증 정보를 생성합니다.
        cred = credentials.Certificate(credential_path)

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
