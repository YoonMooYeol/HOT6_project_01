from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated


from .models import Article, Comment
from .serializers import (
    ArticleSerializer, 
    CommentSerializer, 
    ArticleDetailSerializer
)




# APIView 사용
class ArticleListAPIView(APIView):
    
    permission_classes = [IsAuthenticated]
        
    def get(self, request):
        articles = Article.objects.all()
        serializers = ArticleSerializer(articles, many=True)
        return Response(serializers.data)
    
    def post(self, request):
        serializers = ArticleSerializer(data=request.data)
        if serializers.is_valid(raise_exception=True):
            serializers.save()
            return Response(serializers.data, status=status.HTTP_201_CREATED)
    
    
class ArticleDetailAPIView(APIView):
    
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        return get_object_or_404(Article, pk=pk)
        
    def get(self, request, pk):
        article = self.get_object(pk)
        serializers = ArticleDetailSerializer(article)
        return Response(serializers.data)
    
    def delete(self, request, pk):
        article = self.get_object(pk)
        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def put(self, request, pk):
        article = self.get_object(pk)
        serializers = ArticleSerializer(article, data=request.data, partial=True)
        if serializers.is_valid(raise_exception=True):
            serializers.save()
            return Response(serializers.data)
        
           
class CommentListAPIView(APIView):
    
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        return get_object_or_404(Article, pk=pk)
    
    def get(self, request, pk):
        article = self.get_object(pk)
        comment = article.comments.all()
        serializers = CommentSerializer(comment, many=True)
        return Response(serializers.data)
    
    def post(self, request, pk):
        article = self.get_object(pk)
        serializers = CommentSerializer(data=request.data)
        if serializers.is_valid(raise_exception=True):
            serializers.save(article=article)
            return Response(serializers.data, status=status.HTTP_201_CREATED)
        
        
class CommentDetailAPIView(APIView):
    
    permission_classes = [IsAuthenticated]
        
    def get_object(self, pk):
        return get_object_or_404(Comment, pk=pk)
    
    def get(self, request, pk):
        comment = self.get_object(pk)
        serializers = CommentSerializer(comment)
        return Response(serializers.data)
    
    def delete(self, request, pk):
        comment = self.get_object(pk)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def put(self, request, pk):
        comment = self.get_object(pk)
        serializers = CommentSerializer(comment, data=request.data, partial=True)
        if serializers.is_valid(raise_exception=True):
            serializers.save()
            return Response(serializers.data)


# # 제네릭 뷰 사용
# from django.shortcuts import get_object_or_404
# from .models import Article
# from rest_framework import generics
# from .serializers import ArticleSerializer

# class ArticleListAPIView(generics.ListCreateAPIView):
#     queryset = Article.objects.all()
#     serializer_class = ArticleSerializer

# class ArticleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Article.objects.all()
#     serializer_class = ArticleSerializer        


# # 뷰셋 사용
# from requests import Response
# from rest_framework import viewsets
# from .models import Article, Comment
# from .serializers import ArticleSerializer, CommentSerializer
# from rest_framework.decorators import action

# class ArticleViewSet(viewsets.ModelViewSet):
#     queryset = Article.objects.all()
#     serializer_class = ArticleSerializer
    
    
# class CommentViewSet(viewsets.ModelViewSet):
#     queryset = Comment.objects.all()
#     serializer_class = CommentSerializer
    
#     @action(detail=True, methods=['get'], url_path='comments')
#     def by_article(self, request, pk=None):
#         comments = Comment.objects.filter(article_id=pk)
#         serializer = CommentSerializer(comments, many=True)
#         return Response(serializer.data)