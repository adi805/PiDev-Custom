from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
text = path.read_text(encoding='utf-8')
orig = text

text = text.replace('import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";','import type { ExtensionAPI, ExtensionCommandContext } from "@mariozechner/pi-coding-agent";')

text = text.replace('const CURRENT_SCHEMA = 1 as const;\nconst STATE_FILE = "minimax-persist.json";\n', '''const CURRENT_SCHEMA = 1 as const;
const STATE_FILE = "minimax-persist.json";
const GOAL_ENTRY_TYPE = "minimax-goal";
const GOAL_CONTINUATION_TYPE = "minimax-goal-continuation";
const ERROR_STREAK_THRESHOLD = 3;

type GoalStatus = "active" | "paused" | "complete";
type ErrorKind = "provider_error" | "tooling_error" | "extension_error" | "verification_blocked";
''')

text = text.replace('''interface GrinderRecord {
\tpath: string;
\tlastGrindSent: string;
\tgrindCount: number;
\tlastGrindIteration: number;
}
interface PersistentAutomationState {
\tschemaVersion: 1;
\tvalidations: ValidationRecord[];
\tgrinds: GrinderRecord[];
\tsessionChangedPaths: string[];
\tsessionGrindIteration: number;
}
''', '''interface GrinderRecord {
\tpath: string;
\tlastGrindSent: string;
\tgrindCount: number;
\tlastGrindIteration: number;
}
interface GoalState {
\tgoalId: string;
\tobjective: string;
\tstatus: GoalStatus;
\tcreatedAt: string;
\tupdatedAt: string;
}
interface GoalEntryRecord {
\taction: "set" | "clear";
\tgoal: GoalState | null;
\tsource?: string;
}
interface ErrorState {
\tkind: ErrorKind;
\tsignature: string;
\tsummary: string;
\tcount: number;
\tfirstSeen: string;
\tlastSeen: string;
\tblocked: boolean;
}
interface PersistentAutomationState {
\tschemaVersion: 1;
\tvalidations: ValidationRecord[];
\tgrinds: GrinderRecord[];
\tsessionChangedPaths: string[];
\tsessionGrindIteration: number;
\trecentError: ErrorState | null;
}
''')

text = text.replace('''function freshState(): PersistentAutomationState {
\treturn { schemaVersion: CURRENT_SCHEMA, validations: [], grinds: [], sessionChangedPaths: [], sessionGrindIteration: 0 };
}
''', '''function freshState(): PersistentAutomationState {
\treturn { schemaVersion: CURRENT_SCHEMA, validations: [], grinds: [], sessionChangedPaths: [], sessionGrindIteration: 0, recentError: null };
}
function normalizeGoalState(v: unknown): GoalState | null {
\tif (!isRecord(v)) return null;
\tconst goalId = typeof v["goalId"] === "string" ? v["goalId"] : "";
\tconst objective = typeof v["objective"] === "string" ? v["objective"] : "";
\tconst status = v["status"] === "paused" || v["status"] === "complete" ? v["status"] : (v["status"] === "active" ? "active" : null);
\tconst createdAt = typeof v["createdAt"] === "string" ? v["createdAt"] : "";
\tconst updatedAt = typeof v["updatedAt"] === "string" ? v["updatedAt"] : createdAt;
\tif (!goalId || !objective || !status || !createdAt) return null;
\treturn { goalId, objective, status, createdAt, updatedAt };
}
function normalizeErrorState(v: unknown): ErrorState | null {
\tif (!isRecord(v)) return null;
\tconst kind = v["kind"];
\tif (kind != "provider_error" and kind != "tooling_error" and kind != "extension_error" and kind != "verification_blocked"):
\t\treturn null
\tconst signature = typeof v["signature"] === "string" ? v["signature"] : "";
\tconst summary = typeof v["summary"] === "string" ? v["summary"] : "";
\tconst count = typeof v["count"] === "number" && Number.isFinite(v["count"]) ? Math.max(1, Math.trunc(v["count"])) : 1;
\tconst firstSeen = typeof v["firstSeen"] === "string" ? v["firstSeen"] : new Date().toISOString();
\tconst lastSeen = typeof v["lastSeen"] === "string" ? v["lastSeen"] : firstSeen;
\tconst blocked = Boolean(v["blocked"]);
\tif (!signature || !summary) return null;
\treturn { kind, signature, summary, count, firstSeen, lastSeen, blocked };
}
function normalizeState(v: unknown): PersistentAutomationState {
\tif (!isRecord(v)) return freshState();
\treturn {
\t\tschemaVersion: CURRENT_SCHEMA,
\t\tvalidations: Array.isArray(v["validations"]) ? v["validations"] as ValidationRecord[] : [],
\t\tgrinds: Array.isArray(v["grinds"]) ? v["grinds"] as GrinderRecord[] : [],
\t\tsessionChangedPaths: Array.isArray(v["sessionChangedPaths"]) ? v["sessionChangedPaths"].filter((p): p is string => typeof p === "string") : [],
\t\tsessionGrindIteration: typeof v["sessionGrindIteration"] === "number" && Number.isFinite(v["sessionGrindIteration"]) ? Math.max(0, Math.trunc(v["sessionGrindIteration"])) : 0,
\t\trecentError: normalizeErrorState(v["recentError"]),
\t};
}
''')

text = text.replace('''\tif (!isRecord(parsed) || parsed["schemaVersion"] !== CURRENT_SCHEMA || !isRecord(parsed["state"])) return freshState();
\treturn parsed["state"] as PersistentAutomationState;
}
''', '''\tif (!isRecord(parsed) || parsed["schemaVersion"] !== CURRENT_SCHEMA || !isRecord(parsed["state"])) return freshState();
\treturn normalizeState(parsed["state"]);
}
''')

insert_after = 'function readContractText(): string {\n\tconst root = getPackageRoot();\n\tconst contractPath = path.join(root, "docs", "AGENTS.md");\n\ttry { return fs.readFileSync(contractPath, "utf-8").trim(); }\n\tcatch { return ""; }\n}\n'
addition = '''
function extractTextContent(content: any): string {
\tif (typeof content === "string") return content;
\tif (!Array.isArray(content)) return "";
\treturn content.map((item) => isRecord(item) && typeof item["text"] === "string" ? item["text"] : "").filter(Boolean).join("\\n");
}
function extractErrorText(value: any): string {
\tif (typeof value === "string") return value;
\tif (isRecord(value)) {
\t\tif (typeof value["error"] === "string") return value["error"];
\t\tif (Array.isArray(value["content"])) return extractTextContent(value["content"]);
\t}
\ttry { return JSON.stringify(value); }
\tcatch { return String(value ?? ""); }
}
function classifyErrorText(text: string, context?: { toolName?: string; command?: string; status?: number }): { kind: ErrorKind; signature: string; summary: string } | null {
\tconst raw = (text || "").trim();
\tconst lower = raw.toLowerCase();
\tconst command = (context?.command || "").trim();
\tif (!raw && typeof context?.status !== "number") return null;
\tif (typeof context?.status === "number" && (context.status === 429 || context.status >= 500)) {
\t\treturn { kind: "provider_error", signature: `http:${context.status}`, summary: `Provider returned HTTP ${context.status}` };
\t}
\tif (command === "read-all-changed-files" || command === "verify-changed-files-content") {
\t\treturn { kind: "verification_blocked", signature: `validation:${command}`, summary: `Validation fallback '${command}' is unavailable in this runtime` };
\t}
\tif (lower.includes("connection error") || lower.includes("retry failed after") || lower.includes("getaddrinfo failed") || lower.includes("enotfound") || lower.includes("econnrefused") || lower.includes("timed out") || lower.includes("timeout")) {
\t\treturn { kind: "provider_error", signature: "provider:connection", summary: raw.split("\\n")[0] || "Provider connection error" };
\t}
\tif (lower.includes("failed to load extension") || lower.includes("referenceerror") || lower.includes("syntaxerror") || lower.includes("extension runtime not initialized")) {
\t\treturn { kind: "extension_error", signature: "extension:runtime", summary: raw.split("\\n")[0] || "Extension runtime error" };
\t}
\tif (lower.includes("command not found") || lower.includes("not an available shell command") || lower.includes("enoent")) {
\t\tconst unavailableKind: ErrorKind = command === "read-all-changed-files" || command === "verify-changed-files-content" ? "verification_blocked" : "tooling_error";
\t\treturn { kind: unavailableKind, signature: command ? `tooling:${command}` : "tooling:missing-command", summary: raw.split("\\n")[0] || "Command unavailable" };
\t}
\tif (lower.startswith("blocked:") && (lower.includes("read") || lower.includes("verify") || lower.includes("validation"))) {
\t\treturn { kind: "verification_blocked", signature: "verification:blocked", summary: raw.split("\\n")[0] };
\t}
\treturn null;
}
'''
text = text.replace(insert_after, insert_after + addition)

more_helpers_anchor = 'function unique<T>(items: T[]): T[] { return [...new Set(items)]; }\n'
more_helpers = '''
function createGoalState(objective: string): GoalState {
\tconst now = new Date().toISOString();
\treturn { goalId: `goal-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`, objective: objective.trim(), status: "active", createdAt: now, updatedAt: now };
}
function updateGoalStatus(goal: GoalState, status: GoalStatus): GoalState {
\treturn { ...goal, status, updatedAt: new Date().toISOString() };
}
function formatGoalSummary(goal: GoalState | null): string {
\tif (!goal) return "No active MiniMax goal.";
\treturn `Goal (${goal.status})\\n- objective: ${goal.objective}\\n- id: ${goal.goalId}\\n- updated: ${goal.updatedAt}`;
}
function buildGoalDirective(goal: GoalState | null): string {
\tif (!goal) return "";
\treturn `\\n\\n## Active Goal (always-on)\\n\\n- status: ${goal.status}\\n- objective: ${goal.objective}\\n- Keep work aligned to this goal unless the user explicitly changes it.\\n- If the goal is paused, do not continue it until resumed.\\n`;
}
function buildGoalContinuationPrompt(goal: GoalState): string {
\treturn `Continue the active MiniMax goal.\\nGoal: ${goal.objective}\\nStatus: ${goal.status}\\nStay aligned to the goal, verify meaningful changes, and report blocked states instead of looping.`;
}
function queuedGoalIdFromMessage(message: any): string | null {
\tif (!isRecord(message) || message["role"] !== "custom" || message["customType"] !== GOAL_CONTINUATION_TYPE) return null;
\tconst details = message["details"];
\tif (!isRecord(details) || typeof details["goalId"] !== "string") return null;
\treturn details["goalId"];
}
function reconstructGoalFromBranch(entries: any[]): GoalState | null {
\tlet goal: GoalState | null = null;
\tfor (const entry of entries) {
\t\tif (!isRecord(entry) || entry["type"] !== "custom" || entry["customType"] !== GOAL_ENTRY_TYPE) continue;
\t\tconst data = isRecord(entry["data"]) ? entry["data"] : null;
\t\tif (!data) continue;
\t\tif (data["action"] === "clear") { goal = null; continue; }
\t\tif (data["action"] === "set") goal = normalizeGoalState(data["goal"]);
\t}
\treturn goal;
}
function isVirtualValidationCommand(cmd: string): boolean {
\treturn cmd === "read-all-changed-files" || cmd === "verify-changed-files-content";
}
function buildValidationDirective(validationCmds: string[], changedFiles: string[]): string {
\tif (validationCmds.length === 0) return "";
\tif (validationCmds.every(isVirtualValidationCommand)) {
\t\tconst fileLines = changedFiles.length > 0 ? `Changed files to re-read if available:\\n${changedFiles.map((p) => `- ${p}`).join("\\n")}\\n` : "";
\t\treturn `\\n\\n## Auto Verification Loop (always-on)\\n\\nAfter meaningful code changes, use the read tool to read back each changed file, verify the content matches intent, and report proof in the Status Report.\\n${fileLines}`;
\t}
\treturn `\\n\\n## Auto Verification Loop (always-on)\\n\\nAfter meaningful code changes, run (in order) until the smallest relevant proof passes (or report blocked):\\n${validationCmds.map((c) => `- ${c}`).join("\\n")}\\n`;
}
function buildGrindMessage(validationCmds: string[], changedFiles: string[]): Array<{ type: "text"; text: string }> {
\tif (validationCmds.every(isVirtualValidationCommand)) {
\t\tconst files = changedFiles.length > 0 ? changedFiles.map((p) => `- ${p}`).join("\\n") : "- read back every changed file from this turn";
\t\treturn [
\t\t\t{ type: "text", text: "Run verification now and report results." },
\t\t\t{ type: "text", text: `Use the read tool to re-read these files:\\n${files}` },
\t\t\t{ type: "text", text: "Then verify the content matches the requested change. If proof is missing, mark it unverified instead of inventing success." },
\t\t];
\t}
\treturn [
\t\t{ type: "text", text: "Run verification commands now and report results." },
\t\t{ type: "text", text: "Commands (run in order; stop at first failure):\\n" + validationCmds.map((c) => `- ${c}`).join("\\n") },
\t\t{ type: "text", text: "If any command fails: read the failure output, apply ONE fix, then rerun the failing command." },
\t];
}
function updateRecentError(state: PersistentAutomationState, classified: { kind: ErrorKind; signature: string; summary: string } | null): boolean {
\tif (!classified) return false;
\tconst now = new Date().toISOString();
\tconst previous = state.recentError;
\tif (previous && previous.kind === classified.kind && previous.signature === classified.signature) {
\t\tprevious.count += 1;
\t\tprevious.lastSeen = now;
\t\tprevious.summary = classified.summary;
\t\tprevious.blocked = previous.kind === "verification_blocked" || previous.count >= ERROR_STREAK_THRESHOLD;
\t\tstate.recentError = previous;
\t\treturn true;
\t}
\tstate.recentError = { kind: classified.kind, signature: classified.signature, summary: classified.summary, count: 1, firstSeen: now, lastSeen: now, blocked: classified.kind === "verification_blocked" };
\treturn true;
}
function clearRecentError(state: PersistentAutomationState, allowedKinds?: ErrorKind[]): boolean {
\tif (!state.recentError) return false;
\tif (allowedKinds && !allowedKinds.includes(state.recentError.kind)) return false;
\tstate.recentError = null;
\treturn true;
}
function buildReliabilityDirective(errorState: ErrorState | null): string {
\tif (!errorState || !errorState.blocked) return "";
\treturn `\\n\\n## Reliability Gate (always-on)\\n\\n- recent_error_kind: ${errorState.kind}\\n- recent_error_summary: ${errorState.summary}\\n- repeated_count: ${errorState.count}\\n- Do not loop on the same failing path. After one confirmed repeat, report blocked with the concrete next diagnostic step.\\n`;
}
function automationBlockedByError(errorState: ErrorState | null): boolean {
\tif (!errorState || !errorState.blocked) return false;
\treturn errorState.kind === "provider_error" || errorState.kind === "verification_blocked" || errorState.kind === "tooling_error";
}
function buildBlockedReportLine(errorState: ErrorState | null): string | null {
\tif (!errorState || !errorState.blocked) return null;
\treturn `- blocked: ${errorState.kind} (${errorState.summary})`;
}
'''
text = text.replace(more_helpers_anchor, more_helpers_anchor + more_helpers)

text = text.replace('''\tconst contract = readContractText();
\tlet notified = false;
\tlet grindFiredThisSession = false;
''', '''\tconst contract = readContractText();
\tlet notified = false;
\tlet grindFiredThisSession = false;
\tlet currentGoal: GoalState | null = null;
''')

anchor = '''\tasync function flushState(): Promise<void> {
\t\tif (persistStateRef) await persistState(persistCwd, persistStateRef);
\t}
'''
add = '''
\tfunction refreshGoalStatus(ctx: { hasUI: boolean; ui: any }): void {
\t\tif (!ctx.hasUI) return;
\t\tctx.ui.setStatus("minimax-goal", currentGoal ? `Goal: ${currentGoal.status} • ${currentGoal.objective.slice(0, 36)}` : undefined);
\t}
\tfunction persistGoal(goal: GoalState | null, source: string): void {
\t\tcurrentGoal = goal;
\t\tpi.appendEntry<GoalEntryRecord>(GOAL_ENTRY_TYPE, { action: goal ? "set" : "clear", goal, source });
\t}
\tfunction queueGoalContinuation(goal: GoalState, reason: "start" | "resume"): void {
\t\tpi.sendMessage(
\t\t\t{ customType: GOAL_CONTINUATION_TYPE, content: buildGoalContinuationPrompt(goal), display: false, details: { kind: `goal_${reason}`, goalId: goal.goalId } },
\t\t\t{ triggerTurn: true, deliverAs: "followUp" },
\t\t);
\t}
\tfunction reloadGoalFromSession(ctx: any): void {
\t\tcurrentGoal = reconstructGoalFromBranch(ctx.sessionManager.getBranch());
\t\trefreshGoalStatus(ctx);
\t}
'''
text = text.replace(anchor, anchor + add)

text = text.replace('''\t\tconst inputMsg = event && event.message ? String(event.message.content || "") : "";
\t\tif (inputMsg.includes("Run verification commands now and report results")) {
''', '''\t\tconst inputMsg = event && typeof event.text === "string" ? event.text : "";
\t\tif (inputMsg.includes("Run verification commands now and report results") || inputMsg.includes("Continue the active MiniMax goal.")) {
''')

anchor = '\t// === session_start — notify user once ===\n'
cmd_block = '''\tpi.registerCommand("goal", {
\t\tdescription: "Show or manage the current MiniMax goal.",
\t\tasync handler(args: string, ctx: ExtensionCommandContext) {
\t\t\tconst trimmed = args.trim();
\t\t\tif (!trimmed) {
\t\t\t\tctx.ui.notify(formatGoalSummary(currentGoal), "info");
\t\t\t\trefreshGoalStatus(ctx);
\t\t\t\treturn;
\t\t\t}
\t\t\tif (trimmed === "clear") {
\t\t\t\tpersistGoal(null, "command");
\t\t\t\tctx.ui.notify("MiniMax goal cleared.", "info");
\t\t\t\trefreshGoalStatus(ctx);
\t\t\t\treturn;
\t\t\t}
\t\t\tif (trimmed === "pause") {
\t\t\t\tif (!currentGoal || currentGoal.status !== "active") {
\t\t\t\t\tctx.ui.notify("No active MiniMax goal to pause.", "warning");
\t\t\t\t\treturn;
\t\t\t\t}
\t\t\t\tpersistGoal(updateGoalStatus(currentGoal, "paused"), "command");
\t\t\t\tctx.ui.notify("MiniMax goal paused.", "info");
\t\t\t\trefreshGoalStatus(ctx);
\t\t\t\treturn;
\t\t\t}
\t\t\tif (trimmed === "resume") {
\t\t\t\tif (!currentGoal || currentGoal.status !== "paused") {
\t\t\t\t\tctx.ui.notify("No paused MiniMax goal to resume.", "warning");
\t\t\t\t\treturn;
\t\t\t\t}
\t\t\t\tconst resumedGoal = updateGoalStatus(currentGoal, "active");
\t\t\t\tpersistGoal(resumedGoal, "command");
\t\t\t\tctx.ui.notify("MiniMax goal resumed.", "info");
\t\t\t\trefreshGoalStatus(ctx);
\t\t\t\tqueueGoalContinuation(resumedGoal, "resume");
\t\t\t\treturn;
\t\t\t}
\t\t\tif (currentGoal && currentGoal.status !== "complete" && ctx.hasUI) {
\t\t\t\tconst shouldReplace = await ctx.ui.confirm("Replace MiniMax goal?", `Current goal:\\n${currentGoal.objective}\\n\\nNew goal:\\n${trimmed}`);
\t\t\t\tif (!shouldReplace) {
\t\t\t\t\tctx.ui.notify("MiniMax goal unchanged.", "info");
\t\t\t\t\treturn;
\t\t\t\t}
\t\t\t}
\t\t\tconst nextGoal = createGoalState(trimmed);
\t\t\tpersistGoal(nextGoal, "command");
\t\t\tctx.ui.notify("MiniMax goal started.", "info");
\t\t\trefreshGoalStatus(ctx);
\t\t\tqueueGoalContinuation(nextGoal, "start");
\t\t},
\t});

'''
text = text.replace(anchor, cmd_block + anchor)

text = text.replace('''\tpi.on("session_start", async (_event, ctx) => {
\t\tif (!ctx.hasUI || notified) return;
\t\tnotified = true;
\t\tctx.ui.notify("Global contract pack loaded", "info");
\t});
''', '''\tpi.on("session_start", async (event, ctx) => {
\t\treloadGoalFromSession(ctx);
\t\tif (ctx.hasUI && currentGoal && (event.reason === "resume" || event.reason === "fork" || event.reason === "reload")) {
\t\t\tctx.ui.notify(`MiniMax goal loaded: ${currentGoal.objective}`, "info");
\t\t}
\t\tif (!ctx.hasUI || notified) return;
\t\tnotified = true;
\t\tctx.ui.notify("Global contract pack loaded", "info");
\t});
''')

insert_after = '''\tpi.on("session_start", async (event, ctx) => {
\t\treloadGoalFromSession(ctx);
\t\tif (ctx.hasUI && currentGoal && (event.reason === "resume" || event.reason === "fork" || event.reason === "reload")) {
\t\t\tctx.ui.notify(`MiniMax goal loaded: ${currentGoal.objective}`, "info");
\t\t}
\t\tif (!ctx.hasUI || notified) return;
\t\tnotified = true;
\t\tctx.ui.notify("Global contract pack loaded", "info");
\t});
'''
extra = '''
\tpi.on("session_tree", async (_event, ctx) => {
\t\treloadGoalFromSession(ctx);
\t});

\tpi.on("context", async (event) => {
\t\tlet changed = false;
\t\tconst messages = event.messages.map((message: any) => {
\t\t\tconst queuedGoalId = queuedGoalIdFromMessage(message);
\t\t\tif (!queuedGoalId) return message;
\t\t\tif (currentGoal && currentGoal.status === "active" && currentGoal.goalId === queuedGoalId) return message;
\t\t\tchanged = true;
\t\t\treturn { ...message, content: "This queued MiniMax goal continuation is stale. Do not continue prior goal work.", display: false, details: { kind: "stale_goal_continuation", goalId: queuedGoalId } };
\t\t});
\t\treturn changed ? { messages } : undefined;
\t});
'''
text = text.replace(insert_after, insert_after + extra)

anchor = '\t// === before_agent_start — inject contract + auto skill routing ===\n'
provider_block = '''\tpi.on("after_provider_response", async (event, ctx) => {
\t\tconst classified = classifyErrorText("", { status: event.status });
\t\tif (!classified) {
\t\t\tconst state = await ensureState(ctx.cwd);
\t\t\tif (clearRecentError(state, ["provider_error"])) await flushState();
\t\t\treturn;
\t\t}
\t\tconst state = await ensureState(ctx.cwd);
\t\tif (updateRecentError(state, classified)) await flushState();
\t});

'''
text = text.replace(anchor, provider_block + anchor)

text = text.replace('''\t\tconst validationCmds = detectValidationCommands(ctx.cwd, state.sessionChangedPaths);
\t\tconst validationDirective = validationCmds.length > 0
\t\t\t? `\n\n## Auto Verification Loop (always-on)\n\nAfter meaningful code changes, run (in order) until the smallest relevant proof passes (or report blocked):\n${validationCmds.map((c) => `- ${c}`).join("\n")}\n`
\t\t\t: "";
''', '''\t\tconst validationCmds = detectValidationCommands(ctx.cwd, state.sessionChangedPaths);
\t\tconst validationDirective = buildValidationDirective(validationCmds, state.sessionChangedPaths);
''')
text = text.replace('''\t\tif (event.systemPrompt.includes("## Global Agent Contract (always-on)")) return;

\t\treturn {
\t\t\tsystemPrompt: event.systemPrompt + `\n\n---\n\n## Global Agent Contract (always-on)\n\n${contract}\n${ENFORCEMENT}${skillDirective}${validationDirective}`,
\t\t};
''', '''\t\tconst goalDirective = buildGoalDirective(currentGoal);
\t\tconst reliabilityDirective = buildReliabilityDirective(state.recentError);

\t\tif (event.systemPrompt.includes("## Global Agent Contract (always-on)")) return;

\t\treturn {
\t\t\tsystemPrompt: event.systemPrompt + `\n\n---\n\n## Global Agent Contract (always-on)\n\n${contract}\n${ENFORCEMENT}${goalDirective}${reliabilityDirective}${skillDirective}${validationDirective}`,
\t\t};
''')

text = text.replace('''\t\t// Bash: detect validation command results
\t\tif (toolName === "bash") {
''', '''\t\tif (event.isError) {
\t\t\tconst state = await ensureState(ctx.cwd);
\t\t\tconst classified = classifyErrorText(extractErrorText(event.result), { toolName, command: String(args.command || "") });
\t\t\tif (updateRecentError(state, classified)) await flushState();
\t\t}

\t\t// Bash: detect validation command results
\t\tif (toolName === "bash") {
''')

text = text.replace('''\t\t\tif (!matchedCmd && validationCmds.some((v) => cmd === v || cmd.startsWith(v + " ") || cmd === "read-all-changed-files" || cmd === "verify-changed-files-content") && cmd !== "read" && cmd !== "edit" && cmd !== "write") {
\t\t\t\tconst rec: ValidationRecord = { cmd, lastRun: new Date().toISOString(), lastResult: event.isError ? "fail" : "pass" };
\t\t\t\tupsertValidation(state, rec);
\t\t\t\tawait flushState();
\t\t\t}
\t\t}
''', '''\t\t\tif (!matchedCmd && validationCmds.some((v) => cmd === v || cmd.startsWith(v + " ") || cmd === "read-all-changed-files" || cmd === "verify-changed-files-content") && cmd !== "read" && cmd !== "edit" && cmd !== "write") {
\t\t\t\tconst rec: ValidationRecord = { cmd, lastRun: new Date().toISOString(), lastResult: event.isError ? "fail" : "pass" };
\t\t\t\tupsertValidation(state, rec);
\t\t\t\tawait flushState();
\t\t\t}
\t\t\tif (!event.isError && clearRecentError(state, ["tooling_error", "verification_blocked"])) await flushState();
\t\t}
''')

text = text.replace('''\t\tconst state = await ensureState(ctx.cwd);
\t\tconst validationCmds = detectValidationCommands(ctx.cwd, state.sessionChangedPaths);
''', '''\t\tconst state = await ensureState(ctx.cwd);
\t\tconst validationCmds = detectValidationCommands(ctx.cwd, state.sessionChangedPaths);
\t\tconst messageText = extractTextContent((msg as any).content);
\t\tconst messageError = classifyErrorText(messageText);
\t\tif (updateRecentError(state, messageError)) {
\t\t\tawait flushState();
\t\t} else if (messageText.trim() && clearRecentError(state, ["provider_error", "extension_error"])) {
\t\t\tawait flushState();
\t\t}
''')
text = text.replace('''\t\tif (
\t\t\tgrindEnabled &&
''', '''\t\tif (
\t\t\tgrindEnabled &&
\t\t\t!automationBlockedByError(state.recentError) &&
''')
text = text.replace('''\t\t\t\t\t\t\tconst grindMsg = [

\t\t\t\t\t\t{ type: "text", text: "Run verification commands now and report results." },
\t\t\t\t\t\t{ type: "text", text: "Commands (run in order; stop at first failure):\n" + validationCmds.map((c) => `- ${c}`).join("\n") },
\t\t\t\t\t\t{ type: "text", text: "If any command fails: read the failure output, apply ONE fix, then rerun the failing command." },
\t\t\t\t\t
\t\t\t\t];''', '''\t\t\t\tconst grindMsg = buildGrindMessage(validationCmds, freshPaths);''')
text = text.replace('''\t\tif (report.includes("unverified") && !state.sessionGrindIteration) {
''', '''\t\tif (report.includes("unverified") && !state.sessionGrindIteration && !automationBlockedByError(state.recentError)) {
''')
text = text.replace('''\t\t}
\t});
}
''', '''\t\t}

\t\tconst blockedLine = buildBlockedReportLine(state.recentError);
\t\tconst finalReport = blockedLine ? `${report}\n${blockedLine}` : report;
\t\tconst content = Array.isArray((msg as any).content) ? (msg as any).content.slice() : [];
\t\tcontent.push({ type: "text", text: finalReport });
\t\treturn { message: { ...(msg as any), content } };
\t});
}
''')

if text == orig:
    raise SystemExit('No changes applied')
path.write_bytes(text.replace('\r\n', '\n').replace('\r', '\n').encode('utf-8'))
print('updated')
