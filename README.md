# FastAPI Микросервисы: ToDo и Short URL

Два микросервиса на базе FastAPI с хранением данных в SQLite:
- **ToDo-сервис** - CRUD операции для списка задач
- **Сервис сокращения URL** - создание коротких ссылок с редиректом и статистикой

- [x] Каждый сервис - отдельное FastAPI-приложение
- [x] Автоматическая документация по адресу `/docs`
- [x] Хранение данных в SQLite

### ToDo-сервис:
- [x] POST /items - создание задачи
- [x] GET /items - получение списка задач
- [x] GET /items/{item_id} - получение задачи по ID
- [x] PUT /items/{item_id} - обновление задачи
- [x] DELETE /items/{item_id} - удаление задачи
- [x] Автоматическое создание таблиц

### Сервис сокращения URL:
- [x] POST /shorten - создание короткой ссылки
- [x] GET /{short_id} - редирект на полный URL
- [x] GET /stats/{short_id} - статистика по ссылке
- [x] Автоматическое создание таблиц

### Docker требования:
- [x] Dockerfile для каждого сервиса
- [x] VOLUME /app/data для сохранения данных
- [ ] Сборка образов (проблема с SSL сертификатами)
- [ ] Публикация на Docker Hub (проблема с SSL сертификатами)

---

## Локальный запуск 
### ToDo-сервис:
```bash
cd todo_app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
