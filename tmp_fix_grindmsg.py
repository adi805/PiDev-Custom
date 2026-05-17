from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
text = path.read_text(encoding='utf-8')
old = '''							const grindMsg = [

						{ type: "text", text: "Run verification commands now and report results." },
						{ type: "text", text: "Commands (run in order; stop at first failure):\n" + validationCmds.map((c) => `- ${c}`).join("\n") },
						{ type: "text", text: "If any command fails: read the failure output, apply ONE fix, then rerun the failing command." },
					
				];'''
new = '\t\t\t\tconst grindMsg = buildGrindMessage(validationCmds, freshPaths);'
if old not in text:
    old = '''\t\t\t\t\t\t\tconst grindMsg = [

\t\t\t\t\t\t{ type: "text", text: "Run verification commands now and report results." },
\t\t\t\t\t\t{ type: "text", text: "Commands (run in order; stop at first failure):\n" + validationCmds.map((c) => `- ${c}`).join("\n") },
\t\t\t\t\t\t{ type: "text", text: "If any command fails: read the failure output, apply ONE fix, then rerun the failing command." },
\t\t\t\t\t
\t\t\t\t];'''
text = text.replace(old, new)
path.write_bytes(text.replace('\r\n','\n').replace('\r','\n').encode('utf-8'))
print('fixed grind message block')
