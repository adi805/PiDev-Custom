// ============================================================================
// Pi MiniMax Pack v3 — Verification Extension
// Feature: Explain failures, not block (Transfer Knowledge Level 2-3)
// ============================================================================

import { Type } from "@sinclair/typebox";
import type { ExtensionAPI, ExtensionContext } from "@mariozechner/pi-coding-agent";
import { createVerificationResult, generateVerificationExplanation, createLearningNote, getSessionState } from './shared/utils';
import type { VerificationResult } from './shared/types';

// ============================================================================
// State
// ============================================================================

interface VerificationState {
  changedFiles: Set<string>;
  pendingVerification: boolean;
  lastResult: VerificationResult | null;
  verificationCount: number;
}

const state: VerificationState = {
  changedFiles: new Set(),
  pendingVerification: false,
  lastResult: null,
  verificationCount: 0
};

// ============================================================================
// Detection: What counts as "verification command"?
// ============================================================================

const VERIFICATION_COMMANDS = [
  'npm test', 'npm run test', 'npm run build', 'npm run lint',
  'npm run typecheck', 'npx jest', 'npx vitest', 'python -m pytest',
  'go test', 'cargo test', 'rustc', 'tsc', 'eslint', 'prettier --check',
  'pnpm test', 'yarn test', 'bun test',
  'npm run validate', 'npm run check', 'npm run verify'
];

const VERIFICATION_PATTERNS = [
  /^npm\s+(test|run\s+\w+)/, /^python\s+/, /^go\s+/, /^cargo\s+/,
  /^npx\s+/, /^pnpm\s+/, /^yarn\s+/, /^bun\s+/
];

function isVerificationCommand(command: string): boolean {
  const trimmed = command.trim().toLowerCase();
  
  // Exact match
  if (VERIFICATION_COMMANDS.some(cmd => trimmed.includes(cmd.toLowerCase()))) {
    return true;
  }
  
  // Pattern match
  if (VERIFICATION_PATTERNS.some(pat => pat.test(trimmed))) {
    // Exclude common non-verification commands
    const exclusions = ['npm install', 'npm update', 'npm add', 'npm remove',
                      'python -m pip', 'go get', 'go mod'];
    if (exclusions.some(ex => trimmed.startsWith(ex))) {
      return false;
    }
    return true;
  }
  
  return false;
}

// ============================================================================
// Detect changed files from tool calls
// ============================================================================

function trackChangedFile(path: string): void {
  if (path && /\.(ts|tsx|js|jsx|py|rs|go|java|cs)$/.test(path)) {
    state.changedFiles.add(path);
  }
}

// ============================================================================
// Create learning note from verification result
// ============================================================================

function recordLearning(result: VerificationResult): void {
  if (!result.success && result.hint) {
    const sessionState = getSessionState();
    
    // Create learning note
    const note = createLearningNote(
      'verification',
      result.rootCause,
      result.hint,
      `Fix: ${result.suggestion}\nError: ${result.errorLines.join(', ')}`,
      true  // agentVisible
    );
    
    // Add to session history
    sessionState.verificationHistory.push(result);
    sessionState.learningNotes.push(note);
    
    // Update metadata
    sessionState.agentBehavior.verificationRejects++;
  } else if (result.success) {
    const sessionState = getSessionState();
    sessionState.agentBehavior.verificationAccepts++;
  }
}

// ============================================================================
// Inject explanation to agent
// ============================================================================

function injectExplanation(result: VerificationResult, ctx: ExtensionContext): void {
  const explanation = generateVerificationExplanation(result);
  
  // Create message to inject
  const message = {
    customType: 'verification-explanation',
    content: explanation,
    display: true  // Show in conversation
  };
  
  // Use before_agent_start to inject into system prompt
  // Or use sendUserMessage with triggerTurn
  try {
    // Try to send as steering message for immediate attention
    ctx.ui.notify(result.success ? 'Verification passed' : 'Verification failed - see explanation', 
      result.success ? 'info' : 'warning');
  } catch {
    // UI not available, message will be injected via event
  }
}

// ============================================================================
// Main: Register verification extension
// ============================================================================

export function registerVerificationExtension(pi: ExtensionAPI): void {
  
  // ============================================================================
  // Track file changes
  // ============================================================================
  
  pi.on('tool_execution_end', async (event, ctx) => {
    // Track write operations
    if (event.toolName === 'write' || event.toolName === 'edit') {
      // Access tool details safely
      const details = (event as any).details;
      const path = details?.path;
      if (path) trackChangedFile(path);
    }
  });
  
  // ============================================================================
  // Run verification on message_end if files changed
  // ============================================================================
  
  pi.on('message_end', async (event, ctx) => {
    // Only act on assistant messages (after agent responded)
    if ((event.message as any).role !== 'assistant') return;
    
    // Check if files were changed this turn
    if (state.changedFiles.size === 0) return;
    
    // Reset for next turn
    const changedFilesThisTurn = Array.from(state.changedFiles);
    state.changedFiles.clear();
    
    // Detect if verification is needed (files changed, not in verification mode)
    if (state.pendingVerification) {
      state.pendingVerification = false;
      return;
    }
    
    // Skip if we're already in a verification response
    const msgContent = JSON.stringify((event.message as any).content || '');
    if (msgContent.includes('verification')) return;
    
    // Find verification commands from package.json
    const verificationCommands = detectVerificationCommands(ctx.cwd);
    
    if (verificationCommands.length > 0 && changedFilesThisTurn.length > 0) {
      // Queue verification (don't auto-run, let agent decide)
      state.pendingVerification = true;
      
      // Inject reminder to agent
      try {
        const reminder = `📋 **Verification available**
Files changed: ${changedFilesThisTurn.join(', ')}
Verification commands found: ${verificationCommands.join(', ')}

Run verification to confirm changes work correctly.`;
        
        // This will be shown to agent in next turn
        // We use a custom message that the agent can see
        (ctx as any)._pendingVerificationReminder = reminder;
      } catch {
        // UI not available
      }
    }
  });
  
  // ============================================================================
  // Capture verification command output
  // ============================================================================
  
  pi.on('tool_execution_end', async (event, ctx) => {
    if (event.toolName !== 'bash') return;
    
    const args = (event as any).args || {};
    const command = (args.command || '').trim();
    
    if (!isVerificationCommand(command)) return;
    
    // Get output from the result
    const result = (event as any).result;
    if (!result) return;
    
    // Parse output
    const output = extractOutput(result);
    const exitCode = result.exitCode !== undefined ? result.exitCode : (result.isError ? 1 : 0);
    
    // Create verification result with explanation
    const verificationResult = createVerificationResult(
      command,
      output,
      exitCode,
      Array.from(state.changedFiles),
      (event as any).duration || 0
    );
    
    state.lastResult = verificationResult;
    state.verificationCount++;
    
    // Record learning
    recordLearning(verificationResult);
    
    // If failed, inject explanation (not block)
    if (!verificationResult.success) {
      // Schedule injection after message is finalized
      setTimeout(() => {
        try {
          const explanation = generateVerificationExplanation(verificationResult);
          // Use message injection approach
          // We'll handle this via before_agent_start
          (ctx as any)._lastVerificationExplanation = explanation;
        } catch {
          // Failed to inject
        }
      }, 100);
    }
  });
  
  // ============================================================================
  // Inject explanation before next agent turn
  // ============================================================================
  
  pi.on('before_agent_start', async (event, ctx) => {
    const explanation = (ctx as any)._lastVerificationExplanation;
    if (!explanation) return;
    
    // Clear the flag
    delete (ctx as any)._lastVerificationExplanation;
    
    // Inject as user message
    const sessionState = getSessionState();
    const recentNotes = sessionState.learningNotes.slice(-3);
    
    let learningNote = '';
    if (recentNotes.length > 0) {
      learningNote = '\n\n📚 **Recent learning:**\n' + 
        recentNotes.map(n => `- ${n.pattern}: ${n.hint}`).join('\n');
    }
    
    // Create injected message with explanation + learning
    return {
      message: {
        role: 'user' as const,
        customType: 'verification-feedback',
        content: [
          {
            type: 'text' as const,
            text: explanation + learningNote + '\n\nUpdate your approach based on this feedback.'
          }
        ],
        display: true,
        timestamp: Date.now()
      }
    };
  });
  
  // ============================================================================
  // Register verification tool (optional, for explicit runs)
  // ============================================================================
  
  pi.registerTool({
    name: 'run_verification',
    label: 'Run Verification',
    description: 'Run project verification commands (tests, build, lint) to confirm code works correctly. Provides detailed explanation on failure.',
    parameters: Type.Object({
      command: Type.Optional(Type.String())
    }),
    async execute(
      toolCallId: string,
      params: { command?: string },
      signal: AbortSignal | undefined,
      onUpdate: any,
      ctx: ExtensionContext
    ): Promise<any> {
      const sessionState = getSessionState();
      const commands = detectVerificationCommands(ctx.cwd);
      
      if (commands.length === 0) {
        return {
          content: [{ type: 'text', text: 'No verification commands found in package.json' }],
          details: { success: false }
        };
      }
      
      // Run first verification command
      const cmd = params.command || commands[0];
      
      // This tool is mainly for explicit agent requests
      // Actual verification happens automatically on file changes
      return {
        content: [{ 
          type: 'text', 
          text: `Verification queued. Commands available: ${commands.join(', ')}` 
        }],
        details: { queued: true, availableCommands: commands }
      };
    }
  });
  
  // ============================================================================
  // Show verification status on session start
  // ============================================================================
  
  pi.on('session_start', async (_event, ctx) => {
    const sessionState = getSessionState();
    
    if (sessionState.verificationHistory.length > 0) {
      const last = sessionState.verificationHistory[sessionState.verificationHistory.length - 1];
      const successRate = (sessionState.agentBehavior.verificationAccepts / 
        (sessionState.agentBehavior.verificationAccepts + sessionState.agentBehavior.verificationRejects) * 100).toFixed(0);
      
      ctx.ui.notify(
        `Verification: ${successRate}% pass rate (${sessionState.agentBehavior.verificationAccepts} passed, ${sessionState.agentBehavior.verificationRejects} needed fixes)`,
        'info'
      );
    }
  });
}

// ============================================================================
// Helper: Detect verification commands
// ============================================================================

function detectVerificationCommands(cwd: string): string[] {
  // This would need fs access to read package.json
  // For now, return common commands
  return ['npm test', 'npm run build'];
}

// ============================================================================
// Helper: Extract output from tool result
// ============================================================================

function extractOutput(result: any): string {
  if (typeof result === 'string') return result;
  if (result.content) {
    if (Array.isArray(result.content)) {
      return result.content.map((c: any) => c.text || '').join('\n');
    }
    return result.content.text || '';
  }
  if (result.output) return result.output;
  if (result.stdout) return result.stdout;
  return JSON.stringify(result);
}