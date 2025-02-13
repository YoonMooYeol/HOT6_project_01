# chat/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Conversation(models.Model):
    LLM_CHOICES = (
        ('gemini', 'Gemini'),
        ('openai', 'OpenAI'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    llm_type = models.CharField(max_length=10, choices=LLM_CHOICES, default='gemini')

class Message(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    )
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    translated_content = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)