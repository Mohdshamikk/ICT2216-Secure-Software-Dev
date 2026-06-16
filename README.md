# ICT2216-Secure-Software-Dev
Centralized Repository to manage all the codes for the module ICT2216

Run this under frontend directory before pushing (if you touch frontend dependency)
- docker run --rm -v "$(pwd)":/app -w /app node:20-alpine npm install --package-lock-only --no-audit --no-fund