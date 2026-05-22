import os

directory = "/Users/alexeiferreira/Website"

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
            
            # For class="text-link" footers
            if '<a href="/courses/" class="text-link">Courses</a>' in content:
                content = content.replace(
                    '<a href="/courses/" class="text-link">Courses</a>',
                    '<a href="/courses/" class="text-link">Courses</a>\n    <a href="/products/" class="text-link">Products</a>\n    <a href="/changelog/" class="text-link">Log</a>'
                )
            
            # For plain footers
            elif '<a href="/courses/">Courses</a>' in content:
                content = content.replace(
                    '<a href="/courses/">Courses</a>',
                    '<a href="/courses/">Courses</a>\n    <a href="/products/">Products</a>\n    <a href="/changelog/">Log</a>'
                )
            
            if content != original_content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                count += 1

print(f"Restored links in {count} HTML files.")
