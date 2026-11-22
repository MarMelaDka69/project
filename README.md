# 3D Repository

Веб-каталог 3D-моделей Blender. Гости могут просматривать карточки, открывать превью и скачивать файлы `.blend`. Для добавления модели с изображением нужно зарегистрироваться и войти в аккаунт.

[Публичный сайт](https://3d-blend-repo.duckdns.org/) · [Репозиторий](https://github.com/MarMelaDka69/project) · [GitHub Actions](https://github.com/MarMelaDka69/project/actions)

## Как устроен проект

Браузер загружает HTML-страницу и обращается к FastAPI. SQLAlchemy сохраняет учётные записи, описания моделей и относительные пути к файлам в PostgreSQL. Сами модели и превью лежат в `uploads/`.

| Путь | Назначение |
|---|---|
| `app/main.py` | Маршруты API, загрузка и скачивание файлов |
| `app/database.py`, `app/models.py`, `app/schemas.py` | Подключение к БД, ORM-модели и схема ответа каталога |
| `app/auth.py`, `app/security.py`, `app/csrf.py` | Подписанные сессии, хеширование паролей Argon2 и проверка CSRF |
| `app/static/static.html` | Каталог, формы авторизации и загрузки |
| `contracts/openapi.json`, `tests/` | Снимок OpenAPI и автотесты |
| `Dockerfile`, `compose.yaml` | Образ FastAPI и локальный запуск с PostgreSQL |

## Быстрый запуск через Docker

Понадобятся Git и запущенный Docker с Compose. На Windows можно использовать Docker Desktop.

```powershell
git clone https://github.com/MarMelaDka69/project.git
cd project
```

Создайте два файла в корне проекта. Для пароля БД и ключа сессий сгенерируйте два разных случайных значения. При наличии Python можно дважды выполнить `python -c "import secrets; print(secrets.token_hex(32))"`.

**`.env`** — Compose подставляет этот пароль в адрес подключения и передаёт его контейнеру БД.

```dotenv
DOCKER_DB_PASSWORD=замените_на_случайную_hex_строку
```

**`.env.docker`** — настройки приложения внутри контейнера.

```dotenv
SESSION_SECRET_KEY=замените_на_другую_случайную_hex_строку
```

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose exec web python -c "from app.database import Base, engine; import app.models; Base.metadata.create_all(bind=engine)"
```

Откройте [каталог](http://127.0.0.1:8002/) или [Swagger UI](http://127.0.0.1:8002/docs). В новой базе каталог пуст. Проверьте регистрацию, вход, загрузку небольшой модели с превью и скачивание.

Compose публикует приложение на `127.0.0.1:8002` и задаёт `COOKIE_SECURE=false` для локального HTTP. Сервис `db` доступен внутри сети Compose. Тома `postgres_data`, `model_uploads` и `messages_data` сохраняют данные при обычном `docker compose down`. Команда `docker compose down -v` удаляет эти данные. При первом запуске Docker каталог сообщений пуст. Чтобы инициализировать его перед проверкой `GET /messages`, выполните `docker compose exec web touch /code/data/messages.txt`.

```powershell
docker compose logs --tail 50 web db
docker compose down
```

## Запуск без Docker на Windows

Из корня проекта выполните команды для Python 3.12. Если окружение уже создано, используйте существующее.

```powershell
py -3.12 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Создайте локальную базу PostgreSQL, например `repo3d_db`, с отдельным пользователем-владельцем. В `.env` пропишите его данные и отдельный ключ сессий. Специальные символы в пароле внутри URL нужно кодировать.

```dotenv
DATABASE_URL=postgresql+psycopg://repo3d_user:YOUR_URL_ENCODED_PASSWORD@127.0.0.1:5432/repo3d_db
SESSION_SECRET_KEY=YOUR_RANDOM_SESSION_KEY
COOKIE_SECURE=false
```

```powershell
.\venv\Scripts\python.exe -c "from app.database import Base, engine; import app.models; Base.metadata.create_all(bind=engine)"
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Сайт будет доступен по адресу [127.0.0.1:8000](http://127.0.0.1:8000/). `create_all()` создаёт отсутствующие таблицы. Для обновления столбцов в существующей БД нужна отдельная миграция.

## Основные маршруты

| Метод и путь | Назначение |
|---|---|
| `GET /`, `GET /models` | Главная страница и JSON-каталог |
| `GET /models/{model_id}`, `GET /models/{model_id}/download` | Карточка модели и скачивание |
| `POST /models`, `POST /models/upload` | Создание записи и загрузка модели с изображением |
| `GET /auth/csrf` | Выдача CSRF-токена и cookie |
| `POST /auth/register`, `POST /auth/login`, `POST /auth/logout` | Регистрация, вход и выход |
| `GET /auth/me` | Текущий пользователь |
| `GET /messages`, `POST /messages` | Чтение и добавление текстовых сообщений |

Для POST-запросов сначала получите `GET /auth/csrf`, сохраните cookie и передайте значение поля `csrf_token` в заголовке `X-CSRF-Token`. Запросы создания и загрузки модели дополнительно требуют сессионную cookie. Форма загрузки отправляет `multipart/form-data` с полями `title`, `description`, `file` и `image`. Поддерживаются модели `.blend` и превью JPG, JPEG, PNG и WebP.

## Тесты и контракт API

Команды ниже используют тестовую конфигурацию на время запуска и восстанавливают исходные переменные даже при ошибке.

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$previousDatabaseUrl = $env:DATABASE_URL
$previousSessionSecret = $env:SESSION_SECRET_KEY
$previousCookieSecure = $env:COOKIE_SECURE
try {
    $env:DATABASE_URL = 'sqlite://'
    $env:SESSION_SECRET_KEY = 'local-tests-only'
    $env:COOKIE_SECURE = 'false'
    .\venv\Scripts\python.exe -m pytest -v
} finally {
    $env:DATABASE_URL = $previousDatabaseUrl
    $env:SESSION_SECRET_KEY = $previousSessionSecret
    $env:COOKIE_SECURE = $previousCookieSecure
}
```

Тесты API используют отдельную SQLite и временные каталоги. GitHub Actions запускает их для PR в `main` и при обновлении `main`. При намеренном изменении API обновите снимок из корня проекта с настроенным локальным окружением, просмотрите diff и запустите тесты повторно.

```powershell
.\venv\Scripts\python.exe -c "import json; from pathlib import Path; from app.main import app; Path('contracts/openapi.json').write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')"
git diff -- contracts/openapi.json
```

## Действующий VPS

На общей Ubuntu VPS Nginx обслуживает поддомен по HTTPS и направляет запросы в Uvicorn на `127.0.0.1:8001`. Приложение запускается службой `3d-repository` от пользователя `repo3d`. Код находится в `/srv/3d-repository/app-source`, окружение Python — в `/srv/3d-repository/venv`. Серверный `.env` содержит настройки рабочей БД и `COOKIE_SECURE=true`.

После слияния PR для обновления действующей службы выполните на VPS от администратора:

```bash
cd /srv/3d-repository/app-source
sudo -u repo3d git status --short --branch
```

Если рабочая копия чистая и находится на `main`, обновите код и перезапустите приложение. Команда установки нужна при изменениях зависимостей. Изменения схемы БД применяйте отдельно по инструкции к конкретному релизу.

```bash
sudo -u repo3d git pull --ff-only origin main
/srv/3d-repository/venv/bin/python -m pip install -r requirements.txt
systemctl restart 3d-repository
systemctl is-active 3d-repository
curl -fsS http://127.0.0.1:8001/models
```

При ошибке проверьте `journalctl -u 3d-repository -n 50 --no-pager`. Пользователю `repo3d` нужна запись в `uploads/` и `uploads/images/`. При развёртывании через локальный Compose создаётся отдельная база. Переход рабочего VPS на контейнеры требует отдельной конфигурации и решения о переносе базы и файлов.

Храните резервные копии PostgreSQL и `uploads/` вместе. Файлы окружения, резервные копии и загруженные модели храните вне Git.

## Как отправлять изменения

```powershell
git switch main
git pull --ff-only origin main
git switch -c docs/project-guide
git add -- README.md AGENTS.md
git diff --cached
git commit -m "Document project setup and contribution guidelines"
git push -u origin docs/project-guide
```

На GitHub создайте Pull Request из `docs/project-guide` в `main`. Когда проверки пройдут, выполните merge и обновите локальную `main`.

- [Документация Docker Compose о переменных окружения](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation)
- [Инструкция GitHub по созданию Pull Request](https://docs.github.com/en/pull-requests/get-started/pull-request-quickstart)
