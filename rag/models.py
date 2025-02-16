from django.db import models

# Create your models here.

class Message(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=100)
    input_content = models.TextField()
    output_content = models.TextField()
    translated_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'messages'
        ordering = ['-created_at']

    def __str__(self):
        return f"Message {self.id} from user {self.user_id}"

class JsonFile(models.Model):
    id = models.BigAutoField(primary_key=True)
    file_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'json_files'
