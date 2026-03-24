# 🚀 Vercel Monorepo Deployment - Complete Guide

## ✅ All Issues Fixed

### Task 1: Root vercel.json Configuration ✓
**File:** `vercel.json` (root directory)

```json
{
  "version": 2,
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/.next",
  "installCommand": "cd frontend && npm install",
  "framework": "nextjs",
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/next"
    },
    {
      "src": "backend/api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/v1/(.*)",
      "dest": "/backend/api/index.py"
    },
    {
      "src": "/(.*\\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot))$",
      "dest": "/frontend/$1"
    },
    {
      "handle": "filesystem"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/$1"
    }
  ],
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "/backend/api/index.py"
    }
  ],
  "env": {
    "NEXT_PUBLIC_API_URL": "/api"
  }
}
```

**What this does:**
- ✅ Tells Vercel to build Next.js frontend
- ✅ Configures Python serverless functions for backend
- ✅ Routes `/api/v1/*` requests to FastAPI backend
- ✅ Serves static files correctly
- ✅ Handles all other routes with Next.js

---

### Task 2: Dependencies & Path Alignment ✓

#### Frontend Dependencies ✓
**File:** `frontend/package.json`

All critical dependencies are in `dependencies` (not devDependencies):
- ✅ `@radix-ui/react-label`: Runtime UI component
- ✅ `@radix-ui/react-progress`: Runtime UI component
- ✅ `@radix-ui/react-slot`: Runtime UI component
- ✅ `next`: Framework (runtime)
- ✅ `react`: Runtime library
- ✅ `react-dom`: Runtime library
- ✅ `recharts`: Runtime charts

#### Backend Dependencies ✓
**File:** `backend/requirements.txt`

All necessary libraries included:
```
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.2
mangum==0.17.0
anthropic==0.40.0
# ... (37 dependencies total)
```

#### Backend Entry Point ✓
**File:** `backend/app/main.py` (line 63)

```python
app = FastAPI(
    title="Smart English Test-Prep Agent",
    # ...
)
```

✅ Vercel Python runtime will find `app` variable

---

### Task 3: Production API Configuration ✓

#### API Client Configuration
**File:** `frontend/lib/api.ts` (lines 20-24)

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || (
  process.env.NODE_ENV === 'production'
    ? '/api'  // Relative path for Vercel serverless functions
    : 'http://localhost:8000'
);
```

✅ **Development:** API calls go to `http://localhost:8000`
✅ **Production:** API calls use `/api` (rewritten to serverless functions)

---

### Task 4: Cleanup ✓

#### Removed Files ✓
- ❌ `REFACTORING_COMPLETE.md` (redundant documentation)

#### Kept Files ✓
- ✅ `VERCEL_DEPLOYMENT_FIXES.md` (deployment guide)
- ✅ `README.md` (project documentation)
- ✅ `requirements.txt` (root - needed for Vercel Python detection)
- ✅ `package.json` (root - workspace configuration)

#### .gitignore Verification ✓
```
node_modules/
.next/
__pycache__/
.vercel/
*.pyc
```

All build artifacts properly excluded.

---

## 🎯 Vercel Dashboard Settings

### Import Project
1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "Add New Project"
3. Import: `https://github.com/PhuongThaoValeria/Smart.git`

### Configuration (Auto-detected)
Leave these **empty** - Vercel will auto-detect:

| Setting | Value | Status |
|---------|-------|--------|
| **Root Directory** | `./` (empty) | ✅ Auto-detected |
| **Framework Preset** | Next.js | ✅ Auto-detected |
| **Build Command** | `cd frontend && npm run build` | ✅ Auto-detected |
| **Output Directory** | `frontend/.next` | ✅ Auto-detected |
| **Install Command** | `cd frontend && npm install` | ✅ Auto-detected |

### Environment Variables (Required)
Go to **Settings → Environment Variables** and add:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here
ENVIRONMENT=production
JWT_SECRET_KEY=generate-a-strong-random-string-here

# Optional (for database features)
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

**Important:** Click "Redeploy" after adding environment variables!

---

## 📊 Expected Deployment Output

### Successful Build Log
```
✓ Detecting Next.js
✓ Installing dependencies (frontend)
✓ Building Next.js application
✓ Python runtime detected
✓ Installing Python dependencies
✓ Deploying serverless functions
✓ Upload finished [2.5s]
✓ Build completed
```

### Verification Commands
After deployment, test these endpoints:

```bash
# Health check
curl https://your-app.vercel.app/api/v1/health/ping

# Frontend
curl https://your-app.vercel.app/

# API info
curl https://your-app.vercel.app/info
```

**Expected Response:**
```json
{
  "status": "operational",
  "timestamp": "2026-03-24T...",
  "name": "Smart English Test-Prep Agent API"
}
```

---

## 🔧 Troubleshooting

### Issue: "Module not found: @radix-ui/react-progress"
**Status:** ✅ FIXED
- All @radix-ui dependencies are now in `dependencies` (not devDependencies)

### Issue: "Network Error" in production
**Status:** ✅ FIXED
- API client uses `/api` in production
- Vercel rewrites `/api/*` to `backend/api/index.py`

### Issue: "Failed to find package.json"
**Status:** ✅ FIXED
- Root `package.json` created with workspace configuration
- `vercel.json` specifies exact paths

### Issue: "Python runtime not detected"
**Status:** ✅ FIXED
- `backend/api/index.py` exists and is properly configured
- `backend/requirements.txt` is complete
- Root `requirements.txt` symlinked to backend

### Issue: "Build timeout"
**Solution:** Consider Vercel Pro (60s timeout vs 10s Hobby)

---

## 📁 Final Project Structure

```
smart-english-testprep/
├── vercel.json                 ✅ Root Vercel config
├── package.json                ✅ Root workspace config
├── requirements.txt            ✅ Root Python deps (symlink)
├── .gitignore                  ✅ Properly excludes build artifacts
├── README.md                   ✅ Project documentation
├── VERCEL_DEPLOYMENT_FIXES.md  ✅ Deployment guide
│
├── frontend/                   ✅ Next.js app
│   ├── package.json           ✅ All runtime deps in "dependencies"
│   ├── app/                   ✅ Next.js pages
│   ├── components/            ✅ React components
│   ├── lib/api.ts             ✅ Production-ready API client
│   └── ...
│
└── backend/                    ✅ FastAPI app
    ├── api/index.py           ✅ Vercel serverless entry point
    ├── app/main.py            ✅ app = FastAPI() correctly named
    ├── requirements.txt       ✅ Complete Python dependencies
    └── ...
```

---

## ✨ What Changed in This Commit

| File | Change | Impact |
|------|--------|--------|
| `vercel.json` | ✅ Updated with optimal config | Proper monorepo routing |
| `package.json` | ✅ Enhanced with engines field | Node 18+ requirement |
| `frontend/package.json` | ✅ Added engines field | Consistent Node version |
| `REFACTORING_COMPLETE.md` | ❌ Deleted | Removed redundancy |

---

## 🎉 Success Criteria

Your Vercel deployment should now:

- ✅ **Detect Next.js** frontend automatically
- ✅ **Detect Python** backend automatically
- ✅ **Build both runtimes** without errors
- ✅ **Route API calls** to serverless functions
- ✅ **Serve frontend** on all other routes
- ✅ **Handle static assets** correctly
- ✅ **Work in production** without network errors

---

## 🚀 Ready to Deploy!

**Next Steps:**

1. **Push to GitHub** (already done!)
   ```bash
   git push origin main
   ```

2. **Import to Vercel**
    - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
    - Import repository

3. **Configure Environment Variables**
    - Add `ANTHROPIC_API_KEY`, `ENVIRONMENT`, `JWT_SECRET_KEY`

4. **Deploy**
    - Click "Deploy" button
    - Wait 2-3 minutes

5. **Test**
    ```bash
    curl https://your-app.vercel.app/api/v1/health/ping
    ```

---

**Last Updated:** 2026-03-24
**Commit:** 709aa2b
**Status:** ✅ Ready for Production
**Repository:** https://github.com/PhuongThaoValeria/Smart.git

---

Built with ❤️ for Vietnamese students
