# ICT2216 Secure Software Development — Group 23

## Stack
- **Frontend**: React + TypeScript + Vite, served via Nginx
- **Backend**: Python 3.11 + Flask
- **Database**: Supabase (PostgreSQL)
- **Orchestration**: Docker Compose

## Local Development

1. Copy the env file and fill in your Supabase credentials:
   ```bash
   cp .env.example .env
   ```

2. Run the backend:
   ```bash
   cd backend
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   python run.py
   ```

3. Run the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Running with Docker

```bash
docker compose up --build
```

App will be available at `http://localhost`.

## Branch Strategy

- `main` — production, protected. Only merges from `dev` via reviewed PR.
- `dev` — integration branch. All feature PRs target here.
- `feature/xxx` — individual feature branches.

## CI/CD

- Every push/PR runs: backend tests (pytest), frontend lint + unit tests + build, Docker image build.
- Merges to `main` automatically deploy to the production EC2 via GitHub Actions.

## Notes

- Never commit `.env` to Git.
- If you touch frontend dependencies, regenerate the lockfile using Linux Node to keep it CI-compatible:
  ```bash
  docker run --rm -v "$(pwd)":/app -w /app node:20-alpine npm install --package-lock-only --no-audit --no-fund
  ```
