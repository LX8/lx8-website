import re

html_path = '/Users/alexeiferreira/Lx8Labs/internal/Website/courses/index.html'
with open(html_path, 'r') as f:
    content = f.read()

# Replace the static cards cache
old_script = """  // Filter buttons
  const cards = document.querySelectorAll('.course-card');
  document.querySelectorAll('.filter').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const tag = btn.dataset.tag;
      cards.forEach(c => {
        const tags = (c.dataset.tag || '').split(' ');
        c.classList.toggle('c-card-hide', tag !== 'all' && !tags.includes(tag));
      });
    });
  });"""

new_script = """  // Filter buttons
  document.querySelectorAll('.filter').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const tag = btn.dataset.tag;
      document.querySelectorAll('.course-card').forEach(c => {
        const tags = (c.dataset.tag || '').split(' ');
        c.classList.toggle('c-card-hide', tag !== 'all' && !tags.includes(tag));
      });
    });
  });"""

content = content.replace(old_script, new_script)

with open(html_path, 'w') as f:
    f.write(content)
    
print("Fixed filter buttons!")
