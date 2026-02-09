import base64

with open('ricoh_generator/mask_base64.txt', 'r') as f:
    b64 = f.read().strip()

with open('ricoh_generator/index.html', 'r') as f:
    content = f.read()

new_content = content.replace('REPLACE_WITH_BASE64', b64)

with open('ricoh_generator/index.html', 'w') as f:
    f.write(new_content)
