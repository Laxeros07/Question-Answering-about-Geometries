# App_new

Full-Stack Anwendung mit FastAPI-Backend und React-Frontend für Question-Answering über Geometrien.

## Voraussetzungen

- **Backend:** Python 3.10+, FastAPI, Uvicorn
- **Frontend:** Node.js 18+, npm

## Installation

### Backend

```bash
cd App_new/backend
pip install -r requirements.txt
```

Falls `requirements.txt` nicht existiert:

```bash
pip install fastapi uvicorn python-multipart pandas
```

### Frontend

```bash
cd App_new/frontend
npm install
```

## Starten

### Backend (Terminal 1)

```bash
cd App_new/backend
uvicorn api.main:app --reload --port 8000
```

- Läuft unter: `http://localhost:8000`
- API-Dokumentation: `http://localhost:8000/docs`

### Frontend (Terminal 2)

```bash
cd App_new/frontend
npm start
```

- Läuft unter: `http://localhost:3000`

## API-Endpoints

| Endpoint               | Beschreibung               |
| ---------------------- | -------------------------- |
| `GET /`                | Willkommensnachricht       |
| `GET /geometries`      | Alle Geometrien abrufen    |
| `GET /geometries/{id}` | Einzelne Geometrie abrufen |
| `POST /chat`           | Chat-Anfrage senden        |

## Entwicklung

- **Backend:** Hot-Reload aktiviert (`--reload`)
- **Frontend:** Create React App mit Hot-Reload
- **CORS:** Erlaubt `http://localhost:3000` (React)
