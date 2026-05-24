#!/usr/bin/env python3
import os
import requests
import sys

# Subdomains mapped to Firebase Hosting IPs
SUBDOMAINS = [
    "aimem",
    "tupa",
    "tupaide",
    "suit",
    "bipartitebook",
    "installations",
    "mattermem"
]

FIREBASE_IPS = ["199.36.158.100", "199.36.158.100"] # Both A records commonly required by Firebase
ROOT_DOMAIN = "lx8labs.com"

def get_env_or_exit(key):
    val = os.environ.get(key)
    if not val:
        print(f"ERROR: {key} environment variable is missing.", file=sys.stderr)
        print("Please export it or add it to your GitHub Secrets.", file=sys.stderr)
        sys.exit(1)
    return val

def sync_dns():
    print("==================================================")
    print("      🚀 Lx8 Cloudflare DNS Automation Engine    ")
    print("==================================================")

    api_token = get_env_or_exit("CLOUDFLARE_API_TOKEN")
    zone_id = get_env_or_exit("CLOUDFLARE_ZONE_ID")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    # 1. Fetch existing records
    print(f"• Fetching current DNS records for {ROOT_DOMAIN}...")
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=A&per_page=100"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to connect to Cloudflare: {response.text}")
        sys.exit(1)

    existing_records = response.json().get('result', [])
    existing_map = {}
    
    for record in existing_records:
        name = record['name']
        ip = record['content']
        if name not in existing_map:
            existing_map[name] = []
        existing_map[name].append(ip)

    # 2. Reconcile records
    for subdomain in SUBDOMAINS:
        full_name = f"{subdomain}.{ROOT_DOMAIN}"
        
        # Check if it already exists correctly
        if full_name in existing_map and FIREBASE_IPS[0] in existing_map[full_name]:
            print(f"  ✓ {full_name} is already pointing to Firebase.")
            continue

        print(f"  ⚠️ {full_name} is missing or incorrect. Creating 'A' record...")
        
        # Create record for first IP
        payload = {
            "type": "A",
            "name": full_name,
            "content": FIREBASE_IPS[0],
            "ttl": 1, # Auto
            "proxied": True
        }
        
        post_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        create_res = requests.post(post_url, headers=headers, json=payload)
        
        if create_res.status_code == 200:
            print(f"  [SUCCESS] Created {full_name} -> {FIREBASE_IPS[0]}")
        else:
            print(f"  [ERROR] Failed to create {full_name}: {create_res.text}")

    print("==================================================")
    print("  DNS Synchronization Complete.")
    print("==================================================")

if __name__ == "__main__":
    sync_dns()
