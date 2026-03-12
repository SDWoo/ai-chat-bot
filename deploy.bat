@echo off
chcp 65001 >nul
echo 🚀 Sindoh AI 프로덕션 배포 시작...

if not exist .env (
  echo ❌ .env 파일이 없습니다.
  echo    .env.prod.example을 복사하여 .env를 만들고 필수 값을 설정하세요:
  echo    copy .env.prod.example .env
  exit /b 1
)

echo 📦 Docker 이미지 빌드 및 컨테이너 시작...
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

echo.
echo ✅ 배포 완료!
echo    앱 접속: http://localhost:80
echo    상태 확인: docker compose -f docker-compose.prod.yml ps
