import re

html_path = '/Users/alexeiferreira/Lx8Labs/internal/Website/courses/index.html'
with open(html_path, 'r') as f:
    content = f.read()

# Replace the inner HTML of <div class="courses-grid">
grid_start = content.find('<div class="courses-grid">') + len('<div class="courses-grid">')
grid_end = content.find('</div>\n</section>\n\n<section class="cta">')

loading_html = """
    <!-- Courses loaded dynamically -->
    <div id="courses-loader" style="grid-column: 1 / -1; padding: 4rem 0; text-align: center;">
      <div style="display: inline-block; width: 32px; height: 32px; border: 2px solid var(--border); border-top-color: var(--ind3); border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
      <style>@keyframes spin { to { transform: rotate(360deg); } }</style>
    </div>
"""

new_content = content[:grid_start] + loading_html + content[grid_end:]

# Add script just before </body>
script_injection = """
<script type="module">
  import { db, collection, getDocs } from '../firebase-init.js';

  async function loadCourses() {
    const grid = document.querySelector('.courses-grid');
    try {
      const qs = await getDocs(collection(db, 'courses'));
      const loader = document.getElementById('courses-loader');
      if(loader) loader.remove();

      let i = 0;
      qs.forEach(doc => {
        const d = doc.data();
        let delayClass = '';
        if (i % 3 === 1) delayClass = 'd1';
        else if (i % 3 === 2) delayClass = 'd2';

        const statusClass = d.status === 'live' ? 'cs-live' : (d.status === 'upcoming' ? 'cs-soon' : 'cs-wait');
        const statusText = d.status === 'live' ? '● Live' : (d.status === 'upcoming' ? 'Coming soon' : 'In development');
        
        let currHtml = '<span class="c-curr-h">Curriculum</span>';
        if (d.curriculum && Array.isArray(d.curriculum)) {
            d.curriculum.forEach(item => {
                currHtml += `<span class="c-curr-item">${item}</span>`;
            });
        }

        const html = `
          <div class="c-head">
            <div class="c-ico">${d.icon || ''}</div>
            <div class="c-meta">
              <span class="c-level">${d.level || ''}</span>
              <span class="c-name">${d.title}</span>
            </div>
          </div>
          <p class="c-desc">${d.description || ''}</p>
          <div class="c-curr">${currHtml}</div>
          <div class="c-foot">
            <div class="c-foot-left">
              <span class="c-dur">⏱ ${d.duration || ''}</span>
              <span class="c-mode">💻 ${d.mode || ''}</span>
            </div>
            <span class="c-status ${statusClass}">${statusText}</span>
          </div>
        `;
        
        const art = document.createElement('article');
        art.className = `course-card r ${delayClass}`;
        art.dataset.tag = d.tag || '';
        art.style.setProperty('--c', d.color || '#6366f1');
        art.innerHTML = html;
        
        // Add spotlight logic
        art.addEventListener('pointermove', e => {
          const rect = art.getBoundingClientRect();
          art.style.setProperty('--mx', (e.clientX - rect.left) + 'px');
          art.style.setProperty('--my', (e.clientY - rect.top) + 'px');
        });
        
        grid.appendChild(art);
        i++;
      });
      
      // Re-trigger intersection observer for newly added cards
      if (window.ro) {
        document.querySelectorAll('.course-card.r').forEach(el => window.ro.observe(el));
      }
    } catch (e) {
      console.error("Error loading courses", e);
      grid.innerHTML = '<div style="grid-column: 1/-1; color: var(--text2); text-align: center; padding: 2rem;">Failed to load courses. Please try again later.</div>';
    }
  }

  loadCourses();
</script>
</body>
"""

new_content = new_content.replace('</body>', script_injection)

# Also expose `ro` in the global scope so our fetch script can use it
new_content = new_content.replace('const ro = new IntersectionObserver', 'window.ro = new IntersectionObserver')

with open(html_path, 'w') as f:
    f.write(new_content)
    
print("Updated courses/index.html to fetch dynamically!")
