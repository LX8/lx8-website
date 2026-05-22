import json
import sys

try:
    with open('lighthouse-report.json', 'r') as f:
        data = json.load(f)
        
    categories = data.get('categories', {})
    print("--- Lighthouse Scores ---")
    for cat, details in categories.items():
        score = details.get('score', 0) * 100
        print(f"{details.get('title')}: {score:.0f}/100")
        
    print("\n--- Top Opportunities & Diagnostics ---")
    audits = data.get('audits', {})
    for audit_id, audit in audits.items():
        # Print failed audits that have a score of 0 or are performance metrics
        if audit.get('score') == 0 or (audit.get('score') is not None and audit.get('score') < 0.9 and audit.get('scoreDisplayMode') != 'notApplicable'):
            print(f"- {audit.get('title')} ({audit_id}): {audit.get('displayValue', '')}")
            
except FileNotFoundError:
    print("Lighthouse report not found yet.")
