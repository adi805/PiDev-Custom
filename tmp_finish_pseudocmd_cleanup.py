from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
text = path.read_text(encoding='utf-8')
text = text.replace('''function classifyErrorText(text: string, context?: { toolName?: string; command?: string; status?: number }): { kind: ErrorKind; signature: string; summary: string } | null {
	const raw = (text || "").trim();
	const lower = raw.toLowerCase();
	const command = (context?.command || "").trim();
	if (!raw && typeof context?.status !== "number") return null;
	if (typeof context?.status === "number" && (context.status === 429 || context.status >= 500)) {
		return { kind: "provider_error", signature: `http:${context.status}`, summary: `Provider returned HTTP ${context.status}` };
	}
	if (command === "read-all-changed-files" || command === "verify-changed-files-content") {
		return { kind: "verification_blocked", signature: `validation:${command}`, summary: `Validation fallback '${command}' is unavailable in this runtime` };
	}
''','''function classifyErrorText(text: string, context?: { toolName?: string; command?: string; status?: number }): { kind: ErrorKind; signature: string; summary: string } | null {
	const raw = (text || "").trim();
	const lower = raw.toLowerCase();
	const command = (context?.command || "").trim();
	if (!raw && typeof context?.status !== "number") return null;
	if (typeof context?.status === "number" && (context.status === 429 || context.status >= 500)) {
		return { kind: "provider_error", signature: `http:${context.status}`, summary: `Provider returned HTTP ${context.status}` };
	}
	if (command === VIRTUAL_READBACK_VALIDATION) {
		return { kind: "verification_blocked", signature: `validation:${command}`, summary: "Virtual read-back validation should not execute as a shell command" };
	}
''')
text = text.replace('''	if (lower.includes("command not found") || lower.includes("not an available shell command") || lower.includes("enoent")) {
		const unavailableKind: ErrorKind = command === "read-all-changed-files" || command === "verify-changed-files-content" ? "verification_blocked" : "tooling_error";
		return { kind: unavailableKind, signature: command ? `tooling:${command}` : "tooling:missing-command", summary: raw.split("\n")[0] || "Command unavailable" };
	}
''','''	if (lower.includes("command not found") || lower.includes("not an available shell command") || lower.includes("enoent")) {
		const unavailableKind: ErrorKind = command === VIRTUAL_READBACK_VALIDATION ? "verification_blocked" : "tooling_error";
		return { kind: unavailableKind, signature: command ? `tooling:${command}` : "tooling:missing-command", summary: raw.split("\n")[0] || "Command unavailable" };
	}
''')
text = text.replace('''const VIRTUAL_READBACK_VALIDATION = "__virtual_read_back__";
function isVirtualValidationCommand(cmd: string): boolean {
	return cmd === VIRTUAL_READBACK_VALIDATION || cmd === "read-all-changed-files" || cmd === "verify-changed-files-content";
}
''','''const VIRTUAL_READBACK_VALIDATION = "__virtual_read_back__";
const GRIND_MESSAGE_PREFIXES = [
	"Run verification now and report results.",
	"Run verification commands now and report results.",
];
function isVirtualValidationCommand(cmd: string): boolean {
	return cmd === VIRTUAL_READBACK_VALIDATION;
}
function isGrindMessageText(text: string): boolean {
	return GRIND_MESSAGE_PREFIXES.some((prefix) => text.includes(prefix));
}
''')
text = text.replace('''		const inputMsg = event && typeof event.text === "string" ? event.text : "";
		if (inputMsg.includes("Run verification commands now and report results") || inputMsg.includes("Continue the active MiniMax goal.")) {
''','''		const inputMsg = event && typeof event.text === "string" ? event.text : "";
		if (isGrindMessageText(inputMsg) || inputMsg.includes("Continue the active MiniMax goal.")) {
''')
text = text.replace('''			if (!matchedCmd && validationCmds.some((v) => cmd === v || cmd.startsWith(v + " ") || cmd === "read-all-changed-files" || cmd === "verify-changed-files-content") && cmd !== "read" && cmd !== "edit" && cmd !== "write") {
''','''			if (!matchedCmd && validationCmds.some((v) => cmd === v || cmd.startsWith(v + " ")) && cmd !== "read" && cmd !== "edit" && cmd !== "write") {
''')
path.write_bytes(text.replace('\r\n','\n').replace('\r','\n').encode('utf-8'))
print('finished pseudo-command cleanup and grind detection fix')
