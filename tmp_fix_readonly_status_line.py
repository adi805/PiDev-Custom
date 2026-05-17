from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
lines = path.read_text(encoding='utf-8').splitlines()
start = None
end = None
for i,l in enumerate(lines):
    if l.strip() == 'function buildAutoStatusReport(state: TurnToolState): string | null {':
        start = i
    if start is not None and i > start and l.strip() == 'return lines.join("\\n");':
        end = i
        break
if start is None or end is None:
    raise SystemExit('could not find function bounds')
insert = [
    '\tif (writes.length === 0 && edits.length === 0 && reads.length > 0) {',
    '\t\tfor (const p of unique(reads.map((r) => r.path))) lines.push(`- verified: read ${p}`);',
    '\t}',
    '',
    '\treturn lines.length > 1 ? lines.join("\\n") : null;'
]
# replace only final return line
lines[end:end+1] = insert
path.write_bytes(('\n'.join(lines) + '\n').encode('utf-8'))
print('fixed read-only status report with line patch')
