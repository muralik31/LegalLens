# LegalLens v3.0 - Quick Start Guide

Complete implementation of LLM integration, database persistence, authentication, and file storage.

## 🎯 What's New in v3.0

| Feature | Phase 2 | Phase 3 ✨ |
|---------|---------|-----------|
| **Storage** | In-memory | ✅ PostgreSQL Database |
| **Authentication** | None | ✅ JWT-based Auth |
| **File Storage** | Temporary | ✅ S3/R2/Local Storage |
| **Analysis** | Heuristic only | ✅ LLM (OpenAI/Claude) + Heuristic Fallback |
| **User Management** | N/A | ✅ User accounts & history |
| **Logging** | Basic | ✅ Structured logging |
| **Persistence** | Session-only | ✅ Permanent with auto-expiry |

## ⚡ 5-Minute Setup

### 1. Prerequisites

```bash
# Install PostgreSQL (if not installed)
# macOS
brew install postgresql@14
brew services start postgresql@14

# Ubuntu/Debian
sudo apt-get install postgresql-14

# Create database
createdb legallens
```

### 2. Install & Configure

```bash
cd backend

# Run automated setup script
./setup.sh
```

The script will:
- ✅ Check Python version
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Create .env with generated SECRET_KEY
- ✅ Setup database
- ✅ Run migrations

### 3. Configure API Keys (Optional)

Edit `backend/.env`:

```env
# For AI-powered analysis (optional - works without)
LLM_PROVIDER=openai  # or 'anthropic' or 'local'
OPENAI_API_KEY=sk-...

# For cloud storage (optional - uses local by default)
STORAGE_PROVIDER=s3  # or 'r2' or 'local'
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

### 4. Start Server

```bash
uvicorn app.main_v3:app --reload
```

Visit http://localhost:8000/docs for interactive API documentation.

## 🧪 Test the API

### Step 1: Register User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'
```

### Step 2: Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

Save the `access_token` from the response.

### Step 3: Upload Document

```bash
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@sample_contract.txt"
```

### Step 4: Analyze Document

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "YOUR_DOCUMENT_ID",
    "language": "en"
  }'
```

## 📊 Configuration Options

### LLM Providers

**Local (Heuristic - No API Key Required)**
```env
LLM_PROVIDER=local
```
- ✅ Works offline
- ✅ No cost
- ⚠️ Basic analysis

**OpenAI (Recommended for Production)**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini  # Fast & cost-effective
```
- ✅ Advanced AI analysis
- ✅ Better accuracy
- 💰 ~$0.15 per 1M tokens

**Anthropic Claude**
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```
- ✅ Excellent analysis quality
- ✅ Longer context window
- 💰 ~$3 per 1M tokens

### Storage Providers

**Local (Default)**
```env
STORAGE_PROVIDER=local
STORAGE_LOCAL_PATH=./uploads
```

**AWS S3**
```env
STORAGE_PROVIDER=s3
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=legallens-docs
```

**Cloudflare R2 (S3-compatible, cheaper)**
```env
STORAGE_PROVIDER=r2
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_ENDPOINT_URL=https://xxx.r2.cloudflarestorage.com
S3_BUCKET_NAME=legallens-docs
```

## 🔐 Security Best Practices

### 1. Generate Secure Secret Key

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update in `.env`:
```env
SECRET_KEY=generated-key-here
```

### 2. Database Security

```env
# Use strong password in production
DATABASE_URL=postgresql+asyncpg://user:STRONG_PASSWORD@localhost:5432/legallens
```

### 3. CORS Configuration

```env
# Restrict to your frontend domain in production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## 📈 Monitoring

### Check Health

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "version": "3.0",
  "llm_provider": "openai",
  "storage_provider": "s3"
}
```

### View Logs

Structured JSON logs with all requests:
```bash
# Logs include:
# - user_id, document_id
# - request/response times
# - errors and stack traces
```

## 🐳 Docker Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: legallens
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:secure_password@db:5432/legallens
      SECRET_KEY: your-secret-key
      LLM_PROVIDER: openai
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - db
    volumes:
      - ./uploads:/app/uploads

volumes:
  postgres_data:
```

Deploy:
```bash
docker-compose up -d
```

## 🚀 Cloud Deployment

### Railway (Easiest)

1. Push to GitHub
2. Connect to Railway
3. Add PostgreSQL service
4. Set environment variables
5. Deploy!

Cost: ~$5-10/month

### Render

1. Create Web Service from GitHub
2. Add PostgreSQL database
3. Set environment variables
4. Auto-deploy on push

Cost: Free tier available

## 📚 API Endpoints Summary

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info

### Documents
- `POST /upload` - Upload document
- `POST /analyze` - Analyze document (LLM/heuristic)
- `GET /documents` - List user's documents
- `GET /document/{id}` - Get document details
- `POST /ask-question` - Ask question about document
- `POST /chat` - Chat with document

### Utilities
- `GET /health` - Health check
- `GET /disclaimer` - Legal disclaimer

## 🧪 Testing

```bash
# Run all tests
cd backend
PYTHONPATH=. pytest

# With coverage
PYTHONPATH=. pytest --cov=app --cov-report=html
```

## 🆘 Troubleshooting

### "Connection refused" Error

Check PostgreSQL is running:
```bash
# macOS
brew services list

# Linux
sudo systemctl status postgresql
```

### LLM API Errors

System automatically falls back to heuristic analysis if LLM fails.

Check API key in `.env`:
```env
OPENAI_API_KEY=sk-...  # Must start with sk-
```

### Import Errors

Ensure you're in the backend directory with activated venv:
```bash
cd backend
source venv/bin/activate
```

### Database Migration Issues

Reset migrations:
```bash
alembic downgrade base
alembic upgrade head
```

## 📞 Support

- **Documentation**: README_V3.md
- **Issues**: https://github.com/muralik31/LegalLens/issues
- **API Docs**: http://localhost:8000/docs (when running)

## 🎉 What's Next?

1. **Frontend Development** (Next.js)
   - User dashboard
   - Document upload interface
   - Results visualization

2. **Payment Integration**
   - Razorpay/Stripe
   - Subscription management
   - Usage tracking

3. **Advanced Features**
   - Document comparison
   - Export to PDF
   - Email notifications
   - Collaboration features

---

**Congratulations!** 🎊 You now have a production-ready AI legal document analyzer with:
- ✅ Persistent database storage
- ✅ User authentication
- ✅ Cloud file storage
- ✅ LLM integration
- ✅ Multi-language support
- ✅ Structured logging

Happy building! 🚀
