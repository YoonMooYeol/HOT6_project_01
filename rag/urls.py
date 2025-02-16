from django.urls import path
from .views import RagSetupViewSet, RagChatViewSet, RagSyncViewSet

urlpatterns = [
    path('setup/', RagSetupViewSet.as_view(), name='rag-setup'),
    path('chat/', RagChatViewSet.as_view(), name='rag-chat'),
    path('sync/', RagSyncViewSet.as_view(), name='rag-sync'),
]
