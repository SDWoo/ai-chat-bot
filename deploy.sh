#!/bin/bash
# Sindoh AI 프로덕션 배포 스크립트

set -e

echo "🚀 Sindoh AI 프로덕션 배포 시작..."

# .env 확인
if [ ! -f .env ]; then
  echo "❌ .env 파일이 없습니다."
  echo "   .env.prod.example을 복사하여 .env를 만들고 필수 값을 설정하세요:"
  echo "   cp .env.prod.example .env"
  exit 1
fi

# 필수 환경 변수 확인
for var in OPENAI_API_KEY POSTGRES_PASSWORD JWT_SECRET_KEY; do
  if ! grep -q "^${var}=.\+" .env 2>/dev/null; then
    echo "❌ .env에 ${var}가 설정되지 않았습니다."
    exit 1
  fi
done

echo "📦 Docker 이미지 빌드 및 컨테이너 시작..."
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "✅ 배포 완료!"
echo "   앱 접속: http://localhost:${PORT:-80}"
echo "   상태 확인: docker compose -f docker-compose.prod.yml ps"
