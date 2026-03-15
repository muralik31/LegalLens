# LegalLens Backend v3.0

AI-powered legal document analyzer with database persistence, authentication, file storage, and LLM integration.

## 🚀 Features

### Phase 3 Additions

✅ **Database & Persistence**
- PostgreSQL with SQLAlchemy async ORM
- Alembic migrations
- User accounts and document history
- Auto-expiry (7-day retention)

✅ **Authentication & Authorization**
- JWT-based authentication
- User registration/login
- Token refresh mechanism
- Protected endpoints

✅ **File Storage**
- Local filesystem storage
- AWS S3 support
- Cloudflare R2 support
- Secure file management

✅ **LLM Integration**
- OpenAI GPT-4/GPT-4o-mini support
- Anthropic Claude support
- Automatic fallback to heuristic analysis
- Multi-language analysis (6 languages)

✅ **Observability**
- Structured logging with structlog
- Request/response logging
- Error tracking

✅ **Production Ready**
- CORS configuration
- Environment-based config
- Database migrations
- Comprehensive error handling

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 14+
- (Optional) OpenAI or Anthropic API key
- (Optional) AWS S3 or Cloudflare R2 credentials

## 🛠️ Installation

### 1. Clone and Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and configure:

```env
# Generate secret key:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/legallens

# LLM (optional - leave as 'local' for heuristic mode)
LLM_PROVIDER=openai  # or 'anthropic' or 'local'
OPENAI_API_KEY=sk-...  # if using OpenAI
ANTHROPIC_API_KEY=sk-...  # if using Anthropic

# Storage (optional - leave as 'local' for filesystem)
STORAGE_PROVIDER=local  # or 's3' or 'r2'
```

### 3. Setup Database

**Install PostgreSQL:**

```bash
# macOS
brew install postgresql@14
brew services start postgresql@14

# Ubuntu/Debian
sudo apt-get install postgresql-14
sudo systemctl start postgresql

# Create database
createdb legallens
```

**Run Migrations:**

```bash
# Initialize alembic (first time only)
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 4. Run Application

```bash
# Development
uvicorn app.main_v3:app --reload --port 8000

# Production
uvicorn app.main_v3:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 API Documentation

Once running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Authentication Flow

### 1. Register

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### 3. Use Protected Endpoints

```bash
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@contract.pdf"
```

## 📖 Usage Examples

### Upload Document

```python
import requests

token = "YOUR_ACCESS_TOKEN"
headers = {"Authorization": f"Bearer {token}"}

with open("contract.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        headers=headers,
        files={"file": f}
    )

document_id = response.json()["document_id"]
```

### Analyze Document

```python
response = requests.post(
    "http://localhost:8000/analyze",
    headers=headers,
    json={
        "document_id": document_id,
        "language": "en"
    }
)

analysis = response.json()
print(f"Risk Score: {analysis['contract_risk_score']}/10")
print(f"Summary: {analysis['summary']}")
```

### Ask Questions

```python
response = requests.post(
    "http://localhost:8000/ask-question",
    headers=headers,
    json={
        "document_id": document_id,
        "question": "What is the notice period?",
        "language": "en"
    }
)

print(response.json()["answer"])
```

## 🧪 Testing

```bash
# Run all tests
PYTHONPATH=. pytest

# Run with coverage
PYTHONPATH=. pytest --cov=app --cov-report=html

# Run specific test file
PYTHONPATH=. pytest tests/test_auth.py -v
```

## 🗄️ Database Management

### Create Migration

```bash
alembic revision --autogenerate -m "Add new field"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback

```bash
alembic downgrade -1
```

### View History

```bash
alembic history
```

## 🔧 Configuration Options

### LLM Providers

**Local (Heuristic)**
```env
LLM_PROVIDER=local
```

**OpenAI**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini  # or gpt-4o, gpt-4-turbo
```

**Anthropic Claude**
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022  # or claude-3-5-haiku-20241022
```

### Storage Providers

**Local Filesystem**
```env
STORAGE_PROVIDER=local
STORAGE_LOCAL_PATH=./uploads
```

**AWS S3**
```env
STORAGE_PROVIDER=s3
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET_NAME=legallens-documents
```

**Cloudflare R2**
```env
STORAGE_PROVIDER=r2
AWS_ACCESS_KEY_ID=...  # R2 Access Key
AWS_SECRET_ACCESS_KEY=...  # R2 Secret Key
AWS_REGION=auto
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
S3_BUCKET_NAME=legallens-documents
```

## 📊 Subscription Tiers

Current implementation supports:
- **Free**: 1 document
- **Starter**: 5 documents
- **Pro**: Unlimited

Tracked in `User.subscription_tier` and `User.documents_analyzed`.

## 🔒 Security Considerations

1. **Environment Variables**: Never commit `.env` to version control
2. **Secret Key**: Generate with `openssl rand -hex 32`
3. **Password Hashing**: Uses bcrypt with automatic salt
4. **JWT Tokens**: Short-lived access tokens (30min), longer refresh tokens (7 days)
5. **CORS**: Configure allowed origins in production
6. **File Upload**: 10MB limit, content-type validation
7. **Rate Limiting**: Consider adding slowapi or similar

## 🚀 Deployment

### Docker (Recommended)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main_v3:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: legallens
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/legallens
    depends_on:
      - db
    volumes:
      - ./uploads:/app/uploads

volumes:
  postgres_data:
```

Run:
```bash
docker-compose up -d
```

### Cloud Platforms

**Railway**
1. Connect GitHub repository
2. Add PostgreSQL service
3. Set environment variables
4. Deploy

**Render**
1. Create Web Service from GitHub
2. Add PostgreSQL database
3. Set environment variables
4. Deploy

**AWS/GCP/Azure**
- Use managed PostgreSQL (RDS/Cloud SQL/Azure Database)
- Deploy container to ECS/Cloud Run/App Service
- Configure S3/Cloud Storage for file storage

## 📝 TODO / Roadmap

- [ ] Add rate limiting middleware
- [ ] Implement caching (Redis)
- [ ] Add email verification
- [ ] Payment integration (Razorpay/Stripe)
- [ ] Usage analytics
- [ ] Document sharing
- [ ] Export to PDF
- [ ] Webhook notifications
- [ ] Admin dashboard

## 🐛 Troubleshooting

### Database Connection Error

```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection refused
```

**Solution**: Ensure PostgreSQL is running and connection details are correct.

### Import Error for Models

```
ImportError: cannot import name 'Base' from 'app.models'
```

**Solution**: Ensure you're running from the backend directory with correct PYTHONPATH.

### LLM API Errors

If LLM provider fails, the system automatically falls back to heuristic analysis.

## 📄 License

MIT License - See LICENSE file for details.

## 👥 Contributors

- Murali K ([@muralik31](https://github.com/muralik31))

## 📧 Support

For issues and questions:
- GitHub Issues: https://github.com/muralik31/LegalLens/issues
- Email: support@legallens.ai
