// ============================================================================
// Pi MiniMax Pack v3 — Main Entry Point
// Design: Transfer Knowledge (Level 2-3)
// ============================================================================

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { registerVerificationExtension } from './verification';
import { registerContextExtension } from './context';
import { registerOutputExtension } from './output';
import { registerLearningExtension } from './learning';

// ============================================================================
// Version Info
// ============================================================================

const VERSION = '0.4.0';
const NAME = 'pi-minimax-pack-v3';

// ============================================================================
// Main Export
// ============================================================================

export default async function minimaxPackV3(pi: ExtensionAPI): Promise<void> {
  // Register flags
  pi.registerFlag('minimax-verification', {
    description: 'Verification behavior: explain (default), block, or silent',
    type: 'string',
    default: 'explain'
  });
  
  pi.registerFlag('minimax-context-pruning', {
    description: 'Context pruning: transparent (default), silent, or aggressive',
    type: 'string',
    default: 'transparent'
  });
  
  pi.registerFlag('minimax-learning', {
    description: 'Enable learning notes to agent',
    type: 'boolean',
    default: true
  });
  
  pi.registerFlag('minimax-context-budget', {
    description: 'Context budget threshold for pruning (percentage)',
    type: 'string',
    default: '80'
  });
  
  // Note: numeric config stored as string; parse in extension when needed
  
  // Register extensions
  registerVerificationExtension(pi);
  registerContextExtension(pi);
  registerOutputExtension(pi);
  registerLearningExtension(pi);
  
  // Notify on load
  pi.on('session_start', async (_event, ctx) => {
    if (ctx.hasUI) {
      ctx.ui.notify(`${NAME} v${VERSION} loaded`, 'info');
    }
  });
  
  // Log version for debugging
  console.log(`[${NAME}] Version ${VERSION} initialized`);
}

// ============================================================================
// Named exports for testing
// ============================================================================

export { registerVerificationExtension } from './verification';
export { registerContextExtension } from './context';
export { registerOutputExtension } from './output';
export { registerLearningExtension } from './learning';