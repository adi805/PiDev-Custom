// ============================================================================
// Pi MiniMax Pack v3 — Utility Functions
// Design: Transfer Knowledge (Level 2-3)
// ============================================================================

import type { VerificationResult, PruningResult, LearningNote, SessionState } from './types';
import { findErrorPattern, generateRootCause } from './constants';

// ============================================================================
// Session State Management
// ============================================================================

const SESSION_STATE_KEY = 'minimax-v3-state';

export function getSessionState(): SessionState {
  // Note: In actual extension, this would use pi's state management
  // For now, we use a module-level cache
  const cached = (global as any)[SESSION_STATE_KEY];
  if (cached) return cached;
  
  const fresh: SessionState = {
    verificationHistory: [],
    pruningHistory: [],
    learningNotes: [],
    agentBehavior: {
      verificationAccepts: 0,
      verificationRejects: 0,
      contextEfficiencyScore: 0
    }
  };
  (global as any)[SESSION_STATE_KEY] = fresh;
  return fresh;
}

export function saveSessionState(state: SessionState): void {
  (global as any)[SESSION_STATE_KEY] = state;
}

// ============================================================================
// Verification Result Processing
// ============================================================================

export function createVerificationResult(
  command: string,
  output: string,
  exitCode: number,
  changedFiles: string[],
  duration: number
): VerificationResult {
  const isError = exitCode !== 0;
  const errorLines = output.split('\n').filter(line => 
    /error|Error|failed|Failed|warning|Warning/i.test(line)
  );
  
  const matchedPattern = isError ? findErrorPattern(output) : null;
  const rootCause = isError ? generateRootCause(output, matchedPattern) : 'Success';
  const hint = matchedPattern?.hint || (isError ? 'Review the error message and fix the issue.' : '');
  const suggestion = matchedPattern?.suggestion || (isError ? 'Check the error context and apply a targeted fix.' : '');
  
  return {
    success: !isError,
    command,
    output,
    exitCode,
    errorLines,
    rootCause,
    hint,
    suggestion,
    timestamp: Date.now(),
    changedFiles,
    duration
  };
}

// ============================================================================
// Verification Explanation Generator
// Transfer knowledge: explain WHY and HOW to fix
// ============================================================================

export function generateVerificationExplanation(result: VerificationResult): string {
  if (result.success) {
    return `✅ **Verification passed** (${result.command})
Duration: ${result.duration}ms
Files verified: ${result.changedFiles.join(', ') || 'none'}`;
  }

  // Format error for readability
  const errorSummary = result.errorLines.length > 0
    ? `\nError output:\n${result.errorLines.slice(0, 5).map(l => `  ${l}`).join('\n')}`
    : '';

  return `❌ **Verification failed** (${result.command})
${errorSummary}

**Root cause**: ${result.rootCause}

**Hint**: ${result.hint}

**Suggestion**: ${result.suggestion}

---
This is an opportunity to improve. The explanation above tells you:
1. What went wrong (root cause)
2. Why it failed (hint)  
3. How to fix it (suggestion)

Apply the fix based on the hint, then re-run the verification when ready.`;
}

// ============================================================================
// Context Pruning Analysis
// ============================================================================

export function analyzePruningCandidates(
  messages: Array<{ role: string; content: Array<{ type: string; text?: string }> }>,
  contextBudgetPercent: number
): {
  candidates: Array<{ index: number; reason: string; category: string }>;
  kept: number;
  prunedCount: number;
  tokenSavings: number;
} {
  // Simple heuristic: if messages exceed budget, prune older ones
  const messageCount = messages.length;
  const targetCount = Math.floor(messageCount * (contextBudgetPercent / 100));
  
  // Categorize messages
  const toolCalls: number[] = [];
  const toolResults: number[] = [];
  const userMessages: number[] = [];
  const assistantMessages: number[] = [];
  
  messages.forEach((msg, idx) => {
    if (msg.role === 'tool') {
      toolResults.push(idx);
    } else if (msg.role === 'tool-call') {
      toolCalls.push(idx);
    } else if (msg.role === 'user') {
      userMessages.push(idx);
    } else if (msg.role === 'assistant') {
      assistantMessages.push(idx);
    }
  });

  // Prune older tool calls and results, keep recent
  const candidates: Array<{ index: number; reason: string; category: string }> = [];
  
  // Keep last 5 tool calls/results
  const keepToolCount = 5;
  const pruneToolCalls = toolCalls.slice(0, Math.max(0, toolCalls.length - keepToolCount));
  const pruneToolResults = toolResults.slice(0, Math.max(0, toolResults.length - keepToolCount));
  
  for (const idx of pruneToolCalls) {
    const text = messages[idx].content[0]?.text || '';
    const isLong = text.length > 500;
    candidates.push({
      index: idx,
      reason: isLong 
        ? 'Long tool call no longer needed for current context' 
        : 'Old tool call not relevant to current task',
      category: 'old_tool_calls'
    });
  }
  
  for (const idx of pruneToolResults) {
    const text = messages[idx].content[0]?.text || '';
    const isLong = text.length > 1000;
    candidates.push({
      index: idx,
      reason: isLong
        ? 'Verbose tool output can be summarized'
        : 'Old tool result no longer needed',
      category: 'redundant_results'
    });
  }

  const prunedCount = candidates.length;
  const kept = messageCount - prunedCount;
  
  // Estimate token savings
  let tokenSavings = 0;
  for (const c of candidates) {
    const text = messages[c.index].content[0]?.text || '';
    tokenSavings += Math.ceil(text.length / 4);
  }

  return { candidates, kept, prunedCount, tokenSavings };
}

// ============================================================================
// Pruning Summary Generator
// Transfer knowledge: explain WHAT was lost and WHY
// ============================================================================

export function generatePruningSummary(
  result: { candidates: Array<{ reason: string; category: string }>; prunedCount: number; tokenSavings: number }
): PruningResult {
  // Group by category
  const byCategory: Record<string, number> = {};
  const byReason: Record<string, string> = {};
  
  for (const c of result.candidates) {
    byCategory[c.category] = (byCategory[c.category] || 0) + 1;
    byReason[c.category] = c.reason;
  }
  
  const categories = Object.keys(byCategory);
  const reasons = byReason;
  
  // Generate key points that were lost
  const lostKeyPoints = categories.map(cat => {
    const count = byCategory[cat];
    const reason = byReason[cat];
    return `${count} ${cat.replace('_', ' ')} removed: ${reason}`;
  });
  
  const summary = `Context pruned: ${result.prunedCount} messages removed
Categories: ${categories.join(', ')}
Approximate token savings: ~${result.tokenSavings} tokens

${lostKeyPoints.join('\n')}

Key context is preserved. You can ask me to clarify any pruned information if needed.`;

  return {
    prunedCount: result.prunedCount,
    categories,
    reasons,
    lostKeyPoints,
    summary,
    tokenSavings: result.tokenSavings,
    timestamp: Date.now()
  };
}

// ============================================================================
// Learning Note Management
// ============================================================================

export function createLearningNote(
  category: LearningNote['category'],
  pattern: string,
  explanation: string,
  example?: string,
  agentVisible = true
): LearningNote {
  return {
    id: crypto.randomUUID ? crypto.randomUUID() : `ln_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    timestamp: Date.now(),
    category,
    pattern,
    explanation,
    example,
    agentVisible,
    metadata: {
      occurrenceCount: 1,
      successfulFixes: [],
      lastSeen: Date.now()
    }
  };
}

export function generateLearningSummary(notes: LearningNote[]): string {
  if (notes.length === 0) return '';
  
  const byCategory: Record<string, LearningNote[]> = {};
  for (const note of notes) {
    if (!byCategory[note.category]) {
      byCategory[note.category] = [];
    }
    byCategory[note.category].push(note);
  }
  
  let summary = '\n📚 **Learning Notes**\n\n';
  
  for (const [category, catNotes] of Object.entries(byCategory)) {
    summary += `**${category}** (${catNotes.length} notes):\n`;
    for (const note of catNotes.slice(-3)) {  // Show last 3 per category
      summary += `- ${note.pattern}: ${note.explanation}\n`;
    }
    summary += '\n';
  }
  
  return summary;
}

// ============================================================================
// Message Formatting Helpers
// ============================================================================

export function formatVerificationReminder(): string {
  return `📋 **Verification reminder**
After making code changes, run verification commands to confirm the code works.
If verification fails, I will explain the root cause, hint at the pattern, and suggest how to fix it.`;
}

export function formatContextTip(tokenUsage: number, budget: number): string {
  const percent = Math.round((tokenUsage / budget) * 100);
  return `💡 **Context efficiency tip**
Current context usage: ~${percent}% of budget.
Keep messages focused and concise for optimal performance.`;
}

// ============================================================================
// Pattern Matching Utilities
// ============================================================================

export function extractErrorLocation(errorOutput: string): { line?: number; file?: string } | null {
  // Match patterns like "at line 42" or "in file.ts:10"
  const lineMatch = errorOutput.match(/line\s+(\d+)/i);
  const fileMatch = errorOutput.match(/([^\s]+\.(ts|js|tsx|jsx|py|rs)):\d+/);
  
  if (lineMatch || fileMatch) {
    return {
      line: lineMatch ? parseInt(lineMatch[1], 10) : undefined,
      file: fileMatch ? fileMatch[1] : undefined
    };
  }
  return null;
}

export function extractTestExpectation(errorOutput: string): { expected?: string; received?: string } | null {
  const expectedMatch = errorOutput.match(/Expected[:\s]+"?([^"\n]+)"?/i);
  const receivedMatch = errorOutput.match(/Received[:\s]+"?([^"\n]+)"?/i);
  
  if (expectedMatch || receivedMatch) {
    return {
      expected: expectedMatch ? expectedMatch[1].trim() : undefined,
      received: receivedMatch ? receivedMatch[1].trim() : undefined
    };
  }
  return null;
}

// ============================================================================
// Debounce Helper
// ============================================================================

export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delayMs: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => {
      fn(...args);
      timeout = null;
    }, delayMs);
  };
}

// ============================================================================
// File Path Utilities
// ============================================================================

export function extractChangedFiles(commandOutput: string): string[] {
  // Parse common file patterns from output
  const patterns = [
    /\b([^\s]+\.ts)\b/g,
    /\b([^\s]+\.tsx)\b/g,
    /\b([^\s]+\.js)\b/g,
    /\b([^\s]+\.jsx)\b/g,
    /\b([^\s]+\.py)\b/g,
    /\b([^\s]+\.rs)\b/g,
  ];
  
  const files = new Set<string>();
  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(commandOutput)) !== null) {
      files.add(match[1]);
    }
  }
  
  return Array.from(files);
}

export function isTestCommand(command: string): boolean {
  return /\b(test|jest|vitest|pytest|ruby|npm test|npx jest|go test)\b/i.test(command);
}

export function isBuildCommand(command: string): boolean {
  return /\b(build|compile|tsc|esbuild|vite|webpack|rollup|npm run build)\b/i.test(command);
}

export function isLintCommand(command: string): boolean {
  return /\b(lint|eslint|prettier|ruff|pylint|clippy)\b/i.test(command);
}