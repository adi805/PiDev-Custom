# Pi MiniMax Pack v0.3.0

> **Design Philosophy**: Transfer Knowledge (Level 2-3)

MiniMax engineering pack for [pi.dev](https://pi.dev) — makes AI coding agent smarter, not dependent.

## Install

```bash
pi install git:https://github.com/adi805/pi-minimax-pack@v0.3.0
```

## What's New in v0.3.0

### A. Verification v2 — Explain, Not Block

When tests/build/lint fail:

- **Root cause**: What's actually wrong
- **Hint**: Why it fails (pattern explanation)
- **Suggestion**: How to fix it

**Example**:
```
❌ Test failed at src/utils.test.ts:42

Root cause: Expected "foo" but got "bar" — type mismatch
Hint: Check mock data structure vs actual return value
Suggestion: Verify mock returns same shape as production function
```

### B. Context Intelligence — Transparent Pruning

When context exceeds budget:

- **What was pruned**: Categories and counts
- **Why**: Reason for each category
- **What was lost**: Key points preserved
- **What remains**: Essential context

**Example**:
```
📋 Context pruned: 12 messages (~2000 tokens)
Why: Old tool calls, redundant results
Key info preserved:
  • Created API endpoint with auth
  • Added error handling middleware
  • Wrote unit tests
```

### C. Learning System — Patterns, Not Directives

Accumulated notes visible to agent:

```
📚 Recent Learning:
- type_undefined: Add null checks
- test_expected: Verify implementation matches test
```

---

## Design Philosophy

**Transfer Knowledge (Level 2-3)**:

- ✅ Automation guides, agent learns
- ✅ Explanations over blocks
- ✅ Transparency over magic
- ❌ Not crutches that replace judgment

**Goal**: Agent becomes MORE capable independently, NOT more dependent.

---

## Features

| Feature | Behavior | Agent Learns |
|---------|----------|-------------|
| Verification | Explain failures | Error patterns |
| Context | Transparent pruning | Context management |
| Learning | Visible notes | Pattern recognition |

---

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `minimax-verification` | `explain` | `explain` / `block` / `silent` |
| `minimax-context-pruning` | `transparent` | `transparent` / `silent` / `aggressive` |
| `minimax-learning` | `true` | Enable learning notes |
| `minimax-context-budget` | `80` | Context budget threshold (%) |

---

## Tools

- `run_verification` — Run verification with detailed failure explanations
- `context_summary` — Show context usage and efficiency metrics

---

## Architecture

```
extensions/
├── index.ts           # Entry point
├── verification.ts    # Feature A: Explain failures
├── context.ts         # Feature B: Transparent pruning
└── shared/
    ├── types.ts       # TypeScript types
    ├── constants.ts   # Error patterns
    └── utils.ts       # Helpers
```

---

## For v0.4.0

- C: Output enforcement (reminders)
- D: Pattern detection from notes
- Cross-session learning (optional)

---

## License

MIT