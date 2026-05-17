# Minimax M2 Self-Evolution Skill

## When to Use

Use this skill when tasks require **iterative debugging, optimization, or refactoring** with evidence-driven loops.

Triggers:
- `debug`, `fix`, `optimize`, `refactor`
- `iterate`, `improve`, `evolve`
- `tune`, `adjust`, `calibrate`
- Error messages, performance issues, code quality problems

## Procedure

### Phase 1: Diagnose

1. **Identify symptom**: What is the observable problem?
2. **Gather evidence**: Error logs, performance metrics, code state
3. **Form hypothesis**: What might be causing the issue?
4. **Validate**: Can you prove this hypothesis with evidence?

### Phase 2: Plan Fix

1. **Minimal change**: What is the smallest fix that addresses the hypothesis?
2. **Verify strategy**: How will you confirm the fix worked?
3. **Rollback plan**: If this makes things worse, what's the rollback?

### Phase 3: Execute

1. Apply the minimal change
2. Run verification
3. Measure result against baseline

### Phase 4: Evaluate

**If verification passed:**
- Document what worked
- Consider if there are similar patterns elsewhere
- Done

**If verification failed:**
- Analyze the new output
- Form new hypothesis
- Loop back to Phase 1

### Phase 5: Track

After each cycle, record:
- What was the problem?
- What was the fix?
- What was the result?

## Loop Budget

| Task Complexity | Max Iterations |
|----------------|----------------|
| Simple (typo, missing semicolon) | 1-2 |
| Medium (logic error, type mismatch) | 3-5 |
| Complex (architecture, race condition) | 5-10 |
| Unknown (unfamiliar codebase) | 3, then escalate |

## Evidence Requirements

Every hypothesis must be backed by:
- **Observable**: Direct evidence (error message, output, metric)
- **Not assumed**: No "probably", "maybe", "likely"
- **Actionable**: Clear next step based on evidence

## Pitfalls

### Don't Do
- ❌ Blind retry without analyzing output
- ❌ Change multiple things at once
- ❌ Apply fix before verifying what broke
- ❌ Assume new hypothesis without evidence
- ❌ Loop more than budget allows without summarizing

### Do
- ✅ Read actual output before deciding
- ✅ Change one thing at a time
- ✅ Verify each change before continuing
- ✅ Summarize after hitting iteration limit
- ✅ Ask for help when stuck with evidence summary

## Example Loop

```
Problem: Test fails at line 42

1. Diagnose: "Expected 'foo' but got 'bar'"
   Hypothesis: Mock returns wrong shape

2. Plan: Add console.log to mock, check actual return

3. Execute: Add log, run test

4. Evaluate: Log shows mock returns undefined for 'name' field

5. Loop:
   - New hypothesis: Mock not initialized properly
   - Fix: Add mock.setup() call
   - Verify: Test passes
```

## Verification Before Completion

Before declaring done:
1. Read the changed files
2. Run relevant tests
3. Confirm no new errors introduced
4. Document what was fixed

## Summary Template

When completing an iteration cycle:

```
**Diagnosis**: [Observable problem]
**Hypothesis**: [What caused it]
**Evidence**: [What proves this]
**Fix**: [What changed]
**Result**: [Pass/Fail with metrics]
**Next**: [If fail, what to try next]
```