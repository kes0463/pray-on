# ====================================================
# ai_services.py - AI 기능 모듈 (Gemini 2.0 Flash + Google Cloud TTS)
# ====================================================
# 이 파일에는 두 가지 핵심 AI 기능이 담겨 있습니다:
#
# 1. generate_prayer(emotion): 사용자 감정을 받아 기도문 텍스트 생성 (Gemini 2.0 Flash)
# 2. text_to_speech(text, filename): 기도문 텍스트를 mp3 음성으로 변환 (Google Cloud TTS)
#
# ※ Gemini 무료 할당량: 분당 15회, 하루 1,500회
# ※ Google Cloud TTS WaveNet/Neural2 한국어 음성 사용 (월 100만 자 무료)
# ====================================================

import os
import re
import google.generativeai as genai
import hashlib
from elevenlabs import ElevenLabs, VoiceSettings
from dotenv import load_dotenv

# .env 파일에서 환경 변수(API 키 등)를 불러옵니다.
load_dotenv(override=True)

# --- Gemini 클라이언트 초기화 (기도문 생성용) ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 사용할 Gemini 모델
# gemini-2.0-flash: 빠르고 저렴, 한국어 품질 우수
# gemini-1.5-pro  : 더 강력하지만 느리고 비쌈
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Gemini 시스템 프롬프트 템플릿 (기도문 생성용)
# Gemini 시스템 프롬프트 템플릿 (기도문 생성용)
SYSTEM_PROMPT_TEMPLATE = (
    "당신은 따뜻하고 공감 능력이 탁월한 기독교 목사입니다. "
    "사용자가 자신의 감정이나 기도 제목을 알려주면, 아래 지침에 따라 오직 '기도문'만 출력하십시오.\n\n"
    "[필수 지침]\n"
    "1. 절대 서론 금지: '아이고~', '함께 기쁘네요', '기도하겠다' 등 기도를 시작하기 전의 어떠한 대답이나 대화, 인사말도 절대 쓰지 마십시오.\n"
    "2. 첫 글자 고정: 출력의 첫 글자는 반드시 '하나님 아버지,' 로 시작하십시오. 예외는 없습니다.\n"
    "3. 공감과 위로: '하나님 아버지,'로 기도를 시작한 직후, 기도 내용의 초반부에 사용자의 사연에 대한 공감과 위로를 담아 하나님께 간구하십시오.\n"
    "4. 성경 구절 포함: 관련 성경 말씀을 한두 구절 자연스럽게 기도문 중간에 녹여내십시오. 인용 시 반드시 '\"인용구\"는 (책 장:절) 말씀처럼,' 형식(인용구 뒤에 '는' 조사 추가)을 지키십시오.\n"
    "5. 마무리 고정: 반드시 '예수님의 이름으로 기도합니다. 아멘.' 으로 문장을 완벽히 맺으십시오.\n"
    "6. 말투: 일상적이고 다정하며 따뜻한 대화체를 유지하십시오.\n"
    "7. 분량: 500자 내외로 정성스럽게 작성하십시오. 절대로 문장 중간에 말을 끊지 말고, 반드시 '아멘.'으로 기도를 완결해야 합니다.\n"
    "8. 가독성(줄바꿈): 가독성을 위해 단락을 나누십시오. '하나님 아버지,'(도입), '공감 및 간구'(본문), '성경 인용', '마무리 기도 및 아멘' 사이에는 반드시 빈 줄(`\\n\\n`)을 하나씩 넣어 구분하십시오."
)

# --- ElevenLabs TTS 설정 ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# ElevenLabs 제공 고품질 한국어 지원 목소리 (Multilingual v2 모델)
# 추천 보이스 및 한글 이름 매핑 (파일명 가독성용)
VOICE_NAME_MAP = {
    "21m00Tcm4TlvDq8ikWAM": "김한나",
    "AZnzlk1XvdvUeBnXmlld": "박지민",
    "ErXwobaYiN019PkySvjV": "김동현",
    "2EiwWnXFnvU5JabPnv8n": "장동환",
    "JBFqnCBsd6RMkjVDRZzb": "최민준",
}
TTS_VOICE_NAME = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # 김한나 기본

# 생성된 음성 파일을 저장할 폴더 경로
AUDIO_DIR = os.path.join("static", "audio")


def generate_prayer(emotion: str) -> str:
    """
    사용자가 입력한 감정을 기반으로 기도문을 생성합니다.

    매개변수:
        emotion (str): 사용자가 입력한 감정 또는 기도 제목

    반환값:
        str: AI가 생성한 기도문 텍스트 (성경 구절 포함)
    """
    print(f"🙏 기도문 생성 중... (기도 제목: {emotion}, 모델: {GEMINI_MODEL})")

    # 고정된 프롬프트를 그대로 사용합니다.
    system_instruction = SYSTEM_PROMPT_TEMPLATE

    # Gemini 모델 인스턴스 생성
    # 안전 설정을 '전체 허용'으로 하여 의도치 않은 잘림을 방지합니다.
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    model = genai.GenerativeModel(
        model_name=f"models/{GEMINI_MODEL}",
        system_instruction=system_instruction,
        safety_settings=safety_settings
    )

    # 기도문 생성 요청
    # generation_config를 딕셔너리로 직접 전달하여 SDK 버전 간 호환성을 높입니다.
    response = model.generate_content(
        f"저의 현재 감정과 기도 제목: {emotion}",
        generation_config={
            "temperature": 0.8,
            "max_output_tokens": 2048,
            "top_p": 0.95,
            "top_k": 40
        }
    )

    # 응답 유효성 확인 및 오류 핸들링
    try:
        # candidates가 없거나 내부 part가 없는 경우에 대한 예외 처리
        if not response.candidates or not response.candidates[0].content.parts:
            reason = response.candidates[0].finish_reason if response.candidates else "알 수 없음"
            print(f"⚠️ 모델이 응답을 생성하지 못했습니다. (사유: {reason})")
            return "기도문 생성 중에 모델이 응답을 멈췄습니다. 잠시 후 다시 시도해 주세요."

        prayer_text = response.text.strip()
    except (AttributeError, IndexError) as e:
        print(f"❌ 응답 파싱 중 오류 발생: {e}")
        return "죄송합니다. 기도문을 생성하는 과정에서 기술적인 오류가 발생했습니다."

    if not prayer_text.endswith("아멘."):
        print(f"⚠️ 경고: 기도문이 '아멘.'으로 끝나지 않았습니다. (FinishReason: {response.candidates[0].finish_reason})")
    
    print("✅ 기도문 생성 완료!")
    return prayer_text


def text_to_speech(text: str, voice_id: str = TTS_VOICE_NAME, title: str = "기도문") -> str:
    """
    텍스트를 ElevenLabs API를 사용해 mp3 음성 파일로 변환합니다.

    매개변수:
        text (str): 음성으로 변환할 텍스트 (기도문)
        voice_id (str): 사용할 ElevenLabs 목소리 번호
        title (str): 파일명에 사용할 기도 제목 (감정/주제)

    반환값:
        str: 저장된 mp3 파일의 경로 (HTML audio 태그에서 사용 가능)
    """
    if not ELEVENLABS_API_KEY:
        print("❌ 오류: ELEVENLABS_API_KEY가 등록되지 않았습니다.")
        return ""

    # 음성 파일을 저장할 폴더가 없으면 만듭니다.
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # 1. 목소리 한글 이름 가져오기
    v_name = VOICE_NAME_MAP.get(voice_id, "알수없음")

    # 2. 제목 정제 (파일명으로 사용할 수 없는 문자 제거 및 길이 제한)
    # 특수문자 제거
    clean_title = re.sub(r'[\/:*?"<>|]', '', title).strip()
    # 공백을 언더바로 변경하고 최대 20자까지만 사용
    clean_title = clean_title.replace(" ", "_")[:20]
    if not clean_title: clean_title = "기도제목"

    # 3. 텍스트와 보이스 ID를 조합해 고유한 해시값을 만듭니다 (중복 방지용)
    cache_key = hashlib.md5(f"{text}_{voice_id}".encode("utf-8")).hexdigest()[:8]
    
    # 최종 파일명 형식: [목소리]_[제목]_[해시].mp3
    file_name = f"{v_name}_{clean_title}_{cache_key}.mp3"
    file_path = os.path.join(AUDIO_DIR, file_name)

    # 이미 동일한 음성 파일이 존재하면 바로 반환합니다 (할당량 절약!)
    if os.path.exists(file_path):
        print(f"♻️ 캐시된 음성 파일 재사용: {file_path}")
        return "/" + file_path.replace("\\", "/")

    print(f"🎙️ 음성 변환 중... (ElevenLabs, Voice ID: {voice_id})")

    try:
        # ElevenLabs 클라이언트 생성
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        
        # 음성 합성 요청 (최고 품질인 eleven_multilingual_v2 사용)
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            optimize_streaming_latency="0",
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,        # 0.0~1.0 (감점 표현 풍부하게 0.5)
                similarity_boost=0.75 # 기본 목소리 캐릭터 유지력
            )
        )

        # 제너레이터에서 데이터 읽어와 파일에 쓰기
        with open(file_path, "wb") as f:
            for chunk in audio_generator:
                f.write(chunk)

        print(f"✅ 음성 파일 저장 완료: {file_path}")
        return "/" + file_path.replace("\\", "/")

    except Exception as e:
        print(f"❌ ElevenLabs TTS 오류: {e}")
        return ""
