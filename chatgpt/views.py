# chatgpt/views.py
import re
import os
from dotenv import load_dotenv
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from openai import OpenAI
from django.contrib.auth import get_user_model
import google.generativeai as palm
from time import sleep
from tenacity import retry, stop_after_attempt, wait_exponential
from .models import Conversation, Message
from .serializers import ConversationSerializer

load_dotenv()

User = get_user_model()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    
    def get_admin_user(self):
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'is_staff': True,
                'is_superuser': True,
                'email': 'admin@example.com'
            }
        )
        if created:
            admin_user.set_password('admin')
            admin_user.save()
        return admin_user

    def get_queryset(self):
        admin_user = self.get_admin_user()
        return Conversation.objects.filter(user=admin_user)

    def perform_create(self, serializer):
        admin_user = self.get_admin_user()
        serializer.save(user=admin_user)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def call_gemini_api(self, model, prompt):
        response = model.generate_content(prompt)
        if not response or not response.text:
            raise Exception("API 응답이 비어있습니다.")
        return response.text

    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        conversation = self.get_object()
        user_message = request.data.get('message')
        system_prompt = request.data.get(
            'system_prompt',
            "정말 다정하게."  # 기본값은 다정하게
        )
        
        if not user_message:
            return Response(
                {'error': '메시지를 입력해주세요.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 사용자 메시지 저장
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message
        )

        try:
            # 구글 Gemini API 초기화
            palm.configure(api_key=GOOGLE_API_KEY)
            model = palm.GenerativeModel('gemini-2.0-flash')

            # 대화 기록 구성
            messages_qs = conversation.messages.all().order_by('created_at')
            conversation_history = ""
            for msg in messages_qs:
                if msg.role == 'user':
                    conversation_history += f"사용자: {msg.content}\n"
                else:
                    conversation_history += f"어시스턴트: {msg.content}\n"

            # 프롬프트 구성
            prompt = f"""
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

            # API 호출 (재시도 로직 포함)
            try:
                bot_response = self.call_gemini_api(model, prompt)
            except Exception as api_error:
                print(f"API 호출 실패: {str(api_error)}")
                bot_response = "죄송해요, 지금은 제가 잠시 말을 잘 못하겠어요. 잠시 후에 다시 이야기해주실래요?"
            
            print(f"원본 메시지: {bot_response}")
            
            # 응답에서 번역된 메시지 추출
            try:
                match = re.search(r':\s*"([^"]+)"', bot_response)
                translated_message = match.group(1) if match else bot_response.strip()

                print(f"추출 메시지: {translated_message}")
            except:
                translated_message = bot_response

            
            
            # 봇 응답 저장
            Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=bot_response,
                translated_content=translated_message
            )

            return Response({
                'message': translated_message
            })

        except Exception as e:
            error_msg = f"오류 발생: {str(e)}"
            print(error_msg)
            return Response(
                {'error': error_msg}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def chat_interface(self, request):
        admin_user = self.get_admin_user()
        conversation = Conversation.objects.filter(user=admin_user).first()
        if not conversation:
            conversation = Conversation.objects.create(user=admin_user)
        return render(request, 'chatgpt/chat.html', {
            'conversation_id': conversation.id
        })

    @action(detail=True, methods=['delete'])
    def delete_conversation(self, request, pk=None):
        try:
            conversation = self.get_object()
            # 관련된 메시지들도 함께 삭제됩니다 (모델의 on_delete=CASCADE 설정으로)
            conversation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )