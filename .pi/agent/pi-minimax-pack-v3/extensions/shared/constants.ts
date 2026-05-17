// ============================================================================
// Pi MiniMax Pack v3 — Constants & Configuration
// Design: Transfer Knowledge (Level 2-3)
// ============================================================================

import type { ErrorPattern, ContextCategory, ExtensionConfig } from './types';

// ============================================================================
// Error Patterns for Verification
// Each pattern has: regex to detect, hint to explain, suggestion to fix
// ============================================================================

export const ERROR_PATTERNS: ErrorPattern[] = [
  // Syntax errors
  {
    name: 'syntax_brackets',
    patterns: [/SyntaxError.*Unexpected.*token|missing.*\}|\}\) expected/i],
    category: 'syntax',
    hint: 'Check for mismatched brackets, parentheses, or braces',
    suggestion: 'Review the line mentioned + surrounding code. Count opening vs closing brackets.'
  },
  {
    name: 'syntax_semicolon',
    patterns: [/Unexpected identifier|missing.*;.*after/i],
    category: 'syntax',
    hint: 'Missing semicolon or incorrect statement termination',
    suggestion: 'Add semicolon where required, or check for missing commas in object/array literals.'
  },
  {
    name: 'syntax_template',
    patterns: [/\`[^\`]*\$|\$\{[^}]*$/i],
    category: 'syntax',
    hint: 'Unclosed template literal or missing closing brace in template',
    suggestion: 'Ensure template literals use backticks and ${} properly closed.'
  },

  // Type errors
  {
    name: 'type_undefined',
    patterns: [/TypeError.*Cannot read|Cannot read.*property.*of undefined|TypeError.*is not a function/i],
    category: 'type',
    hint: 'Variable is undefined or wrong type when accessed',
    suggestion: 'Add null/undefined checks, or verify the variable is initialized before use.'
  },
  {
    name: 'type_mismatch',
    patterns: [/Type.*expected|is not assignable|cannot be assigned to/i],
    category: 'type',
    hint: 'Type mismatch between expected and actual',
    suggestion: 'Check the type annotation vs the actual value. Add type assertions or fix the value.'
  },
  {
    name: 'type_null',
    patterns: [/null.*not.*function|cannot call.*null/i],
    category: 'type',
    hint: 'Trying to call a method on null/undefined',
    suggestion: 'Verify the object exists before calling its methods.'
  },

  // Import errors
  {
    name: 'import_not_found',
    patterns: [/Cannot find module|Cannot resolve module|ERR_MODULE_NOT_FOUND/i],
    category: 'import',
    hint: 'Module path or name is incorrect',
    suggestion: 'Check package.json dependencies and verify import path matches file location.'
  },
  {
    name: 'import_named',
    patterns: [/has no exported member|export.*not found|Named export.*not found/i],
    category: 'import',
    hint: 'The named export doesn\'t exist or is named differently',
    suggestion: 'Check the actual export name in the source file.'
  },
  {
    name: 'import_default',
    patterns: [/has no default export|default.*not.*function/i],
    category: 'import',
    hint: 'Trying to use default import from module without one',
    suggestion: 'Use named import instead, or check if default export exists in source.'
  },

  // Test errors
  {
    name: 'test_expected',
    patterns: [/Expected|expected.*but received|Expected.*but got/i],
    category: 'test',
    hint: 'Test expectation doesn\'t match actual value',
    suggestion: 'Review test assertions vs implementation. Either fix the test or the implementation.'
  },
  {
    name: 'test_timeout',
    patterns: [/timeout|timed out|TIME_LIMIT|jest.*timeout/i],
    category: 'test',
    hint: 'Test or operation took too long',
    suggestion: 'Increase timeout, optimize the operation, or mock expensive dependencies.'
  },
  {
    name: 'test_assertion',
    patterns: [/Assertion failed|expect.*toBe|expect.*toEqual|toBeTruthy|toBeFalsy/i],
    category: 'test',
    hint: 'Assertion in test failed',
    suggestion: 'Check what the test expects vs what the code actually does.'
  },

  // Runtime errors
  {
    name: 'runtime_reference',
    patterns: [/is not defined|ReferenceError|variable.*not defined/i],
    category: 'runtime',
    hint: 'Using a variable that doesn\'t exist in scope',
    suggestion: 'Check spelling, ensure variable is declared/imported, or fix scope issues.'
  },
  {
    name: 'runtime_range',
    patterns: [/index out of range|out of bounds|Array index.*invalid/i],
    category: 'runtime',
    hint: 'Accessing array/list index that doesn\'t exist',
    suggestion: 'Check array length before access, or use safe access patterns.'
  },
  {
    name: 'runtime_recursion',
    patterns: [/Maximum call stack|stack overflow|Recursion too deep/i],
    category: 'runtime',
    hint: 'Too many recursive calls (infinite loop)',
    suggestion: 'Add base case, reduce recursion depth, or convert to iteration.'
  },

  // Network errors
  {
    name: 'network_connection',
    patterns: [/ECONNREFUSED|ENOTFOUND|fetch.*failed|network error/i],
    category: 'network',
    hint: 'Network connection failed',
    suggestion: 'Check if server is running, verify URL, check firewall/proxy settings.'
  },
  {
    name: 'network_timeout',
    patterns: [/ETIMEDOUT|request timeout|timeout.*exceeded/i],
    category: 'network',
    hint: 'Network request took too long',
    suggestion: 'Increase timeout, check network latency, or optimize request.'
  },

  // Permission errors
  {
    name: 'permission_file',
    patterns: [/EACCES|permission denied|ENOENT.*not.*exist/i],
    category: 'permission',
    hint: 'File or directory access issue',
    suggestion: 'Check file permissions, verify path, or run with appropriate permissions.'
  },
];

// ============================================================================
// Context Categories for Pruning
// Each category has reason and how many recent to keep
// ============================================================================

export const CONTEXT_CATEGORIES: ContextCategory[] = [
  {
    name: 'old_tool_calls',
    reason: 'Old tool execution results no longer relevant to current task',
    keepRecent: 5  // Keep last 5 tool calls
  },
  {
    name: 'redundant_results',
    reason: 'Repeated or redundant information can be summarized',
    keepRecent: 3
  },
  {
    name: 'outdated_context',
    reason: 'Context from earlier session phase no longer relevant',
    keepRecent: 10
  },
  {
    name: 'long_output',
    reason: 'Verbose output can be condensed without losing key information',
    keepRecent: 5
  },
  {
    name: 'exploration_phase',
    reason: 'Exploratory messages from early problem-solving not needed now',
    keepRecent: 3
  }
];

// ============================================================================
// Default Configuration
// ============================================================================

export const DEFAULT_CONFIG: ExtensionConfig = {
  verificationPatterns: ERROR_PATTERNS,
  contextCategories: CONTEXT_CATEGORIES,
  contextBudgetPercent: 80,  // Start pruning at 80% context usage
  learningEnabled: true
};

// ============================================================================
// Helper: Find matching error pattern
// ============================================================================

export function findErrorPattern(errorOutput: string): ErrorPattern | null {
  for (const pattern of ERROR_PATTERNS) {
    for (const regex of pattern.patterns) {
      if (regex.test(errorOutput)) {
        return pattern;
      }
    }
  }
  return null;
}

// ============================================================================
// Helper: Generate root cause explanation
// ============================================================================

export function generateRootCause(
  errorOutput: string,
  matchedPattern: ErrorPattern | null
): string {
  if (matchedPattern) {
    return `Error matches pattern: ${matchedPattern.name}`;
  }
  
  // Generic root cause detection
  if (/Cannot find module/.test(errorOutput)) {
    return 'Missing or misnamed module import';
  }
  if (/TypeError/.test(errorOutput)) {
    return 'Type-related runtime error — likely undefined/null or wrong type';
  }
  if (/SyntaxError/.test(errorOutput)) {
    return 'Syntax error — check for typos, missing punctuation, or mismatched brackets';
  }
  if (/Expected/.test(errorOutput)) {
    return 'Test expectation mismatch — assertion doesn\'t match actual value';
  }
  
  return 'Unknown error type — review the error message for details';
}

// ============================================================================
// Token estimation (rough)
// ============================================================================

export function estimateTokens(text: string): number {
  // Rough estimate: ~4 chars per token for English
  return Math.ceil(text.length / 4);
}

export function estimateMessagesTokens(messages: Array<{ content: Array<{ text?: string }> }>): number {
  let total = 0;
  for (const msg of messages) {
    for (const content of msg.content) {
      if (content.text) {
        total += estimateTokens(content.text);
      }
    }
  }
  return total;
}