import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Body
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel





from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Body
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from fastapi.staticfiles import StaticFiles
import os
import sqlite3
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Body
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

DB_PATH = os.path.join(os.path.dirname(__file__), "food_planner.db")


app = FastAPI()
images_dir = os.path.join(os.path.dirname(__file__), "images")
app.mount("/images", StaticFiles(directory=images_dir), name="images")
app.mount("/style.css", StaticFiles(directory=os.path.dirname(__file__)))
app.mount("/static", StaticFiles(directory=os.path.dirname(__file__)), name="static")

class Comment(BaseModel):
    name: str
    email: str
    comment: str

class Dish(BaseModel):
    category: str
    name: str
    calories: int
    recipe: str

@app.on_event("startup")
def startup():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for table in ["breakfasts", "lunches", "dinners", "snacks"]:
        c.execute(f"""
        CREATE TABLE IF NOT EXISTS {table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            calories INTEGER NOT NULL,
            recipe TEXT NOT NULL,
            image_url TEXT
        )
        """)
    # Таблиця для коментарів
    c.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        comment TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

@app.get("/", response_class=HTMLResponse)
async def home():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

@app.get("/feedback", response_class=HTMLResponse)
async def add_page():
    return FileResponse(os.path.join(os.path.dirname(__file__), "feedback.html"))

@app.get("/add", response_class=HTMLResponse)
async def add_page():
    return FileResponse(os.path.join(os.path.dirname(__file__), "add.html"))

@app.get("/dishes/{category}")
async def get_dishes(category: str):
    if category not in ["breakfasts", "lunches", "dinners", "snacks"]:
        raise HTTPException(status_code=400, detail="Невірна категорія")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"SELECT id, name, calories, recipe, image_url FROM {category} ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(zip(["id", "name", "calories", "recipe", "image_url"], row)) for row in rows]

@app.post("/add_dish")
async def add_dish(dish: Dish):
    if dish.category not in ["breakfasts", "lunches", "dinners", "snacks"]:
        raise HTTPException(status_code=400, detail="Невірна категорія")
    # image_url додається лише через завантаження
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"INSERT INTO {dish.category} (name, calories, recipe, image_url) VALUES (?, ?, ?, ?)",
              (dish.name, dish.calories, dish.recipe, None))
    conn.commit()
    conn.close()
    return {"message": "Страву додано"}

@app.put("/dishes/{category}/{dish_id}")
async def update_dish(category: str, dish_id: int, data: dict = Body(...)):
    if category not in ["breakfasts", "lunches", "dinners", "snacks"]:
        raise HTTPException(status_code=400, detail="Невірна категорія")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"UPDATE {category} SET name=?, calories=?, recipe=? WHERE id=?",
              (data["name"], data["calories"], data["recipe"], dish_id))
    conn.commit()
    conn.close()
    return {"message": "Страву оновлено"}

# PATCH endpoint to update image_url for a dish
@app.patch("/dishes/{category}/{dish_id}/image")
async def update_dish_image(category: str, dish_id: int, data: dict = Body(...)):
    if category not in ["breakfasts", "lunches", "dinners", "snacks"]:
        raise HTTPException(status_code=400, detail="Невірна категорія")
    image_url = data.get("image_url")
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url обов'язковий")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"UPDATE {category} SET image_url=? WHERE id=?", (image_url, dish_id))
    conn.commit()
    conn.close()
    return {"message": "Зображення оновлено"}

@app.delete("/dishes/{category}/{dish_id}")
async def delete_dish(category: str, dish_id: int):
    if category not in ["breakfasts", "lunches", "dinners", "snacks"]:
        raise HTTPException(status_code=400, detail="Невірна категорія")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"DELETE FROM {category} WHERE id=?", (dish_id,))
    conn.commit()
    conn.close()
    return {"message": "Страву видалено"}

@app.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1]
    if ext.lower() not in [".jpg", ".jpeg", ".png", ".gif"]:
        raise HTTPException(status_code=400, detail="Тільки jpg, png, gif")
    save_dir = os.path.join(os.path.dirname(__file__), "images")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, file.filename)
    with open(save_path, "wb") as f:
        f.write(await file.read())
    return {"url": f"/images/{file.filename}"}

# Додати коментар
@app.post("/comments")
async def add_comment(comment: Comment):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO comments (name, email, comment) VALUES (?, ?, ?)",
              (comment.name, comment.email, comment.comment))
    conn.commit()
    conn.close()
    send_email_notification(comment.name, comment.email, comment.comment)
    return {"message": "Коментар додано"}

# Отримати всі коментарі
@app.get("/comments")
async def get_comments():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, email, comment, created_at FROM comments ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    result = []
    for name, email, comment, created_at in rows:
        item = {"name": name, "comment": comment, "created_at": created_at}
        if email:
            item["email"] = email
        else:
            item["email"] = "email не вказано"
        result.append(item)
    return result

def send_email_notification(name, email, comment):
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    to_email = os.environ.get('NOTIFY_EMAIL')
    if not (smtp_user and smtp_password and to_email):
        return  # Не надсилати, якщо не налаштовано
    subject = 'Новий коментар на Food Planner'
    body = f"Ім'я: {name}\nEmail: {email}\nКоментар: {comment}"
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = to_email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [to_email], msg.as_string())
        server.quit()
    except Exception as e:
        print('Email send error:', e)
        
@app.get("/favicon.svg")
async def favicon():
    return FileResponse(os.path.join(os.path.dirname(__file__), "favicon.svg"))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)