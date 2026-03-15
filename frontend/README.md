# LegalLens Frontend

Next.js 14 frontend application for LegalLens - AI-powered legal document analysis.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local

# Update .env.local with your backend URL
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Run development server
npm run dev

# Open http://localhost:3000
```

## 📦 Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State**: Zustand
- **HTTP**: Axios
- **Validation**: Zod + React Hook Form
- **Dates**: date-fns

## 🏗️ Project Structure

```
src/
├── app/                      # Next.js pages
│   ├── page.tsx             # Landing page
│   ├── login/               # Login page
│   ├── register/            # Registration page
│   ├── dashboard/           # User dashboard
│   ├── upload/              # Document upload
│   ├── results/[id]/        # Analysis results
│   ├── layout.tsx           # Root layout
│   └── globals.css          # Global styles
├── lib/
│   ├── api.ts               # Axios client with JWT refresh
│   └── utils.ts             # Helper functions
├── store/
│   └── authStore.ts         # Zustand auth store
└── types/
    └── index.ts             # TypeScript interfaces
```

## 📄 Pages

### 1. Landing Page (`/`)
- Hero section with value proposition
- Feature showcase
- CTA buttons

### 2. Login Page (`/login`)
- Email/password authentication
- Auto-redirect to dashboard
- Error handling

### 3. Registration Page (`/register`)
- User signup with validation
- Password strength indicator
- Auto-login after registration

### 4. Dashboard (`/dashboard`)
- User statistics
- Document list
- Subscription info
- Quick actions

### 5. Upload Page (`/upload`)
- Drag & drop file upload
- File validation (type, size)
- Upload progress
- Language selection (6 languages)

### 6. Results Page (`/results/[id]`)
- Risk score visualization
- Summary and alerts
- Key clauses analysis
- Financial obligations
- Negotiation suggestions
- Market comparisons
- Legal terms glossary
- Q&A feature

## 🔐 Authentication Flow

1. User registers/logs in
2. Backend returns JWT tokens (access + refresh)
3. Tokens stored in localStorage
4. Axios interceptor adds token to requests
5. Auto-refresh on 401 errors
6. Logout clears tokens

## 🎨 Features

- ✅ Complete authentication flow
- ✅ JWT auto-refresh
- ✅ Drag & drop file upload
- ✅ Real-time upload progress
- ✅ Multi-language support (6 languages)
- ✅ Responsive design
- ✅ Error handling
- ✅ Loading states
- ✅ Empty states

## 📝 Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=LegalLens
```

## 🛠️ Development

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Type checking
npm run type-check

# Build for production
npm run build

# Run production server
npm start

# Lint code
npm run lint
```

## 📦 Build & Deploy

```bash
# Production build
npm run build

# Test production build locally
npm start

# Deploy to Vercel
vercel --prod

# Deploy to Netlify
netlify deploy --prod
```

## 🔗 API Integration

The frontend connects to the FastAPI backend at `NEXT_PUBLIC_API_URL`.

### Key Endpoints Used:

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Token refresh
- `GET /auth/me` - Get user profile
- `GET /documents` - List documents
- `POST /upload` - Upload document
- `POST /analyze` - Analyze document
- `GET /document/{id}` - Get analysis results
- `POST /ask-question` - Ask question about document

## 🐛 Troubleshooting

### CORS Errors
Ensure backend CORS is configured:
```python
# backend/.env
CORS_ORIGINS=http://localhost:3000
```

### 401 Unauthorized
- Check backend is running
- Verify API URL is correct
- Clear localStorage and re-login

### Build Errors
```bash
# Clear cache
rm -rf .next node_modules
npm install
npm run build
```

## 📚 Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [TailwindCSS](https://tailwindcss.com)
- [Zustand](https://github.com/pmndrs/zustand)
- [React Hook Form](https://react-hook-form.com)

## ✅ TODO

- [ ] Add form validation with react-hook-form
- [ ] Add toast notifications
- [ ] Add loading skeletons
- [ ] Implement E2E tests (Playwright)
- [ ] Add error boundary
- [ ] Add 404 page
- [ ] Add subscription management
- [ ] Add payment integration
- [ ] Optimize bundle size
- [ ] Add meta tags for SEO
- [ ] Add analytics

## 📄 License

MIT
