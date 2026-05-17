from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
text = path.read_text(encoding='utf-8')
text = text.replace('''function buildDiagnosticMessage(errorState: ErrorState, changedFiles: string[]): Array<{ type: "text"; text: string }> {
	const changed = changedFiles.length > 0 ? changedFiles.map((p) => `- ${p}`).join("
") : "- no changed files recorded";
	if (errorState.kind === "verification_blocked") {
		return [
			{ type: "text", text: "Investigate the verification failure before retrying." },
			{ type: "text", text: `Changed files to inspect with the read tool:
${changed}` },
''','''function buildDiagnosticMessage(errorState: ErrorState, changedFiles: string[]): Array<{ type: "text"; text: string }> {
	const changed = changedFiles.length > 0 ? changedFiles.map((p) => `- ${p}`).join("\\n") : "- no changed files recorded";
	if (errorState.kind === "verification_blocked") {
		return [
			{ type: "text", text: "Investigate the verification failure before retrying." },
			{ type: "text", text: `Changed files to inspect with the read tool:\n${changed}` },
''')
path.write_bytes(text.replace('\r\n','\n').replace('\r','\n').encode('utf-8'))
print('fixed diagnostic string escaping')
