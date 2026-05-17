from pathlib import Path
path = Path(r'C:\Users\acer\.pi\agent\git\github.com\adi805\pi-minimax-pack\extensions\global-contract.ts')
text = path.read_text(encoding='utf-8')
text = text.replace('if (kind != "provider_error" and kind != "tooling_error" and kind != "extension_error" and kind != "verification_blocked"):\n\t\treturn null', 'if (kind !== "provider_error" && kind !== "tooling_error" && kind !== "extension_error" && kind !== "verification_blocked") return null;')
text = text.replace('lower.startswith("blocked:")', 'lower.startsWith("blocked:")')
path.write_bytes(text.replace('\r\n','\n').replace('\r','\n').encode('utf-8'))
print('fixed syntax tokens')
