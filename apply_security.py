import os

directory = "/Users/alexeiferreira/Website"

security_headers = """  <!-- Zero-Cost Security Hardening -->
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.bunny.net; font-src 'self' https://fonts.bunny.net https://fonts.gstatic.com; img-src 'self' data: https://avatars.githubusercontent.com; connect-src 'self'; base-uri 'self';">
  <meta name="referrer" content="no-referrer">
  <script>if (window !== window.top) window.top.location = window.location;</script>
"""

count = 0
for root, dirs, files in os.walk(directory):
    if '.git' in root or '.github' in root:
        continue
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if "Zero-Cost Security Hardening" in content:
                continue
                
            head_idx = content.lower().find("<head>")
            if head_idx != -1:
                insert_idx = head_idx + 6
                new_content = content[:insert_idx] + "\n" + security_headers + content[insert_idx:]
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                count += 1
                print(f"Secured: {path}")

print(f"Injected security headers into {count} HTML files.")
