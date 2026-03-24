# YouTube Link Processor - Project Structure

**Created:** 2026-03-24 | **Version:** 1.0.0 | **Status:** Arhitektuuriline ülevaade

---

## 1. Üldine Ülevaade

See dokument kirjeldab YouTube link processor projekti struktuuri teksti tasemel. Eesmärk on visualiseerida süsteemi komponendid ja nende seosed enne implementationit.

### 1.1 Core Flow

```
 kasutaja → API (auth) → database
    ↓
 POST /downloads → job_created
    ↓
 worker (yt-dlp) → file_storage
    ↓
 kasutaja → GET /downloads/{id}/file
```

---

## 2. Kataloogi Struktuur

```
yt-downloader/
├── docker-compose.yml          # Docker Compose konfiguratsioon
├── Dockerfile                  # Peakäivitus container
├── Dockerfile.worker           # Worker container (yt-dlp)
├── requirements.txt             # Python sõltuvused
├── .env.example                # Keskkonnamuutujad (template)
├── .gitignore                   # Git ignore reeglid
├── README.md                    # Projektide dokumentatsioon
│
├── app/                         # Peamine rakenduskood
│   ├── __init__.py
│   ├── main.py                  # FastAPI rakenduse entry point
│   ├── config.py                # Keskkonnamuutujad ja seaded
│   ├── auth.py                  # Autentimise loogika (JWT)
│   ├── database.py              # SQLAlchemy andmebaas setup
│   │
│   ├── api/                     # API endpointid
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # /auth/* endpointid
│   │   │   ├── downloads.py     # /downloads/* endpointid
│   │   │   └── health.py        # /health endpoint
│   │   └── dependencies/
│   │       └── __init__.py      # API dependencyd (get_current_user)
│   │
│   ├── models/                  # Andmebaasi mudelid
│   │   ├── __init__.py
│   │   ├── user.py              # User mudel
│   │   └── download_job.py     # DownloadJob mudel
│   │
│   ├── schemas/                # Pydantic skeemid
│   │   ├── __init__.py
│   │   ├── user.py              # UserCreate, UserResponse
│   │   ├── token.py             # Token, TokenData
│   │   └── download.py          # DownloadCreate, DownloadResponse
│   │
│   ├── services/                # Äriloogika
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Autentimise teenus
│   │   └── yt_dlp_service.py    # yt-dlp integtsioon
│   │
│   └── utils/                   # Abifunktsioonid
│       ├── __init__.py
│       ├── exceptions.py        # Erandid (YTDLPError jne)
│       └── validators.py        # URL validatsioon
│
├── storage/                     # Failide hoidla
│   ├── downloads/               # Allalaaditud failid
│   └── temp/                    # Ajutised failid
│
├── worker/                      # Taustatöötleja
│   ├── __init__.py
│   ├── main.py                  # Worker entry point
│   ├── processor.py             # Download töötluse loogika
│   └── queue.py                 # Job queue haldus
│
├── infra/                       # Infrastruktuur
│   ├── docker-compose.yml       # Täis docker-compose koos teenustega
│   ├── nginx/
│   │   └── default.conf         # Nginx konfiguratsioon
│   └── ssl/
│       └── .gitkeep             # SSL sertifikaadid
│
└── tests/                       # Testid
    ├── __init__.py
    ├── conftest.py              # Pytest fixtuurid
    ├── test_api/
    │   ├── __init__.py
    │   ├── test_auth.py
    │   └── test_downloads.py
    └── test_services/
        ├── __init__.py
        └── test_yt_dlp.py
```

---

## 3. Andmebaasi Skeem

### 3.1 User Tabel

| Väli | Tüüp | Kirjeldus |
|------|------|-----------|
| id | UUID | Primaarvõti |
| email | VARCHAR(255) | Unikaalne email |
| password_hash | VARCHAR(255) | Bcrypt hashitud parool |
| is_active | BOOLEAN | Kas kasutaja on aktiivne |
| created_at | TIMESTAMP | Loomise aeg |

### 3.2 DownloadJob Tabel

| Väli | Tüüp | Kirjeldus |
|------|------|-----------|
| id | UUID | Primaarvõti |
| user_id | UUID | Viide User tabelile |
| url | TEXT | YouTube URL |
| status | VARCHAR(20) | pending/processing/completed/failed |
| file_path | VARCHAR(500) | Faili tee (kui valmis) |
| file_name | VARCHAR(255) | Faili nimi |
| error | TEXT | Viga (kui ebaõnnestus) |
| created_at | TIMESTAMP | Loomise aeg |
| completed_at | TIMESTAMP | Valmimise aeg |
| expires_at | TIMESTAMP | Aegumise aeg |

---

## 4. API Endpointid

### 4.1 Autentimine (Auth)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/register` | Kasutaja registreerimine | No |
| POST | `/api/v1/auth/login` | Sisselogimine, tokenite saamine | No |
| POST | `/api/v1/auth/refresh` | Access tokeni uuendamine | Yes |
| GET | `/api/v1/me` | Kasutaja andmete küsimine | Yes |

### 4.2 Allalaadimised (Downloads)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/downloads` | Uue download jobi loomine | Yes |
| GET | `/api/v1/downloads` | Kasutaja downloadide nimekiri | Yes |
| GET | `/api/v1/downloads/{job_id}` | konkreetse jobi staatus | Yes |
| GET | `/api/v1/downloads/{job_id}/file` | Faili allalaadimise URL | Yes |
| DELETE | `/api/v1/downloads/{job_id}` | Jobi kustutamine | Yes |

### 4.3 Tervis

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/health` | Teenuse tervise check | No |

---

## 5. Autentimise Flow

### 5.1 Registreerimine

```
Kasutaja → POST /auth/register
    ↓
API kontrollib, kas email on vaba
    ↓
Hashib parooli (bcrypt)
    ↓
Salvestab User andmebaasi
    ↓
Tagastab UserResponse (id, email)
```

### 5.2 Sisselogimine

```
Kasutaja → POST /auth/login (email, password)
    ↓
Leiab kasutaja emaili järgi
    ↓
Kontrollib parooli (verify_password)
    ↓
Loob JWT access + refresh tokenid
    ↓
Tagastab Token (access_token, refresh_token, token_type)
```

### 5.3 Tokenite Kasutamine

```
Iga API päring → Authorization: Bearer {access_token}
    ↓
get_current_user dependency decodeb tokeni
    ↓
Kontrollib, kas token ei ole aegunud
    ↓
Leiab kasutaja andmebaasist
    ↓
Lisab kasutaja request ctxisse
```

---

## 6. Download Flow

### 6.1 Jobi Loomine

```
Kasutaja → POST /downloads {url: "youtube.com/..."}
    ↓
Valideerib URL (youtube.com, youtu.be)
    ↓
Kontrollib, kas URL on juba töötlemas
    ↓
Loob DownloadJob (status: "pending")
    ↓
Lisab jobi queueisse (Redis/RabbitMQ)
    ↓
Tagastab job_id
```

### 6.2 Worker Töötlus

```
Worker võtab jobi queuest
    ↓
Uuendab status → "processing"
    ↓
Runneb yt-dlp -g {url}
    ↓
Kui edukas:
    - Salvestab faili storage/download/
    - Uuendab file_path, file_name
    - Uuendab status → "completed"
    ↓
Kui ebaõnnestub:
    - Salvestab error teate
    - Uuendab status → "failed"
    ↓
Määrab expires_at (default: 24h)
```

### 6.3 Faili Küsimine

```
Kasutaja → GET /downloads/{job_id}/file
    ↓
Kontrollib, kas job kuulub kasutajale
    ↓
Kontrollib, kas status == "completed"
    ↓
Genereerib signed URL (või tagastab file_path)
    ↓
Kasutaja saab faili alla laadida
```

---

## 7. Docker Architektuur

### 7.1 Teenused (docker-compose.yml)

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ytprocessor
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./storage:/app/storage

  worker:
    build: .
    dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ytprocessor
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./storage:/app/storage

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: ytprocessor
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

### 7.2 Volume Struktuur

```
storage/
├── downloads/          # Valmis failid
│   └── {user_id}/
│       └── {job_id}.mp4
└── temp/               # Ajutised failid
    └── {job_id}.part
```

---

## 8. Worker Arhitektuur

### 8.1 Queue Süsteem

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  API    │────▶│  Redis  │────▶│ Worker  │
│ (POST)  │     │ (Queue) │     │ (yt-dlp)│
└─────────┘     └─────────┘     └─────────┘
```

### 8.2 Worker Protsess

```
1. Võta job from queue (BRPOP)
2. Fetch job from database
3. Update status → "processing"
4. Execute yt-dlp command
5. Save file to storage/
6. Update job with file_path
7. Update status → "completed"
8. Set expires_at
9. ACK job (LPACK)
```

---

## 9. Turvalisus

### 9.1 JWT Seaded

- **Algorithm:** HS256
- **Access Token:** 15 min expiry
- **Refresh Token:** 7 päeva expiry
- **Secret Key:** ścret_key keskkonnamuutujast

### 9.2 Rate Limiting

- Autentimata: 10 päringut tunnis
- Autentitud: 100 päringut tunnis
- Implementeerida: Redis key-based counter

### 9.3 Parooli Turve

- Minimum pikkus: 8 tähemärki
- Hash algoritm: bcrypt
- Salt: automaatne

---

## 10. Keskkonnamuutujad

| Muutuja | Kirjeldus | Default |
|---------|-----------|---------|
| DATABASE_URL | PostgreSQL ühendusstring | postgresql://user:pass@localhost:5432/ytprocessor |
| SECRET_KEY | JWT secret | random_string |
| REDIS_URL | Redis ühendusstring | redis://localhost:6379 |
| CORS_ORIGINS | CORS lubatud originid | * |
| ACCESS_TOKEN_EXPIRE_MINUTES | Tokeni aegumisaeg | 15 |
| REFRESH_TOKEN_EXPIRE_DAYS | Refresh token aegumisaeg | 7 |
| FILE_EXPIRE_HOURS | Faili säilimisaeg | 24 |
| STORAGE_PATH | Faili hoidla path | ./storage |

---

## 11. Edasised Otsused

### 11.1 Täpsustamist Vajavad

- [ ] Kas kasutada Redis või RabbitMQ queue jaoks?
- [ ] Kas faile serveerida otse või läbi API (signed URLs)?
- [ ] Kas implementeerida rate limiting kohe või hiljem?
- [ ] Kas kasutada async workerit või sync?
- [ ] Milline storage: local, S3, või mõni muu?

### 11.2 Võimalikud Edasiarendused

- Mitme formaadi tugi (mp3, mp4, webm)
- Queue süsteem mitme workeriga
- API analytics/dashboard
- Email notificationid
- Premium kasutajad (suurem rate limit)

---

## 12. Kokkuvõte

See dokument kirjeldab YouTube Link Processor projekti arhitektuuri teksti tasemel. Peamised komponendid on:

| Komponent | Kirjeldus |
|-----------|-----------|
| **FastAPI** | REST API framework |
| **PostgreSQL** | Andmebaas (User, DownloadJob) |
| **Redis** | Queue + rate limiting |
| **yt-dlp** | YouTube URL extraction |
| **Worker** | Taustatöötleja |
| **Docker** | Containeriseerimine |

Kõik komponendid on üksteisest sõltumatud ja saavad suhelda läbi defineeritud liideste (API, database, queue).

---

*See dokument on aluseks implementationile. Kõik otsused tuleb läbi mängida ja vajadusel kohandada.*
