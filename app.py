# ====================================================
# app.py - Pray ON (프레이온) 메인 Flask 서버
# ====================================================
# 이 파일이 앱의 심장입니다.
# "python app.py" 명령어로 실행하면
# http://localhost:5000 주소에서 웹 서비스가 시작됩니다.
# ====================================================

import os
import re
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# 우리가 만든 모듈들을 불러옵니다.
from firebase_config import get_db
from ai_services import generate_prayer, text_to_speech

# ─────────────────────────────────────────────
# 기본 설정
# ─────────────────────────────────────────────

# .env 파일에서 환경 변수를 불러옵니다.
load_dotenv(override=True)  # 시스템 환경 변수보다 .env 파일을 우선 적용

# Flask 앱 객체를 생성합니다.
# __name__은 현재 파일 이름으로, Flask가 파일 위치를 파악하는 데 사용됩니다.
app = Flask(__name__)

# CORS: 안드로이드 앱(Capacitor)에서 API 호출을 허용합니다.
CORS(app)

# 세션 보안을 위한 비밀 키를 설정합니다.
app.secret_key = os.getenv("FLASK_SECRET_KEY", "pray-on-default-secret-key-change-this")

# Buy Me a Coffee URL을 환경변수에서 읽어옵니다.
COFFEE_URL = os.getenv("BUY_ME_A_COFFEE_URL", "https://www.buymeacoffee.com/YOUR_NAME")


# ─────────────────────────────────────────────
# 라우트(Route) 정의
# 라우트란 URL과 함수를 연결하는 것입니다.
# 예: 사용자가 "/" 주소로 접속하면 index() 함수가 실행됩니다.
# ─────────────────────────────────────────────

@app.route("/")
def index():
    """
    메인 페이지를 보여주는 함수.
    사용자가 http://localhost:5000 으로 접속하면 실행됩니다.
    """
    # templates/index.html 파일을 렌더링해서 사용자에게 보냅니다.
    # coffee_url은 HTML 파일 안에서 {{ coffee_url }} 형태로 사용됩니다.
    return render_template("index.html", coffee_url=COFFEE_URL)


@app.route("/generate", methods=["POST"])
def generate():
    """
    기도문 생성 API.
    프론트엔드에서 POST 요청을 보내면 실행됩니다.
    
    요청 형식 (JSON):
        { 
            "emotion": "요즘 너무 지쳐있어요",
            "tone": "따뜻하고 공감하는",
            "voice": "ko-KR-Neural2-C"
        }
    
    응답 형식 (JSON):
        {
            "success": true,
            "prayer": "하나님 아버지...",
            "audio_url": "/static/audio/prayer_xxx.mp3",
            "doc_id": "Firestore 문서 ID"
        }
    """
    try:
        # 요청 본문에서 JSON 데이터를 꺼냅니다.
        data = request.get_json()

        # 사용자가 입력한 데이터 가져오기
        emotion = data.get("emotion", "").strip()
        voice = data.get("voice", "uyVNoMrnUku1dZyVEXwD") # 김안나 (기본값)

        # 감정 입력이 비어 있으면 오류를 반환합니다.
        if not emotion:
            return jsonify({"success": False, "error": "기도 제목을 입력해 주세요."}), 400

        # 입력이 너무 길면 자릅니다 (API 비용 절약).
        if len(emotion) > 500:
            emotion = emotion[:500]

        # ① 기도문 생성 (Gemini)
        # 톤 파라미터는 기본값 처리하도록 수정됨
        prayer_text = generate_prayer(emotion)

        # ③ 음성 파일 생성 (Google Cloud TTS)
        # TTS 기계음이 성경 장/절(예: 시편 23:4)을 어색하게 읽지 않도록 텍스트에서 정규식으로 제거합니다.
        # 정규식 패턴: 괄호 안에 들어가 있는 문자+숫자:숫자 조합을 찾아서 제거
        clean_prayer_for_tts = re.sub(r'\(.*?\d+:\d+.*?\)', '', prayer_text).strip()

        audio_url = text_to_speech(clean_prayer_for_tts, voice, title=emotion)

        # ③ Firestore에 기도 기록 저장
        db = get_db()

        # 저장할 데이터를 딕셔너리로 구성합니다.
        prayer_data = {
            "emotion": emotion,           # 사용자가 입력한 감정
            "voice": voice,               # 사용자가 선택한 목소리
            "prayer": prayer_text,        # AI가 생성한 기도문
            "audio_url": audio_url,       # 음성 파일 경로
            "created_at": datetime.now(), # 생성 시각
        }

        # Firestore의 "prayers" 컬렉션에 문서를 추가합니다.
        # add()는 자동으로 문서 ID를 생성하고, 타임스탬프 기준으로 정렬됩니다.
        _, doc_ref = db.collection("prayers").add(prayer_data)

        print(f"✅ Firestore 저장 완료! 문서 ID: {doc_ref.id}")

        # 프론트엔드에 성공 응답을 보냅니다.
        return jsonify({
            "success": True,
            "prayer": prayer_text,
            "audio_url": audio_url,
            "doc_id": doc_ref.id,
            "created_at": prayer_data["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
        })

    except Exception as e:
        # 오류가 발생하면 콘솔에 출력하고 오류 응답을 반환합니다.
        print(f"❌ 기도문 생성 오류: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/tts-only", methods=["POST"])
def tts_only():
    """
    기도문 텍스트는 그대로 두고 목소리만 변경하여 다시 음성 파일을 생성하는 API.
    캐싱 덕분에 동일한 텍스트/목소리 조합은 즉시 반환됩니다.
    """
    try:
        data = request.json
        prayer_text = data.get("prayer", "").strip()
        voice = data.get("voice", "21m00Tcm4TlvDq8ikWAM")
        title = data.get("title", "기도문")

        if not prayer_text:
            return jsonify({"success": False, "error": "기도문 내용이 없습니다."}), 400

        # 특수 기호(성경 구절 등) 제거 후 TTS 변환
        clean_prayer_for_tts = re.sub(r'\(.*?\d+:\d+.*?\)', '', prayer_text).strip()
        audio_url = text_to_speech(clean_prayer_for_tts, voice, title=title)

        return jsonify({
            "success": True,
            "audio_url": audio_url
        })

    except Exception as e:
        print(f"❌ TTS 변환 오류: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/history", methods=["GET"])
def get_history():
    """
    저장된 기도 기록을 최신순으로 가져오는 API.
    
    응답 형식 (JSON):
        {
            "success": true,
            "prayers": [
                {
                    "id": "문서ID",
                    "emotion": "우울해요",
                    "prayer": "하나님 아버지...",
                    "audio_url": "/static/audio/...",
                    "created_at": "2024-01-01 12:00:00"
                },
                ...
            ]
        }
    """
    try:
        db = get_db()

        # Firestore에서 "prayers" 컬렉션의 문서를 최신순으로 최대 20개 가져옵니다.
        docs = (
            db.collection("prayers")
            .order_by("created_at", direction="DESCENDING")  # 최신 순 정렬
            .limit(20)                                         # 최대 20개
            .stream()                                          # 실제로 데이터 가져오기
        )

        # 가져온 문서들을 파이썬 딕셔너리 리스트로 변환합니다.
        prayers = []
        for doc in docs:
            data = doc.to_dict()

            # datetime 객체는 JSON 직렬화가 안 되므로 문자열로 변환합니다.
            created_at = data.get("created_at")
            if created_at:
                # Firestore Timestamp나 datetime 객체를 문자열로 변환
                if hasattr(created_at, "strftime"):
                    created_at = created_at.strftime("%Y년 %m월 %d일 %H:%M")
                else:
                    created_at = str(created_at)
            else:
                created_at = "시간 정보 없음"

            prayers.append({
                "id": doc.id,
                "emotion": data.get("emotion", ""),
                "prayer": data.get("prayer", ""),
                "audio_url": data.get("audio_url", ""),
                "created_at": created_at,
            })

        return jsonify({"success": True, "prayers": prayers})

    except Exception as e:
        print(f"❌ 기도 기록 조회 오류: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/history/<doc_id>", methods=["DELETE"])
def delete_prayer(doc_id):
    """
    특정 기도 기록을 삭제하는 API.
    
    URL 예시: DELETE /history/abc123xyz
    """
    try:
        db = get_db()

        # Firestore에서 해당 문서를 삭제합니다.
        db.collection("prayers").document(doc_id).delete()

        print(f"🗑️ 기도 기록 삭제 완료: {doc_id}")
        return jsonify({"success": True, "message": "삭제되었습니다."})

    except Exception as e:
        print(f"❌ 삭제 오류: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────
# 서버 실행
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # static/audio 폴더가 없으면 미리 생성합니다.
    os.makedirs(os.path.join("static", "audio"), exist_ok=True)

    print("=" * 50)
    print("🙏 Pray ON 서버가 시작됩니다...")
    print("📌 브라우저에서 http://localhost:5000 으로 접속하세요!")
    print("=" * 50)

    # Railway는 PORT 환경변수를 동적으로 할당합니다.
    port = int(os.getenv("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
