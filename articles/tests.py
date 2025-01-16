from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Article, Comment

class ArticleTests(APITestCase):
    def setUp(self):
        self.article_data = {'title': 'Test Article', 'content': 'This is a test article.'}
        self.article = Article.objects.create(**self.article_data)
        self.comment_data = {'content': 'This is a test comment.', 'article': self.article}
        self.comment = Comment.objects.create(**self.comment_data)

    def test_create_article(self):
        url = reverse('articles:article_list')
        response = self.client.post(url, self.article_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Article.objects.get(id=response.data['id']).title, self.article_data['title'])

    def test_get_article_list(self):
        url = reverse('articles:article_list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_article_detail(self):
        url = reverse('articles:article', args=[self.article.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.article_data['title'])

    def test_update_article(self):
        url = reverse('articles:article', args=[self.article.id])
        updated_data = {'title': 'Updated Test Article', 'content': 'This is an updated test article.'}
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Article.objects.get(id=self.article.id).title, updated_data['title'])

    def test_delete_article(self):
        url = reverse('articles:article', args=[self.article.id])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Article.objects.count(), 0)

    def test_create_comment(self):
        url = reverse('articles:comment_list', args=[self.article.id])
        comment_data = {'content': 'This is another test comment.'}
        response = self.client.post(url, comment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 2)
        self.assertEqual(Comment.objects.get(id=response.data['id']).content, comment_data['content'])

    def test_get_comment_list(self):
        url = reverse('articles:comment_list', args=[self.article.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_comment_detail(self):
        url = reverse('articles:comment', args=[self.comment.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], self.comment_data['content'])

    def test_update_comment(self):
        url = reverse('articles:comment', args=[self.comment.id])
        updated_data = {'content': 'This is an updated test comment.'}
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Comment.objects.get(id=self.comment.id).content, updated_data['content'])

    def test_delete_comment(self):
        url = reverse('articles:comment', args=[self.comment.id])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)
