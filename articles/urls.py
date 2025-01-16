# from django.urls import path
# from . import views

# app_name = "articles"
# urlpatterns = [
#     path("", views.ArticleListAPIView.as_view(), name="article_list"),
#     path("<int:pk>/", views.ArticleDetailAPIView.as_view(), name="article"),
    
# ]


from django.urls import path
from . import views

app_name = "articles"
urlpatterns = [
    path("", views.ArticleListAPIView.as_view(), name="article_list"),
    path("<int:pk>/", views.ArticleDetailAPIView.as_view(), name="article"),
    path("<int:pk>/comments/", views.CommentListAPIView.as_view(), name="comment_list"),
    path("comment/<int:pk>/", views.CommentDetailAPIView.as_view(), name="comment"),
]


# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import ArticleViewSet, CommentViewSet

# router = DefaultRouter()
# router.register(r'articles', ArticleViewSet)
# router.register(r'comments', CommentViewSet)

# urlpatterns = [
#     path('', include(router.urls)),
# ]