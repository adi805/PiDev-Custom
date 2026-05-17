from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
text = path.read_text(encoding='utf-8')
text = text.replace('''type GoalStatus = "active" | "paused" | "complete";
type ErrorKind = "provider_error" | "tooling_error" | "extension_error" | "verification_blocked";
''','''type GoalStatus = "active" | "paused" | "complete";
type ErrorKind = "provider_error" | "tooling_error" | "extension_error" | "verification_blocked";
type PreferredLanguage = "id" | "en";
''')
text = text.replace('''function buildBlockedReportLine(errorState: ErrorState | null): string | null {
	if (!errorState || !errorState.blocked) return null;
	return `- blocked: ${errorState.kind} (${errorState.summary})`;
}
''','''function buildBlockedReportLine(errorState: ErrorState | null): string | null {
	if (!errorState || !errorState.blocked) return null;
	return `- blocked: ${errorState.kind} (${errorState.summary})`;
}
function detectPreferredLanguage(text: string): PreferredLanguage {
	const lower = (text || "").toLowerCase();
	if (!lower.trim()) return "id";
	const idSignals = /\b(yang|dan|atau|tidak|apakah|tolong|buat|baca|jalankan|gagal|berarti|kenapa|bagaimana|tambahkan|hapus|ubah|lanjutkan)\b/;
	const enSignals = /\b(the|and|or|not|please|create|read|run|failed|why|how|add|remove|change|continue)\b/;
	if (idSignals.test(lower) && !enSignals.test(lower)) return "id";
	if (enSignals.test(lower) && !idSignals.test(lower)) return "en";
	return "id";
}
function buildLanguageDirective(preferredLanguage: PreferredLanguage): string {
	return preferredLanguage === "id"
		? `\n\n## Language Consistency (always-on)\n\n- Jawab dalam Bahasa Indonesia kecuali user secara eksplisit meminta bahasa lain.\n- Jangan berpindah ke bahasa lain saat clarifying, diagnosis, atau blocked reporting.`
		: `\n\n## Language Consistency (always-on)\n\n- Reply in English unless the user explicitly asks for another language.\n- Do not switch languages during clarification, diagnosis, or blocked reporting.`;
}
''')
text = text.replace('''function buildDiagnosticMessage(errorState: ErrorState, changedFiles: string[]): Array<{ type: "text"; text: string }> {
''','''function buildDiagnosticMessage(errorState: ErrorState, changedFiles: string[], preferredLanguage: PreferredLanguage): Array<{ type: "text"; text: string }> {
''')
text = text.replace('''	if (errorState.kind === "verification_blocked") {
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
''','''	if (preferredLanguage === "id") {
		if (errorState.kind === "verification_blocked") {
			return [
				{ type: "text", text: "Selidiki kegagalan verifikasi sebelum mencoba lagi." },
				{ type: "text", text: `File yang perlu diperiksa dengan tool read:\n${changed}` },
				{ type: "text", text: "Baca ulang file yang berubah, bandingkan dengan intent perubahan, lalu laporkan proof verified atau satu mismatch konkret. Jangan retry command verifikasi palsu." },
			];
		}
		if (errorState.kind === "tooling_error") {
			return [
				{ type: "text", text: "Selidiki kegagalan tooling sebelum mencoba lagi." },
				{ type: "text", text: `Kegagalan yang terlihat: ${errorState.summary}` },
				{ type: "text", text: "Cari alternatif terdekat yang valid: periksa package.json / pyproject / dokumentasi repo, pilih satu command nyata atau jalur proof berbasis read, lakukan satu fix, lalu rerun hanya jalur yang sudah dikoreksi." },
			];
		}
		if (errorState.kind === "provider_error") {
			return [
				{ type: "text", text: "Selidiki kegagalan provider sebelum mencoba lagi." },
				{ type: "text", text: `Kegagalan yang terlihat: ${errorState.summary}` },
				{ type: "text", text: "Tentukan apakah ini terkait DNS/network/rate limit/provider dari bukti yang sudah ada. Lakukan satu langkah diagnosis termurah, lalu retry sekali dengan alasan atau laporkan blocked beserta hipotesis root cause." },
			];
		}
		return [
			{ type: "text", text: "Selidiki kegagalan extension/runtime sebelum mencoba lagi." },
			{ type: "text", text: `Kegagalan yang terlihat: ${errorState.summary}` },
			{ type: "text", text: "Baca source atau konteks stack yang relevan, tentukan satu fix konkret, terapkan, lalu verifikasi extension bisa load bersih sebelum melanjutkan pekerjaan lain." },
		];
	}
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
''')
text = text.replace('''	let notified = false;
	let grindFiredThisSession = false;
	let currentGoal: GoalState | null = null;
''','''	let notified = false;
	let grindFiredThisSession = false;
	let currentGoal: GoalState | null = null;
	let preferredLanguage: PreferredLanguage = "id";
''')
text = text.replace('''		const inputMsg = event && typeof event.text === "string" ? event.text : "";
		if (isGrindMessageText(inputMsg) || inputMsg.includes("Continue the active MiniMax goal.")) {
			return;
		}
''','''		const inputMsg = event && typeof event.text === "string" ? event.text : "";
		if (isGrindMessageText(inputMsg) || inputMsg.includes("Continue the active MiniMax goal.")) {
			return;
		}
		preferredLanguage = detectPreferredLanguage(inputMsg);
''')
text = text.replace('''		const goalDirective = buildGoalDirective(currentGoal);
		const reliabilityDirective = buildReliabilityDirective(state.recentError);
''','''		const goalDirective = buildGoalDirective(currentGoal);
		const reliabilityDirective = buildReliabilityDirective(state.recentError);
		const languageDirective = buildLanguageDirective(preferredLanguage);
''')
text = text.replace('''		return {
			systemPrompt: event.systemPrompt + `\n\n---\n\n## Global Agent Contract (always-on)\n\n${contract}\n${ENFORCEMENT}${goalDirective}${reliabilityDirective}${skillDirective}${validationDirective}`,
		};
''','''		return {
			systemPrompt: event.systemPrompt + `\n\n---\n\n## Global Agent Contract (always-on)\n\n${contract}\n${ENFORCEMENT}${languageDirective}${goalDirective}${reliabilityDirective}${skillDirective}${validationDirective}`,
		};
''')
text = text.replace('''			const diagnosticMsg = buildDiagnosticMessage(state.recentError!, state.sessionChangedPaths.slice());
''','''			const diagnosticMsg = buildDiagnosticMessage(state.recentError!, state.sessionChangedPaths.slice(), preferredLanguage);
''')
path.write_bytes(text.replace('\r\n','\n').replace('\r','\n').encode('utf-8'))
print('added language guard for diagnostics')
