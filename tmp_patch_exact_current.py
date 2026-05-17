from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
text = path.read_text(encoding='utf-8')
old = '''		const validationCmds = detectValidationCommands(ctx.cwd, state.sessionChangedPaths);
		const validationDirective = validationCmds.length > 0
			? `\n\n## Auto Verification Loop (always-on)\n\nAfter meaningful code changes, run (in order) until the smallest relevant proof passes (or report blocked):\n${validationCmds.map((c) => `- ${c}`).join("\n")}\n`
			: "";

		const ENFORCEMENT = `
'''
new = '''		const validationCmds = detectValidationCommands(ctx.cwd, state.sessionChangedPaths);
		const validationDirective = buildValidationDirective(validationCmds, state.sessionChangedPaths);

		const ENFORCEMENT = `
'''
text = text.replace(old, new)
old2 = '''		if (event.systemPrompt.includes("## Global Agent Contract (always-on)")) return;

		return {
			systemPrompt: event.systemPrompt + `\n\n---\n\n## Global Agent Contract (always-on)\n\n${contract}\n${ENFORCEMENT}${skillDirective}${validationDirective}`,
		};
'''
new2 = '''		const goalDirective = buildGoalDirective(currentGoal);
		const reliabilityDirective = buildReliabilityDirective(state.recentError);

		if (event.systemPrompt.includes("## Global Agent Contract (always-on)")) return;

		return {
			systemPrompt: event.systemPrompt + `\n\n---\n\n## Global Agent Contract (always-on)\n\n${contract}\n${ENFORCEMENT}${goalDirective}${reliabilityDirective}${skillDirective}${validationDirective}`,
		};
'''
text = text.replace(old2, new2)
old3 = '''
							const grindMsg = [

						{ type: "text", text: "Run verification commands now and report results." },
						{ type: "text", text: "Commands (run in order; stop at first failure):\n" + validationCmds.map((c) => `- ${c}`).join("\n") },
						{ type: "text", text: "If any command fails: read the failure output, apply ONE fix, then rerun the failing command." },
					
				];
'''
new3 = '\n\t\t\t\tconst grindMsg = buildGrindMessage(validationCmds, freshPaths);\n'
text = text.replace(old3, new3)
path.write_bytes((text.replace('\r\n','\n').replace('\r','\n')).encode('utf-8'))
print('patched exact current blocks')
