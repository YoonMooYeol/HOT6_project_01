# chat/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GeminiChatViewSet, OpenAIChatViewSet

gemini_router = DefaultRouter()
gemini_router.register(r'conversations', GeminiChatViewSet, basename='gemini_conversation')

openai_router = DefaultRouter()
openai_router.register(r'conversations', OpenAIChatViewSet, basename='openai_conversation')

urlpatterns = [
    path('gemini/', include((gemini_router.urls, 'gemini'))),
    path('openai/', include((openai_router.urls, 'openai'))),
]   