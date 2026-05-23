import re

# 1. Update index.html .al-frame
with open('/Users/alexeiferreira/Lx8Labs/internal/Website/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace iframe inline style
content = content.replace(
    'style="width:100%; height:88vh; border:none; display:block;"',
    'style="width:100%; flex: 1; border:none; display:block;"'
)

# Replace .al-frame CSS
old_frame_css = ".al-frame { margin-top: 2.5rem; border-radius: 16px; overflow: hidden; border: 1px solid var(--border); background: #050511; box-shadow: 0 30px 80px rgba(99,102,241,0.08); }"
new_frame_css = ".al-frame { margin: 4rem auto; border-radius: 16px; overflow: hidden; border: 1px solid var(--border); background: #050511; box-shadow: 0 40px 100px rgba(99,102,241,0.12); width: 100%; max-width: 900px; aspect-ratio: 1 / 1; display: flex; flex-direction: column; }"
content = content.replace(old_frame_css, new_frame_css)

with open('/Users/alexeiferreira/Lx8Labs/internal/Website/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

# 2. Update algorithms/index.html #app-container
with open('/Users/alexeiferreira/Lx8Labs/internal/Website/algorithms/index.html', 'r', encoding='utf-8') as f:
    content2 = f.read()

old_app_css = """    #app-container {
      max-width: 1200px;
      margin: 100px auto 4rem;
      height: 75vh;
      min-height: 600px;
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 30px 60px rgba(0,0,0,0.5);
      position: relative;
      z-index: 10;
    }"""
new_app_css = """    #app-container {
      max-width: 940px;
      margin: 6rem auto 4rem;
      aspect-ratio: 1 / 1;
      height: auto;
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 40px 100px rgba(0,0,0,0.6);
      position: relative;
      z-index: 10;
    }"""
content2 = content2.replace(old_app_css, new_app_css)

with open('/Users/alexeiferreira/Lx8Labs/internal/Website/algorithms/index.html', 'w', encoding='utf-8') as f:
    f.write(content2)

print("Updated index.html and algorithms/index.html containers to be elegant squares.")
