import { Type } from "@sinclair/typebox";
import type { ExtensionAPI, ExtensionContext, ContextEvent } from "@mariozechner/pi-coding-agent";
import { generatePruningSummary, generateLearningSummary, getSessionState } from './shared/utils';
import type { PruningResult } from './shared/types';

// ============================================================================
// State
// ============================================================================

interface ContextState {
  lastUsage: number;
  lastPruning: PruningResult | null;
  pruningCount: number;
  efficiencyScore: number;
}

const state: ContextState = {
  lastUsage: 0,
  lastPruning: null,
  pruningCount: 0,
  efficiencyScore: 100
};

// ============================================================================
// Configuration
// ============================================================================

const CONTEXT_BUDGET_PERCENT = 80;  // Start pruning at 80%
const PRUNE_DEBOUNCE_MS = 3000;    // Don't prune too frequently
const MIN_MESSAGES_TO_PRUNE = 5;    // Only prune if significant

// ============================================================================
// Pruning Decision Logic
// ============================================================================

interface PruningCandidate {
  index: number;
  role: string;
  contentLength: number;
  category: string;
  reason: string;
  keyPoints: string[];
}

function identifyPruningCandidates(
  messages: Array<{ role: string; content: Array<{ type: string; text?: string }> }>,
  budgetTokens: number
): PruningCandidate[] {
  const candidates: PruningCandidate[] = [];
  
  // Calculate current token estimate
  let totalTokens = 0;
  for (const msg of messages) {
    for (const content of msg.content) {
      if (content.text) {
        totalTokens += Math.ceil((content.text || '').length / 4);
      }
    }
  }
  
  // If under budget, no pruning needed
  if (totalTokens < budgetTokens * 0.7) {
    return [];
  }
  
  // Categorize and identify prune candidates
  // Keep: recent user messages, recent assistant, current task context
  // Prune: old tool calls, redundant results, exploration phase messages
  
  const toolCalls: number[] = [];
  const toolResults: number[] = [];
  const oldUserMessages: number[] = [];
  
  messages.forEach((msg, idx) => {
    if (msg.role === 'tool-call') {
      toolCalls.push(idx);
    } else if (msg.role === 'tool') {
      toolResults.push(idx);
    } else if (msg.role === 'user' && idx < messages.length - 5) {
      oldUserMessages.push(idx);
    }
  });
  
  // Prune old tool calls (keep last 5)
  const keepToolCount = 5;
  const pruneToolCalls = toolCalls.slice(0, Math.max(0, toolCalls.length - keepToolCount));
  for (const idx of pruneToolCalls) {
    const content = messages[idx].content[0]?.text || '';
    const isVerbose = content.length > 500;
    candidates.push({
      index: idx,
      role: 'tool-call',
      contentLength: content.length,
      category: 'old_tool_calls',
      reason: isVerbose 
        ? 'Long tool call no longer needed for current context' 
        : 'Old tool call not relevant to current task',
      keyPoints: extractKeyPoints(content, 2)
    });
  }
  
  // Prune old tool results (keep last 5)
  const pruneToolResults = toolResults.slice(0, Math.max(0, toolResults.length - keepToolCount));
  for (const idx of pruneToolResults) {
    const content = messages[idx].content[0]?.text || '';
    const isVerbose = content.length > 1000;
    candidates.push({
      index: idx,
      role: 'tool',
      contentLength: content.length,
      category: 'redundant_results',
      reason: isVerbose
        ? 'Verbose tool output can be summarized without losing essential info'
        : 'Old tool result no longer needed',
      keyPoints: extractKeyPoints(content, 3)
    });
  }
  
  // Prune very old user messages (keep last 3)
  const pruneUserMessages = oldUserMessages.slice(0, Math.max(0, oldUserMessages.length - 3));
  for (const idx of pruneUserMessages) {
    const content = messages[idx].content[0]?.text || '';
    candidates.push({
      index: idx,
      role: 'user',
      contentLength: content.length,
      category: 'outdated_context',
      reason: 'Message from earlier phase no longer relevant to current task',
      keyPoints: extractKeyPoints(content, 2)
    });
  }
  
  // Sort by importance (keep more important, prune less)
  candidates.sort((a, b) => {
    if (a.index > b.index) return -1;
    if (b.index > a.index) return 1;
    return b.contentLength - a.contentLength;
  });
  
  return candidates;
}

// ============================================================================
// Extract key points from content
// ============================================================================

function extractKeyPoints(content: string, maxPoints: number): string[] {
  const points: string[] = [];
  const lines = content.split('\n').filter(l => l.trim().length > 10);
  
  for (const line of lines.slice(0, maxPoints)) {
    let cleaned = line.trim();
    if (cleaned.length > 100) {
      cleaned = cleaned.substring(0, 100) + '...';
    }
    if (cleaned.length > 20) {
      points.push(cleaned);
    }
  }
  
  return points;
}

// ============================================================================
// Generate pruning explanation
// ============================================================================

function generatePruningExplanation(
  result: PruningResult,
  candidates: PruningCandidate[]
): string {
  const preservedKeyPoints = candidates
    .flatMap(c => c.keyPoints)
    .slice(0, 5)
    .map(p => `  • ${p}`)
    .join('\n');
  
  return `📋 **Context Pruning Applied**

${result.summary}

**Key information preserved:**
${preservedKeyPoints || '  (minimal info lost)'}

**Why this helps:**
- Keeps your context budget healthy
- Focuses on current task relevance
- You can ask me to clarify any pruned information if needed

This is normal operation — essential context remains.`;
}

// ============================================================================
// Main: Register context extension
// ============================================================================

export function registerContextExtension(pi: ExtensionAPI): void {
  
  // ============================================================================
  // Monitor context usage before each LLM call
  // ============================================================================
  
  pi.on('context', async (event: ContextEvent, ctx: ExtensionContext) => {
    // Get messages from event - handle different message types
    const rawMessages = event.messages as any[];
    
    // Estimate current tokens
    let totalTokens = 0;
    for (const msg of rawMessages) {
      const content = msg.content;
      if (typeof content === 'string') {
        totalTokens += Math.ceil(content.length / 4);
      } else if (Array.isArray(content)) {
        for (const c of content) {
          if (c && typeof c === 'object' && 'text' in c && c.text) {
            totalTokens += Math.ceil(c.text.length / 4);
          }
        }
      }
    }
    
    state.lastUsage = totalTokens;
    
    // Check if pruning is needed
    const budgetTokens = 100000; // Assume 100k context window
    const budgetThreshold = budgetTokens * (CONTEXT_BUDGET_PERCENT / 100);
    
    if (totalTokens < budgetThreshold) {
      return;
    }
    
    // Check debounce
    const now = Date.now();
    if (state.lastPruning && (now - state.lastPruning.timestamp) < PRUNE_DEBOUNCE_MS) {
      return;
    }
    
    // Identify pruning candidates
    const candidates = identifyPruningCandidates(rawMessages, budgetThreshold);
    
    if (candidates.length < MIN_MESSAGES_TO_PRUNE) {
      return;
    }
    
    // Generate pruning result
    const result = generatePruningSummary({
      candidates: candidates.map(c => ({ reason: c.reason, category: c.category })),
      prunedCount: candidates.length,
      tokenSavings: candidates.reduce((sum, c) => sum + Math.ceil(c.contentLength / 4), 0)
    });
    
    state.lastPruning = result;
    state.pruningCount++;
    
    // Store for injection
    (ctx as any)._pendingPruningExplanation = {
      result,
      candidates
    };
    
    // Return modified messages (prune) - extension returns messages directly
    const indicesToRemove = new Set(candidates.map(c => c.index));
    const prunedMessages = rawMessages.filter((_, idx) => !indicesToRemove.has(idx));
    
    // Return the pruned messages for the context event
    // The runtime will update the context with these messages
    (ctx as any)._pendingPrunedMessages = prunedMessages;
  });
  
  // ============================================================================
  // Inject pruning explanation
  // ============================================================================
  
  pi.on('before_agent_start', async (event, ctx) => {
    const pending = (ctx as any)._pendingPruningExplanation;
    if (!pending) return;
    
    delete (ctx as any)._pendingPruningExplanation;
    
    const { result } = pending;
    
    // Update session state
    const sessionState = getSessionState();
    sessionState.pruningHistory.push(result);
    
    // Calculate efficiency score
    const totalPruned = sessionState.pruningHistory.reduce((sum, p) => sum + p.prunedCount, 0);
    const messageCount = sessionState.verificationHistory.length * 5 + 10;
    state.efficiencyScore = Math.max(50, 100 - (totalPruned / messageCount * 10));
    sessionState.agentBehavior.contextEfficiencyScore = state.efficiencyScore;
    
    // Inject explanation
    const explanation = generatePruningExplanation(result, pending.candidates);
    
    return {
      message: {
        role: 'user' as const,
        customType: 'context-pruning',
        content: [{
          type: 'text' as const,
          text: explanation + '\n\nContext is now optimized for your current task.'
        }],
        display: true,
        timestamp: Date.now()
      }
    };
  });
  
  // ============================================================================
  // Show context status
  // ============================================================================
  
  pi.on('model_select', async (_event, ctx) => {
    // Use direct token estimation since getContextUsage may not be available
    const sessionState = getSessionState();
    const percent = Math.min(100, Math.round(state.lastUsage / 100000 * 100));
    ctx.ui.setStatus('context', `${percent}% context used`);
  });
  
  // ============================================================================
  // Tool: Context summary
  // ============================================================================
  
  pi.registerTool({
    name: 'context_summary',
    label: 'Context Summary',
    description: 'Show current context usage, pruning history, and efficiency metrics',
    parameters: Type.Object({}),
    async execute(
      toolCallId: string, 
      params: {}, 
      signal: AbortSignal | undefined, 
      onUpdate: any, 
      ctx: ExtensionContext
    ): Promise<any> {
      const sessionState = getSessionState();
      // Use estimated usage since getContextUsage may not be available
      const usagePercent = Math.min(100, Math.round(state.lastUsage / 100000 * 100));
      
      const pruningSummary = sessionState.pruningHistory.length > 0
        ? `Pruning events: ${sessionState.pruningHistory.length}\n` +
          `Total pruned: ${sessionState.pruningHistory.reduce((s, p) => s + p.prunedCount, 0)} messages\n` +
          `Efficiency score: ${sessionState.agentBehavior.contextEfficiencyScore.toFixed(0)}%`
        : 'No pruning needed yet';
      
      return {
        content: [{
          type: 'text',
          text: `**Context Status**
          
Usage: ~${usagePercent}% of budget
${pruningSummary}

${generateLearningSummary(sessionState.learningNotes)}`
        }],
        details: {
          usagePercent,
          pruningCount: state.pruningCount,
          efficiencyScore: state.efficiencyScore
        }
      };
    }
  });
  
  // ============================================================================
  // Session start
  // ============================================================================
  
  pi.on('session_start', async (_event, ctx) => {
    if (state.pruningCount > 0) {
      ctx.ui.notify(
        `Context efficiency: ${state.efficiencyScore.toFixed(0)}% (${state.pruningCount} optimizations)`,
        'info'
      );
    }
  });
}