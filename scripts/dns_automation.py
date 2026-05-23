#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.error
import yaml

# Visual logging tokens
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_PRIMARY = "\033[36m"
C_SUCCESS = "\033[32m"
C_WARN = "\033[33m"
C_FAIL = "\033[31m"

REGISTRY_FILE = "lx8_registry.yaml"

def main():
    print("==================================================")
    print(f"      {C_BOLD}☁️ Lx8 Cloudflare DNS Automation Engine{C_RESET}      ")
    print("==================================================")

    # 1. Retrieve API Keys from environment variables
    # (To maintain absolute zero-cost and local SRE security, we read from environment variables)
    cf_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    cf_zone = os.environ.get("CLOUDFLARE_ZONE_ID")

    if not cf_token or not cf_zone:
        print(f"  {C_WARN}Credentials Missing! Please set environment variables:{C_RESET}")
        print("  export CLOUDFLARE_API_TOKEN=\"your-token-here\"")
        print("  export CLOUDFLARE_ZONE_ID=\"your-zone-id-here\"\n")
        print(f"  {C_PRIMARY}Step 1: Point your nameservers to Cloudflare (100% Free).{C_RESET}")
        print(f"  {C_PRIMARY}Step 2: Generate an API Token with 'Zone.DNS' edit permissions.{C_RESET}")
        print(f"  {C_PRIMARY}Step 3: Run this script to sync all subdomains instantly!{C_RESET}")
        sys.exit(0)

    # 2. Load Registry
    if not os.path.exists(REGISTRY_FILE):
        print(f"  {C_FAIL}✗ Registry file {REGISTRY_FILE} missing.{C_RESET}")
        sys.exit(1)

    with open(REGISTRY_FILE, "r") as f:
        registry = yaml.safe_load(f)

    # Hardcoded Firebase Hosting IPs for custom subdomains
    firebase_ips = ["199.36.158.100"] 

    print(f"\n{C_BOLD}1. FETCHING EXISTING CLOUDFLARE DNS RECORDS{C_RESET}")
    url = f"https://api.cloudflare.com/client/v4/zones/{cf_zone}/dns_records?type=A&per_page=100"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {cf_token}",
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            existing_records = {rec["name"]: rec["id"] for rec in data.get("result", [])}
            print(f"  {C_SUCCESS}✓ Retrieved {len(existing_records)} existing DNS records.{C_RESET}")
    except urllib.error.HTTPError as e:
        print(f"  {C_FAIL}✗ Failed to fetch records: {e.code} - {e.read().decode()}{C_RESET}")
        sys.exit(1)

    print(f"\n{C_BOLD}2. SYNCHRONIZING SUBDOMAINS{C_RESET}")
    for prod in registry.get("products", []):
        sub = prod["subdomain"]
        domain = f"{sub}.lx8labs.com"
        
        # Check if record already exists
        record_id = existing_records.get(domain)

        for ip in firebase_ips:
            payload = {
                "type": "A",
                "name": domain,
                "content": ip,
                "ttl": 3600,
                "proxied": False  # Firebase requires direct A records for SSL handshakes
            }

            if record_id:
                # Update existing record
                print(f"  • Updating '{domain}' -> {ip}")
                action_url = f"https://api.cloudflare.com/client/v4/zones/{cf_zone}/dns_records/{record_id}"
                method = "PUT"
            else:
                # Create new record
                print(f"  • Creating '{domain}' -> {ip}")
                action_url = f"https://api.cloudflare.com/client/v4/zones/{cf_zone}/dns_records"
                method = "POST"

            action_req = urllib.request.Request(
                action_url,
                data=json.dumps(payload).encode(),
                headers={
                    "Authorization": f"Bearer {cf_token}",
                    "Content-Type": "application/json"
                },
                method=method
            )

            try:
                with urllib.request.urlopen(action_req) as action_res:
                    print(f"    {C_SUCCESS}✓ Successfully synced {domain} to {ip}{C_RESET}")
            except urllib.error.HTTPError as e:
                print(f"    {C_FAIL}✗ Failed syncing {domain}: {e.read().decode()}{C_RESET}")

    print("\n==================================================")
    print(f"      {C_SUCCESS}✓ DNS Synchronization Completed Successfully!{C_RESET}     ")
    print("==================================================")

if __name__ == "__main__":
    main()
