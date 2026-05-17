from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
lines = path.read_text(encoding='utf-8').splitlines()

# before_agent_start validation directive block
for i,l in enumerate(lines):
    if l.strip() == 'const validationCmds = detectValidationCommands(ctx.cwd, state.sessionChangedPaths);' and i > 650:
        lines[i:i+4] = [
            '\t\tconst validationCmds = detectValidationCommands(ctx.cwd, state.sessionChangedPaths);',
            '\t\tconst validationDirective = buildValidationDirective(validationCmds, state.sessionChangedPaths);'
        ]
        break

# before_agent_start prompt injection block
for i,l in enumerate(lines):
    if l.strip() == 'if (event.systemPrompt.includes("## Global Agent Contract (always-on)")) return;' and i > 680:
        lines[i:i+5] = [
            '\t\tconst goalDirective = buildGoalDirective(currentGoal);',
            '\t\tconst reliabilityDirective = buildReliabilityDirective(state.recentError);',
            '',
            '\t\tif (event.systemPrompt.includes("## Global Agent Contract (always-on)")) return;',
            '',
            '\t\treturn {',
            '\t\t\tsystemPrompt: event.systemPrompt + `\\n\\n---\\n\\n## Global Agent Contract (always-on)\\n\\n${contract}\\n${ENFORCEMENT}${goalDirective}${reliabilityDirective}${skillDirective}${validationDirective}`,' ,
            '\t\t};'
        ]
        break

# grind message block
for i,l in enumerate(lines):
    if 'const grindMsg = [' in l and i > 730:
        end = i
        while end < len(lines) and '];' not in lines[end]:
            end += 1
        if end < len(lines):
            lines[i:end+1] = ['\t\t\t\tconst grindMsg = buildGrindMessage(validationCmds, freshPaths);']
        break

path.write_bytes(('\n'.join(lines) + '\n').encode('utf-8'))
print('line patch done')
