// ============================================================================
// Pi MiniMax Pack v3 — Shared Types
// Design: Transfer Knowledge (Level 2-3)
// ============================================================================

// Verification result structure
export interface VerificationResult {
  success: boolean;
  command: string;
  output: string;
  exitCode: number;
  errorLines: string[];
  // Transfer knowledge fields
  rootCause: string;
  hint: string;
  suggestion: string;
  // Metadata
  timestamp: number;
  changedFiles: string[];
  duration: number; // ms
}

// Context pruning result
export interface PruningResult {
  prunedCount: number;
  categories: string[];
  reasons: Record<string, string>;
  lostKeyPoints: string[];
  summary: string;
  tokenSavings: number;
  timestamp: number;
}

// Learning note structure
export interface LearningNote {
  id: string;
  timestamp: number;
  category: 'verification' | 'context' | 'format' | 'pattern';
  pattern: string;       // What pattern was detected
  explanation: string;  // Why it's important
  hint?: string;       // Hint for verification errors
  example?: string;      // Concrete example
  agentVisible: boolean; // Show to agent in session?
  metadata: {
    occurrenceCount: number;
    successfulFixes: string[];
    lastSeen: number;
  };
}

// Error pattern definition
export interface ErrorPattern {
  name: string;
  patterns: RegExp[];
  category: 'syntax' | 'type' | 'import' | 'test' | 'runtime' | 'network' | 'permission';
  hint: string;
  suggestion: string;
}

// Context category for pruning decisions
export interface ContextCategory {
  name: string;
  reason: string;
  keepRecent: number;  // Keep this many recent of this type
}

// Session state (visible to agent)
export interface SessionState {
  verificationHistory: VerificationResult[];
  pruningHistory: PruningResult[];
  learningNotes: LearningNote[];
  agentBehavior: {
    verificationAccepts: number;
    verificationRejects: number;
    contextEfficiencyScore: number;
  };
}

// Metadata state (extension-only)
export interface MetaState {
  patterns: Record<string, {
    count: number;
    firstSeen: number;
    lastSeen: number;
  }>;
  fixes: Record<string, string[]>;  // error -> successful fix patterns
  projectBehavior: Record<string, number>;
}

// Extension flags
export interface MiniMaxFlags {
  'minimax-verification': 'explain' | 'block' | 'silent';
  'minimax-context-pruning': 'transparent' | 'silent' | 'aggressive';
  'minimax-learning': boolean;
  'minimax-context-budget': number;  // percentage (e.g., 80)
  'minimax-pruning-keep-recent': number;  // messages to keep
}

// Event types for type-safe handlers
export interface ToolExecutionEvent {
  toolCallId: string;
  toolName: string;
  args: Record<string, unknown>;
  result?: unknown;
  isError?: boolean;
  duration?: number;
}

export interface ContextEvent {
  messages: Array<{
    role: string;
    content: Array<{ type: string; text?: string }>;
    timestamp?: number;
  }>;
}

// Config for extension initialization
export interface ExtensionConfig {
  verificationPatterns: ErrorPattern[];
  contextCategories: ContextCategory[];
  contextBudgetPercent: number;
  learningEnabled: boolean;
}