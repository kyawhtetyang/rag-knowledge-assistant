# Terminal Command Documentation Rule

Use this rule for all future terminal-based tasks in this repo.

## Goal

- Keep a clear step-by-step history of terminal work.
- Keep deployment behavior reproducible from docs and automation files.
- Separate project history from global computer/infra history.

## Scope Boundary Rule

Use one of these modes before writing a step file:

1. Project mode (default)
- Use when the change is specific to this repo/app.
- Write step files under:
  - `<project_root>/__install/terminal`

2. Global Ops mode
- Use when the change is shared computer/system/VPS policy that is not only this repo.
- Write raw step files under:
  - `/Users/kyawhtet/Library/CloudStorage/GoogleDrive-kyaw.htet.yang@gmail.com/My Drive/(1) Timeline/25.07 Obsidian/2. Computer/00_Inbox/Terminal/YYYY/YYYY-MM`

## Direct Raw Write Rule (No Manual Copy)

For Global Ops mode, do not write to project terminal folders and copy later.

Required behavior:
1. Generate the raw step file directly in `2. Computer/00_Inbox/Terminal/YYYY/YYYY-MM/`.
2. Use `--output-dir` or `TERMINAL_DIR` to point to that final destination at write time.
3. Treat manual transfer/copy as fallback only for recovery, not normal workflow.

## Deploy Automation Rule (One-Click)

When a task changes deployment behavior, update all relevant files in the same change:

1. GitHub workflow:
   - `.github/workflows/deploy-vps.yml`
2. VPS deploy script:
   - `scripts/deploy_vps.sh`
3. Human runbook:
   - `DEPLOY_RUNBOOK.md`
4. Terminal history step file:
   - `__install/terminal/StepN_<topic>.md`

Do not update only one of the above when behavior changed.

## Global Ops Promotion Rule

If a step includes global infra/security effects, promote the result to `2. Computer` in the same task:

1. Raw evidence entry:
- `2. Computer/00_Inbox/Terminal/YYYY/YYYY-MM/StepN_<topic>.md`

2. Curated docs update (as applicable):
- `2. Computer/20_Knowledge/Inventory/*`
- `2. Computer/20_Knowledge/File_System/*`
- `2. Computer/20_Knowledge/Security/*`
- `2. Computer/20_Knowledge/Setup/*`
- `2. Computer/20_Knowledge/Operations/*`

3. Audit and state update:
- `2. Computer/90_Archive/Changes/YYYY/YYYY-MM-DD.md`
- `2. Computer/99_System/STATUS.md`
- `2. Computer/99_System/Index.json`

## Secrets Rule

- Never commit tokens, private keys, or credentials in repo files.
- Store CI secrets only in GitHub Actions Secrets/Variables.
- Use secret names in docs (example: `VPS_SSH_KEY`) instead of raw values.
- If a command needs auth and fails, document the failure and required secret/key setup in the step file.

## Output Path Resolution

### Project mode
- Use this priority order:
  1. `--output-dir` argument (if provided)
  2. `TERMINAL_DIR` environment variable (if set)
  3. Default: `<project_root>/__install/terminal`
- Path safety:
  - Final output path must stay inside `<project_root>/__install`.
  - If a provided path resolves outside that boundary, ignore it and use the next fallback.

### Global Ops mode
- Use this priority order:
  1. `--output-dir` argument (if provided)
  2. `TERMINAL_DIR` environment variable (if set)
  3. Default: `/Users/kyawhtet/Library/CloudStorage/GoogleDrive-kyaw.htet.yang@gmail.com/My Drive/(1) Timeline/25.07 Obsidian/2. Computer/00_Inbox/Terminal/YYYY/YYYY-MM`
- Path safety:
  - Final output path must stay inside `2. Computer/00_Inbox/Terminal`.
  - If a provided path resolves outside that boundary, ignore it and use the next fallback.

## Naming Convention

- Create files in ordered format:
  - `Step1_<short-topic>.md`
  - `Step2_<short-topic>.md`
  - `Step3_<short-topic>.md`
- If step files already exist, create the next number (max existing step + 1).
- Do not reuse an existing step number for a different task.
- Use ASCII names with `_` and no spaces.

## Required Content in Each Step File

1. Scope: what this step solves.
2. Exact terminal commands used.
3. Key outputs/verification checks.
4. Result status (`done` / `failed` / `needs follow-up`).
5. Next step reference (if any).
6. If deployment-related:
   - workflow/script files touched
   - secrets/variables names used
   - health-check URLs validated
7. If global-ops related:
   - promoted `2. Computer` files list
   - change-log file path

## Style Rules

- No chat transcript.
- No long discussion text.
- Keep it execution-focused and reproducible.
- Use absolute paths when helpful.

## Starter Template

````md
# Step N: <Title>

## Scope
- <what this step does>

## Commands
```bash
<exact commands>
```

## Verification
```bash
<check commands>
```

## Result
- Status: done
- Notes: <short notes>

## Next
- Step(N+1): <next file name>
````
