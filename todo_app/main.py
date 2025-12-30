from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import os

app = FastAPI(title="ToDo Service", version="1.0.0")

# ИСПРАВЛЕНО: Используем относительный путь для локального запуска
# В Docker будет /app/data, локально - ./data
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)
DATABASE_URL = os.path.join(DATA_DIR, "todo.db")

# Модель данных
class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class ItemResponse(ItemCreate):
    id: int

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
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    conn.close()

# Инициализация БД при старте
@app.on_event("startup")
def startup_event():
    init_db()

# CRUD операции
@app.post("/items", response_model=ItemResponse, status_code=201)
def create_item(item: ItemCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO items (title, description, completed) VALUES (?, ?, ?)",
        (item.title, item.description, item.completed)
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    
    return {**item.dict(), "id": item_id}

@app.get("/items", response_model=List[ItemResponse])
def read_items():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items ORDER BY id")
    items = cursor.fetchall()
    conn.close()
    
    return [dict(item) for item in items]

@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()
    
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return dict(item)

@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item_update: ItemCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем существование
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Обновляем
    cursor.execute(
        "UPDATE items SET title = ?, description = ?, completed = ? WHERE id = ?",
        (item_update.title, item_update.description, item_update.completed, item_id)
    )
    conn.commit()
    
    # Получаем обновленную запись
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    updated_item = cursor.fetchone()
    conn.close()
    
    return dict(updated_item)

@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем существование
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Удаляем
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

# ИСПРАВЛЕНО: Для локального запуска меняем порт на 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
