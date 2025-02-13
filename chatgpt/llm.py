import os
import re
from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as palm
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class GeminiLLM:
    def __init__(self):
        self.api_key = GOOGLE_API_KEY
        palm.configure(api_key=self.api_key)
        self.model = palm.GenerativeModel('gemini-2.0-flash')

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def call_gemini_api(self, prompt):
        response = self.model.generate_content(prompt)
        if not response or not response.text:
            raise Exception("API 응답이 비어있습니다.")
        return response.text

    def create_prompt(self, conversation_history, user_message, system_prompt):
        return f"""
규칙:
1. 저의 메시지에 응답할 때 대립적이지 않고 부드러운 어조를 유지하면서 마치 제가 직접 말하는 것처럼 제 말로 번역해서 답변해주세요.(여기서 번역의 뜻은 한국어로 번역이 아닙니다. 다정한 말투로 나의 말을 바꿔달라는 의미입니다.) 차분하고 존중하는 태도로 상대방의 감정과 우려를 전달할 수 있는 저의 답변만을 간략하게 작성해 주세요.
2.(제일중요)저는 ai와 대화하는게 아닙니다. 저의 연인과 대화하는중입니다. 간단하게 10글자 이내로 나의 말을 다음과 같은 태도로 번역해서 답변해주세요.
3. 다음 입력되는 태도로 말해주십시오. : {system_prompt}

이전 대화:
{conversation_history}

사용자의 메시지: {user_message}

사용자의 메세지를 읽고 번역된 메세지를 반드시 다음의 형식으로 작성해주세요.
답변형식: "사용자의 메세지" : "번역된 메세지"
"""

    def extract_translated_message(self, bot_response):
        try:
            match = re.search(r':\s*"([^"]+)"', bot_response)
            return match.group(1) if match else bot_response.strip()
        except:
            return bot_response

    def get_response(self, conversation_history, user_message, system_prompt):
        try:
            prompt = self.create_prompt(conversation_history, user_message, system_prompt)
            bot_response = self.call_gemini_api(prompt)
            translated_message = self.extract_translated_message(bot_response)
            
            return {
                'success': True,
                'original_response': bot_response,
                'translated_message': translated_message
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'translated_message': "죄송해요, 지금은 제가 잠시 말을 잘 못하겠어요. 잠시 후에 다시 이야기해주실래요?"
            }


class OpenAILLM:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = "gpt-4-turbo-preview"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def call_openai_api(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        if not response.choices or not response.choices[0].message.content:
            raise Exception("API 응답이 비어있습니다.")
        return response.choices[0].message.content

    def create_messages(self, conversation_history, user_message, system_prompt):
        return [
            {
                "role": "system",
                "content": f"""
당신은 연인 사이의 대화를 더 부드럽게 만들어주는 번역기입니다.
다음 규칙을 반드시 따라주세요:
1. 사용자의 메시지를 10글자 이내로 번역해주세요.
2. 번역된 메시지는 반드시 "{system_prompt}" 태도로 표현해주세요.
3. 응답은 반드시 다음 형식을 지켜주세요: "사용자의 메세지" : "번역된 메세지"
"""
            },
            {
                "role": "user",
                "content": f"대화 기록:\n{conversation_history}\n\n현재 메시지: {user_message}"
            }
        ]

    def extract_translated_message(self, bot_response):
        try:
            match = re.search(r':\s*"([^"]+)"', bot_response)
            return match.group(1) if match else bot_response.strip()
        except:
            return bot_response

    def get_response(self, conversation_history, user_message, system_prompt):
        try:
            messages = self.create_messages(conversation_history, user_message, system_prompt)
            bot_response = self.call_openai_api(messages)
            translated_message = self.extract_translated_message(bot_response)
            
            return {
                'success': True,
                'original_response': bot_response,
                'translated_message': translated_message
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'translated_message': "죄송해요, 지금은 제가 잠시 말을 잘 못하겠어요. 잠시 후에 다시 이야기해주실래요?"
            }
