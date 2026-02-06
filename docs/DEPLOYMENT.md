# Деплой CrowdCount на Dokploy

## Архитектура

```
Internet
    │
    ▼
┌─────────────────────┐
│  Cloudflare Tunnel  │  (уже настроен на другой VM)
│  crown.nemytnaya.ru │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│           Dokploy / Traefik             │
│               (port 80)                 │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│         crowdcount-internal             │
│         (Docker network)                │
│                                         │
│  ┌─────────────┐    ┌─────────────┐    │
│  │  frontend   │───►│  backend    │    │
│  │  (Next.js)  │    │  (FastAPI)  │    │
│  │  :3000      │    │  :8000      │    │
│  │             │    │  INTERNAL   │    │
│  │  EXPOSED    │    │  ONLY       │    │
│  └─────────────┘    └─────────────┘    │
│                            │            │
│                            ▼            │
│                     ┌─────────────┐    │
│                     │   SQLite    │    │
│                     │   volume    │    │
│                     └─────────────┘    │
└─────────────────────────────────────────┘
```

**Важно:**
- Только frontend доступен снаружи через `crown.nemytnaya.ru`
- Backend API доступен ТОЛЬКО внутри Docker сети
- Все API запросы от браузера проксируются через Next.js API routes

## Деплой через Dokploy

### 1. Создание приложения

1. В Dokploy создайте новое приложение типа **Compose**
2. Укажите URL репозитория или загрузите код
3. Compose файл: `docker-compose.yml`

### 2. Настройка домена

В Dokploy настройте домен для сервиса `frontend`:
- Domain: `crown.nemytnaya.ru`
- Container Port: `3000`
- HTTPS: через Cloudflare Tunnel (Let's Encrypt отключить)

**Не добавляйте домен для backend** — он должен быть только внутренним.

### 3. Cloudflare Tunnel

Туннель уже настроен на другой VM. Убедитесь, что:
- Public hostname: `crown.nemytnaya.ru`
- Service: `http://dokploy-traefik:80` или IP вашего сервера
- SSL: Full (Strict) в настройках Cloudflare

### 4. Deploy

```bash
# Через Dokploy UI или CLI
dokploy deploy
```

## Структура запросов

```
Браузер пользователя
        │
        │  GET https://crown.nemytnaya.ru/api/rooms
        ▼
┌─────────────────────┐
│  Cloudflare Tunnel  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  frontend (Next.js) │
│                     │
│  /api/[...path]     │  ← API route proxy
│         │           │
│         ▼           │
│  fetch(backend:8000)│
└──────────┬──────────┘
           │  (внутренняя сеть Docker)
           ▼
┌─────────────────────┐
│  backend (FastAPI)  │
│  :8000 (internal)   │
└─────────────────────┘
```

## Проверка после деплоя

### Проверка фронтенда
```bash
curl https://crown.nemytnaya.ru
# Должен вернуть HTML страницу
```

### Проверка API через прокси
```bash
curl https://crown.nemytnaya.ru/api/status
# Должен вернуть JSON со статусом системы
```

### Проверка что backend НЕ доступен снаружи
```bash
curl http://your-server-ip:8000/health
# Должна быть ошибка Connection refused
```

## Первоначальная настройка

1. Откройте `https://crown.nemytnaya.ru`
2. Перейдите в **Settings → Залы**
3. Добавьте зал:
   - ID: `hall-1`
   - Название: `Главный зал`
   - Вместимость: `300`
   - URL камеры: `rtsp://admin:password@10.0.0.101:554/Streaming/Channels/102`

## Логи

```bash
# Backend
docker logs crowdcount-backend -f

# Frontend
docker logs crowdcount-frontend -f
```

## Бэкап базы данных

```bash
# Бэкап
docker cp crowdcount-backend:/app/data/crowdcount.db ./backup.db

# Восстановление
docker cp ./backup.db crowdcount-backend:/app/data/crowdcount.db
```

## Troubleshooting

### API возвращает 502 Bad Gateway

1. Проверьте что backend запущен:
   ```bash
   docker logs crowdcount-backend
   ```
2. Проверьте healthcheck:
   ```bash
   docker exec crowdcount-backend curl http://localhost:8000/health
   ```

### Камера не подключается

Backend должен иметь сетевой доступ к камерам. Убедитесь что:
1. Сервер в одной сети с камерами
2. Порт 554 (RTSP) открыт
3. Учётные данные камеры верны
