from rest_framework import serializers
from .models import Article, Comment

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"
        read_only_fields = ['article']
        
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret.pop('article')
        return ret
        

class ArticleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'created_at', 'updated_at',]
        
        
class ArticleDetailSerializer(ArticleSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    
    class Meta(ArticleSerializer.Meta):
        fields = ArticleSerializer.Meta.fields + ['comments_count', 'comments',]