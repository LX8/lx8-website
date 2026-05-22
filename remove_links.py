import os

directory = "/Users/alexeiferreira/Website"
strings_to_remove = [
    '<a href="/products/" class="text-link">Products</a>',
    '<a href="/products/">Products</a>',
    '<a href="/research/" class="text-link">Research</a>',
    '<a href="/research/">Research</a>',
    '<a href="/changelog/" class="text-link">Log</a>',
    '<a href="/changelog/">Log</a>',
    # Also remove any trailing spaces or newlines that might cause gaps
]

count = 0
for root, dirs, files in os.walk(directory):
    if '.git' in root or '.github' in root:
        continue
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            original_content = content
            for s in strings_to_remove:
                content = content.replace(s, "")
            
            # clean up blank lines created by removal
            lines = content.split('\n')
            clean_lines = []
            for line in lines:
                if line.strip() == "":
                    # check if the original line was a link that was just removed
                    # to avoid removing all blank lines, we can just skip it if it was empty, 
                    # but maybe just let it be. Actually, trailing whitespace is fine for HTML.
                    pass
            
            if content != original_content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                count += 1

print(f"Removed sensitive links from {count} HTML files.")
