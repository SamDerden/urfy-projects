from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import Optional
import sqlite3
import os
import shortuuid
from datetime import datetime

app = FastAPI(title="Short URL Service", version="1.0.0")

# ИСПРАВЛЕНО: Используем относительный путь для локального запуска
# В Docker будет /app/data, локально - ./data
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)
DATABASE_URL = os.path.join(DATA_DIR, "shorturl.db")

# Модель данных
class URLRequest(BaseModel):
    url: str

class URLStats(BaseModel):
    short_id: str
    original_url: str
    created_at: str
    access_count: int

# Подключение к БД
def get_db_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn

# Создание таблицы при запуске
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_id TEXT UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            created_at TEXT NOT NULL,
            access_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Инициализация БД при старте
@app.on_event("startup")
def startup_event():
    init_db()

# Эндпоинты
@app.post("/shorten")
def create_short_url(url_request: URLRequest):
    original_url = url_request.url
    
    # Генерируем короткий идентификатор
    short_id = shortuuid.ShortUUID().random(length=6)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем, не существует ли уже такой short_id
    cursor.execute("SELECT short_id FROM urls WHERE short_id = ?", (short_id,))
    while cursor.fetchone() is not None:
        short_id = shortuuid.ShortUUID().random(length=6)
        cursor.execute("SELECT short_id FROM urls WHERE short_id = ?", (short_id,))
    
    # Сохраняем в БД
    created_at = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO urls (short_id, original_url, created_at, access_count) VALUES (?, ?, ?, ?)",
        (short_id, original_url, created_at, 0)
    )
    conn.commit()
    conn.close()
    
    return {"short_id": short_id, "short_url": f"http://localhost:8001/{short_id}"}

@app.get("/{short_id}")
def redirect_to_url(short_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Находим URL
    cursor.execute("SELECT original_url FROM urls WHERE short_id = ?", (short_id,))
    result = cursor.fetchone()
    
    if result is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    # Увеличиваем счетчик обращений
    cursor.execute(
        "UPDATE urls SET access_count = access_count + 1 WHERE short_id = ?",
        (short_id,)
    )
    conn.commit()
    conn.close()
    
    # Редирект
    original_url = result["original_url"]
    return Response(status_code=307, headers={"Location": original_url})

@app.get("/stats/{short_id}")
def get_url_stats(short_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT short_id, original_url, created_at, access_count FROM urls WHERE short_id = ?",
        (short_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if result is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    return URLStats(
        short_id=result["short_id"],
        original_url=result["original_url"],
        created_at=result["created_at"],
        access_count=result["access_count"]
    )

# ИСПРАВЛЕНО: Для локального запуска меняем порт на 8001
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
