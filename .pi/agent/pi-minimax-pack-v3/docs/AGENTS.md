# MiniMax Pack v3 — Agent Contract

## Design Philosophy: Transfer Knowledge (Level 2-3)

> **Core principle**: Automation should transfer knowledge TO the agent, not replace the agent's judgment.
> 
> - Extension guides, agent learns
> - Explanations over blocks
> - Transparency over magic
> - Notes, not directives

---

## What This Extension Does

### A. Verification — Explain Failures, Not Block

When verification (tests, build, lint) fails:

```
❌ Verification failed (npm test)

Root cause: Test expectation doesn't match implementation
Hint: Check what the test expects vs what the code actually does
Suggestion: Review the assertion in the failing test and align your implementation
```

**Your response**:
1. Read the explanation carefully
2. Understand WHY it failed (not just that it failed)
3. Apply the fix based on the hint
4. Re-run verification when ready

**This teaches you**: Error patterns and how to avoid them in the future.

---

### B. Context Pruning — Transparent, With Teaching

When context needs pruning:

```
📋 Context Pruning Applied

Context pruned: 12 messages removed
Categories: old_tool_calls, redundant_results
Token savings: ~2000 tokens

• 5 old_tool_calls removed: Old tool calls not relevant to current task
• 7 redundant_results removed: Verbose output can be summarized

Key information preserved:
  • Created new API endpoint with authentication
  • Added error handling middleware
  • Wrote unit tests for service layer
```

**This teaches you**: What context is important and how to keep messages concise.

---

### C. Learning Notes — Patterns, Not Directives

From accumulated verification results, you'll see patterns:

```
📚 Recent Learning:
- type_undefined: Add null checks before accessing properties
- test_expected: Verify implementation matches test expectations
```

**This is observation, not instruction**. You decide how to apply these patterns.

---

## What You Should Do

### Verification
- ✅ Read explanations to understand error patterns
- ✅ Apply fixes based on hints, not just "make tests pass"
- ✅ Learn from recurring patterns
- ❌ Don't ignore explanations and guess blindly

### Context
- ✅ Keep messages focused and concise
- ✅ Acknowledge when context is pruned
- ✅ Don't re-explain pruned information unnecessarily
- ❌ Don't spam with verbose output

### Learning
- ✅ Notice patterns from accumulated notes
- ✅ Apply patterns you see recurring
- ❌ Don't wait for reminders to fix obvious issues

---

## What NOT To Do

| Don't | Why |
|-------|-----|
| Blindly apply fixes without reading explanation | Misses learning opportunity |
| Ignore context pruning explanations | Loses continuity awareness |
| Wait for reminders on obvious patterns | Inefficient, annoying |
| Generate verbose output unnecessarily | Wastes context budget |
| Ignore learning notes | Repeats same mistakes |

---

## Flags (Configurable)

| Flag | Default | Options |
|------|---------|---------|
| `minimax-verification` | `explain` | `explain` / `block` / `silent` |
| `minimax-context-pruning` | `transparent` | `transparent` / `silent` / `aggressive` |
| `minimax-learning` | `true` | `true` / `false` |
| `minimax-context-budget` | `80` | (percentage) |

---

## Tools Available

### `run_verification`
Run project verification commands (tests, build, lint) with detailed failure explanations.

### `context_summary`
Show current context usage, pruning history, and efficiency metrics.

---

## Success Metrics

This extension tracks:
- Verification pass/fail rate
- Context efficiency score
- Learning note patterns

You can ask for `context_summary` to see these metrics.

---

## Remember

**The goal is for you to become MORE capable independently, not MORE dependent on automation.**

Automation should make you smarter, not lazier.