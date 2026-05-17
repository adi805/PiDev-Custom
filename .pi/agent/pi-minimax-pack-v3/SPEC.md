# Pi MiniMax Pack v0.3.0 — SPEC

## Design Philosophy: Transfer Knowledge (Level 2-3)

> Automation should transfer knowledge TO the agent, not replace the agent's judgment.
> 
> - Extension guides, agent learns
> - Explanations over blocks
> - Transparency over magic
> - Notes, not directives

---

## Goal

Build AI coding agent extension yang bikin agent **lebih capable independently**, bukan lebih dependent on automation.

---

## Features (v0.3.0)

### A. Verification v2 — Explain, Not Block

**Current behavior**: Extension auto-run tests, block if fail.

**New behavior**: 
- Run verification commands
- If fail: inject message with:
  - **Root cause**: What's actually wrong
  - **Hint**: Pattern explanation why this fails
  - **Suggestion**: Concrete fix approach
- Agent learns from failure, doesn't just react

**Example output**:
```
Test failed at src/utils.test.ts:42
Root cause: Expected "foo" but got "bar" — type mismatch in mock data
Hint: Mocks need to match the actual data structure being returned
Suggestion: Check if the mock returns same shape as production function
```

### B. Context Intelligence — Transparent Pruning

**Current behavior**: Silent compaction when context exceeds budget.

**New behavior**:
- Monitor context usage via `ctx.getContextUsage()`
- Before pruning: identify what's about to be lost
- After pruning: inject summary explaining:
  - **What was pruned**: categories and count
  - **Why**: reason for each category
  - **What was lost**: key points from pruned content
- Agent learns context management, doesn't lose continuity silently

**Example output**:
```
Context pruned: 12 messages removed (4 tool calls, 5 results, 3 user prompts)
Why: Tool-heavy section not relevant to current task, early context exceeded budget
Key points lost: [Original spec mentioned X, which is no longer in scope]
```

---

## Architecture

### File Structure
```
pi-minimax-pack-v3/
├── extensions/
│   ├── index.ts              # Entry point, registers all extensions
│   ├── verification.ts       # Feature A: Explain failures
│   ├── context.ts            # Feature B: Transparent pruning
│   └── shared/
│       ├── types.ts          # Shared TypeScript types
│       ├── utils.ts          # Helpers
│       └── constants.ts      # Config values
├── skills/
│   └── (existing skills, migrate later)
├── docs/
│   └── AGENTS.md             # Updated contract
└── package.json
```

### Core Types

```typescript
interface VerificationResult {
  success: boolean;
  command: string;
  output: string;
  errorLines: string[];
  rootCause: string;
  hint: string;
  suggestion: string;
}

interface PruningResult {
  prunedCount: number;
  categories: string[];
  reasons: Record<string, string>;
  lostKeyPoints: string[];
  summary: string;
}

interface LearningNote {
  id: string;
  timestamp: number;
  category: 'verification' | 'context' | 'format' | 'pattern';
  pattern: string;
  explanation: string;
  example?: string;
  agentVisible: boolean;
}
```

---

## Verification Flow (Feature A)

```
1. Agent writes code
2. message_end fires → detect changed files
3. Run verification commands
4. If pass → record success, continue
5. If fail → 
   a. Parse error output
   b. Identify root cause (pattern matching)
   c. Generate hint based on error type
   d. Generate suggestion based on common fixes
   e. Inject message to agent (NOT block)
   f. Record as learning note (both visible + metadata)
6. Agent reads message, fixes based on explanation
7. Re-run verification (optional, controlled by agent)
```

### Error Pattern Recognition

```typescript
const ERROR_PATTERNS = {
  syntax: {
    pattern: /SyntaxError|Unexpected token/,
    hint: 'Check for missing brackets, semicolons, or typos',
    suggestion: 'Review the line mentioned in the error + surrounding context'
  },
  type: {
    pattern: /TypeError|Cannot read property/,
    hint: 'Variable may be undefined or wrong type',
    suggestion: 'Add null checks or verify type assumptions'
  },
  import: {
    pattern: /Cannot find module|Module not found/,
    hint: 'Module path or name may be incorrect',
    suggestion: 'Check package.json dependencies and import paths'
  },
  test: {
    pattern: /Expected|Received/,
    hint: 'Test expectation may not match implementation',
    suggestion: 'Review what the test expects vs what the code does'
  },
  // ... more patterns
};
```

---

## Context Flow (Feature B)

```
1. Before each LLM call (context event)
2. Check ctx.getContextUsage()
3. If approaching limit (e.g., >80%):
   a. Analyze messages for pruning candidates
   b. Categorize: old tool calls, redundant results, outdated context
   c. Identify key points that would be lost
   d. Prune with metadata
   e. Inject summary to agent explaining what happened
4. Agent sees context trimmed but understands why
5. Learning: agent learns to keep context efficient
```

---

## Learning System (Feature D — v0.4.0)

For v0.3.0, we prep the infrastructure:

```typescript
class LearningEngine {
  notes: LearningNote[] = [];
  
  record(note: Omit<LearningNote, 'id'>) {
    const learningNote = {
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      ...note,
    };
    
    // Store in session (visible to agent)
    this.storeInSession(learningNote);
    
    // Store metadata (extension-only, for patterns)
    this.storeMetadata(learningNote);
    
    return learningNote;
  }
  
  detectPattern(newEvent: Event): LearningNote | null {
    // Look for recurring patterns in metadata
    // If pattern repeats, generate general learning note
  }
}
```

---

## State Management

### Session State (visible to agent)
```typescript
interface SessionState {
  verificationHistory: VerificationResult[];
  pruningHistory: PruningResult[];
  learningNotes: LearningNote[];  // agent can read these
}
```

### Metadata State (extension-only)
```typescript
interface MetaState {
  patterns: Record<string, number>;  // pattern -> occurrence count
  fixes: Record<string, string[]>;   // error pattern -> successful fixes
  agentBehavior: Record<string, number>;  // behavior tracking
}
```

---

## Extension Events Used

| Feature | Event | Purpose |
|---------|-------|---------|
| A | `tool_execution_end` | Track verification commands |
| A | `message_end` | Detect when to run verification |
| A | `before_agent_start` | Inject explanation if verification failed |
| B | `context` | Monitor and prune if needed |
| B | `before_agent_start` | Inject pruning summary |
| D | `tool_result` | Record patterns for learning |
| D | `session_end` | Persist metadata |

---

## Flags (configurable)

```typescript
pi.registerFlag("minimax-verification", {
  type: "string",
  default: "explain",  // "explain" | "block" | "silent"
  description: "Verification behavior"
});

pi.registerFlag("minimax-context-pruning", {
  type: "string", 
  default: "transparent",  // "transparent" | "silent" | "aggressive"
  description: "Context pruning behavior"
});

pi.registerFlag("minimax-learning", {
  type: "boolean",
  default: true,
  description: "Enable learning notes to agent"
});
```

---

## Non-Goals (for v0.3.0)

- No automatic retry loops (agent decides to retry)
- No forced format enforcement (reminders only)
- No cross-session memory (session-scoped only)
- No UI changes (all transparent to user)

---

## Success Criteria (v0.3.0)

1. ✅ Verification shows root cause + hint + suggestion, not just fail/pass
2. ✅ Context pruning explains what was lost and why
3. ✅ Agent produces better code (fewer repeated mistakes)
4. ✅ Learning notes visible to agent, not just hidden metadata
5. ✅ Extension is documented and maintainable

---

## Future (v0.4.0)

- C: Output enforcement (reminders before agent ends)
- D: Pattern detection from accumulated notes
- Cross-session learning (optional)
- Custom rendering for verification results