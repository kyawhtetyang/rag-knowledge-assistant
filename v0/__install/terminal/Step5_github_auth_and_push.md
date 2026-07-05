# Step 5: GitHub Auth And Push

## Scope
- Resolve GitHub push authentication failure.
- Load GitHub SSH key into agent.
- Push `main` branch to remote repository.

## Commands
```bash
cd /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG

# inspect key state
ssh-add -l
ls -la ~/.ssh
sed -n '1,220p' ~/.ssh/config

# load github key
ssh-add --apple-use-keychain ~/.ssh/id_github
ssh-add -l

# verify github auth
ssh -T git@github.com

# push
git remote set-url origin git@github.com:kyawhtetyang/RAG_Knowledge_Assistant.git
git push -u origin main
```

## Verification
```bash
# ssh auth
# Hi kyawhtetyang! You've successfully authenticated, but GitHub does not provide shell access.

# push
# [new branch] main -> main
# branch 'main' set up to track 'origin/main'
```

## Result
- Status: done
- Notes:
  - `~/.ssh/id_github` key was present but not loaded in `ssh-agent`.
  - After loading, GitHub SSH auth succeeded and push completed.

## Next
- Step6_fastapi_migration_plan.md: migrate Flask backend to FastAPI while preserving API contract.
