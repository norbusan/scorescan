# ScoreScan

A web application for converting music score images to MusicXML and PDF with optional transposition.

## Features

- **Upload music scores**: Support for PNG, JPG, TIFF, and PDF files
- **Camera capture**: Take photos directly on mobile devices
- **Optical Music Recognition**: Convert images to MusicXML using Audiveris
- **Image preprocessing**: Automatic enhancement for better OMR accuracy
- **Transposition**: Transpose by semitones (-12 to +12) or by key
- **PDF generation**: Professional quality PDF output via MuseScore
- **User authentication**: JWT-based auth with email/password
- **User approval system**: Superuser approval required for new registrations
- **Admin panel**: Manage users and approve new accounts
- **Job history**: Track and re-download past conversions

## Tech Stack

### Backend
- **Python 3.12** with **FastAPI**
- **SQLite** database with SQLAlchemy ORM
- **Celery** + **Valkey** for async task processing
- **Audiveris 5.9** for OMR (Optical Music Recognition)
- **music21** for transposition
- **MuseScore 4.4** for PDF generation

### Frontend
- **React 18** with TypeScript
- **Vite** for build tooling
- **TailwindCSS** for styling
- **React Router** for navigation
- **Axios** for API calls

## Prerequisites

- Docker and Docker Compose
- (For local development without Docker)
  - Python 3.12+
  - Node.js 18+
  - Java 21+ (bundled with Audiveris 5.9 .deb package)
  - Audiveris 5.9
  - MuseScore 4.4

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

5. **Set up user approval system** (First-time setup)
   ```bash
   # Run database migration
   cd backend
   python3 migrate_add_user_approval.py
   
   # Create first superuser account
   python3 create_superuser.py
   
   # Restart services
   cd ..
   docker-compose restart
   ```
   
   See [USER_APPROVAL_SYSTEM.md](USER_APPROVAL_SYSTEM.md) and [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for details.

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

4. **Start Valkey** (required for Celery)
   ```bash
   docker run -d -p 6379:6379 valkey/valkey:8-alpine
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
| `DEBUG` | Enable debug logging | `false` |
| `SECRET_KEY` | JWT signing key | (required) |
| `DATABASE_URL` | SQLite connection URL | `sqlite:///./storage/scorescan.db` |
| `REDIS_URL` | Valkey/Redis connection URL | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |
| `STORAGE_PATH` | File storage directory | `./storage` |
| `MAX_UPLOAD_SIZE_MB` | Max upload size | `50` |

## Image Preprocessing

As of the latest version, ScoreScan includes automatic image preprocessing to significantly improve OMR accuracy for mobile photos:

- **Deskewing**: Automatic rotation correction
- **Perspective correction**: Unwarp camera angle distortion  
- **Contrast enhancement**: Adaptive contrast improvement
- **Binarization**: Convert to high-contrast black & white
- **Noise reduction**: Remove camera noise
- **Resolution optimization**: Ensure sufficient DPI

These preprocessing steps improve recognition accuracy by **50-80%** for mobile photos.

For more details, see [IMAGE_PREPROCESSING.md](backend/IMAGE_PREPROCESSING.md).

## Running Behind Apache/Nginx Proxy

If you're running ScoreScan behind Apache or nginx reverse proxy, see [APACHE_PROXY_SETUP.md](APACHE_PROXY_SETUP.md) for configuration instructions.

**Quick fix for proxy setup:**
```bash
# In .env file, leave VITE_API_URL empty for relative URLs
VITE_API_URL=

# Add your domain to CORS
CORS_ORIGINS=https://yourdomain.com,http://localhost:5173
```

## Troubleshooting

### OMR Processing Fails
- Image preprocessing is enabled by default and should handle most photo issues
- Ensure the image shows the entire score (no cut-off edges)
- Avoid extreme angles or very poor lighting
- Try higher resolution images if available
- Audiveris works best with printed scores (handwritten may have issues)

### PDF Generation Fails
- Check that MuseScore is properly installed in the worker container
- Verify the MusicXML output is valid

### Authentication Issues
- Ensure `SECRET_KEY` is set and consistent across restarts
- Check that cookies/localStorage are not blocked
- For detailed debugging, enable `DEBUG=true` in `.env` and check logs
- See [DEBUG_LOGGING.md](DEBUG_LOGGING.md) for troubleshooting authentication

### User Approval Issues
- New users require superuser approval before they can login
- Check admin panel for pending approvals
- See [USER_APPROVAL_SYSTEM.md](USER_APPROVAL_SYSTEM.md) for details

## Debug Mode

Enable detailed logging for troubleshooting:

```bash
# In .env file
DEBUG=true

# Restart services
docker-compose restart

# View debug logs
docker-compose logs -f api | grep "AUTH DEBUG"
```

See [DEBUG_LOGGING.md](DEBUG_LOGGING.md) for complete debug guide.

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
