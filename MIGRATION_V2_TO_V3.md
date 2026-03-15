# Migration Guide: v2 to v3

This guide helps you migrate from the Phase 2 (in-memory) version to Phase 3 (production-ready with database, auth, and LLM).

## 📋 Overview of Changes

| Component | v2 | v3 |
|-----------|----|----|
| **Main File** | `app/main.py` | `app/main_v3.py` |
| **Storage** | In-memory dict | PostgreSQL |
| **Auth** | None | JWT-based |
| **Files** | Deleted after processing | Stored (S3/R2/local) |
| **Analysis** | Heuristic only | LLM + heuristic fallback |
| **Endpoints** | Public | Protected (require auth) |

## 🔄 Migration Steps

### Step 1: Backup Your Data

If you have important data in the v2 instance:

```bash
# Export any test data you want to keep
# (v2 data is lost on restart anyway due to in-memory storage)
```

### Step 2: Install New Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `sqlalchemy` - ORM
- `alembic` - Migrations
- `psycopg2-binary`, `asyncpg` - PostgreSQL drivers
- `python-jose`, `passlib` - Authentication
- `boto3` - File storage
- `openai`, `anthropic` - LLM providers
- `structlog` - Structured logging

### Step 3: Setup Database

```bash
# Install PostgreSQL
brew install postgresql@14  # macOS
# OR
sudo apt-get install postgresql-14  # Ubuntu

# Start PostgreSQL
brew services start postgresql@14

# Create database
createdb legallens
```

### Step 4: Configure Environment

```bash
cp .env.example .env
```

Generate secret key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update `.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/legallens
SECRET_KEY=<generated-key>

# Optional: Add LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Optional: Add cloud storage
STORAGE_PROVIDER=s3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

### Step 5: Run Migrations

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### Step 6: Update Application Entry Point

**Old (v2):**
```bash
uvicorn app.main:app --reload
```

**New (v3):**
```bash
uvicorn app.main_v3:app --reload
```

Or rename `main_v3.py` to `main.py`:
```bash
mv app/main.py app/main_v2_backup.py
mv app/main_v3.py app/main.py
```

### Step 7: Update Client Code

## API Changes

### Authentication Required

**v2 (No Auth):**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@contract.pdf"
```

**v3 (With Auth):**
```bash
# 1. Register/Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123"}'

# 2. Use token in requests
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@contract.pdf"
```

### Response Format Changes

**UploadResponse** - No changes

**AnalysisResponse** - No changes (fully backward compatible)

**DocumentRecord** - Now from database, not in response directly

### New Endpoints

```bash
# Authentication
POST /auth/register
POST /auth/login
POST /auth/refresh
GET /auth/me

# Document management
GET /documents  # List all user documents
GET /document/{id}  # Get document with analysis
```

## 🔧 Code Migration Examples

### Example 1: Simple Upload & Analyze (Python)

**v2:**
```python
import requests

# Upload
response = requests.post(
    "http://localhost:8000/upload",
    files={"file": open("contract.pdf", "rb")}
)
doc_id = response.json()["document_id"]

# Analyze
response = requests.post(
    "http://localhost:8000/analyze",
    json={"document_id": doc_id, "language": "en"}
)
print(response.json())
```

**v3:**
```python
import requests

# Login first
auth_response = requests.post(
    "http://localhost:8000/auth/login",
    json={"email": "user@example.com", "password": "password123"}
)
token = auth_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Upload
response = requests.post(
    "http://localhost:8000/upload",
    headers=headers,
    files={"file": open("contract.pdf", "rb")}
)
doc_id = response.json()["document_id"]

# Analyze
response = requests.post(
    "http://localhost:8000/analyze",
    headers=headers,
    json={"document_id": doc_id, "language": "en"}
)
print(response.json())
```

### Example 2: JavaScript/TypeScript Client

**v2:**
```javascript
const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('http://localhost:8000/upload', {
    method: 'POST',
    body: formData
  });

  return response.json();
};
```

**v3:**
```javascript
// Add authentication
const login = async (email, password) => {
  const response = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });

  const { access_token } = await response.json();
  localStorage.setItem('token', access_token);
  return access_token;
};

const uploadDocument = async (file) => {
  const token = localStorage.getItem('token');
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('http://localhost:8000/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  return response.json();
};
```

## 🗄️ Data Persistence

### v2 Limitations (Solved in v3)

❌ Data lost on server restart
❌ No user accounts or history
❌ Files deleted immediately after processing
❌ No way to retrieve past analyses

### v3 Benefits

✅ Permanent storage in PostgreSQL
✅ User accounts with document history
✅ Files retained for 7 days (configurable)
✅ Full document and analysis history
✅ User subscription tracking

## ⚡ Performance Considerations

### v2 Performance

- Fast startup (no database)
- Low latency (in-memory)
- Limited by server memory
- No horizontal scaling

### v3 Performance

- Slightly slower startup (database connection)
- Similar API latency with proper indexing
- Unlimited storage capacity
- Horizontally scalable (multiple instances)
- Connection pooling for efficiency

### Optimization Tips

1. **Database Indexing** (already configured):
   ```python
   # In models.py
   email: Mapped[str] = mapped_column(..., index=True)
   document_id: Mapped[str] = mapped_column(..., index=True)
   ```

2. **Connection Pooling** (already configured):
   ```python
   # In database.py
   engine = create_async_engine(
       ...,
       pool_size=5,
       max_overflow=10
   )
   ```

3. **Add Redis Caching** (future enhancement):
   ```python
   # Cache frequently accessed documents
   ```

## 🧪 Testing Your Migration

### 1. Test Basic Flow

```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123456","full_name":"Test User"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123456"}'
# Save the access_token

# Upload document
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.txt"

# Analyze
curl -X POST http://localhost:8000/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"document_id":"DOCUMENT_ID","language":"en"}'

# List documents
curl -X GET http://localhost:8000/documents \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Test Persistence

```bash
# Upload a document
# Restart server
# Login again
# List documents - should still see your document!
```

### 3. Test LLM Integration

Update `.env`:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

Restart server and analyze a document. You should get higher quality analysis!

## 🔒 Security Improvements

### v2 Security (None)

❌ No authentication
❌ No rate limiting
❌ No CORS protection
❌ Anyone can access any document

### v3 Security

✅ JWT-based authentication
✅ Password hashing with bcrypt
✅ User-scoped documents (users can only access their own)
✅ CORS configuration
✅ Token expiration (30min access, 7day refresh)
✅ Secure file storage

### Additional Security Recommendations

1. **Add Rate Limiting**:
   ```bash
   pip install slowapi
   ```

2. **Enable HTTPS** (in production):
   ```bash
   uvicorn app.main_v3:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
   ```

3. **Environment Variables**:
   Never commit `.env` to git!

4. **Regular Updates**:
   ```bash
   pip list --outdated
   pip install --upgrade package-name
   ```

## 🚨 Breaking Changes

### 1. All Endpoints Now Require Authentication

Except:
- `GET /health`
- `GET /disclaimer`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`

### 2. Document Store Removed

`app/store.py` still exists but is not used in v3.

Use database instead:
```python
from app.database import get_db
from app.models import Document

async def get_document(doc_id: str, db: AsyncSession):
    result = await db.execute(
        select(Document).where(Document.document_id == doc_id)
    )
    return result.scalar_one_or_none()
```

### 3. Synchronous → Asynchronous

Functions now use async/await:

**v2:**
```python
def analyze_document(doc_id, text, language):
    ...
```

**v3:**
```python
async def analyze_document(doc_id, text, language):
    ...
```

## 📦 Running Both Versions Simultaneously

If you need to run both:

```bash
# v2 on port 8000
uvicorn app.main:app --port 8000

# v3 on port 8001
uvicorn app.main_v3:app --port 8001
```

## 🎯 Rollback Plan

If you need to rollback:

```bash
# Keep v2 code as backup
cp app/main.py app/main_v2.py

# Use v2
uvicorn app.main_v2:app --reload
```

## ✅ Migration Checklist

- [ ] Install PostgreSQL
- [ ] Install new dependencies
- [ ] Create `.env` file
- [ ] Generate SECRET_KEY
- [ ] Setup database
- [ ] Run migrations
- [ ] Update application entry point
- [ ] Update client code for authentication
- [ ] Test complete flow
- [ ] Test persistence (restart server)
- [ ] Configure LLM (optional)
- [ ] Configure cloud storage (optional)
- [ ] Update deployment scripts
- [ ] Update CI/CD pipeline
- [ ] Update documentation

## 🆘 Need Help?

- **Check logs**: Structured logs show all errors
- **Database issues**: `alembic downgrade base && alembic upgrade head`
- **Auth issues**: Regenerate SECRET_KEY in `.env`
- **LLM issues**: Set `LLM_PROVIDER=local` to test without API keys

## 📞 Support

- GitHub Issues: https://github.com/muralik31/LegalLens/issues
- Documentation: README_V3.md
- Quick Start: QUICKSTART_V3.md

---

**Congratulations on upgrading to v3!** 🎉

You now have a production-ready system with proper data persistence, authentication, and advanced AI capabilities!
