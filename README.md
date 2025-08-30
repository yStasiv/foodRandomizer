# Food Planner

Веб-додаток для випадкового вибору страви, додавання рецептів, зворотнього зв'язку та коментарів.

## Запуск локально

1. Встановіть залежності:
   ```
   pip install -r requirements.txt
   ```
2. Запустіть сервер:
   ```
   uvicorn server.main:app --reload
   ```
3. Відкрийте [http://localhost:8000](http://localhost:8000) у браузері.

## Функціонал
- Випадковий вибір страви по категорії
- Додавання/редагування/видалення страв
- Завантаження зображень
- Зворотній зв'язок з коментарями
- Email-сповіщення про нові коментарі (налаштуйте SMTP через .env)

## Налаштування SMTP для email-сповіщень
Створіть файл `.env` у корені проекту:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=ваш_email@gmail.com
SMTP_PASSWORD=пароль_додатку
NOTIFY_EMAIL=ваш_email@gmail.com
```

## Структура проекту
- server/main.py — бекенд FastAPI
- server/index.html — головна сторінка
- server/add.html — додавання страви
- server/feedback.html — зворотній зв'язок
- server/style.css — стилі
- server/images/ — зображення страв

## GitHub Actions
Workflow для CI/CD знаходиться у `.github/workflows/main.yml`.

## Ліцензія
MIT
