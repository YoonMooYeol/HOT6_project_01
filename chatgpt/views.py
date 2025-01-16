# chatgpt/views.py
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from openai import OpenAI
from django.contrib.auth import get_user_model

from api_pjt.config import OPENAI_API_KEY
from .models import Conversation, Message
from .serializers import ConversationSerializer



User = get_user_model()

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

    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        conversation = self.get_object()
        user_message = request.data.get('message')
        
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

        # ChatGPT API 호출
        client = OpenAI(api_key=OPENAI_API_KEY)
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        messages.extend([
            {"role": msg.role, "content": msg.content}
            for msg in conversation.messages.all().order_by('created_at')
        ])

        try:
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            
            bot_response = completion.choices[0].message.content
            
            # 봇 응답 저장
            Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=bot_response
            )

            return Response({
                'message': bot_response
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
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