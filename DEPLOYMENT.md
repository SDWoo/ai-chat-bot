# Deployment Guide

## Production Deployment

### 환경 준비

1. 서버 요구사항:
   - Ubuntu 20.04+ 또는 유사 Linux 배포판
   - Docker & Docker Compose 설치
   - 최소 4GB RAM, 20GB 디스크
   - 도메인 및 SSL 인증서 (Let's Encrypt 권장)

2. 환경 변수 설정:

```bash
cp .env.example .env
nano .env
```

필수 환경 변수:
```env
OPENAI_API_KEY=your-production-api-key
JWT_SECRET_KEY=your-strong-secret-key
ENVIRONMENT=production
DEBUG=False
CORS_ORIGINS=https://yourdomain.com
```

### Docker Compose로 배포

```bash
docker-compose -f docker-compose.yml up -d
```

### Nginx 리버스 프록시 설정

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
    }
}
```

### SSL 인증서 발급 (Let's Encrypt)

```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### 백업 설정

#### 데이터베이스 백업

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)

docker exec chatbot-postgres pg_dump -U chatbot chatbot > $BACKUP_DIR/backup_$DATE.sql

find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
```

cron 설정:
```bash
0 2 * * * /path/to/backup.sh
```

#### 벡터DB 백업

```bash
tar -czf /backups/chromadb_$(date +%Y%m%d).tar.gz ./data/chromadb
```

### 모니터링

#### 로그 확인

```bash
docker-compose logs -f --tail=100 backend
```

#### 시스템 상태 확인

```bash
curl https://yourdomain.com/api/health
```

#### 리소스 모니터링

```bash
docker stats
```

### 업데이트 절차

1. 최신 코드 가져오기:
```bash
git pull origin main
```

2. 서비스 재시작:
```bash
docker-compose down
docker-compose up -d --build
```

3. 마이그레이션 실행 (필요시):
```bash
docker exec chatbot-backend alembic upgrade head
```

### 트러블슈팅

#### 컨테이너가 재시작을 반복할 때

```bash
docker-compose logs backend
docker-compose restart backend
```

#### 데이터베이스 연결 오류

```bash
docker-compose exec postgres psql -U chatbot
```

#### 디스크 공간 부족

```bash
docker system prune -a
docker volume prune
```

## 스케일링

### 수평 스케일링

여러 백엔드 인스턴스 실행:

```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      replicas: 3
    environment:
      - WORKERS=4
```

### 로드 밸런서 설정

Nginx 업스트림:

```nginx
upstream backend {
    least_conn;
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}
```

### 데이터베이스 최적화

PostgreSQL 설정 튜닝:

```conf
# postgresql.conf
max_connections = 200
shared_buffers = 1GB
effective_cache_size = 3GB
work_mem = 16MB
maintenance_work_mem = 256MB
```

### Redis 클러스터링

프로덕션 환경에서는 Redis Sentinel 또는 Cluster 사용 권장

## 보안 체크리스트

- [ ] 환경 변수에 비밀 키 설정
- [ ] HTTPS 활성화
- [ ] CORS 설정 제한
- [ ] Rate Limiting 구현
- [ ] 파일 업로드 검증 강화
- [ ] 정기적인 보안 업데이트
- [ ] 데이터베이스 백업 자동화
- [ ] 로그 모니터링 설정
- [ ] 방화벽 규칙 설정
- [ ] JWT 토큰 만료 시간 설정

## 성능 최적화

1. **임베딩 캐싱**: Redis를 통한 자동 캐싱
2. **연결 풀링**: PostgreSQL 연결 풀 최적화
3. **CDN 사용**: 정적 파일 캐싱
4. **Gzip 압축**: Nginx에서 활성화
5. **인덱싱**: 데이터베이스 쿼리 최적화

## 비용 최적화

1. **OpenAI API**: 
   - 임베딩 결과 캐싱으로 API 호출 감소
   - GPT-3.5-turbo 사용 고려 (비용 효율적)

2. **인프라**:
   - 사용하지 않는 리소스 정리
   - Auto-scaling 설정
   - 예약 인스턴스 활용

## 지원

문제가 발생하면 GitHub Issues에 보고해주세요.
