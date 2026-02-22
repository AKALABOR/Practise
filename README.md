Технологічний стек
Мова: Python 3.11

Фреймворк: FastAPI

База даних: PostgreSQL 16

ORM: SQLAlchemy (асинхронна)

Контейнеризація: Docker та Docker Compose

Інструкція із запуску
1. Передумови
Переконайтися, що на вашому комп'ютері встановлено та запущено Docker Desktop.

2. Налаштування оточення
Створіть файл .env у кореневій директорії проекту та додайте параметри підключення до бази даних:

Ini, TOML
DB_USER=admin
DB_PASSWORD=securepassword
DB_NAME=metrics_db
DB_HOST=db
DB_PORT=5432
3. Запуск сервісів
Відкрийте термінал у папці проекту та виконайте команду для збірки та запуску контейнерів у фоновому режимі:

Bash
docker-compose up -d --build
Сервіс буде доступний за адресою: http://localhost:8000

4. Зупинка сервісів
Для зупинки роботи контейнерів без втрати даних:

Bash
docker-compose stop
Для повного видалення контейнерів та очищення бази даних:

Bash
docker-compose down -v
Структура API (OpenAPI / Swagger)
Після успішного запуску інтерактивна документація Swagger доступна за адресою:
http://localhost:8000/docs

Нижче наведено основні ендпоінти та приклади роботи з ними.

1. Перевірка стану (Healthcheck)
GET /health
Повертає поточний статус сервісу.

Відповідь (200 OK):

JSON
{
  "status": "ok",
  "service": "measurement-service"
}
2. Створення вимірювання (Create)
POST /measurements/
Додає новий запис. Автоматично генерує data_hash та пов'язує його з prev_hash попереднього запису.

Тіло запиту:

JSON
{
  "sensor_id": 1,
  "value": 24.5,
  "unit": "C",
  "metadata_info": {"location": "Kyiv"}
}
Відповідь (201 Created): Повертає збережений об'єкт із згенерованими полями хешів та ідентифікатором.

3. Отримання записів (Read)
GET /measurements/
Повертає список записів. Підтримує пагінацію, сортування (новіші зверху) та фільтрацію.

Параметри запиту (Query):

skip (int): кількість записів для пропуску.

limit (int): ліміт вибірки.

sensor_id (int): фільтр за ID датчика.

start_date / end_date (datetime): фільтр за часовим діапазоном.

location (str): пошук міст всередині JSON-поля metadata_info.

4. Редагування та Видалення (Update / Delete)
PUT /measurements/{m_id} — часткове оновлення запису.
DELETE /measurements/{m_id} — видалення запису за ID.

5. Аудит цілісності (Blockchain Verify)
GET /blockchain/verify
Перевіряє криптографічну цілісність усієї бази даних. Система перераховує хеші та звіряє їх з наявними. Відповідь, якщо дані цілі (200 OK):

JSON
{
  "status": "SECURE",
  "length": 5
}
Відповідь у разі виявлення втручання або використання методів PUT/DELETE (200 OK):

JSON
{
  "status": "CORRUPTED",
  "errors": [
    "Block 2: Broken Link! PrevHash doesn't match Block 1",
    "Block 1: Data Tampered! Hash mismatch."
  ]
}