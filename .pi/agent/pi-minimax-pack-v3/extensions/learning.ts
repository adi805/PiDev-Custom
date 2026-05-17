// ============================================================================
// Pi MiniMax Pack v3 — Learning Loop Extension
// Feature: Cross-session pattern detection (Transfer Knowledge Level 2-3)
// ============================================================================

import { Type } from "@sinclair/typebox";
import type { ExtensionAPI, ExtensionContext } from "@mariozechner/pi-coding-agent";
import { getSessionState } from './shared/utils';
import type { LearningNote } from './shared/types';

// ============================================================================
// Configuration
// ============================================================================

const PATTERN_THRESHOLD = 3;        // Occurrences before suggesting general note
const SESSION_HISTORY_FILE = '.minimax-pack-learning.json';
const MAX_PERSISTED_PATTERNS = 50;

// ============================================================================
// Pattern Types
// ============================================================================

interface PatternEntry {
  pattern: string;
  category: LearningNote['category'];
  hint: string;
  count: number;
  firstSeen: number;
  lastSeen: number;
  successfulFixes: string[];
}

interface PersistedLearning {
  patterns: PatternEntry[];
  lastUpdated: number;
  version: string;
}

// ============================================================================
// State
// ============================================================================

interface LearningState {
  sessionPatterns: PatternEntry[];
  crossSessionPatterns: PatternEntry[];
  suggestionsGenerated: number;
}

const state: LearningState = {
  sessionPatterns: [],
  crossSessionPatterns: [],
  suggestionsGenerated: 0
};

// ============================================================================
// Pattern Detection Logic
// ============================================================================

function detectPatternFromNote(note: LearningNote): string | null {
  // Extract pattern from error/hint
  if (note.category === 'verification' && note.hint) {
    // Generalize specific error hints
    const hints = [
      { specific: /line \d+/i, general: 'Line-specific errors' },
      { specific: /undefined/i, general: 'Undefined values' },
      { specific: /null/i, general: 'Null handling' },
      { specific: /import.*not found/i, general: 'Module import issues' },
      { specific: /type.*mismatch/i, general: 'Type mismatches' },
      { specific: /syntax/i, general: 'Syntax errors' },
      { specific: /permission denied/i, general: 'Permission issues' },
    ];
    
    for (const h of hints) {
      if (h.specific.test(note.hint) || h.specific.test(note.pattern)) {
        return h.general;
      }
    }
    
    // Fallback: first 30 chars of hint
    return note.hint.substring(0, 30);
  }
  
  return null;
}

function mergeWithExistingPattern(
  existing: PatternEntry,
  note: LearningNote,
  hint: string
): PatternEntry {
  return {
    ...existing,
    count: existing.count + 1,
    lastSeen: Date.now(),
    successfulFixes: note.metadata?.successfulFixes 
      ? [...new Set([...existing.successfulFixes, ...note.metadata.successfulFixes])]
      : existing.successfulFixes
  };
}

function createNewPatternEntry(
  note: LearningNote,
  generalizedPattern: string
): PatternEntry {
  return {
    pattern: generalizedPattern,
    category: note.category,
    hint: note.hint || note.explanation || '',
    count: 1,
    firstSeen: Date.now(),
    lastSeen: Date.now(),
    successfulFixes: note.metadata?.successfulFixes || []
  };
}

// ============================================================================
// Cross-Session Pattern Storage (simulated - would need fs access in real impl)
// ============================================================================

// In a real implementation, this would persist to a file
let persistedLearning: PersistedLearning = {
  patterns: [],
  lastUpdated: 0,
  version: '0.3.0'
};

function loadPersistedPatterns(): void {
  // This would read from SESSION_HISTORY_FILE
  // For now, use in-memory state
  state.crossSessionPatterns = persistedLearning.patterns;
}

function persistPatterns(): void {
  // This would write to SESSION_HISTORY_FILE
  persistedLearning.patterns = state.crossSessionPatterns
    .slice(0, MAX_PERSISTED_PATTERNS)
    .sort((a, b) => b.count - a.count);
  persistedLearning.lastUpdated = Date.now();
}

// ============================================================================
// Pattern Analysis
// ============================================================================

function analyzeSessionPatterns(sessionState: ReturnType<typeof getSessionState>): PatternEntry[] {
  const patterns: Map<string, PatternEntry> = new Map();
  
  for (const note of sessionState.learningNotes) {
    const generalized = detectPatternFromNote(note);
    if (!generalized) continue;
    
    const existing = patterns.get(generalized);
    if (existing) {
      patterns.set(generalized, mergeWithExistingPattern(existing, note, generalized));
    } else {
      patterns.set(generalized, createNewPatternEntry(note, generalized));
    }
  }
  
  return Array.from(patterns.values());
}

function generatePatternSuggestion(pattern: PatternEntry): string {
  const fixes = pattern.successfulFixes.slice(0, 2);
  const fixText = fixes.length > 0 
    ? `\n\nKnown fixes that worked:\n${fixes.map(f => `• ${f}`).join('\n')}`
    : '';
  
  return `📚 **Pattern Detected: ${pattern.pattern}**

You've encountered this ${pattern.count} time${pattern.count > 1 ? 's' : ''}.

**Hint**: ${pattern.hint}${fixText}

**Advice**: Apply this pattern proactively to avoid similar issues.`;
}

// ============================================================================
// Main: Register learning extension
// ============================================================================

export function registerLearningExtension(pi: ExtensionAPI): void {
  
  // ==========================================================================
  // Load persisted patterns on session start
  // ==========================================================================
  
  pi.on('session_start', async (_event, ctx) => {
    loadPersistedPatterns();
    
    // Check for frequent patterns
    const frequentPatterns = state.crossSessionPatterns.filter(p => p.count >= PATTERN_THRESHOLD);
    
    if (frequentPatterns.length > 0) {
      // Pre-load suggestions
      state.suggestionsGenerated = frequentPatterns.length;
      
      ctx.ui.notify(
        `📚 ${frequentPatterns.length} patterns from previous sessions available`,
        'info'
      );
    }
  });
  
  // ==========================================================================
  // Analyze patterns during session
  // ==========================================================================
  
  pi.on('before_agent_start', async (event, ctx) => {
    const sessionState = getSessionState();
    
    // Analyze session patterns
    state.sessionPatterns = analyzeSessionPatterns(sessionState);
    
    // Find patterns that appear frequently (cross-session)
    const frequentSessionPatterns = state.sessionPatterns
      .filter(p => {
        const existing = state.crossSessionPatterns.find(ep => ep.pattern === p.pattern);
        return existing && (existing.count + p.count) >= PATTERN_THRESHOLD;
      });
    
    // Generate suggestions for frequent patterns
    if (frequentSessionPatterns.length > 0 && state.suggestionsGenerated < 2) {
      // Only suggest once per session
      state.suggestionsGenerated++;
      
      const pattern = frequentSessionPatterns[0];
      const suggestion = generatePatternSuggestion(pattern);
      
      return {
        message: {
          role: 'user' as const,
          customType: 'pattern-suggestion',
          content: [{
            type: 'text' as const,
            text: suggestion
          }],
          display: true,
          timestamp: Date.now()
        }
      };
    }
  });
  
  // ==========================================================================
  // Record patterns on session end
  // ==========================================================================
  
  pi.on('session_shutdown', async (_event, _ctx) => {
    const sessionState = getSessionState();
    
    // Update cross-session patterns
    for (const sessionPattern of state.sessionPatterns) {
      const existingIdx = state.crossSessionPatterns.findIndex(
        p => p.pattern === sessionPattern.pattern
      );
      
      if (existingIdx >= 0) {
        // Merge with existing
        const existing = state.crossSessionPatterns[existingIdx];
        state.crossSessionPatterns[existingIdx] = {
          ...existing,
          count: existing.count + sessionPattern.count,
          lastSeen: Date.now(),
          successfulFixes: [
            ...existing.successfulFixes,
            ...sessionPattern.successfulFixes
          ].slice(0, 5)  // Keep top 5
        };
      } else {
        // Add new pattern
        state.crossSessionPatterns.push(sessionPattern);
      }
    }
    
    // Persist updated patterns
    persistPatterns();
    
    // Log summary
    const totalPatterns = state.sessionPatterns.length;
    if (totalPatterns > 0) {
      console.log(`[pi-minimax-pack] Learned ${totalPatterns} patterns this session`);
    }
  });
  
  // ==========================================================================
  // Tool: Show learned patterns
  // ==========================================================================
  
  pi.registerTool({
    name: 'show_learned_patterns',
    label: 'Show Learned Patterns',
    description: 'Display patterns learned from recent sessions that may help avoid similar issues',
    parameters: Type.Object({}),
    async execute(
      toolCallId: string, 
      params: {}, 
      signal: AbortSignal | undefined, 
      onUpdate: any, 
      ctx: ExtensionContext
    ): Promise<any> {
      const allPatterns = [
        ...state.sessionPatterns,
        ...state.crossSessionPatterns
      ];
      
      // Dedupe and sort by count
      const uniquePatterns = new Map<string, PatternEntry>();
      for (const p of allPatterns) {
        const existing = uniquePatterns.get(p.pattern);
        if (existing) {
          existing.count += p.count;
        } else {
          uniquePatterns.set(p.pattern, { ...p });
        }
      }
      
      const sortedPatterns = Array.from(uniquePatterns.values())
        .sort((a, b) => b.count - a.count)
        .slice(0, 10);
      
      if (sortedPatterns.length === 0) {
        return {
          content: [{
            type: 'text',
            text: 'No patterns learned yet. Patterns are recorded as you work through verification failures and context pruning.'
          }],
          details: { patternCount: 0 }
        };
      }
      
      const patternList = sortedPatterns
        .map(p => `**${p.pattern}** (×${p.count})\n   Hint: ${p.hint}`)
        .join('\n\n');
      
      return {
        content: [{
          type: 'text',
          text: `📚 **Learned Patterns (${sortedPatterns.length})**\n\n${patternList}\n\n---\n*Patterns with higher counts are recurring issues to watch for.*`
        }],
        details: {
          patternCount: sortedPatterns.length,
          patterns: sortedPatterns.map(p => ({
            pattern: p.pattern,
            count: p.count,
            hint: p.hint
          }))
        }
      };
    }
  });
  
  // ==========================================================================
  // Tool: Clear session patterns
  // ==========================================================================
  
  pi.registerTool({
    name: 'clear_learning',
    label: 'Clear Learning',
    description: 'Clear patterns learned this session (for testing or fresh start)',
    parameters: Type.Object({}),
    async execute(
      toolCallId: string, 
      params: {}, 
      signal: AbortSignal | undefined, 
      onUpdate: any, 
      ctx: ExtensionContext
    ): Promise<any> {
      state.sessionPatterns = [];
      state.suggestionsGenerated = 0;
      
      return {
        content: [{
          type: 'text',
          text: 'Session patterns cleared. Cross-session patterns are preserved.'
        }],
        details: { cleared: true }
      };
    }
  });
}

// ============================================================================
// Named exports for testing
// ============================================================================

export { detectPatternFromNote, analyzeSessionPatterns, generatePatternSuggestion };
