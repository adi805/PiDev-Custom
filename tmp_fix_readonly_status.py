from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
text = path.read_text(encoding='utf-8')
old = '''function buildAutoStatusReport(state: TurnToolState): string | null {
	const ops = state.ops;
	if (ops.length === 0) return null;

	const writes = ops.filter((o) => o.toolName === "write" && o.path).map((o) => ({ path: o.path!, index: o.index }));
	const reads = ops.filter((o) => o.toolName === "read" && o.path).map((o) => ({ path: o.path!, index: o.index }));
	const edits = ops.filter((o) => o.toolName === "edit" && (o.path || o.editsPaths?.length)).flatMap((o) => {
		const paths = o.path ? [o.path] : (o.editsPaths || []);
		return paths.map((p) => ({ path: p, index: o.index }));
	});

	const changedPaths = unique([...writes.map((w) => w.path), ...edits.map((e) => e.path)]);
	const lines: string[] = ["\n\nStatus Report (auto)"];

	for (const p of changedPaths) lines.push(`- changed: ${p}`);

	for (const w of writes) {
		const hasReadBack = reads.some((r) => r.path === w.path && r.index > w.index);
		lines.push(hasReadBack ? `- verified: wrote then read-back ${w.path}` : `- unverified: wrote ${w.path} but no read-back proof`);
	}

	for (const e of edits) {
		const hasReadBefore = reads.some((r) => r.path === e.path && r.index < e.index);
		const hasReadAfter = reads.some((r) => r.path === e.path && r.index > e.index);
		lines.push(
			hasReadBefore && hasReadAfter
				? `- verified: edited with read-before & read-after ${e.path}`
				: `- unverified: edited ${e.path} without full read-before/read-after proof`,
		);
	}

	return lines.join("\n");
}
'''
new = '''function buildAutoStatusReport(state: TurnToolState): string | null {
	const ops = state.ops;
	if (ops.length === 0) return null;

	const writes = ops.filter((o) => o.toolName === "write" && o.path).map((o) => ({ path: o.path!, index: o.index }));
	const reads = ops.filter((o) => o.toolName === "read" && o.path).map((o) => ({ path: o.path!, index: o.index }));
	const edits = ops.filter((o) => o.toolName === "edit" && (o.path || o.editsPaths?.length)).flatMap((o) => {
		const paths = o.path ? [o.path] : (o.editsPaths || []);
		return paths.map((p) => ({ path: p, index: o.index }));
	});

	const changedPaths = unique([...writes.map((w) => w.path), ...edits.map((e) => e.path)]);
	const lines: string[] = ["\n\nStatus Report (auto)"];

	for (const p of changedPaths) lines.push(`- changed: ${p}`);

	for (const w of writes) {
		const hasReadBack = reads.some((r) => r.path === w.path && r.index > w.index);
		lines.push(hasReadBack ? `- verified: wrote then read-back ${w.path}` : `- unverified: wrote ${w.path} but no read-back proof`);
	}

	for (const e of edits) {
		const hasReadBefore = reads.some((r) => r.path === e.path && r.index < e.index);
		const hasReadAfter = reads.some((r) => r.path === e.path && r.index > e.index);
		lines.push(
			hasReadBefore && hasReadAfter
				? `- verified: edited with read-before & read-after ${e.path}`
				: `- unverified: edited ${e.path} without full read-before/read-after proof`,
		);
	}

	if (writes.length === 0 && edits.length === 0 && reads.length > 0) {
		for (const p of unique(reads.map((r) => r.path))) lines.push(`- verified: read ${p}`);
	}

	return lines.length > 1 ? lines.join("\n") : null;
}
'''
if old not in text:
    raise SystemExit('target block not found')
text = text.replace(old, new)
path.write_bytes(text.replace('\r\n','\n').replace('\r','\n').encode('utf-8'))
print('fixed read-only status report')
