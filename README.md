# ScoreScan

A web application for converting music score images to MusicXML and PDF with optional transposition.

## Features

- **Upload music scores**: Support for PNG, JPG, TIFF, and PDF files
- **Camera capture**: Take photos directly on mobile devices
- **Optical Music Recognition**: Convert images to MusicXML using Audiveris
- **Transposition**: Transpose by semitones (-12 to +12) or by key
- **PDF generation**: Professional quality PDF output via MuseScore
- **User authentication**: JWT-based auth with email/password
- **Job history**: Track and re-download past conversions

## Tech Stack

### Backend
- **Python 3.11** with **FastAPI**
- **SQLite** database with SQLAlchemy ORM
- **Celery** + **Redis** for async task processing
- **Audiveris** for OMR (Optical Music Recognition)
- **music21** for transposition
- **MuseScore 4** for PDF generation

### Frontend
- **React 18** with TypeScript
- **Vite** for build tooling
- **TailwindCSS** for styling
- **React Router** for navigation
- **Axios** for API calls

## Prerequisites

- Docker and Docker Compose
- (For local development without Docker)
  - Python 3.11+
  - Node.js 18+
  - Java 17+ (for Audiveris)
  - MuseScore 4

## Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ScoreScan
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and set a secure SECRET_KEY
   ```

3. **Start all services**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Local Development Setup

### Backend

1. **Create a virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

4. **Start Redis** (required for Celery)
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

5. **Start the backend server**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Start the Celery worker** (in a separate terminal)
   ```bash
   celery -A app.tasks.celery_app worker --loglevel=info
   ```

### Frontend

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server**
   ```bash
   npm run dev
   ```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create a new account |
| POST | `/api/auth/login` | Login and get tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| POST | `/api/auth/logout` | Logout |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/me` | Get current user profile |

### Jobs
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/jobs` | Create new conversion job |
| GET | `/api/jobs` | List user's jobs (paginated) |
| GET | `/api/jobs/{id}` | Get job status/details |
| GET | `/api/jobs/{id}/download/pdf` | Download result PDF |
| GET | `/api/jobs/{id}/download/musicxml` | Download MusicXML |
| DELETE | `/api/jobs/{id}` | Delete job and files |

## Project Structure

```
ScoreScan/
├── docker-compose.yml
├── README.md
├── .env.example
│
├── backend/
│   ├── Dockerfile
│   ├── Dockerfile.worker
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings
│   │   ├── database.py          # Database connection
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Business logic
│   │   ├── tasks/               # Celery tasks
│   │   └── utils/               # Utilities
│   └── storage/                 # File storage
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/                 # API client
        ├── components/          # React components
        ├── pages/               # Page components
        ├── hooks/               # Custom hooks
        ├── context/             # React context
        └── types/               # TypeScript types
```

## Processing Pipeline

1. **Upload**: User uploads an image of a music score
2. **OMR (Audiveris)**: Image is processed to extract music notation → MusicXML
3. **Transpose (music21)**: If requested, transpose the score
4. **Render (MuseScore)**: Convert MusicXML to professional PDF

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | (required) |
| `DATABASE_URL` | SQLite connection URL | `sqlite:///./storage/scorescan.db` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |
| `STORAGE_PATH` | File storage directory | `./storage` |
| `MAX_UPLOAD_SIZE_MB` | Max upload size | `50` |

## Troubleshooting

### OMR Processing Fails
- Ensure the image is clear and well-lit
- Try higher resolution images
- Audiveris works best with printed scores (handwritten may have issues)

### PDF Generation Fails
- Check that MuseScore is properly installed in the worker container
- Verify the MusicXML output is valid

### Authentication Issues
- Ensure `SECRET_KEY` is set and consistent across restarts
- Check that cookies/localStorage are not blocked

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
