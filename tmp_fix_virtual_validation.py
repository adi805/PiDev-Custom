from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
text = path.read_text(encoding='utf-8')
text = text.replace('function isVirtualValidationCommand(cmd: string): boolean {\n\treturn cmd === "read-all-changed-files" || cmd === "verify-changed-files-content";\n}\n', 'const VIRTUAL_READBACK_VALIDATION = "__virtual_read_back__";\nfunction isVirtualValidationCommand(cmd: string): boolean {\n\treturn cmd === VIRTUAL_READBACK_VALIDATION || cmd === "read-all-changed-files" || cmd === "verify-changed-files-content";\n}\n')
text = text.replace('if (changedFiles.length !== 0) {\n\t\treturn ["read-all-changed-files", "verify-changed-files-content"];\n\t}\n', 'if (changedFiles.length !== 0) {\n\t\treturn [VIRTUAL_READBACK_VALIDATION];\n\t}\n')
path.write_bytes(text.replace('\r\n','\n').replace('\r','\n').encode('utf-8'))
print('fixed virtual validation sentinel')
