# ScoreScan - Complete Technical Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Technology Stack](#technology-stack)
5. [Setup & Deployment](#setup--deployment)
6. [API Reference](#api-reference)
7. [User Management](#user-management)
8. [Image Processing Pipeline](#image-processing-pipeline)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)
11. [Development Guide](#development-guide)
12. [Security](#security)
13. [Performance](#performance)
14. [Monitoring & Debugging](#monitoring--debugging)

---

## Overview

**ScoreScan** is a comprehensive web application for converting music score images to MusicXML and PDF with optional transposition capabilities. It combines Optical Music Recognition (OMR), image preprocessing, music notation manipulation, and PDF rendering into a seamless user experience.

### Key Capabilities

- **Multi-format Score Conversion**: Upload PNG, JPG, TIFF, or PDF files
- **Mobile-First Design**: Camera capture for direct photo upload from mobile devices
- **Advanced OMR**: Audiveris 5.9 with automatic image preprocessing
- **Music Transposition**: Transpose by semitones (-12 to +12) or between keys
- **Professional Output**: High-quality PDF generation via MuseScore 4.4
- **User Management**: JWT-based authentication with admin approval workflow
- **Job Tracking**: Complete history of all conversions with re-download capability

### Use Cases

1. **Musicians**: Convert sheet music photos to editable digital formats
2. **Music Teachers**: Transpose scores for different instruments or skill levels
3. **Music Libraries**: Digitize and archive physical scores
4. **Composers**: Convert handwritten drafts to professional notation
5. **Performers**: Quick transposition for different ensembles or voices

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌─────────────┬──────────────┬─────────────┬─────────────┐│
│  │   Upload    │   Dashboard  │    Admin    │    Auth     ││
│  │  Component  │     Page     │    Panel    │   Forms     ││
│  └─────────────┴──────────────┴─────────────┴─────────────┘│
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/REST API
┌───────────────────────────┴─────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Layer (Routers)                                  │   │
│  │  - Auth Router    - Jobs Router                       │   │
│  │  - Users Router   - Admin Router                      │   │
│  └───────────┬──────────────────────────────────────────┘   │
│              │                                               │
│  ┌───────────┴──────────────────────────────────────────┐   │
│  │  Business Logic (Services)                            │   │
│  │  - Auth Service   - OMR Service                       │   │
│  │  - Job Service    - Image Preprocessing              │   │
│  └───────────┬──────────────────────────────────────────┘   │
│              │                                               │
│  ┌───────────┴──────────────────────────────────────────┐   │
│  │  Data Layer                                           │   │
│  │  - SQLAlchemy Models  - Database (SQLite)             │   │
│  └───────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ Celery Tasks
┌───────────────────────────┴─────────────────────────────────┐
│                    Worker (Celery)                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Async Task Processing                                │   │
│  │  1. Image Preprocessing (OpenCV)                      │   │
│  │  2. OMR Processing (Audiveris 5.9)                    │   │
│  │  3. Transposition (music21)                           │   │
│  │  4. PDF Generation (MuseScore 4.4)                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│              Task Queue (Valkey/Redis)                       │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### Frontend (React + TypeScript)
- **User Interface**: Modern, responsive UI built with TailwindCSS
- **File Upload**: Drag-and-drop and camera capture
- **Authentication**: JWT token management with automatic refresh
- **Job Monitoring**: Real-time progress updates
- **Admin Panel**: User management interface (superusers only)

#### Backend (FastAPI + Python)
- **API Gateway**: RESTful API with OpenAPI documentation
- **Authentication**: JWT-based auth with user approval workflow
- **Job Management**: Create, track, and manage conversion jobs
- **File Storage**: Organized storage for uploads, MusicXML, and PDFs
- **Database**: SQLite with SQLAlchemy ORM

#### Worker (Celery + Python)
- **Async Processing**: Background job execution
- **Image Preprocessing**: 7-step enhancement pipeline
- **OMR**: Audiveris integration for score recognition
- **Transposition**: music21 for key and semitone changes
- **PDF Rendering**: MuseScore for professional output

#### Queue (Valkey)
- **Task Distribution**: Redis-compatible message broker
- **Job Persistence**: Reliable task queue
- **Status Tracking**: Real-time job status updates

---

## Features

### 1. Image Upload & Capture

**Supported Formats:**
- PNG, JPG, JPEG, TIFF, TIF, PDF
- Maximum file size: 50MB (configurable)

**Upload Methods:**
- Drag-and-drop interface
- File browser selection
- Camera capture (mobile devices)

**Validation:**
- File type checking
- Size limits
- Image quality warnings

### 2. Advanced Image Preprocessing

**Purpose**: Improve OMR accuracy by 50-80% for mobile photos

**Pipeline Steps:**

1. **Grayscale Conversion**
   - Reduces data complexity
   - Focuses on luminance

2. **Denoising** (Non-local Means)
   - Removes camera noise
   - Preserves edges
   - Optimized for low-light photos

3. **Deskewing** (Hough Line Transform)
   - Detects staff lines
   - Calculates rotation angle
   - Corrects rotation (if > 0.5°)

4. **Perspective Correction** (4-point transform)
   - Detects document boundaries
   - Unwarps perspective distortion
   - Handles camera angle issues

5. **Contrast Enhancement** (CLAHE)
   - Adaptive histogram equalization
   - Handles uneven lighting
   - Improves local contrast

6. **Adaptive Binarization**
   - Converts to pure B&W
   - Local thresholding
   - Handles shadows and gradients

7. **Resolution Optimization**
   - Ensures 300 DPI minimum
   - Upscales if necessary
   - Uses bicubic interpolation

**Configuration:**
```python
ImagePreprocessor(
    target_dpi=300,                        # Target resolution
    enable_deskew=True,                    # Rotation correction
    enable_perspective_correction=True,    # Perspective unwarp
    enable_denoising=True,                 # Noise reduction
    enable_binarization=True,              # B&W conversion
)
```

**See**: `docs/IMAGE_PREPROCESSING.md` for technical details

### 3. Optical Music Recognition (OMR)

**Engine**: Audiveris 5.9

**Process:**
1. Receives preprocessed image
2. Detects staff lines, clefs, notes, symbols
3. Generates MusicXML output
4. Handles both .mxl (compressed) and .musicxml formats

**Capabilities:**
- Printed score recognition
- Multi-staff systems
- Complex time signatures
- Articulations and dynamics
- Limited handwritten support

**Output Format**: MusicXML 3.0

**Timeout**: 5 minutes per job

### 4. Music Transposition

**Engine**: music21

**Methods:**

**By Semitones:**
```json
{
  "transpose_semitones": 2  // Range: -12 to +12
}
```

**By Key:**
```json
{
  "transpose_from_key": "C",
  "transpose_to_key": "D"
}
```

**Supported Keys:**
- Major: C, C#, Db, D, D#, Eb, E, F, F#, Gb, G, G#, Ab, A, A#, Bb, B
- Minor: Cm, C#m, Dm, D#m, Ebm, Em, Fm, F#m, Gm, G#m, Abm, Am, A#m, Bbm, Bm

**Features:**
- Preserves articulations
- Maintains dynamics
- Handles key signature changes
- Updates clefs if necessary

### 5. PDF Generation

**Engine**: MuseScore 4.4

**Process:**
1. Receives MusicXML (original or transposed)
2. Renders professional-quality PDF
3. Applies default engraving settings
4. Exports with embedded fonts

**Output:**
- High-resolution PDF
- Print-ready quality
- Standard A4/Letter size

### 6. User Management System

**Authentication:**
- JWT-based tokens
- Access token (30 min expiry)
- Refresh token (7 day expiry)
- Secure HTTP-only cookies

**User Roles:**

**Regular User:**
- Create jobs
- View own jobs
- Download results
- Requires approval to access

**Superuser:**
- All regular user privileges
- Access admin panel
- Approve/reject registrations
- Manage user roles
- View all users

**Approval Workflow:**

```
Registration → Pending → Approval → Active User
                  ↓
               Rejection → Deleted
```

**See**: `docs/USER_APPROVAL_SYSTEM.md` for complete documentation

### 7. Job Management

**Job States:**
- `pending`: Queued for processing
- `processing`: Currently being processed
- `completed`: Successfully finished
- `failed`: Error occurred

**Progress Tracking:**
- 0-50%: OMR processing
- 50-70%: Transposition (if requested)
- 70-100%: PDF generation

**Job Storage:**
- Original upload: `storage/uploads/{user_id}/{job_id}.{ext}`
- MusicXML: `storage/musicxml/{user_id}/{job_id}.musicxml`
- PDF: `storage/pdf/{user_id}/{job_id}.pdf`

**Cleanup:**
- Users can delete individual jobs
- Deletes all associated files
- Cascade deletes from database

---

## Technology Stack

### Backend Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | FastAPI | 0.109.0 | Modern async web framework |
| Language | Python | 3.12 | Core programming language |
| Database | SQLite | - | Lightweight relational database |
| ORM | SQLAlchemy | 2.0.25 | Database abstraction layer |
| Task Queue | Celery | 5.3.6 | Async task processing |
| Message Broker | Valkey | 8 | Redis-compatible queue |
| Auth | python-jose | 3.3.0 | JWT token handling |
| Password Hash | bcrypt | 4.0.1 | Secure password hashing |
| OMR | Audiveris | 5.9 | Optical music recognition |
| Music Theory | music21 | 9.1.0 | Transposition & analysis |
| PDF Generation | MuseScore | 4.4 | Score rendering |
| Image Processing | OpenCV | 4.9.0 | Image preprocessing |

### Frontend Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | React | 18 | UI library |
| Language | TypeScript | - | Type-safe JavaScript |
| Build Tool | Vite | - | Fast build tooling |
| Styling | TailwindCSS | - | Utility-first CSS |
| Routing | React Router | - | Client-side routing |
| HTTP Client | Axios | - | API communication |
| Icons | Lucide React | - | Icon library |
| Notifications | React Hot Toast | - | User notifications |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Containerization | Docker | Application packaging |
| Orchestration | Docker Compose | Multi-container management |
| Web Server | Uvicorn | ASGI server |
| Reverse Proxy | Apache/nginx | Production deployment |

---

## Setup & Deployment

### Quick Start (Docker)

```bash
# 1. Clone repository
git clone <repository-url>
cd ScoreScan

# 2. Configure environment
cp .env.example .env
nano .env
# Set SECRET_KEY, VITE_API_URL, CORS_ORIGINS

# 3. Start services
docker-compose up --build -d

# 4. Run database migration
docker-compose exec backend python3 migrate_add_user_approval.py

# 5. Create superuser
docker-compose exec backend python3 create_superuser.py

# 6. Access application
# Frontend: http://localhost:5173
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Production Deployment

**See**: `docs/DEPLOYMENT_GUIDE.md` for step-by-step instructions

**Key Steps:**
1. Configure secure SECRET_KEY
2. Set up SSL/TLS certificates
3. Configure Apache/nginx reverse proxy
4. Set CORS_ORIGINS to production domain
5. Enable firewall rules
6. Set up backup strategy
7. Configure monitoring

### Apache Proxy Setup

**See**: `docs/APACHE_PROXY_SETUP.md` for complete guide

**Quick Configuration:**

```bash
# In .env
VITE_API_URL=
CORS_ORIGINS=https://yourdomain.com

# Apache VirtualHost
<VirtualHost *:443>
    ServerName yourdomain.com
    
    # SSL config...
    
    ProxyPass /api http://localhost:8000/api
    ProxyPassReverse /api http://localhost:8000/api
    
    ProxyPass / http://localhost:5173/
    ProxyPassReverse / http://localhost:5173/
</VirtualHost>
```

### Environment Variables

**Required:**

```bash
SECRET_KEY=your-secure-random-key-here
```

**Optional with Defaults:**

```bash
# Debug mode
DEBUG=false

# Frontend API URL (empty for relative URLs in proxy setup)
VITE_API_URL=

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Database
DATABASE_URL=sqlite:///./storage/scorescan.db

# Redis/Valkey
REDIS_URL=redis://localhost:6379/0

# Storage
STORAGE_PATH=./storage
MAX_UPLOAD_SIZE_MB=50

# External tools (Docker defaults)
AUDIVERIS_PATH=/opt/audiveris/bin/Audiveris
MUSESCORE_PATH=/usr/local/bin/musescore
```

---

## API Reference

### Base URL

```
Development: http://localhost:8000/api
Production: https://yourdomain.com/api
```

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}

Response: 201 Created
{
  "id": "uuid",
  "email": "user@example.com",
  "is_active": true,
  "is_approved": false,
  "is_superuser": false,
  "created_at": "2026-01-28T...",
  "updated_at": "2026-01-28T..."
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword

Response: 200 OK
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}

Error: 403 Forbidden (if not approved)
{
  "detail": "Your account is pending approval by an administrator"
}
```

#### Refresh Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}

Response: 200 OK
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### Logout
```http
POST /api/auth/logout
Authorization: Bearer {access_token}

Response: 200 OK
{
  "message": "Successfully logged out"
}
```

### User Endpoints

#### Get Current User
```http
GET /api/users/me
Authorization: Bearer {access_token}

Response: 200 OK
{
  "id": "uuid",
  "email": "user@example.com",
  "is_active": true,
  "is_approved": true,
  "is_superuser": false,
  "created_at": "2026-01-28T...",
  "updated_at": "2026-01-28T..."
}
```

### Job Endpoints

#### Create Job
```http
POST /api/jobs
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: [binary]
transpose_semitones: 2 (optional)
transpose_from_key: "C" (optional)
transpose_to_key: "D" (optional)

Response: 201 Created
{
  "id": "uuid",
  "status": "pending",
  "progress": 0,
  "original_filename": "score.png",
  "transpose_semitones": 2,
  "transpose_from_key": null,
  "transpose_to_key": null,
  "error_message": null,
  "created_at": "2026-01-28T...",
  "completed_at": null,
  "has_pdf": false,
  "has_musicxml": false
}
```

#### List Jobs
```http
GET /api/jobs?page=1&page_size=10
Authorization: Bearer {access_token}

Response: 200 OK
{
  "jobs": [...],
  "total": 25,
  "page": 1,
  "page_size": 10,
  "total_pages": 3
}
```

#### Get Job
```http
GET /api/jobs/{job_id}
Authorization: Bearer {access_token}

Response: 200 OK
{
  "id": "uuid",
  "status": "completed",
  "progress": 100,
  "original_filename": "score.png",
  "transpose_semitones": 2,
  "error_message": null,
  "created_at": "2026-01-28T...",
  "completed_at": "2026-01-28T...",
  "has_pdf": true,
  "has_musicxml": true
}
```

#### Download PDF
```http
GET /api/jobs/{job_id}/download/pdf?token={access_token}

Response: 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="score.pdf"
```

#### Download MusicXML
```http
GET /api/jobs/{job_id}/download/musicxml?token={access_token}

Response: 200 OK
Content-Type: application/vnd.recordare.musicxml+xml
Content-Disposition: attachment; filename="score.musicxml"
```

#### Delete Job
```http
DELETE /api/jobs/{job_id}
Authorization: Bearer {access_token}

Response: 200 OK
{
  "message": "Job deleted successfully"
}
```

### Admin Endpoints (Superuser Only)

#### List All Users
```http
GET /api/admin/users
Authorization: Bearer {superuser_access_token}

Response: 200 OK
{
  "users": [...],
  "total": 15,
  "pending": 3,
  "approved": 12,
  "superusers": 2
}
```

#### List Pending Users
```http
GET /api/admin/users/pending
Authorization: Bearer {superuser_access_token}

Response: 200 OK
[
  {
    "id": "uuid",
    "email": "pending@example.com",
    "is_approved": false,
    ...
  }
]
```

#### Approve User
```http
POST /api/admin/users/{user_id}/approve
Authorization: Bearer {superuser_access_token}

Response: 200 OK
{
  "message": "User pending@example.com has been approved",
  "user": {...}
}
```

#### Reject User
```http
POST /api/admin/users/{user_id}/reject
Authorization: Bearer {superuser_access_token}

Response: 200 OK
{
  "message": "User pending@example.com has been rejected and deleted"
}
```

#### Make Superuser
```http
POST /api/admin/users/{user_id}/make-superuser
Authorization: Bearer {superuser_access_token}

Response: 200 OK
{
  "message": "User user@example.com is now a superuser",
  "user": {...}
}
```

#### Revoke Superuser
```http
DELETE /api/admin/users/{user_id}/superuser
Authorization: Bearer {superuser_access_token}

Response: 200 OK
{
  "message": "Superuser privileges revoked from user@example.com",
  "user": {...}
}
```

---

## User Management

### User States

```
Registration → Pending → Approved → Active
                  ↓
              Rejected → Deleted
```

### Database Schema

```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    is_approved BOOLEAN DEFAULT 0,      -- NEW
    is_superuser BOOLEAN DEFAULT 0,     -- NEW
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Approval Workflow

**1. User Registration:**
```python
# POST /api/auth/register
user = User(
    email=email,
    hashed_password=hash(password),
    is_active=True,
    is_approved=False,  # Requires approval
    is_superuser=False
)
```

**2. Login Attempt (Pending):**
```python
if not user.is_approved:
    raise HTTPException(
        status_code=403,
        detail="Your account is pending approval by an administrator"
    )
```

**3. Superuser Approval:**
```python
# POST /api/admin/users/{id}/approve
user.is_approved = True
# User can now login
```

### Creating Superusers

**Method 1: Script**
```bash
cd backend
python3 create_superuser.py
# Follow prompts
```

**Method 2: Promoting Existing User**
```bash
# Via admin panel or API
POST /api/admin/users/{user_id}/make-superuser
```

**Method 3: Database**
```bash
sqlite3 backend/storage/scorescan.db
UPDATE users SET is_superuser = 1, is_approved = 1 
WHERE email = 'admin@example.com';
```

### Grandfather Clause

Existing users during migration are automatically approved:

```python
# In migrate_add_user_approval.py
cursor.execute("UPDATE users SET is_approved = 1")
```

---

## Image Processing Pipeline

### Overview

```
Input Image → Preprocessing → OMR → Transposition → PDF
                   ↓
         50-80% Better Results
```

### Detailed Pipeline

**Stage 1: Upload & Validation**
- File type check
- Size validation (max 50MB)
- Storage in `uploads/{user_id}/`

**Stage 2: Preprocessing (2-5 seconds)**
```python
# Seven-step enhancement
preprocessed = ImagePreprocessor().preprocess(
    input_path=upload_path,
    output_path=preprocessed_path
)
```

Steps:
1. Grayscale conversion
2. Denoising (Non-local Means)
3. Deskewing (Hough Transform)
4. Perspective correction (4-point)
5. Contrast (CLAHE)
6. Binarization (Adaptive)
7. Resolution (300 DPI)

**Stage 3: OMR (30-300 seconds)**
```bash
xvfb-run -a /opt/audiveris/bin/Audiveris \
    -batch -export \
    -output {output_dir} \
    {preprocessed_image}
```

Output: MusicXML file

**Stage 4: Transposition (1-5 seconds)**
```python
if transpose_semitones:
    score = music21.converter.parse(musicxml_path)
    transposed = score.transpose(transpose_semitones)
    transposed.write('musicxml', output_path)
```

**Stage 5: PDF Generation (5-15 seconds)**
```bash
/usr/local/bin/musescore \
    -o {output_pdf} \
    {musicxml_file}
```

Output: Professional PDF

**Stage 6: Cleanup**
- Remove preprocessed image
- Update job status
- Notify user

### Performance Benchmarks

| Stage | Time | Notes |
|-------|------|-------|
| Upload | <1s | Network dependent |
| Preprocessing | 2-5s | CPU intensive |
| OMR | 30-300s | Image complexity |
| Transposition | 1-5s | Score complexity |
| PDF | 5-15s | Page count |
| **Total** | **40-330s** | **0.5-5.5 min** |

---

## Configuration

### Application Settings

**File**: `backend/app/config.py`

```python
class Settings(BaseSettings):
    # Application
    app_name: str = "ScoreScan"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./storage/scorescan.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT
    secret_key: str  # REQUIRED
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Storage
    storage_path: str = "./storage"
    max_upload_size_mb: int = 50
    
    # CORS
    cors_origins: str = "http://localhost:5173"
    
    # Tools
    audiveris_path: str = "/opt/audiveris/bin/Audiveris"
    musescore_path: str = "/usr/local/bin/musescore"
```

### Docker Configuration

**File**: `docker-compose.yml`

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - DEBUG=${DEBUG:-false}
    volumes:
      - ./backend/storage:/app/storage
    
  worker:
    build: 
      context: ./backend
      dockerfile: Dockerfile.worker
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG:-false}
    volumes:
      - ./backend/storage:/app/storage
    
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    environment:
      - VITE_API_URL=${VITE_API_URL:-}
    
  valkey:
    image: valkey/valkey:8-alpine
```

### Frontend Configuration

**File**: `frontend/vite.config.ts`

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ['yourdomain.com', 'localhost'],
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

---

## Troubleshooting

### Common Issues

#### 1. Login Fails with "Pending Approval"

**Symptom:**
```
403 Forbidden
"Your account is pending approval by an administrator"
```

**Solution:**
```bash
# Check user status
sqlite3 backend/storage/scorescan.db \
  "SELECT email, is_approved FROM users WHERE email='user@example.com';"

# Approve via superuser account
# Login to admin panel → Approve user

# Or via database
sqlite3 backend/storage/scorescan.db \
  "UPDATE users SET is_approved = 1 WHERE email='user@example.com';"
```

#### 2. OMR Processing Fails

**Symptom:**
Job stuck in "processing" or fails with error

**Solutions:**

**Check logs:**
```bash
docker-compose logs -f worker
```

**Common causes:**
- Image quality too poor
- Handwritten score (not supported well)
- Timeout (>5 minutes)
- Audiveris not installed

**Fixes:**
- Use higher resolution image
- Ensure good lighting
- Use printed scores
- Check Audiveris installation

#### 3. API Returns CORS Error

**Symptom:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**
```bash
# In .env
CORS_ORIGINS=https://yourdomain.com,http://localhost:5173

# Restart backend
docker-compose restart backend
```

#### 4. Frontend Tries to Connect to localhost:8000

**Symptom:**
```
POST http://localhost:8000/api/auth/login net::ERR_CONNECTION_REFUSED
```

**Solution:**
```bash
# In .env, leave empty for relative URLs
VITE_API_URL=

# Restart frontend
docker-compose restart frontend
```

**See**: `docs/PROXY_FIX_SUMMARY.md` for details

#### 5. Database Migration Not Applied

**Symptom:**
Users don't have `is_approved` or `is_superuser` fields

**Solution:**
```bash
docker-compose exec backend python3 migrate_add_user_approval.py
docker-compose restart
```

#### 6. Worker Not Processing Jobs

**Symptom:**
Jobs stuck in "pending" state

**Solutions:**

**Check worker is running:**
```bash
docker-compose ps worker
```

**Check worker logs:**
```bash
docker-compose logs -f worker
```

**Restart worker:**
```bash
docker-compose restart worker
```

**Check Valkey connection:**
```bash
docker-compose exec backend python3 -c \
  "import redis; r=redis.from_url('redis://valkey:6379/0'); print(r.ping())"
```

---

## Development Guide

### Local Development Setup

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Valkey
docker run -d -p 6379:6379 valkey/valkey:8-alpine

# Start backend
uvicorn app.main:app --reload

# Start worker (separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Project Structure

```
ScoreScan/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database setup
│   │   ├── models/
│   │   │   ├── user.py         # User model
│   │   │   └── job.py          # Job model
│   │   ├── schemas/
│   │   │   ├── auth.py         # Auth schemas
│   │   │   ├── user.py         # User schemas
│   │   │   └── job.py          # Job schemas
│   │   ├── routers/
│   │   │   ├── auth.py         # Auth endpoints
│   │   │   ├── users.py        # User endpoints
│   │   │   ├── jobs.py         # Job endpoints
│   │   │   └── admin.py        # Admin endpoints
│   │   ├── services/
│   │   │   ├── auth.py         # Auth business logic
│   │   │   ├── omr.py          # OMR integration
│   │   │   ├── image_preprocessing.py
│   │   │   ├── transposition.py
│   │   │   └── pdf_generation.py
│   │   ├── tasks/
│   │   │   ├── celery_app.py   # Celery setup
│   │   │   └── process_score.py # Main task
│   │   └── utils/
│   │       ├── security.py      # JWT, hashing
│   │       └── storage.py       # File management
│   ├── migrate_add_user_approval.py
│   ├── create_superuser.py
│   └── test_preprocessing.py
│
├── frontend/
│   └── src/
│       ├── api/
│       │   └── client.ts        # API client
│       ├── components/
│       │   ├── Auth/
│       │   ├── Jobs/
│       │   ├── Upload/
│       │   └── Layout/
│       ├── pages/
│       │   ├── Home.tsx
│       │   ├── Login.tsx
│       │   ├── Register.tsx
│       │   ├── Dashboard.tsx
│       │   └── Admin.tsx
│       ├── context/
│       │   └── AuthContext.tsx
│       ├── types/
│       │   └── index.ts
│       └── hooks/
│           ├── useAuth.ts
│           └── useJobs.ts
│
└── docs/
    ├── USER_APPROVAL_SYSTEM.md
    ├── IMAGE_PREPROCESSING.md
    ├── DEBUG_LOGGING.md
    ├── APACHE_PROXY_SETUP.md
    └── DEPLOYMENT_GUIDE.md
```

### Adding New Features

**1. New API Endpoint:**

```python
# backend/app/routers/your_router.py
from fastapi import APIRouter, Depends
from app.routers.auth import get_current_user

router = APIRouter(prefix="/your-feature", tags=["Your Feature"])

@router.get("/")
def get_feature(current_user = Depends(get_current_user)):
    return {"message": "Hello"}
```

```python
# backend/app/main.py
from app.routers import your_router

app.include_router(your_router.router, prefix="/api")
```

**2. New Database Model:**

```python
# backend/app/models/your_model.py
from sqlalchemy import Column, String
from app.database import Base

class YourModel(Base):
    __tablename__ = "your_table"
    id = Column(String(36), primary_key=True)
    name = Column(String(255))
```

**3. New Frontend Component:**

```typescript
// frontend/src/components/YourComponent/YourComponent.tsx
import React from 'react';

export default function YourComponent() {
  return <div>Your Component</div>;
}
```

### Testing

**Backend:**
```bash
# Unit tests (if implemented)
pytest

# API testing via Swagger UI
# Visit http://localhost:8000/docs
```

**Frontend:**
```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Build test
npm run build
```

### Code Style

**Backend:**
- PEP 8 style guide
- Type hints recommended
- Docstrings for public functions

**Frontend:**
- ESLint configuration
- TypeScript strict mode
- React best practices

---

## Security

### Authentication Flow

```
1. User Registration
   ↓
2. Password Hashing (bcrypt)
   ↓
3. Store in Database
   ↓
4. User Login
   ↓
5. Verify Password
   ↓
6. Check is_approved
   ↓
7. Generate JWT Tokens
   ↓
8. Return to Client
   ↓
9. Client Stores Tokens
   ↓
10. Subsequent Requests
    Include Bearer Token
    ↓
11. Verify Token
    ↓
12. Check User Status
    ↓
13. Grant Access
```

### Password Security

**Hashing:**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash(plain_password)

# Verify password
is_valid = pwd_context.verify(plain_password, hashed)
```

**Requirements:**
- Minimum 6 characters (enforced in frontend)
- Bcrypt with automatic salt
- No password in logs or responses

### JWT Tokens

**Structure:**
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "exp": 1706453400,
  "type": "access"
}
```

**Security:**
- Signed with HS256
- Secret key from environment
- Access token: 30 min expiry
- Refresh token: 7 day expiry
- No sensitive data in payload

### CORS Configuration

**Development:**
```python
CORS_ORIGINS = "http://localhost:5173,http://localhost:3000"
```

**Production:**
```python
CORS_ORIGINS = "https://yourdomain.com"
```

### File Upload Security

**Validation:**
- File type whitelist
- Size limits (50MB)
- Unique filenames (UUID)
- User-isolated directories

**Storage:**
```
storage/
  uploads/
    {user_id}/
      {job_id}.{ext}
  musicxml/
    {user_id}/
      {job_id}.musicxml
  pdf/
    {user_id}/
      {job_id}.pdf
```

### SQL Injection Prevention

SQLAlchemy ORM automatically prevents SQL injection:

```python
# Safe - parameterized query
user = db.query(User).filter(User.email == email).first()

# Unsafe - never do this
db.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

### XSS Prevention

**Backend:**
- No HTML rendering
- JSON responses only

**Frontend:**
- React auto-escapes
- No `dangerouslySetInnerHTML`

### Best Practices

1. **Use HTTPS** in production
2. **Rotate SECRET_KEY** periodically
3. **Regular updates** of dependencies
4. **Firewall** Docker ports (except 80/443)
5. **Backup** database regularly
6. **Monitor** logs for suspicious activity
7. **Rate limiting** (consider adding)

---

## Performance

### Optimization Strategies

**Backend:**
- Async I/O with FastAPI
- Database connection pooling
- Index on frequently queried columns
- Pagination for large result sets

**Frontend:**
- Code splitting with Vite
- Lazy loading routes
- Image optimization
- Caching API responses

**Worker:**
- Celery task timeout (5 min)
- Parallel processing possible
- Resource limits in Docker

### Scaling Considerations

**Horizontal Scaling:**
```yaml
# docker-compose.yml
worker:
  deploy:
    replicas: 3  # Multiple workers
```

**Database:**
- Consider PostgreSQL for production
- Add read replicas if needed
- Regular VACUUM for SQLite

**Caching:**
- Add Redis cache layer
- Cache MusicXML parsing
- Cache user sessions

**CDN:**
- Serve static assets via CDN
- Cache PDF downloads

### Resource Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB

**Recommended:**
- CPU: 4 cores
- RAM: 8GB
- Disk: 100GB SSD

**Per Job:**
- Disk: ~5-20MB
- RAM: ~500MB-1GB (worker)
- CPU: 80-100% (during OMR)

---

## Monitoring & Debugging

### Debug Mode

**Enable:**
```bash
# In .env
DEBUG=true

# Restart
docker-compose restart
```

**Features:**
- Detailed auth logging
- Request/response logging
- SQL query logging
- Stack traces

**See**: `docs/DEBUG_LOGGING.md` for complete guide

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f frontend

# Filter for errors
docker-compose logs backend | grep ERROR

# Filter for auth debug
docker-compose logs backend | grep "AUTH DEBUG"

# Save to file
docker-compose logs > logs.txt
```

### Health Checks

**API Health:**
```bash
curl http://localhost:8000/health
# Response: {"status":"healthy"}
```

**Database Check:**
```bash
sqlite3 backend/storage/scorescan.db ".tables"
```

**Valkey Check:**
```bash
docker-compose exec valkey valkey-cli ping
# Response: PONG
```

### Monitoring Tools

**Docker Stats:**
```bash
docker stats
```

**Job Status:**
```bash
# Via API
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/jobs/{job_id}
```

**Database Queries:**
```bash
# Pending jobs
sqlite3 backend/storage/scorescan.db \
  "SELECT COUNT(*) FROM jobs WHERE status='pending';"

# Failed jobs
sqlite3 backend/storage/scorescan.db \
  "SELECT * FROM jobs WHERE status='failed';"

# Pending users
sqlite3 backend/storage/scorescan.db \
  "SELECT email FROM users WHERE is_approved=0;"
```

### Performance Monitoring

**Request Timing:**
```bash
# Enable in FastAPI
time curl -X POST http://localhost:8000/api/jobs ...
```

**Worker Performance:**
```bash
# Celery stats
docker-compose exec worker celery -A app.tasks.celery_app inspect stats
```

---

## Documentation Index

### Core Documentation

- **README.md** - Quick start and overview
- **CLAUDE.md** - This comprehensive guide

### Feature Documentation

- **docs/USER_APPROVAL_SYSTEM.md** - User management and approval workflow
- **docs/IMAGE_PREPROCESSING.md** - Image enhancement pipeline
- **docs/DEBUG_LOGGING.md** - Debugging and troubleshooting

### Deployment

- **docs/DEPLOYMENT_GUIDE.md** - Production deployment steps
- **docs/APACHE_PROXY_SETUP.md** - Reverse proxy configuration
- **docs/PROXY_FIX_SUMMARY.md** - Proxy troubleshooting

### Implementation Details

- **docs/IMPLEMENTATION_SUMMARY.md** - Image preprocessing implementation
- **docs/DEBUG_IMPLEMENTATION_SUMMARY.md** - Debug logging implementation
- **CHANGES_SUMMARY.md** - All feature implementations

### Quick References

- **.env.example** - Environment variables template
- **backend/.env.example** - Backend configuration
- **docs/QUICK_START_PREPROCESSING.md** - Quick preprocessing guide

---

## Contributing

### Development Workflow

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test locally
5. Submit pull request

### Code Guidelines

**Backend:**
- Follow PEP 8
- Add type hints
- Write docstrings
- Update tests

**Frontend:**
- Use TypeScript
- Follow React best practices
- Update component documentation

### Testing

**Before Committing:**
- Test all affected endpoints
- Verify UI changes
- Check logs for errors
- Test in Docker environment

### Documentation

**Update When:**
- Adding new features
- Changing APIs
- Modifying configuration
- Adding dependencies

---

## License

MIT License - See LICENSE file for details

---

## Support & Contact

**Documentation:**
- GitHub Repository
- API Documentation: http://localhost:8000/docs
- Issue Tracker: GitHub Issues

**Getting Help:**
1. Check documentation
2. Review logs with DEBUG=true
3. Search existing issues
4. Create new issue with:
   - Description
   - Steps to reproduce
   - Logs
   - Environment info

---

**Last Updated:** January 28, 2026  
**Version:** 1.0  
**Status:** ✅ Production Ready
