from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
text = path.read_text(encoding='utf-8')
text = text.replace('''		// Read
		if (toolName === "read") {
			const p = asPath(args.path);
			turnState.ops.push({ toolName, path: p, index: opIndex++ });
			if (p) lastReadByPath.set(p, opIndex);
			return;
		}

		// Write
		if (toolName === "write") {
			const p = asPath(args.path);
			turnState.ops.push({ toolName, path: p, index: opIndex++ });
			if (p) {
				const state = await ensureState(ctx.cwd);
				trackChangedPath(state, p);
				const existing = getGrindRecord(state, p);
				if (existing) { existing.grindCount = 0; existing.lastGrindIteration = 0; upsertGrindRecord(state, existing); }
				await flushState();
			}
			return;
		}

		// Edit
		if (toolName === "edit") {
			const p = asPath(args.path);
			turnState.ops.push({ toolName, path: p, index: opIndex++ });
			if (p) {
				const state = await ensureState(ctx.cwd);
				trackChangedPath(state, p);
				const existing = getGrindRecord(state, p);
				if (existing) { existing.grindCount = 0; existing.lastGrindIteration = 0; upsertGrindRecord(state, existing); }
				await flushState();
			}
			return;
		}
''','''		// Read
		if (toolName === "read") {
			if (event.isError) return;
			const p = asPath(args.path);
			turnState.ops.push({ toolName, path: p, index: opIndex++ });
			if (p) lastReadByPath.set(p, opIndex);
			return;
		}

		// Write
		if (toolName === "write") {
			if (event.isError) return;
			const p = asPath(args.path);
			turnState.ops.push({ toolName, path: p, index: opIndex++ });
			if (p) {
				const state = await ensureState(ctx.cwd);
				trackChangedPath(state, p);
				const existing = getGrindRecord(state, p);
				if (existing) { existing.grindCount = 0; existing.lastGrindIteration = 0; upsertGrindRecord(state, existing); }
				await flushState();
			}
			return;
		}

		// Edit
		if (toolName === "edit") {
			if (event.isError) return;
			const p = asPath(args.path);
			turnState.ops.push({ toolName, path: p, index: opIndex++ });
			if (p) {
				const state = await ensureState(ctx.cwd);
				trackChangedPath(state, p);
				const existing = getGrindRecord(state, p);
				if (existing) { existing.grindCount = 0; existing.lastGrindIteration = 0; upsertGrindRecord(state, existing); }
				await flushState();
			}
			return;
		}
''')
text = text.replace('''		const blockedLine = buildBlockedReportLine(state.recentError);
		const finalReport = blockedLine ? `${report}
${blockedLine}` : report;
		const content = Array.isArray((msg as any).content) ? (msg as any).content.slice() : [];
		content.push({ type: "text", text: finalReport });
		return { message: { ...(msg as any), content } };
''','''		const blockedLine = buildBlockedReportLine(state.recentError);
		const finalReport = blockedLine ? `${report}
${blockedLine}` : report;
		const content = Array.isArray((msg as any).content)
			? (msg as any).content.filter((item: any) => !(isRecord(item) && typeof item["text"] === "string" && item["text"].includes("Status Report (auto)")))
			: [];
		content.push({ type: "text", text: finalReport });
		return { message: { ...(msg as any), content } };
''')
path.write_bytes(text.replace('\r\n','\n').replace('\r','\n').encode('utf-8'))
print('fixed status report tracking and dedupe')
