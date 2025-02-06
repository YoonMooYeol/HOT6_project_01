
# Project : 화내지마 자기야

## 프로젝트 소개
연인사이의 대화를 좀 더 다정하게 만들어주는 채팅 서비스입니다.
## 팀원 소개
- 한세희(리더)
- 윤무열
- 김현호
- 장지윤


## 기술 스택

### Backend
- Python 3.10
- Django 5.1.4
- Django REST Framework
- PostgreSQL
- Redis

### Frontend
- Vue.js

### Authentication
- JWT Authentication

### External API
- Google ai studio API

## 주요 기능

- JWT 기반 사용자 인증
- LLM API 연동
- Redis 캐싱
- 성능 모니터링 (Silk)

## 설치 방법

1. 저장소 클론
```bash
git clone [repository URL]
cd api_pjt
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경변수 설정
```bash
# .env 파일 생성
GOOGLE_API_KEY=your_api_key_here
```

5. 데이터베이스 마이그레이션
```bash
python manage.py makemigrations
python manage.py migrate
```

6. 서버 실행
```bash
python manage.py runserver
```

## API 문서

- Swagger UI: `/api/v1/schema/swagger-ui/`
- ReDoc: `/api/v1/schema/redoc/`

## 성능 모니터링

- Silk: `/silk/`

## 주요 엔드포인트

- Admin: `/admin/`
- ChatGPT API: `/api/v1/chatgpt/chat`

## 캐싱 설정

Redis를 사용하여 캐싱을 구현했습니다. Redis 서버가 필요합니다:
```bash
# Redis 서버 실행 (Windows의 경우 WSL 또는 Docker 사용 권장)
redis-server
```

## 라이선스

This project is licensed under the MIT License - see the LICENSE file for details
```

이 README.md는 프로젝트의 주요 기능, 설치 방법, API 문서 위치 등 중요한 정보를 포함하고 있습니다. 필요에 따라 내용을 수정하거나 추가하실 수 있습니다.
