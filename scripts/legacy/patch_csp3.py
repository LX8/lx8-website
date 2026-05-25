import os

directory = "/Users/alexeiferreira/Lx8Labs/internal/Website"
# We'll just search for the end of the CSP and inject frame-src
insertion = " frame-src 'self' https://lx8-labs-website.firebaseapp.com;"

count = 0
for root, dirs, files in os.walk(directory):
    if '.git' in root or '.github' in root:
        continue
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Find the CSP meta tag
            csp_start = content.find('<meta http-equiv="Content-Security-Policy" content="')
            if csp_start != -1:
                csp_end = content.find('">', csp_start)
                if csp_end != -1:
                    csp_value = content[csp_start:csp_end]
                    if "frame-src" not in csp_value:
                        new_csp_value = csp_value + insertion
                        new_content = content[:csp_start] + new_csp_value + content[csp_end:]
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        count += 1

print(f"Patched frame-src in {count} HTML files for Firebase Auth iframe.")
