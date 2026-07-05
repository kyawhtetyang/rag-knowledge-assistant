# Step 4: GitHub Push Attempt

## Scope
- Initialize git at project root `13_RAG`.
- Commit current `v0` project state.
- Push to `https://github.com/kyawhtetyang/RAG_Knowledge_Assistant`.

## Commands
```bash
cd /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG

# setup repo and ignore local artifacts
cat > .gitignore <<'EOT'
# OS / editor
.DS_Store
.vscode/
.idea/

# Python
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Virtual environments
.venv/
venv/
env/

# Project-local artifacts
v0/backend/.venv/
v0/backend/output/

# Logs
*.log

# Env files
.env
.env.*
!.env.example
EOT

git init
git add .
git commit -m "Initial commit: RAG Knowledge Assistant v0"

git remote add origin https://github.com/kyawhtetyang/RAG_Knowledge_Assistant.git

# push attempts
git push -u origin main
git remote set-url origin git@github.com:kyawhtetyang/RAG_Knowledge_Assistant.git
git push -u origin main

# reset remote to requested URL
git remote set-url origin https://github.com/kyawhtetyang/RAG_Knowledge_Assistant.git
git remote -v
```

## Verification
```bash
# commit created
# 3f5b0a7 Initial commit: RAG Knowledge Assistant v0

# push via https
# fatal: could not read Username for 'https://github.com': Device not configured

# push via ssh
# Permission denied (publickey)

# origin reset
# origin https://github.com/kyawhtetyang/RAG_Knowledge_Assistant.git (fetch)
# origin https://github.com/kyawhtetyang/RAG_Knowledge_Assistant.git (push)
```

## Result
- Status: needs follow-up
- Notes:
  - Local repository and initial commit were successful.
  - Remote push blocked by missing GitHub authentication in current environment.

## Next
- Step5_github_auth_and_push.md: authenticate GitHub CLI or configure SSH key, then run `git push -u origin main`.
