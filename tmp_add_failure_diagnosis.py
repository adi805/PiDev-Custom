from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
text = path.read_text(encoding='utf-8')
text = text.replace('''interface PersistentAutomationState {
	schemaVersion: 1;
	validations: ValidationRecord[];
	grinds: GrinderRecord[];
	sessionChangedPaths: string[];
	sessionGrindIteration: number;
	recentError: ErrorState | null;
}
''','''interface PersistentAutomationState {
	schemaVersion: 1;
	validations: ValidationRecord[];
	grinds: GrinderRecord[];
	sessionChangedPaths: string[];
	sessionGrindIteration: number;
	recentError: ErrorState | null;
	diagnosticCursor: string | null;
}
''')
text = text.replace('''function freshState(): PersistentAutomationState {
	return { schemaVersion: CURRENT_SCHEMA, validations: [], grinds: [], sessionChangedPaths: [], sessionGrindIteration: 0, recentError: null };
}
''','''function freshState(): PersistentAutomationState {
	return { schemaVersion: CURRENT_SCHEMA, validations: [], grinds: [], sessionChangedPaths: [], sessionGrindIteration: 0, recentError: null, diagnosticCursor: null };
}
''')
text = text.replace('''		sessionGrindIteration: typeof v["sessionGrindIteration"] === "number" && Number.isFinite(v["sessionGrindIteration"]) ? Math.max(0, Math.trunc(v["sessionGrindIteration"])) : 0,
		recentError: normalizeErrorState(v["recentError"]),
	};
}
''','''		sessionGrindIteration: typeof v["sessionGrindIteration"] === "number" && Number.isFinite(v["sessionGrindIteration"]) ? Math.max(0, Math.trunc(v["sessionGrindIteration"])) : 0,
		recentError: normalizeErrorState(v["recentError"]),
		diagnosticCursor: typeof v["diagnosticCursor"] === "string" ? v["diagnosticCursor"] : null,
	};
}
''')
text = text.replace('''function clearRecentError(state: PersistentAutomationState, allowedKinds?: ErrorKind[]): boolean {
	if (!state.recentError) return false;
	if (allowedKinds && !allowedKinds.includes(state.recentError.kind)) return false;
	state.recentError = null;
	return true;
}
''','''function clearRecentError(state: PersistentAutomationState, allowedKinds?: ErrorKind[]): boolean {
	if (!state.recentError) return false;
	if (allowedKinds && !allowedKinds.includes(state.recentError.kind)) return false;
	state.recentError = null;
	state.diagnosticCursor = null;
	return true;
}
''')
text = text.replace('''function buildBlockedReportLine(errorState: ErrorState | null): string | null {
	if (!errorState || !errorState.blocked) return null;
	return `- blocked: ${errorState.kind} (${errorState.summary})`;
}
''','''function buildBlockedReportLine(errorState: ErrorState | null): string | null {
	if (!errorState || !errorState.blocked) return null;
	return `- blocked: ${errorState.kind} (${errorState.summary})`;
}
function diagnosticCursorFor(errorState: ErrorState): string {
	return `${errorState.kind}:${errorState.signature}:${errorState.count}:${errorState.blocked ? "blocked" : "active"}`;
}
function shouldQueueDiagnostic(state: PersistentAutomationState, errorState: ErrorState | null): boolean {
	if (!errorState) return false;
	if (errorState.count > 2 && !errorState.blocked) return false;
	const cursor = diagnosticCursorFor(errorState);
	if (state.diagnosticCursor === cursor) return false;
	state.diagnosticCursor = cursor;
	return true;
}
function buildDiagnosticMessage(errorState: ErrorState, changedFiles: string[]): Array<{ type: "text"; text: string }> {
	const changed = changedFiles.length > 0 ? changedFiles.map((p) => `- ${p}`).join("\n") : "- no changed files recorded";
	if (errorState.kind === "verification_blocked") {
		return [
			{ type: "text", text: "Investigate the verification failure before retrying." },
			{ type: "text", text: `Changed files to inspect with the read tool:\n${changed}` },
			{ type: "text", text: "Read back the changed files, compare them with the requested intent, then either report verified proof or one concrete mismatch. Do not retry fake shell validation commands." },
		];
	}
	if (errorState.kind === "tooling_error") {
		return [
			{ type: "text", text: "Investigate the tooling failure before retrying." },
			{ type: "text", text: `Observed failure: ${errorState.summary}` },
			{ type: "text", text: "Find the nearest valid alternative: inspect package.json / pyproject / repo docs, choose one real command or a read-based proof path, apply one fix, then rerun only that corrected path." },
		];
	}
	if (errorState.kind === "provider_error") {
		return [
			{ type: "text", text: "Investigate the provider failure before retrying." },
			{ type: "text", text: `Observed failure: ${errorState.summary}` },
			{ type: "text", text: "Identify whether this is DNS/network/provider-rate-limit related from existing evidence. Do one cheapest diagnostic step, then either retry once with a reason or report blocked with the root-cause hypothesis." },
		];
	}
	return [
		{ type: "text", text: "Investigate the extension/runtime failure before retrying." },
		{ type: "text", text: `Observed failure: ${errorState.summary}` },
		{ type: "text", text: "Read the relevant source or stack context, identify one concrete fix, apply it, and verify the extension loads cleanly before continuing broader work." },
	];
}
''')
anchor = '''		if (updateRecentError(state, messageError)) {
			await flushState();
		} else if (messageText.trim() && clearRecentError(state, ["provider_error", "extension_error"])) {
			await flushState();
		}
'''
replacement = '''		if (updateRecentError(state, messageError)) {
			await flushState();
		} else if (messageText.trim() && clearRecentError(state, ["provider_error", "extension_error"])) {
			await flushState();
		}

		if (shouldQueueDiagnostic(state, state.recentError)) {
			await flushState();
			const diagnosticMsg = buildDiagnosticMessage(state.recentError!, state.sessionChangedPaths.slice());
			setTimeout(async () => {
				try {
					await pi.sendUserMessage(diagnosticMsg, { triggerTurn: true });
				} catch (_e) {
					await pi.sendUserMessage(diagnosticMsg, { deliverAs: "steer" });
				}
			}, 250);
		}
'''
if anchor not in text:
    raise SystemExit('message_end anchor not found')
text = text.replace(anchor, replacement)
path.write_bytes(text.replace('\r\n','\n').replace('\r','\n').encode('utf-8'))
print('added failure diagnosis automation')
