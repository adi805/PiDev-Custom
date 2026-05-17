from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
text = path.read_text(encoding='utf-8')
text = text.replace('const unavailableKind: ErrorKind = command === "read-all-changed-files" || command === "verify-changed-files-content" ? "verification_blocked" : "tooling_error";', 'const unavailableKind: ErrorKind = command === VIRTUAL_READBACK_VALIDATION ? "verification_blocked" : "tooling_error";')
path.write_bytes(text.replace('\r\n','\n').replace('\r','\n').encode('utf-8'))
print('removed last legacy validation reference')
