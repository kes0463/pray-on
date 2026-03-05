import os
from dotenv import load_dotenv
import requests

# .env 파일에서 환경 변수 불러오기
load_dotenv(override=True)

api_key = os.getenv('ELEVENLABS_API_KEY')
print(f'Using API Key check: {api_key[:5]}...{api_key[-5:]}' if api_key else 'No API Key found')

url = 'https://api.elevenlabs.io/v1/user/subscription'
headers = {'xi-api-key': api_key}

try:
    response = requests.get(url, headers=headers)
    print(f'Status Code: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print('--- Subscription Info ---')
        print(f'Character Count: {data.get("character_count")}')
        print(f'Character Limit: {data.get("character_limit")}')
        print(f'Remaining: {data.get("character_limit") - data.get("character_count")}')
        print(f'Tier: {data.get("tier")}')
    else:
        print(f'Error Body: {response.text}')
except Exception as e:
    print(f'Exception: {e}')
