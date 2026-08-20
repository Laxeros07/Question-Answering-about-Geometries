# FastAPI

This folder contains the FastAPI backend, which provides the API endpoints for accessing geometry data and processing chat requests.

## Start

```bash
uvicorn api.main:app --reload --port 8000
```

- Runs at: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`

## API-Endpoints

| Endpoint               | Description               |
| ---------------------- | -------------------------- |
| `GET /`                | Returns a welcome message       |
| `GET /geometries/{id}` | Returns geometry data for the given ID |
| `POST /chat`           | Processes a chat request       |
