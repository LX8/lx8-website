import os

directory = "/Users/alexeiferreira/Website"
old_csp = "connect-src 'self';"
new_csp = "connect-src 'self' https://identitytoolkit.googleapis.com https://securetoken.googleapis.com;"

count = 0
for root, dirs, files in os.walk(directory):
    if '.git' in root or '.github' in root:
        continue
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if old_csp in content:
                new_content = content.replace(old_csp, new_csp)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                count += 1

print(f"Patched CSP in {count} HTML files to allow Firebase Auth.")
