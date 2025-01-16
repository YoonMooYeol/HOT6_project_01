from django import forms
from .models import Article, Comment


class AricleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = "__all__"
        exclude = ()    
        
        
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = "__all__"
        read_only_fields = ['article']   
        