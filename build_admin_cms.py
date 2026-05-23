import re

with open('/Users/alexeiferreira/Lx8Labs/internal/Website/admin/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Firebase logic at the top of the body
firebase_script = """
<script type="module">
  import { auth, db, signInWithEmailAndPassword, onAuthStateChanged, signOut, collection, getDocs, doc, setDoc, updateDoc } from '../firebase-init.js';

  const authOverlay = document.getElementById('auth-overlay');
  const logoutBtn = document.getElementById('logout-btn');

  // Simple UI Auth state
  onAuthStateChanged(auth, (user) => {
    if (user) {
      authOverlay.style.display = 'none';
      loadCourses();
    } else {
      authOverlay.innerHTML = `
        <div style="background: var(--bg1); padding: 2rem; border-radius: var(--r); border: 1px solid var(--border); width: 320px; text-align: center;">
          <h2 style="color: #fff; margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">Admin Login</h2>
          <input type="email" id="email" placeholder="Email" style="width: 100%; padding: 0.8rem; margin-bottom: 1rem; background: var(--bg); border: 1px solid var(--border); color: #fff; border-radius: 4px;" />
          <input type="password" id="password" placeholder="Password" style="width: 100%; padding: 0.8rem; margin-bottom: 1rem; background: var(--bg); border: 1px solid var(--border); color: #fff; border-radius: 4px;" />
          <button id="login-btn" class="btn-action btn-primary" style="width: 100%; justify-content: center;">Sign In</button>
          <p id="auth-err" style="color: #f87171; font-size: 0.8rem; margin-top: 1rem; display: none;"></p>
        </div>
      `;
      document.getElementById('login-btn').onclick = () => {
        const e = document.getElementById('email').value;
        const p = document.getElementById('password').value;
        signInWithEmailAndPassword(auth, e, p).catch(err => {
          const errEl = document.getElementById('auth-err');
          errEl.textContent = err.message;
          errEl.style.display = 'block';
        });
      };
    }
  });

  logoutBtn.onclick = () => signOut(auth);

  window.editCourse = function(id) {
    const course = window.courseData.find(c => c.id === id);
    if(!course) return;
    document.getElementById('modal-id').value = course.id;
    document.getElementById('modal-title').value = course.title || '';
    document.getElementById('modal-desc').value = course.description || '';
    document.getElementById('modal-workload').value = course.workload || '';
    document.getElementById('modal-status').value = course.status || 'live';
    document.getElementById('course-modal').style.display = 'flex';
  }

  window.closeModal = function() {
    document.getElementById('course-modal').style.display = 'none';
  }

  window.saveCourse = async function() {
    const id = document.getElementById('modal-id').value || crypto.randomUUID();
    const data = {
      title: document.getElementById('modal-title').value,
      description: document.getElementById('modal-desc').value,
      workload: document.getElementById('modal-workload').value,
      status: document.getElementById('modal-status').value
    };
    await setDoc(doc(db, 'courses', id), data);
    closeModal();
    loadCourses();
  }

  window.openNewCourseModal = function() {
    document.getElementById('modal-id').value = '';
    document.getElementById('modal-title').value = '';
    document.getElementById('modal-desc').value = '';
    document.getElementById('modal-workload').value = '';
    document.getElementById('modal-status').value = 'upcoming';
    document.getElementById('course-modal').style.display = 'flex';
  }

  async function loadCourses() {
    const snap = await getDocs(collection(db, 'courses'));
    window.courseData = snap.docs.map(d => ({id: d.id, ...d.data()}));
    
    const tbody = document.getElementById('courses-tbody');
    tbody.innerHTML = window.courseData.map(c => `
      <tr>
        <td><strong>${c.title}</strong></td>
        <td>${c.workload || '-'}</td>
        <td><span class="badge ${c.status === 'live' ? 'active' : 'inactive'}">${c.status || 'upcoming'}</span></td>
        <td>
          <button onclick="editCourse('${c.id}')" class="btn-action">Edit</button>
        </td>
      </tr>
    `).join('');
  }
</script>
<style>
  #course-modal { position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 2000; display: none; align-items: center; justify-content: center; }
  .modal-content { background: var(--bg1); padding: 2rem; border-radius: var(--r); border: 1px solid var(--border); width: 500px; max-width: 90%; }
  .modal-content input, .modal-content textarea, .modal-content select { width: 100%; padding: 0.8rem; margin-bottom: 1rem; background: var(--bg); border: 1px solid var(--border); color: #fff; border-radius: 4px; font-family: 'Inter', sans-serif; }
</style>
<div id="course-modal">
  <div class="modal-content">
    <h2 style="color: #fff; margin-bottom: 1.5rem; font-family: 'Space Grotesk', sans-serif;">Edit Course</h2>
    <input type="hidden" id="modal-id" />
    <input type="text" id="modal-title" placeholder="Course Title" />
    <textarea id="modal-desc" placeholder="Course Description" rows="4"></textarea>
    <input type="text" id="modal-workload" placeholder="Workload (e.g. PT18H)" />
    <select id="modal-status">
      <option value="live">Live</option>
      <option value="upcoming">Upcoming</option>
    </select>
    <div style="display: flex; gap: 1rem; justify-content: flex-end;">
      <button onclick="closeModal()" class="btn-action">Cancel</button>
      <button onclick="saveCourse()" class="btn-action btn-primary">Save Course</button>
    </div>
  </div>
</div>
"""

html = html.replace('<script defer src="/a11y.js"></script>', '<script defer src="/a11y.js"></script>\n' + firebase_script)

# 2. Replace the dashboard grid with the Courses CMS
courses_cms = """
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">Manage Courses</div>
        <button onclick="openNewCourseModal()" class="btn-action btn-primary">+ Add Course</button>
      </div>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Workload</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="courses-tbody">
            <tr><td colspan="4" style="text-align: center;">Loading courses...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
"""

# We'll use regex to replace everything inside .dashboard-grid
html = re.sub(r'<div class="dashboard-grid">.*?</div>\s*</div>\s*</main>', 
              f'<div class="dashboard-grid" style="grid-template-columns: 1fr;">\n{courses_cms}\n</div>\n</main>', 
              html, flags=re.DOTALL)

with open('/Users/alexeiferreira/Lx8Labs/internal/Website/admin/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Admin CMS UI injected.")
