# OCR Document Search System

A full-stack web application that extracts text from uploaded images and PDFs using OCR, stores the results, and lets you search across all your documents using full-text search.

---

## Features

- **Document Upload** — drag-and-drop or click to upload images (JPG, PNG, TIFF, BMP, WEBP) and PDFs up to 50 MB
- **OCR Extraction** — automatically extracts text from uploaded files using Tesseract OCR with adaptive image preprocessing
- **Full-Text Search** — search across all extracted text with ranked results and highlighted snippets
- **Multi-page PDF support** — processes each page individually and stores per-page results
- **User Authentication** — register and log in with JWT-based auth; documents are private to each user
- **Quality-adaptive pipeline** — high-quality images use Otsu binarization; low-quality images go through deskew, denoising, and adaptive thresholding
Note: the search feature is currently not available
---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Search | PostgreSQL full-text search (`tsvector`, `tsquery`, GIN index) |
| OCR | Tesseract OCR, pytesseract |
| Image processing | OpenCV |
| Auth | JWT (`python-jose`), bcrypt (`passlib`) |
| Infrastructure | Docker, Docker Compose |

---

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- [Node.js](https://nodejs.org/) 18+ (for the frontend dev server)
- Git

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ocr-document-search.git
cd ocr-document-search
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
POSTGRES_USER=ocruser
POSTGRES_PASSWORD=ocrpassword
POSTGRES_DB=ocrdb
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:9000
```

### 3. Start the backend (Docker)

```bash
docker compose up --build
```

This starts the FastAPI backend on **port 9000** and PostgreSQL on **port 5434**.

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on **http://localhost:4000**.

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Log in and receive a JWT token |

### Documents
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/documents/upload` | Upload a file and run OCR |
| GET | `/api/v1/documents/` | List all documents for the current user |
| GET | `/api/v1/documents/{id}` | Get a document with per-page OCR results |
| DELETE | `/api/v1/documents/{id}` | Delete a document |

### Search
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/search/?q=...` | Full-text search with ranking and snippets |

All document and search endpoints require `Authorization: Bearer <token>` header.

Interactive API docs available at **http://localhost:9000/docs**.

---

## Project Structure

```
ocr-document-search/
├── backend/
│   ├── api/
│   │   ├── dependencies.py       # get_current_user JWT dependency
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── documents.py
│   │       └── search.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py           # JWT + bcrypt helpers
│   ├── models/                   # SQLAlchemy models
│   ├── schemas/                  # Pydantic schemas
│   ├── repositories/             # Database access layer
│   ├── services/                 # Business logic layer
│   ├── utils/
│   │   ├── file_handler.py
│   │   ├── image_processor.py    # Adaptive OCR preprocessing
│   │   └── pdf_converter.py
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── lib/auth.ts           # Token helpers + API calls
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   ├── search/page.tsx
│   │   └── page.tsx              # Upload page
│   └── .env.local
├── .env
└── docker-compose.yml
```

---

## Ports

| Service | Port |
|---|---|
| Frontend | 4000 |
| Backend | 9000 |
| PostgreSQL (host) | 5434 |

---

## Supported File Types

Images: JPG, JPEG, PNG, TIFF, BMP, WEBP  
Documents: PDF (multi-page supported)  
Max file size: 50 MB
OCR Languages: English, Vietnamese
