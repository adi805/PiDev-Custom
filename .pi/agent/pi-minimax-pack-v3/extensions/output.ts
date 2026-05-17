// ============================================================================
// Pi MiniMax Pack v3 — Output Enforcement Extension
// Feature: Remind agent to produce Status Report (Transfer Knowledge Level 2-3)
// ============================================================================

import { Type } from "@sinclair/typebox";
import type { ExtensionAPI, ExtensionContext } from "@mariozechner/pi-coding-agent";
import { getSessionState } from './shared/utils';

// ============================================================================
// Configuration
// ============================================================================

const STATUS_REPORT_REMINDER_THRESHOLD = 3;  // Remind after N tool calls
const ENABLE_VERIFICATION_REMINDER = true;
const ENABLE_COMPLETION_REMINDER = true;

// ============================================================================
// Status Report Template
// ============================================================================

const STATUS_REPORT_TEMPLATE = `
// ============================================================================
// Status Report Template
// ============================================================================

## Summary
[One paragraph: What was accomplished]

## Files Touched
- [file1]: [what changed]
- [file2]: [what changed]

## Verification
- [x] Tests pass / ⚠️ Tests failed (see below)
- [x] TypeScript compiles / ⚠️ TypeScript errors (see below)

## Verification Evidence
[Commands run, output, surfaces exercised]

## Risks & Unverified Items
- [Untested edge cases]
- [Assumptions not verified]

## Next Steps
- [ ] [immediate next action]
- [ ] [follow-up]

---
`;

// ============================================================================
// Keywords that trigger completion mode
// ============================================================================

const COMPLETION_KEYWORDS = [
  'done', 'complete', 'finished', 'selesai', 'jadi', 'sudah',
  'final', 'deliver', 'submit', 'ship', 'deploy',
  'fix complete', 'task done', 'issue resolved'
];

const VERIFICATION_KEYWORDS = [
  'fixed', 'resolved', 'implemented', 'added', 'created',
  'changed', 'updated', 'modified', 'refactored',
  'build', 'compile', 'test', 'run', 'verify'
];

// ============================================================================
// State
// ============================================================================

interface OutputState {
  toolCallCount: number;
  lastReminderType: string | null;
  reminderCooldown: number;  // Don't spam reminders
  modificationsSinceReminder: number;
}

const state: OutputState = {
  toolCallCount: 0,
  lastReminderType: null,
  reminderCooldown: 0,
  modificationsSinceReminder: 0
};

// ============================================================================
// Detect if agent is likely completing a task
// ============================================================================

function detectCompletionMode(message: string): boolean {
  const lower = message.toLowerCase();
  return COMPLETION_KEYWORDS.some(keyword => lower.includes(keyword));
}

// ============================================================================
// Detect significant changes (verification-worthy)
// ============================================================================

function detectSignificantChanges(message: string): boolean {
  const lower = message.toLowerCase();
  return VERIFICATION_KEYWORDS.some(keyword => lower.includes(keyword));
}

// ============================================================================
// Generate appropriate reminder
// ============================================================================

function generateReminder(
  type: 'status' | 'verification' | 'completion',
  sessionState: ReturnType<typeof getSessionState>
): string {
  switch (type) {
    case 'status':
      return `📋 **Reminder: Include Status Report**

Before declaring task complete, include:

${STATUS_REPORT_TEMPLATE}

This helps:
- Document what was verified (and what wasn't)
- Track what changed and why
- Communicate status to reviewers`;

    case 'verification':
      return `⚠️ **Reminder: Verification Suggested**

Files were modified. Consider running:
- \`npm test\` or project tests
- \`npm run build\` or typecheck
- \`npm run lint\`

This confirms changes work correctly.`;

    case 'completion':
      return `✅ **Reminder: Task Completion Checklist**

Before finishing:
1. Run verification (tests, build, lint)
2. Document what was changed (Status Report)
3. Note any unverified assumptions

Good completion = verified + documented.`;

    default:
      return '';
  }
}

// ============================================================================
// Check if reminder should be shown (avoid spam)
// ============================================================================

function shouldShowReminder(type: string): boolean {
  // Cooldown check
  if (state.reminderCooldown > 0) {
    state.reminderCooldown--;
    return false;
  }
  
  // Don't repeat same reminder type consecutively
  if (state.lastReminderType === type) {
    return false;
  }
  
  return true;
}

// ============================================================================
// Main: Register output enforcement extension
// ============================================================================

export function registerOutputExtension(pi: ExtensionAPI): void {
  
  // ==========================================================================
  // Track tool calls for reminder timing
  // ==========================================================================
  
  pi.on('tool_execution_end', async (event, ctx) => {
    state.toolCallCount++;
    state.reminderCooldown = Math.max(0, state.reminderCooldown - 1);
    
    // Check if significant changes were made
    const result = (event as any).result;
    if (result && typeof result === 'object') {
      const output = JSON.stringify(result);
      
      // Track file modifications
      if (event.toolName === 'write' || event.toolName === 'edit') {
        state.modificationsSinceReminder++;
      }
    }
  });
  
  // ==========================================================================
  // Inject reminders before agent responds
  // ==========================================================================
  
  pi.on('before_agent_start', async (event, ctx) => {
    const sessionState = getSessionState();
    
    // Access messages from event safely
    const messages = (event as any).messages || [];
    const recentMessages = messages.slice(-5);
    const lastContent = recentMessages.length > 0 
      ? (typeof recentMessages[recentMessages.length - 1]?.content === 'string'
          ? recentMessages[recentMessages.length - 1].content
          : JSON.stringify(recentMessages[recentMessages.length - 1]?.content || ''))
      : '';
    
    // Check for completion keywords
    const isCompleting = detectCompletionMode(lastContent);
    const hasVerification = detectSignificantChanges(lastContent);
    
    // Decide reminder type
    let reminderType: 'status' | 'verification' | 'completion' | null = null;
    
    if (isCompleting && ENABLE_COMPLETION_REMINDER) {
      reminderType = 'status';
    } else if (hasVerification && !sessionState.verificationHistory.length) {
      // Agent did things but no verification yet
      reminderType = 'verification';
    }
    
    // Show reminder if appropriate
    if (reminderType && shouldShowReminder(reminderType)) {
      state.lastReminderType = reminderType;
      state.reminderCooldown = 3;  // Don't remind for next 3 tool calls
      
      const reminder = generateReminder(reminderType, sessionState);
      
      return {
        message: {
          role: 'user' as const,
          customType: 'output-reminder',
          content: [{
            type: 'text' as const,
            text: reminder
          }],
          display: true,
          timestamp: Date.now()
        }
      };
    }
    
    // Inject learning notes from recent activity
    if (sessionState.learningNotes.length > 0 && ENABLE_VERIFICATION_REMINDER) {
      const recentNotes = sessionState.learningNotes.slice(-3);
      const relevantNotes = recentNotes.filter(n => 
        n.agentVisible && 
        (Date.now() - n.timestamp) < 300000  // Last 5 minutes
      );
      
      if (relevantNotes.length > 0) {
        const notesText = relevantNotes
          .map(n => `• **${n.pattern}**: ${n.explanation}${n.hint ? ` → ${n.hint}` : ''}`)
          .join('\n');
        
        return {
          message: {
            role: 'user' as const,
            customType: 'learning-reminder',
            content: [{
              type: 'text' as const,
              text: `📚 **Learning from recent work:**\n${notesText}`
            }],
            display: true,
            timestamp: Date.now()
          }
        };
      }
    }
  });
  
  // ==========================================================================
  // Session start: reset counters
  // ==========================================================================
  
  pi.on('session_start', async (_event, ctx) => {
    state.toolCallCount = 0;
    state.lastReminderType = null;
    state.reminderCooldown = 0;
    
    // Check for existing learning notes
    const sessionState = getSessionState();
    if (sessionState.learningNotes.length > 0) {
      const recentNotes = sessionState.learningNotes.slice(-5);
      const patterns = [...new Set(recentNotes.map(n => n.pattern))];
      
      if (patterns.length > 0) {
        ctx.ui.notify(
          `📚 ${patterns.length} patterns learned from recent sessions`,
          'info'
        );
      }
    }
  });
  
  // ==========================================================================
  // Tool: Request Status Report
  // ==========================================================================
  
  pi.registerTool({
    name: 'request_status_report',
    label: 'Request Status Report',
    description: 'Display the Status Report template for documenting completed work',
    parameters: Type.Object({}),
    async execute(toolCallId: string, params: {}, signal: AbortSignal | undefined, onUpdate: any, ctx: ExtensionContext): Promise<any> {
      return {
        content: [{
          type: 'text',
          text: STATUS_REPORT_TEMPLATE
        }],
        details: {
          templateShown: true
        }
      };
    }
  });
  
  // ==========================================================================
  // Session end: Persist learning notes metadata
  // ==========================================================================
  
  pi.on('session_shutdown', async (_event, _ctx) => {
    const sessionState = getSessionState();
    
    if (sessionState.learningNotes.length > 0) {
      // Log for potential cross-session use
      const patterns = sessionState.learningNotes
        .filter(n => n.category === 'verification')
        .map(n => ({
          pattern: n.pattern,
          hint: n.hint,
          count: n.metadata.occurrenceCount
        }));
      
      if (patterns.length > 0) {
        console.log('[pi-minimax-pack] Session patterns:', JSON.stringify(patterns));
      }
    }
  });
}

// ============================================================================
// Named exports for testing
// ============================================================================

export { STATUS_REPORT_TEMPLATE };
