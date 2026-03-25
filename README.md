# Theatre API

---

## Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Project Structure](#project-structure)
4. [API Endpoints](#api-endpoints)
5. [Run with Docker](#run-with-docker)
6. [Run Locally](#run-locally)
7. [Testing](#testing)
8. [Technologies](#technologies)

---

## Project Overview

Theatre API is a Django REST Framework backend for managing a theatre catalog and ticket reservations. It exposes public read endpoints for catalogue data, admin-only write endpoints for theatre management, and authenticated endpoints for booking seats.

The project includes:

- JWT authentication with refresh tokens
- Search, ordering, and filtering on catalogue endpoints
- Reservation creation with nested tickets
- Auto-generated Swagger, ReDoc, and OpenAPI schema
- Docker support for running the app in a container

---

## Features

- Public catalogue browsing for genres, actors, plays, theatre halls, and performances
- Admin-only create, update, and delete operations for theatre content
- User-specific reservations so each user sees only their own bookings
- Seat validation and unique seat reservation per performance
- Performance availability details, including taken places and free tickets
- Built-in throttling for anonymous and authenticated requests
- Generated schema file in `schema.yaml`

---

## Project Structure

```text
theatre-api/
|-- config/                    # Django project configuration
|   |-- settings.py            # Django, DRF, JWT, schema, and env settings
|   |-- urls.py                # Root routes, docs, and auth endpoints
|   |-- asgi.py
|   |-- wsgi.py
|   `-- __init__.py
|-- theatre/                   # Main application
|   |-- migrations/
|   |   `-- 0001_initial.py    # Initial schema migration
|   |-- admin.py
|   |-- models.py              # Genre, Actor, Play, Hall, Performance, Reservation, Ticket
|   |-- permissions.py         # Admin-or-read-only permission
|   |-- serializers.py         # API serializers
|   |-- tests.py               # Automated tests
|   |-- urls.py                # App router
|   |-- views.py               # Viewsets and queryset behavior
|   `-- __init__.py
|-- Dockerfile
|-- docker-compose.yml
|-- entrypoint.sh              # Runs migrations, collectstatic, and Gunicorn
|-- manage.py
|-- requirements.txt
|-- schema.yaml                # Generated OpenAPI schema
`-- README.md
```

---

## API Endpoints

Base URL: `http://127.0.0.1:8000/`

Main routes:

- `/api/theatre/genres/`
- `/api/theatre/actors/`
- `/api/theatre/plays/`
- `/api/theatre/theatre-halls/`
- `/api/theatre/performances/`
- `/api/theatre/reservations/`
- `/api/token/`
- `/api/token/refresh/`

Documentation routes:

- `/api/docs/swagger/`
- `/api/docs/redoc/`
- `/api/schema/`
- `/admin/`

Example token request:

```http
POST /api/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

Use the access token in authenticated requests:

```text
Authorization: Bearer <access_token>
```

---

## Run with Docker

### Prerequisites

- Docker
- Docker Compose

### Start the app

1. Clone the repository and move into the project directory:

```bash
git clone https://github.com/mishagitcode/theatre-api.git
cd theatre-api
```

2. Create your environment file:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

3. Build and start the container:

```bash
docker compose up --build
```

The container startup runs migrations automatically, collects static files, and starts Gunicorn on port `8000`.

Open:

- `http://127.0.0.1:8000/api/docs/swagger/`
- `http://127.0.0.1:8000/api/docs/redoc/`
- `http://127.0.0.1:8000/api/schema/`
- `http://127.0.0.1:8000/admin/`

### Optional Docker commands

Create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

Run tests:

```bash
docker compose exec web python manage.py test
```

Stop the app:

```bash
docker compose down
```

If your `.env` values contain a `$` character, escape it as `$$` before running Docker Compose to avoid interpolation warnings.

---

## Run Locally

### Prerequisites

- Python 3.12+
- `venv`

### Setup

1. Clone the repository:

```bash
git clone https://github.com/mishagitcode/theatre-api.git
cd theatre-api
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create an environment file:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

5. Apply migrations:

```bash
python manage.py migrate
```

6. Optionally create a superuser:

```bash
python manage.py createsuperuser
```

7. Start the development server:

```bash
python manage.py runserver
```

---

## Testing

Run the test suite locally:

```bash
python manage.py test
```

---

## Technologies

- Python 3.12
- Django 6
- Django REST Framework
- Simple JWT
- drf-spectacular
- django-filter
- Gunicorn
- SQLite
- Docker and Docker Compose

---

Developed by [mishagitcode](https://github.com/mishagitcode)
