import re
import json
import urllib.request
import uuid

# 1. Read courses/index.html and extract the Schema.org JSON
with open('/Users/alexeiferreira/Website/courses/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'<script type="application/ld\+json">\s*({.*?})\s*</script>', content, re.DOTALL)
if not match:
    print("Schema JSON not found!")
    exit(1)

schema_data = json.loads(match.group(1))
courses = []
for item in schema_data['@graph'][0]['itemListElement']:
    course_item = item['item']
    title = course_item.get('name', '')
    desc = course_item.get('description', '')
    workload = course_item.get('hasCourseInstance', {}).get('courseWorkload', '')
    category = course_item.get('offers', {}).get('category', 'Upcoming')
    if category == 'Live':
        status = 'live'
    else:
        status = 'upcoming'

    courses.append({
        'title': title,
        'description': desc,
        'workload': workload,
        'status': status
    })

print(f"Found {len(courses)} courses to seed.")

# 2. Push to Firestore via REST API
PROJECT_ID = 'lx8-labs-website'
BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/courses"

for c in courses:
    doc_id = str(uuid.uuid4())
    url = f"{BASE_URL}?documentId={doc_id}"
    
    # Construct Firestore document structure
    doc_data = {
        "fields": {
            "title": {"stringValue": c['title']},
            "description": {"stringValue": c['description']},
            "workload": {"stringValue": c['workload']},
            "status": {"stringValue": c['status']}
        }
    }
    
    req = urllib.request.Request(url, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, data=json.dumps(doc_data).encode('utf-8')) as response:
            print(f"Created {c['title']} - {response.status}")
    except urllib.error.HTTPError as e:
        print(f"Failed to create {c['title']}: {e.code} {e.reason}")
        print(e.read().decode())
