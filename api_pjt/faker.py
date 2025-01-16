from articles.models import Article, Comment
from faker import Faker

fake = Faker()

# 아티클 20개 생성
for _ in range(20):
    article = Article.objects.create(
        title=fake.sentence(),
        content=fake.paragraph()
    )
    # 각 아티클에 코멘트 5개 생성
    for _ in range(5):
        Comment.objects.create(
            article=article,
            content=fake.sentence()
        )
        
        
