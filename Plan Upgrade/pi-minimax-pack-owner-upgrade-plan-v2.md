# PI-MINIMAX-PACK — Owner Mode Upgrade Plan v2

Dokumen ini menggantikan plan sebelumnya. Versi ini dibuat dalam **Owner Mode**: repo `pi-minimax-pack` adalah repo Anda sendiri, jadi agent **boleh mengubah file mana pun**, termasuk `extensions/global-contract.ts`, selama perubahan dilakukan dengan cara yang aman, terukur, dan bisa diverifikasi.

Hal yang saya koreksi dari plan sebelumnya:

> Bukan berarti `extensions/global-contract.ts` “tidak boleh diedit”.
>
> Yang benar: **boleh dan memang kemungkinan harus diedit**, tetapi file itu harus diedit dengan metode yang menjaga escape sequence `\n`, karena `docs/AI_AGENT_GUIDE.md` di repo Anda sendiri mencatat bahwa tool `write/edit` biasa pernah merusak string literal di file tersebut.

Jadi aturan barunya:

```text
Owner permission: boleh edit semua file repo.
Engineering rule: untuk global-contract.ts, gunakan binary-safe write / patch yang diverifikasi.
```

---

## 1. Tujuan Besar Upgrade

Tujuan upgrade `pi-minimax-pack` bukan membuatnya khusus untuk Inventory/Wails, tetapi menjadikannya **generic agent harness** yang bisa dipakai untuk semua project Pi Anda.

Target akhir:

1. Agent tidak sekadar mengingat kesalahan, tetapi **mencegah kesalahan berulang**.
2. Memory/correction bisa naik menjadi rule yang enforceable.
3. Extension mampu membaca policy project, bukan hardcode satu kasus.
4. Agent bisa memakai extension/prompt/skill yang sudah terpasang sebelum menyarankan tool baru.
5. Agent tidak lompat-lompat dari build ke CI, database, backend, atau refactor tanpa izin.
6. Semua perubahan punya state, bukti, verifikasi, rollback, dan status report.

---

## 2. Fakta Repo Saat Ini

Berdasarkan repo `adi805/pi-minimax-pack`:

- Package bernama `pi-minimax-pack`.
- Versi di `package.json`: `0.3.4`.
- Package config Pi memuat:
  - `extensions: ["./extensions"]`
  - `skills: ["./skills"]`
  - `prompts: []`
- Extension utama sekarang: `extensions/global-contract.ts`.
- `README.md` masih mengarahkan install ke tag lama `v0.2.25`.
- `docs/INSTALLATION.md` masih mengarah ke versi lama `v0.2.20/v0.2.21`.
- `docs/HOW_IT_WORKS.md` menjelaskan lifecycle hook utama:
  - `input`
  - `before_agent_start`
  - `tool_execution_end`
  - `tool_call`
  - `message_end`
- `docs/AI_AGENT_GUIDE.md` berisi peringatan teknis untuk `global-contract.ts`: jangan memakai tool write/edit biasa karena pernah merusak escape sequence `\n`; gunakan binary write dan verifikasi bytes.

Fitur yang sudah ada:

1. Global contract injection.
2. Auto skill routing berbasis keyword.
3. Validation command detection.
4. Auto-grind setelah file berubah.
5. Status Report otomatis.
6. Persistence per project di `.pi/agent/minimax-state/minimax-persist.json`.
7. Safety gates awal:
   - read-before-edit
   - no shell redirection

Masalah inti:

1. Guardrail masih terlalu sedikit.
2. Banyak verifikasi terjadi **setelah** agent berbuat, bukan sebelum command berisiko.
3. Belum ada project detector yang kuat.
4. Belum ada policy loader berlapis.
5. Belum ada task state machine.
6. Belum ada drift detector.
7. Belum ada memory-to-rule promotion.
8. Belum ada artifact consistency validator.
9. Documentation versioning tidak sinkron.
10. `global-contract.ts` terlalu monolitik dan rawan rusak saat diedit tanpa metode aman.

---

## 3. Prinsip Desain Baru

### 3.1 Core harus generic

Jangan hardcode kasus Inventory/Wails di core.

Contoh yang salah:

```ts
if (cwd.includes("inventory-desktop-wails") && cmd.includes("go build")) block();
```

Contoh yang benar:

```text
Project Detector mendeteksi projectType = ["go", "wails", "frontend"]
Policy Loader memuat profile wails
Command Policy memblok go build karena profile wails aktif
```

### 3.2 Aturan spesifik masuk sebagai policy/profile

Core engine harus berlaku untuk semua project:

- Node
- Go
- Wails
- Rust
- Tauri
- Python
- PHP
- Laravel
- PostgreSQL
- Docker
- Desktop app
- Web app
- Docs project

Aturan khusus project masuk ke:

```text
.pi/minimax-policy.json
```

Aturan khusus teknologi masuk ke:

```text
profiles/*.json
```

### 3.3 Memory bukan rem; policy adalah rem

Hermes Memory atau memory extension lain bisa menyimpan pelajaran, tetapi harness harus punya mekanisme:

```text
correction → candidate memory → proposed rule → approved rule → enforced gate
```

Tanpa tahap rule/gate, self-improvement hanya menjadi catatan pasif.

---

## 4. Target Arsitektur Baru

Rancang ulang `pi-minimax-pack` menjadi lapisan seperti ini:

```text
pi-minimax-pack
├── extensions/
│   └── global-contract.ts              # bootstrap utama; boleh tetap single-file pada fase awal
├── docs/
│   ├── AGENTS.md
│   ├── HOW_IT_WORKS.md
│   ├── INSTALLATION.md
│   ├── AI_AGENT_GUIDE.md
│   ├── POLICY_SCHEMA.md                # baru
│   ├── PROFILES.md                     # baru
│   ├── MEMORY_TO_RULE.md               # baru
│   └── EXTENSION_USAGE_GUIDE.md        # baru
├── skills/
│   └── ...
├── prompts/
│   ├── minimax-preflight.md            # baru kalau Pi package support prompts
│   ├── minimax-diagnose.md
│   ├── minimax-risk-fix.md
│   ├── minimax-promote-memory.md
│   └── minimax-review.md
├── profiles/
│   ├── generic.json                    # baru
│   ├── node.json
│   ├── go.json
│   ├── wails.json
│   ├── tauri.json
│   ├── rust.json
│   ├── python.json
│   ├── php.json
│   ├── postgres.json
│   └── docker.json
├── test/
│   ├── extension-runtime-smoke.cjs
│   ├── verification-snapshot-eval.cjs
│   ├── policy-loader.test.cjs          # baru
│   ├── project-detector.test.cjs       # baru
│   ├── command-risk-classifier.test.cjs# baru
│   ├── task-state-machine.test.cjs     # baru
│   └── memory-to-rule.test.cjs         # baru
└── package.json
```

Jika Pi runtime belum nyaman dengan import banyak file, lakukan fase awal tetap di `global-contract.ts`, tetapi struktur internalnya dipisah sebagai section:

```ts
// POLICY TYPES
// POLICY LOADER
// PROJECT DETECTOR
// COMMAND RISK CLASSIFIER
// TASK STATE MACHINE
// DRIFT DETECTOR
// ARTIFACT VALIDATOR
// MEMORY-TO-RULE PROMOTION
// EXTENSION ADVISOR
// HOOKS
```

Setelah stabil, baru refactor ke multi-file.

---

## 5. Komponen yang Harus Ditambahkan

### 5.1 Project Detector

Fungsi: mendeteksi jenis project dari file/folder.

Deteksi minimal:

| Marker | Project Type |
|---|---|
| `package.json` | node/frontend |
| `vite.config.*` | vite |
| `svelte.config.*` | svelte/sveltekit |
| `go.mod` | go |
| `wails.json` | wails |
| `Cargo.toml` | rust |
| `src-tauri/tauri.conf.json` | tauri |
| `requirements.txt`, `pyproject.toml` | python |
| `composer.json` | php |
| `artisan` | laravel |
| `docker-compose.yml` | docker |
| `migrations/`, `schema.sql` | database |

Output:

```json
{
  "root": "D:/Estate/Pi_Project/Inventory/inventory-desktop-wails",
  "types": ["go", "wails", "frontend"],
  "confidence": 0.95,
  "markers": ["go.mod", "wails.json", "frontend/package.json"]
}
```

### 5.2 Layered Policy Loader

Policy harus dibaca berlapis:

```text
Global policy      → ~/.pi/minimax-policy.json
Workspace policy   → D:/Estate/Pi_Project/.pi/minimax-policy.json
Project policy     → <project-root>/.pi/minimax-policy.json
Task policy        → in-memory untuk request saat ini
```

Merge rule:

1. Project policy override workspace.
2. Workspace override global.
3. Task policy paling tinggi.
4. Block rule menang atas allow rule, kecuali ada explicit user override.

### 5.3 Command Risk Classifier

Klasifikasi command sebelum dijalankan:

```text
SAFE_READ       : dir, ls, cat, Get-Content, git status, git diff
BUILD           : npm run build, wails build, cargo build, go test
INSTALL         : npm install, go install, pip install, composer install
DESTRUCTIVE     : rm -rf, Remove-Item -Recurse, git reset --hard
DEPLOY          : git push, gh workflow run, vercel deploy
DATABASE        : migrate, drop, truncate, seed
NETWORK         : curl remote script, download installer
UNKNOWN         : command tidak dikenal
```

Default action:

| Risk | Default Action |
|---|---|
| SAFE_READ | allow |
| BUILD | require preflight |
| INSTALL | require reason |
| DESTRUCTIVE | require explicit approval |
| DEPLOY | require explicit user request |
| DATABASE | require backup/dry-run |
| NETWORK | require reason + target URL |
| UNKNOWN | ask or dry-run |

### 5.4 Task State Machine

State umum:

```text
IDLE
SNAPSHOT
DIAGNOSE
PLAN
WAIT_APPROVAL
IMPLEMENT
VERIFY
REPORT
DONE
BLOCKED
```

Transitions:

```text
IDLE → SNAPSHOT → DIAGNOSE → PLAN → WAIT_APPROVAL → IMPLEMENT → VERIFY → REPORT → DONE
```

Emergency transitions:

```text
Any state → BLOCKED if:
- popup error
- corrupted installer
- empty output
- command blocked by policy
- task drift
- file mismatch
- destructive command without approval
```

### 5.5 Drift Detector

Cegah agent pindah task tanpa izin.

Contoh drift:

```text
Current task: local build debug
Proposed action: setup CI
Result: BLOCK
```

```text
Current task: installer packaging
Proposed action: port SQLite backend
Result: BLOCK
```

Detection bisa memakai keyword dan task category:

```json
{
  "currentTask": "installer-debug",
  "blockedDriftCategories": ["ci", "deployment", "backend-port", "database-migration", "large-refactor"]
}
```

### 5.6 Artifact Validator

General validator untuk file output.

Validasi umum:

1. Output file exists.
2. Output size > minimum.
3. Output timestamp setelah command start.
4. Hash source vs copied artifact cocok jika artifact dicopy.
5. Output folder tidak kosong.
6. Jika installer/package, lakukan extract/test minimal.

Contoh generic:

```json
{
  "artifactRules": [
    {
      "id": "copied-artifact-hash-match",
      "when": "fileCopied",
      "check": "sourceHash == targetHash",
      "action": "block_on_mismatch"
    }
  ]
}
```

### 5.7 Memory-to-Rule Promotion

Saat user mengoreksi agent:

```text
No, never use X for Y.
```

Harness harus:

1. Deteksi sebagai correction.
2. Simpan sebagai candidate rule.
3. Tanyakan apakah ingin dipromosikan menjadi rule project.
4. Jika approved, tulis ke `.pi/minimax-policy.json`.
5. Enforce rule di `tool_call`.

Contoh candidate rule:

```json
{
  "id": "wails-no-plain-go-build",
  "source": "user-correction",
  "scope": "project",
  "status": "candidate",
  "condition": {
    "projectType": "wails",
    "tool": "bash",
    "commandRegex": "\\bgo\\s+build\\b"
  },
  "action": "block",
  "message": "This is a Wails project. Use wails build -clean."
}
```

### 5.8 Installed Extension Advisor

Karena Pi Anda sudah punya banyak extension, harness harus menganjurkan agent untuk **memakai yang sudah terpasang dulu**.

Yang harus dilakukan harness:

1. Baca loaded resources jika tersedia dari startup context.
2. Jangan sarankan install extension baru sebelum audit extension yang sudah ada.
3. Untuk task tertentu, sarankan prompt/extension yang relevan:
   - debugging → `/bug-diagnose`, `/risk-fix`
   - recon project → `/recon-all`, `codebase-recon`
   - verification → `/lean-verify`
   - review → `pi-review-mode`, `/review-arch`
   - docs → `pi-docparser`, `documentation`
   - diagram → `pi-mermaid`
   - memory → `pi-hermes-memory`, `/memory-insights`, `/memory-consolidate`
   - subtask audit → `@tintinweb/pi-subagents`

Rule:

```text
Before recommending new package/extension, list existing installed options that could solve the task.
```

---

## 6. Policy Schema v1

Buat `docs/POLICY_SCHEMA.md` dan jadikan contoh ini sebagai baseline.

```json
{
  "version": 1,
  "name": "project policy name",
  "scope": "global | workspace | project | task",
  "project": {
    "name": "auto",
    "root": "auto",
    "types": ["auto"]
  },
  "workflow": {
    "requireDiagnosisBeforeEdit": true,
    "requirePlanBeforeRiskyCommand": true,
    "oneNextStepAfterFailure": true,
    "stopOnTaskDrift": true,
    "stopOnPopupError": true,
    "stopOnEmptyOutput": true,
    "stopOnArtifactMismatch": true
  },
  "commandPolicy": {
    "safeRead": "allow",
    "build": "preflight",
    "install": "require_reason",
    "destructive": "require_approval",
    "deploy": "require_explicit_user_request",
    "database": "require_backup_or_dry_run",
    "network": "require_reason",
    "unknown": "ask"
  },
  "rules": [
    {
      "id": "example-block-command",
      "description": "Example command block rule",
      "enabled": true,
      "when": {
        "projectType": "wails",
        "tool": "bash",
        "commandRegex": "\\bgo\\s+build\\b"
      },
      "action": "block",
      "message": "Use wails build -clean for Wails apps."
    }
  ],
  "artifactPolicy": {
    "verifyOutputExists": true,
    "verifyOutputTimestamp": true,
    "verifyHashWhenCopyingArtifacts": true,
    "verifyNonEmptyOutputDir": true
  },
  "todoPolicy": {
    "maxActiveTodos": 3,
    "blockUnrelatedTodos": true,
    "requireUserApprovalForNewWorkstream": true
  },
  "memoryPolicy": {
    "detectCorrections": true,
    "proposeRulePromotion": true,
    "autoPromote": false,
    "storeCandidateRules": true
  },
  "extensionPolicy": {
    "preferInstalledExtensions": true,
    "requireAuditBeforeNewExtension": true
  }
}
```

---

## 7. Default Profiles

### 7.1 `profiles/generic.json`

```json
{
  "profile": "generic",
  "detectWhen": [],
  "rules": [],
  "validationCommands": [],
  "stopConditions": [
    "popup_error",
    "empty_output",
    "task_drift",
    "destructive_without_approval"
  ]
}
```

### 7.2 `profiles/node.json`

```json
{
  "profile": "node",
  "detectWhen": ["package.json"],
  "validationCommands": [
    "npm test",
    "npm run lint",
    "npm run build"
  ],
  "packageManagers": ["npm", "pnpm", "yarn", "bun"],
  "rules": [
    {
      "id": "node-lockfile-mismatch-warning",
      "when": {
        "filesExistAny": ["package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb"]
      },
      "action": "warn_if_multiple_lockfiles",
      "message": "Multiple package manager lockfiles found. Ask before switching package manager."
    }
  ]
}
```

### 7.3 `profiles/go.json`

```json
{
  "profile": "go",
  "detectWhen": ["go.mod"],
  "validationCommands": ["go test ./..."],
  "rules": [
    {
      "id": "go-mod-before-build-warning",
      "when": { "commandRegex": "\\bgo\\s+build\\b" },
      "action": "preflight",
      "message": "Check go.mod, module path, and project type before building."
    }
  ]
}
```

### 7.4 `profiles/wails.json`

```json
{
  "profile": "wails",
  "detectWhen": ["wails.json", "go.mod"],
  "preferredCommands": {
    "build": "wails build -clean"
  },
  "rules": [
    {
      "id": "wails-block-plain-go-build",
      "when": { "commandRegex": "\\bgo\\s+build\\b" },
      "action": "block",
      "message": "Wails apps must be built with wails build -clean, not plain go build."
    },
    {
      "id": "wails-installer-after-exe-validation",
      "when": { "commandRegex": "ISCC|Inno|installer" },
      "action": "require_artifact_verified",
      "artifact": "build/bin/*.exe",
      "message": "Verify Wails EXE runs before building installer."
    }
  ]
}
```

### 7.5 `profiles/tauri.json`

```json
{
  "profile": "tauri",
  "detectWhen": ["src-tauri/tauri.conf.json", "Cargo.toml"],
  "preferredCommands": {
    "build": "npm run tauri build"
  },
  "rules": [
    {
      "id": "tauri-check-rust-and-frontend",
      "when": { "commandRegex": "tauri build|cargo build" },
      "action": "preflight",
      "message": "Check frontend build and Rust toolchain before Tauri packaging."
    }
  ]
}
```

---

## 8. Perubahan yang Harus Dilakukan di `global-contract.ts`

### 8.1 Boleh diedit, jangan takut

Karena ini repo owner, agent boleh mengubah `global-contract.ts`.

Tetapi agent wajib mengikuti metode ini:

```text
1. git status
2. git diff -- extensions/global-contract.ts
3. ambil source bytes dari git atau file saat ini
4. patch dengan script yang menjaga escape sequence
5. tulis binary-safe
6. verifikasi CRLF dan escape sequence
7. jalankan npm run smoke
8. jalankan npm run eval:snapshot
```

### 8.2 Tambahkan types internal

Tambahkan type minimal:

```ts
type ProjectType =
  | "generic"
  | "node"
  | "frontend"
  | "go"
  | "wails"
  | "rust"
  | "tauri"
  | "python"
  | "php"
  | "postgres"
  | "docker";

type CommandRisk =
  | "safe_read"
  | "build"
  | "install"
  | "destructive"
  | "deploy"
  | "database"
  | "network"
  | "unknown";

type PolicyAction =
  | "allow"
  | "warn"
  | "preflight"
  | "block"
  | "ask"
  | "require_approval";
```

### 8.3 Tambahkan command classifier

Pseudo-code:

```ts
function classifyCommand(cmd: string): CommandRisk {
  const c = cmd.trim().toLowerCase();

  if (/^(dir|ls|pwd|cat|type|get-content|git status|git diff)\b/.test(c)) return "safe_read";
  if (/\b(npm|pnpm|yarn|bun)\s+(install|add)\b/.test(c)) return "install";
  if (/\b(pip|uv|poetry|composer|go)\s+(install|get)\b/.test(c)) return "install";
  if (/\b(npm run build|pnpm build|yarn build|cargo build|go build|wails build|go test|cargo test)\b/.test(c)) return "build";
  if (/\b(rm -rf|remove-item .*\-recurse|del /s|git reset --hard)\b/.test(c)) return "destructive";
  if (/\b(git push|gh workflow run|vercel deploy|netlify deploy|docker push)\b/.test(c)) return "deploy";
  if (/\b(drop table|truncate|migrate|migration|seed)\b/.test(c)) return "database";
  if (/\b(curl|wget|irm|iwr)\b/.test(c)) return "network";

  return "unknown";
}
```

### 8.4 Tambahkan project detector

Pseudo-code:

```ts
function detectProject(cwd: string): DetectedProject {
  const markers: string[] = [];
  const types = new Set<ProjectType>(["generic"]);

  if (exists(cwd, "package.json")) { types.add("node"); markers.push("package.json"); }
  if (exists(cwd, "frontend/package.json")) { types.add("frontend"); markers.push("frontend/package.json"); }
  if (exists(cwd, "go.mod")) { types.add("go"); markers.push("go.mod"); }
  if (exists(cwd, "wails.json")) { types.add("wails"); markers.push("wails.json"); }
  if (exists(cwd, "Cargo.toml")) { types.add("rust"); markers.push("Cargo.toml"); }
  if (exists(cwd, "src-tauri/tauri.conf.json")) { types.add("tauri"); markers.push("src-tauri/tauri.conf.json"); }
  if (exists(cwd, "requirements.txt") || exists(cwd, "pyproject.toml")) { types.add("python"); }
  if (exists(cwd, "composer.json")) { types.add("php"); }
  if (exists(cwd, "docker-compose.yml") || exists(cwd, "Dockerfile")) { types.add("docker"); }

  return { root: cwd, types: [...types], markers, confidence: markers.length ? 0.8 : 0.2 };
}
```

### 8.5 Tambahkan policy enforcement di `tool_call`

Pintu utama ada di event `tool_call`, karena di sana command bisa diblok **sebelum dijalankan**.

Pseudo-code:

```ts
pi.on("tool_call", async (event, ctx) => {
  if (event.toolName === "bash") {
    const cmd = String((event as any).input?.command || "");
    const project = detectProject(ctx.cwd);
    const policy = loadMergedPolicy(ctx.cwd, project);
    const decision = evaluateCommandPolicy(cmd, project, policy);

    if (decision.action === "block") {
      return { block: true, reason: decision.message };
    }

    if (decision.action === "ask" || decision.action === "require_approval") {
      return { block: true, reason: decision.message + " Ask the user before proceeding." };
    }
  }

  // existing read-before-edit and no redirect gates remain active
});
```

---

## 9. Extension Usage Reminder

Harness harus selalu mengingatkan agent untuk memakai extension/prompt/skill yang sudah terpasang.

Dari Pi environment Anda, resource yang relevan sudah ada:

```text
Prompts:
/preflight
/bug-diagnose
/bug-implement
/feature-design
/feature-implement
/lean-verify
/recon-all
/review-arch
/risk-fix
/refactor-design
/refactor-implement

Extensions:
pi-hermes-memory
pi-review-mode
pi-mcp-adapter
pi-docparser
pi-mermaid
@firstpick/pi-extension-git-footer-status
@tintinweb/pi-subagents
rpiv suite
```

Rule baru:

```text
Before suggesting any new Pi extension or MCP, check installed prompts/extensions first.
```

Tambahkan ke contract injection:

```md
## Installed Resource Discipline
Before recommending new extensions/tools, inspect and prefer already-loaded Pi prompts, skills, and extensions.
Use project-appropriate existing resources first:
- Debugging: /bug-diagnose, /risk-fix
- Recon: /preflight, /recon-all
- Verification: /lean-verify
- Review: pi-review-mode, /review-arch
- Docs: pi-docparser
- Diagram: pi-mermaid
- Memory: pi-hermes-memory, /memory-insights, /memory-consolidate
- Subtasks: @tintinweb/pi-subagents
```

---

## 10. Package Scripts yang Perlu Ditambah

Update `package.json`:

```json
{
  "scripts": {
    "smoke": "node test/extension-runtime-smoke.cjs",
    "eval:snapshot": "node test/verification-snapshot-eval.cjs",
    "test:policy": "node test/policy-loader.test.cjs",
    "test:project": "node test/project-detector.test.cjs",
    "test:command": "node test/command-risk-classifier.test.cjs",
    "test:state": "node test/task-state-machine.test.cjs",
    "test:memory": "node test/memory-to-rule.test.cjs",
    "test:all": "npm run smoke && npm run eval:snapshot && npm run test:policy && npm run test:project && npm run test:command && npm run test:state && npm run test:memory"
  }
}
```

---

## 11. Dokumentasi yang Harus Diupdate

### 11.1 `README.md`

Update:

- versi install ke tag terbaru setelah release baru
- jelaskan core harness generic
- jelaskan policy system
- jelaskan memory-to-rule promotion
- jelaskan profiles
- jelaskan extension advisor

Contoh:

```md
## Install
pi install git:https://github.com/adi805/pi-minimax-pack@v0.4.0
```

### 11.2 `docs/INSTALLATION.md`

Ganti semua tag lama `v0.2.20`, `v0.2.21`, `v0.2.25` menjadi versi rilis yang benar.

### 11.3 `docs/HOW_IT_WORKS.md`

Tambahkan flow baru:

```text
input
  → reset state
before_agent_start
  → inject global contract
  → detect project
  → load policy
  → route skills
  → inject installed resource hints
tool_call
  → command risk classify
  → policy gate
  → task drift gate
  → existing safety gates
tool_execution_end
  → track ops
  → artifact observation
message_end
  → status report
  → auto-grind
  → memory-to-rule candidate prompt if correction detected
```

### 11.4 `docs/AI_AGENT_GUIDE.md`

Ubah framing supaya tidak membuat agent takut mengedit repo owner.

Ganti dari nuansa:

```text
DO NOT edit global-contract.ts
```

menjadi:

```text
global-contract.ts may be edited, but only with binary-safe write or a verified patch process. Do not use naive write/edit tools that corrupt escape sequences.
```

Bahasa yang disarankan:

```md
## Critical: Safe Editing Rules for global-contract.ts

This repository is owner-controlled; agents may modify `extensions/global-contract.ts` when required.

However, this file contains string literals with escape sequences. Past naive `write`/`edit` operations corrupted `\n` sequences by converting them into literal newlines.

Therefore, use a binary-safe patch/write process and verify bytes after editing.
```

### 11.5 Docs baru

Buat:

```text
docs/POLICY_SCHEMA.md
docs/PROFILES.md
docs/MEMORY_TO_RULE.md
docs/EXTENSION_USAGE_GUIDE.md
docs/RELEASE_WORKFLOW.md
```

---

## 12. Test Cases Wajib

### 12.1 Project detector tests

1. Folder dengan `package.json` → node.
2. Folder dengan `go.mod` → go.
3. Folder dengan `go.mod + wails.json` → go + wails.
4. Folder dengan `Cargo.toml + src-tauri/tauri.conf.json` → rust + tauri.
5. Folder kosong → generic.

### 12.2 Command classifier tests

1. `git status` → safe_read.
2. `npm install` → install.
3. `go build ./...` → build.
4. `rm -rf dist` → destructive.
5. `git push origin main` → deploy.
6. `psql -c "drop table users"` → database.
7. unknown command → unknown.

### 12.3 Policy enforcement tests

1. Wails profile blocks `go build`.
2. Node project allows `npm run build` with preflight.
3. Deploy command blocked unless explicit user request.
4. Destructive command blocked without approval.
5. Unknown command asks.

### 12.4 Drift detector tests

1. Current task `bug-diagnose`, proposed `setup CI` → block.
2. Current task `installer-debug`, proposed `port backend` → block.
3. Current task `feature-implement`, proposed `write tests` → allow.

### 12.5 Memory-to-rule tests

1. User correction detected.
2. Candidate rule created.
3. Candidate not auto-promoted unless configured.
4. Approved candidate written to `.pi/minimax-policy.json`.
5. New rule enforced on next tool call.

### 12.6 Artifact validator tests

1. Output directory empty → block.
2. Output file timestamp older than command start → fail.
3. Copied artifact hash mismatch → block.
4. Installer source artifact differs from build artifact → block.

---

## 13. Implementation Phases

### Phase 0 — Baseline

Agent harus menjalankan:

```bash
git status
node -v
npm -v
npm run smoke
npm run eval:snapshot
```

Output:

```text
Baseline pass/fail
Current version
Files touched: none
```

### Phase 1 — Docs and Version Cleanup

1. Sinkronkan README dan INSTALLATION tag.
2. Tambahkan docs baru skeleton.
3. Ubah AI_AGENT_GUIDE framing: boleh edit, tapi binary-safe.
4. Tidak ubah runtime behavior dulu.

### Phase 2 — Internal Types + Project Detector

1. Tambah type internal.
2. Tambah `detectProject`.
3. Tambah tests.
4. Pastikan smoke tetap pass.

### Phase 3 — Command Classifier

1. Tambah classifier.
2. Tambah tests.
3. Belum enforce keras kecuali log/warn.

### Phase 4 — Policy Loader

1. Tambah loader layered.
2. Tambah schema docs.
3. Tambah tests.
4. Default behavior harus backward-compatible.

### Phase 5 — Tool Call Enforcement

1. Integrasikan classifier + policy di `tool_call`.
2. Block command yang jelas berbahaya.
3. Require approval untuk destructive/deploy/database.
4. Tambahkan status report blocked reason.

### Phase 6 — Task State + Drift Detector

1. Simpan current task category di persistent/in-memory state.
2. Deteksi drift.
3. Block new workstream tanpa approval.

### Phase 7 — Memory-to-Rule Promotion

1. Deteksi correction patterns.
2. Buat candidate rule.
3. Minta approval untuk promote.
4. Tulis policy.
5. Enforce.

### Phase 8 — Artifact Validator

1. Tambah artifact observation.
2. Hash validator.
3. Non-empty output validator.
4. Timestamp validator.

### Phase 9 — Release

1. Run `npm run test:all`.
2. Update docs.
3. Commit.
4. Tag `v0.4.0` atau versi berikutnya.
5. Push tag.
6. Jalankan `pi-minimax-update v0.4.0`.
7. Restart Pi.

---

## 14. Prompt Utama untuk Agent yang Akan Modifikasi Repo

Copy prompt ini ke Pi agent:

```text
/preflight

Project:
D:\path\to\pi-minimax-pack

Mode:
OWNER MODE. Repo ini milik user. Kamu boleh mengubah file mana pun, termasuk extensions/global-contract.ts, jika memang diperlukan.

Namun untuk extensions/global-contract.ts:
- jangan pakai naive write/edit yang merusak escape sequence
- gunakan binary-safe patch/write
- verifikasi bytes setelah perubahan
- pastikan tidak ada CRLF
- pastikan escape sequence \\n tetap benar

Tujuan:
Upgrade pi-minimax-pack dari verification harness menjadi generic policy-driven agent harness.

Jangan hardcode Inventory/Wails di core.
Wails hanya boleh menjadi profile/policy, bukan global behavior.

Tugas tahap ini:
1. Baca README.md
2. Baca package.json
3. Baca extensions/global-contract.ts
4. Baca docs/AGENTS.md
5. Baca docs/HOW_IT_WORKS.md
6. Baca docs/AI_AGENT_GUIDE.md
7. Baca docs/INSTALLATION.md
8. Baca folder skills
9. Baca folder test
10. Buat implementation plan berdasarkan dokumen upgrade v2

Jangan coding dulu sebelum laporan preflight.

Output wajib:
A. Repo summary
B. Current features
C. Current risks
D. Files likely to change
E. Safe edit method for global-contract.ts
F. Implementation phases
G. Tests to run
H. One next step only
```

---

## 15. Prompt Implementasi Phase 1

```text
/risk-fix

Gunakan upgrade plan v2.

Tugas Phase 1:
- sinkronkan README.md dan docs/INSTALLATION.md dengan version strategy terbaru
- update docs/AI_AGENT_GUIDE.md agar jelas: global-contract.ts boleh diedit karena repo owner, tapi harus binary-safe
- buat docs skeleton:
  - docs/POLICY_SCHEMA.md
  - docs/PROFILES.md
  - docs/MEMORY_TO_RULE.md
  - docs/EXTENSION_USAGE_GUIDE.md
  - docs/RELEASE_WORKFLOW.md

Jangan ubah runtime logic dulu.
Jangan edit global-contract.ts di phase ini kecuali benar-benar perlu.

Setelah perubahan:
- baca ulang file yang diubah
- jalankan npm run smoke
- jalankan npm run eval:snapshot

Output:
A. Files changed
B. Verification command results
C. Any unverified item
D. One next step only
```

---

## 16. Prompt Implementasi Core Runtime

```text
/risk-fix

Gunakan upgrade plan v2.

Tugas Phase 2-5:
Tambahkan secara bertahap:
1. Project Detector
2. Command Risk Classifier
3. Layered Policy Loader
4. Tool Call Enforcement

Owner mode: boleh edit global-contract.ts.
Untuk global-contract.ts gunakan binary-safe write/patch dan verifikasi bytes.

Jangan hardcode Inventory/Wails.
Wails hanya profile.

Wajib backward-compatible:
- existing auto-grind tetap jalan
- status report tetap jalan
- read-before-edit gate tetap jalan
- no shell redirection gate tetap jalan

Tests:
- npm run smoke
- npm run eval:snapshot
- tests baru untuk detector/classifier/policy

Output:
A. Design summary
B. Files changed
C. Tests added
D. Tests result
E. Risk
F. Rollback command
G. One next step only
```

---

## 17. Prompt Memory-to-Rule

```text
/feature-design

Desain memory-to-rule promotion untuk pi-minimax-pack.

Target:
Saat user memberi correction seperti:
"No, never use plain go build for Wails"

Harness harus:
1. mendeteksi correction
2. membuat candidate rule
3. menanyakan approval
4. jika approved, menulis ke .pi/minimax-policy.json
5. enforce pada tool_call berikutnya

Jangan coding dulu.
Output:
A. Detection patterns
B. Candidate rule schema
C. Approval flow
D. Policy write flow
E. Enforcement flow
F. Tests
G. Minimal implementation plan
```

---

## 18. Prompt Review Setelah Agent Mengubah Repo

```text
/review-arch

Review perubahan pi-minimax-pack.

Fokus:
1. Apakah core tetap generic?
2. Apakah ada hardcode Inventory/Wails di core?
3. Apakah global-contract.ts diedit dengan aman?
4. Apakah tests pass?
5. Apakah docs sinkron dengan package version?
6. Apakah policy loader punya fallback aman?
7. Apakah command blocking terlalu agresif?
8. Apakah installed extension advisor tidak menyarankan tool baru sembarangan?

Output:
A. Pass/fail summary
B. Blocking issues
C. Non-blocking issues
D. Suggested fixes
E. Release readiness
```

---

## 19. Stop Conditions untuk Agent

Agent wajib berhenti dan lapor jika:

1. `global-contract.ts` berubah tetapi byte verification gagal.
2. Escape sequence `\n` rusak.
3. Tests existing gagal.
4. Policy loader memblok command aman.
5. Agent hampir hardcode project tertentu ke core.
6. Agent mau install dependency baru tanpa alasan.
7. Agent mau setup CI sebelum local tests pass.
8. Agent mau refactor besar tanpa approval.
9. Output file kosong.
10. Task drift dari phase saat ini.

---

## 20. Release Checklist

```text
[ ] git status clean before starting
[ ] README version updated
[ ] INSTALLATION version updated
[ ] AI_AGENT_GUIDE owner-mode wording updated
[ ] POLICY_SCHEMA.md added
[ ] PROFILES.md added
[ ] MEMORY_TO_RULE.md added
[ ] EXTENSION_USAGE_GUIDE.md added
[ ] RELEASE_WORKFLOW.md added
[ ] project detector added
[ ] command classifier added
[ ] policy loader added
[ ] tool_call enforcement added
[ ] drift detector added
[ ] memory-to-rule candidate flow added
[ ] artifact validator added
[ ] npm run smoke pass
[ ] npm run eval:snapshot pass
[ ] npm run test:all pass
[ ] tag created
[ ] tag pushed
[ ] pi-minimax-update run
[ ] Pi restarted
[ ] startup shows package loaded
[ ] /preflight test passes
```

---

## 21. Kesimpulan Final

`pi-minimax-pack` saat ini sudah bagus sebagai:

```text
contract injector + auto verification + status report + simple safety gates
```

Tapi untuk membuat agent benar-benar lebih pintar dan tidak mengulang kesalahan, harus naik menjadi:

```text
policy-driven behavior governor
```

Kunci upgrade:

1. Project detector.
2. Layered policy loader.
3. Command risk classifier.
4. Task state machine.
5. Drift detector.
6. Memory-to-rule promotion.
7. Artifact validator.
8. Installed extension advisor.
9. Owner-safe editing workflow untuk `global-contract.ts`.

Dan koreksi terpenting:

```text
extensions/global-contract.ts boleh diedit.
Yang tidak boleh adalah mengeditnya dengan cara ceroboh yang merusak escape sequence.
```
