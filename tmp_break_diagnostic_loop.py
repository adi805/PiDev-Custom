from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
text = path.read_text(encoding='utf-8')
text = text.replace('''const GRIND_MESSAGE_PREFIXES = [
	"Run verification now and report results.",
	"Run verification commands now and report results.",
];
function isVirtualValidationCommand(cmd: string): boolean {
	return cmd === VIRTUAL_READBACK_VALIDATION;
}
function isGrindMessageText(text: string): boolean {
	return GRIND_MESSAGE_PREFIXES.some((prefix) => text.includes(prefix));
}
''','''const GRIND_MESSAGE_PREFIXES = [
	"Run verification now and report results.",
	"Run verification commands now and report results.",
];
const DIAGNOSTIC_MESSAGE_PREFIXES = [
	"Selidiki kegagalan ",
	"Investigate the ",
];
function isVirtualValidationCommand(cmd: string): boolean {
	return cmd === VIRTUAL_READBACK_VALIDATION;
}
function isGrindMessageText(text: string): boolean {
	return GRIND_MESSAGE_PREFIXES.some((prefix) => text.includes(prefix));
}
function isDiagnosticMessageText(text: string): boolean {
	return DIAGNOSTIC_MESSAGE_PREFIXES.some((prefix) => text.includes(prefix));
}
''')
text = text.replace('''	let notified = false;
	let grindFiredThisSession = false;
	let currentGoal: GoalState | null = null;
	let preferredLanguage: PreferredLanguage = "id";
''','''	let notified = false;
	let grindFiredThisSession = false;
	let currentGoal: GoalState | null = null;
	let preferredLanguage: PreferredLanguage = "id";
	let activeDiagnosticTurn = false;
''')
text = text.replace('''		if (isGrindMessageText(inputMsg) || inputMsg.includes("Continue the active MiniMax goal.")) {
			return;
		}
		preferredLanguage = detectPreferredLanguage(inputMsg);
''','''		activeDiagnosticTurn = isDiagnosticMessageText(inputMsg);
		if (isGrindMessageText(inputMsg) || inputMsg.includes("Continue the active MiniMax goal.")) {
			return;
		}
		preferredLanguage = detectPreferredLanguage(inputMsg);
''')
text = text.replace('${contract}\n${ENFORCEMENT}${goalDirective}${reliabilityDirective}${skillDirective}${validationDirective}`','${contract}\n${ENFORCEMENT}${languageDirective}${goalDirective}${reliabilityDirective}${skillDirective}${validationDirective}`')
text = text.replace('''		const messageError = classifyErrorText(messageText);
		if (updateRecentError(state, messageError)) {
			await flushState();
		} else if (messageText.trim() && clearRecentError(state, ["provider_error", "extension_error"])) {
			await flushState();
		}

		if (shouldQueueDiagnostic(state, state.recentError)) {
			await flushState();
			const diagnosticMsg = buildDiagnosticMessage(state.recentError!, state.sessionChangedPaths.slice(), preferredLanguage);
			setTimeout(async () => {
				try {
					await pi.sendUserMessage(diagnosticMsg, { triggerTurn: true });
				} catch (_e) {
					await pi.sendUserMessage(diagnosticMsg, { deliverAs: "steer" });
				}
			}, 250);
		}
''','''		const messageError = activeDiagnosticTurn ? null : classifyErrorText(messageText);
		if (updateRecentError(state, messageError)) {
			await flushState();
		} else if (messageText.trim() && clearRecentError(state, ["provider_error", "extension_error"])) {
			await flushState();
		}

		if (!activeDiagnosticTurn && shouldQueueDiagnostic(state, state.recentError)) {
			await flushState();
			const diagnosticMsg = buildDiagnosticMessage(state.recentError!, state.sessionChangedPaths.slice(), preferredLanguage);
			setTimeout(async () => {
				try {
					await pi.sendUserMessage(diagnosticMsg, { triggerTurn: true });
				} catch (_e) {
					await pi.sendUserMessage(diagnosticMsg, { deliverAs: "steer" });
				}
			}, 250);
		}
		activeDiagnosticTurn = false;
''')
path.write_bytes(text.replace('\r\n','\n').replace('\r','\n').encode('utf-8'))
print('added diagnostic loop breaker and language directive fix')
