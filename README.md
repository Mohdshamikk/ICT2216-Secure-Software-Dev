# ICT2216 Secure Software Development — Group 23

## Stack
- **Frontend**: React + TypeScript + Vite, deployed on Vercel
- **Backend**: Python 3.11 + Flask, deployed on EC2 via Docker + Gunicorn
- **Database**: Supabase (PostgreSQL)
- **Orchestration**: Docker Compose (production backend only)
- **Reverse Proxy**: Nginx on EC2 (routes `/api/` to backend container)

---

## New Collaborator Setup

If you just got access to this repo, follow these steps before anything else.

### 1. Clone the repo
```bash
git clone https://github.com/<org>/ICT2216-Secure-Software-Dev.git
cd ICT2216-Secure-Software-Dev
git checkout dev
```

### 2. Get the `.env` file
The `.env` file is not in the repo. Get it from a teammate over a secure channel and place it at the project root:
```
ICT2216-Secure-Software-Dev/.env
```
See `.env.example` for the full list of required values.

### 3. Set up the backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Set up the frontend
```bash
cd frontend
npm install
```

### 5. Run locally
Open two terminals:
```bash
# Terminal 1 — backend (http://localhost:5000)
cd backend && source venv/bin/activate && python run.py

# Terminal 2 — frontend (http://localhost:5173)
cd frontend && npm run dev
```

Open `http://localhost:5173`. API calls are automatically proxied to the local Flask backend via Vite — no extra config needed.

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Production. Protected — no direct pushes. |
| `dev` | Integration branch. All feature PRs target here. |
| `feature/xxx` | Individual features. Branch off `dev`. |

**Never push directly to `main` or `dev`.**

```bash
# Always start a new feature like this
git checkout dev
git pull origin dev
git checkout -b feature/your-feature-name
```

`dev` → `main` is done by the team lead when ready to release, via a reviewed PR.

---

## Local Development Flow

```
git checkout -b feature/your-feature (from dev)
         │
         ▼
┌─────────────────────────────────┐
│         Terminal 1 — Backend    │
│  cd backend                     │
│  source venv/bin/activate       │
│  python run.py                  │
│  → Flask on localhost:5000      │
└─────────────────────────────────┘
┌─────────────────────────────────┐
│         Terminal 2 — Frontend   │
│  cd frontend                    │
│  npm run dev                    │
│  → Vite on localhost:5173       │
│  → /api/* proxied to :5000      │
└─────────────────────────────────┘
         │
         ▼
  Develop and test at http://localhost:5173
         │
         ▼
  git add / commit / push feature branch
         │
         ▼
  Open PR → dev (CI runs, no deploy)
```

---

## Production CI/CD Flow

```
feature/xxx → PR → dev → PR → main
                              │
                              ├──► Vercel auto-deploys frontend
                              │
                              └──► GitHub Actions (deploy-prod.yml)
                                   SSH into EC2
                                   → git pull
                                   → rewrite .env
                                   → docker compose up (backend only)
                                   → nginx serves /api/ → backend
```

Every PR triggers CI automatically:
- Backend: `pytest`
- Frontend: ESLint + Vitest + TypeScript build
- Docker: image build check

Merges to `main` only happen through a reviewed PR that passed CI.

---

## Local vs Production

| | Local | Production |
|---|---|---|
| Frontend | Vite dev server (`:5173`) | Vercel |
| Backend | Flask directly (`:5000`) | Docker + Gunicorn on EC2 |
| API routing | Vite proxy | Nginx → backend container |
| Database | Supabase (shared) | Supabase |
| HTTPS | No | Yes (Certbot + DuckDNS) |
| Triggered by | Manual | Merge to `main` |

---

## What Collaborators Do NOT Need to Touch
- EC2 or SSH keys
- Vercel — auto-deploys on merge to `main`, nothing to configure
- GitHub Secrets — already set up
- Docker — only needed to test the prod build locally (`docker compose up --build`)

---

## Running with Docker (optional, prod-like local test)
```bash
cp .env.example .env  # fill in real values
docker compose up --build
```
App will be available at `http://localhost`.

---

## Notes
- Never commit `.env` to Git.
- If you touch frontend dependencies, regenerate the lockfile using Linux Node to keep it CI-compatible:
  ```bash
  docker run --rm -v "$(pwd)":/app -w /app node:20-alpine npm install --package-lock-only --no-audit --no-fund
  ```
