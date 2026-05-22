import re

with open('/Users/alexeiferreira/Website/algorithms/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

injection = """
<script>
// If embedded in an iframe (e.g. the homepage preview), remove the container's margins and borders
// so it seamlessly fills the mock window frame.
if (window.self !== window.top) {
  document.addEventListener("DOMContentLoaded", () => {
    const appC = document.getElementById('app-container');
    if (appC) {
      appC.style.margin = '0';
      appC.style.border = 'none';
      appC.style.boxShadow = 'none';
      appC.style.borderRadius = '0';
      appC.style.maxWidth = '100%';
      appC.style.height = '100vh';
      appC.style.aspectRatio = 'auto';
    }
  });
}
</script>
"""

if "window.self !== window.top" not in content:
    content = content.replace("</head>", injection + "</head>")
    with open('/Users/alexeiferreira/Website/algorithms/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Injected iframe style overrides into algorithms/index.html.")
else:
    print("Already injected.")
