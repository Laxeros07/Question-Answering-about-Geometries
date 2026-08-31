# App_new

Full-stack application with a FastAPI backend and React frontend for question answering about geometries.

## Requirements

- **Backend:** Python 3.10+, FastAPI, Uvicorn
- **Frontend:** Node.js 18+, npm

## Installation

### Backend

```bash
cd App_new/backend
pip install -r requirements.txt
```

If `requirements.txt` does not exist:

```bash
pip install fastapi uvicorn python-multipart pandas
```

### Frontend

```bash
cd App_new/frontend
npm install
```

## Start

### Backend (Terminal 1)

```bash
cd App_new/backend
uvicorn api.main:app --reload --port 8000
```

- Runs at: `http://localhost:8000`
- API-Documentation: `http://localhost:8000/docs`

### Frontend (Terminal 2)

```bash
cd App_new/frontend
npm start
```

- Runs at: `http://localhost:3000`

## API-Endpoints

| Endpoint               | Beschreibung               |
| ---------------------- | -------------------------- |
| `GET /`                | Welcome message       |
| `GET /geometries`      | Get all geometries    |
| `GET /geometries/{id}` | Retrieve a single geometry |
| `POST /chat`           | Send a chat request      |

## Development

- **Backend:** Hot-Reload activated (`--reload`)
- **Frontend:** Create React App with Hot-Reload
- **CORS:** Allows `http://localhost:3000` (React)
