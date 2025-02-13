# chatgpt/views.py
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Conversation, Message
from .serializers import ConversationSerializer
from .llm import GeminiLLM, OpenAILLM

User = get_user_model()

class BaseChatViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def process_chat(self, request, llm, pk=None):
        conversation = self.get_object()
        user_message = request.data.get('message')
        system_prompt = request.data.get(
            'system_prompt',
            "상대방에게 원하는 태도를 입력해주세요."
        )
        
        if not user_message:
            return Response(
                {'error': '메시지를 입력해주세요.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message
        )

        messages_qs = conversation.messages.all().order_by('created_at')
        conversation_history = ""
        for msg in messages_qs:
            if msg.role == 'user':
                conversation_history += f"사용자: {msg.content}\n"
            else:
                conversation_history += f"어시스턴트: {msg.content}\n"

        response = llm.get_response(conversation_history, user_message, system_prompt)
        
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response['original_response'] if response['success'] else response['translated_message'],
            translated_content=response['translated_message']
        )

        return Response({'message': response['translated_message']})

    @action(detail=True, methods=['delete'])
    def delete_conversation(self, request, pk=None):
        conversation = self.get_object()
        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GeminiChatViewSet(BaseChatViewSet):
    llm = GeminiLLM()

    def get_queryset(self):
        return Conversation.objects.filter(
            user=self.request.user,
            llm_type='gemini'
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, llm_type='gemini')

    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        return self.process_chat(request, self.llm, pk)

    @action(detail=False, methods=['get'])
    def chat_interface(self, request):
        conversation = Conversation.objects.filter(
            user=request.user,
            llm_type='gemini'
        ).first()
        if not conversation:
            conversation = Conversation.objects.create(
                user=request.user,
                llm_type='gemini'
            )
        return render(request, 'chatgpt/chat_gemini.html', {
            'conversation_id': conversation.id
        })


class OpenAIChatViewSet(BaseChatViewSet):
    llm = OpenAILLM()

    def get_queryset(self):
        return Conversation.objects.filter(
            user=self.request.user,
            llm_type='openai'
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, llm_type='openai')

    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        return self.process_chat(request, self.llm, pk)

    @action(detail=False, methods=['get'])
    def chat_interface(self, request):
        conversation = Conversation.objects.filter(
            user=request.user,
            llm_type='openai'
        ).first()
        if not conversation:
            conversation = Conversation.objects.create(
                user=request.user,
                llm_type='openai'
            )
        return render(request, 'chatgpt/chat_openai.html', {
            'conversation_id': conversation.id
        })