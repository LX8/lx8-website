#!/usr/bin/env python3
import yaml
import json
import os
import shutil

REGISTRY_FILE = "lx8_registry.yaml"
FIREBASE_JSON_FILE = "firebase.json"
FIREBASERC_FILE = ".firebaserc"
PROJECT_ID = "lx8-labs-website"

def sync_assets(target_dir):
    # Ensure target directory exists
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # Copy a11y.js
    src_a11y = "a11y.js"
    dst_a11y = os.path.join(target_dir, "a11y.js")
    if os.path.exists(src_a11y):
        shutil.copy2(src_a11y, dst_a11y)
        
    # Copy firebase-init.js
    src_fb = "firebase-init.js"
    dst_fb = os.path.join(target_dir, "firebase-init.js")
    if os.path.exists(src_fb):
        shutil.copy2(src_fb, dst_fb)
        
    # Copy i18n/
    src_i18n = "i18n"
    dst_i18n = os.path.join(target_dir, "i18n")
    if os.path.exists(src_i18n):
        if os.path.exists(dst_i18n):
            shutil.rmtree(dst_i18n)
        shutil.copytree(src_i18n, dst_i18n)

    # Copy built dashboard dist to subdomain/dashboard/
    src_dash = os.path.join("dashboard", "dist")
    dst_dash = os.path.join(target_dir, "dashboard")
    if os.path.exists(src_dash):
        if os.path.exists(dst_dash):
            shutil.rmtree(dst_dash)
        shutil.copytree(src_dash, dst_dash)
        print(f"  -> Synced Dashboard dist to {dst_dash}")

def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        print(f"Error: {REGISTRY_FILE} not found.")
        return None
    with open(REGISTRY_FILE, "r") as f:
        return yaml.safe_load(f)

def update_firebase_config(registry_data):
    # 1. Update firebase.json
    if os.path.exists(FIREBASE_JSON_FILE):
        with open(FIREBASE_JSON_FILE, "r") as f:
            fb_json = json.load(f)
    else:
        fb_json = {"hosting": []}
    
    # Keep non-hosting configs, overwrite hosting
    new_hosting = []
    
    # Add root main website target (lx8labs.com primary site)
    new_hosting.append({
        "target": "main",
        "public": ".",
        "ignore": [
            "firebase.json",
            "**/.*",
            "**/node_modules/**",
            "aimem/**",
            "tupa/**",
            "tupaide/**",
            "suit/**",
            "bipartitebook/**",
            "installations/**",
            "mattermem/**",
            "dashboard/**",
            ".deploy_cache.json"
        ],
        "rewrites": [
            {
                "source": "**",
                "destination": "/index.html"
            }
        ],
        "headers": [
            {
                "source": "**/*.@(js|css|png|jpg|jpeg|gif|svg|woff|woff2)",
                "headers": [
                    {
                        "key": "Cache-Control",
                        "value": "max-age=31536000"
                    }
                ]
            },
            {
                "source": "**/*.html",
                "headers": [
                    {
                        "key": "Cache-Control",
                        "value": "no-cache"
                    }
                ]
            }
        ]
    })
    
    # 2. Update .firebaserc
    if os.path.exists(FIREBASERC_FILE):
        with open(FIREBASERC_FILE, "r") as f:
            fb_rc = json.load(f)
    else:
        fb_rc = {"projects": {"default": PROJECT_ID}, "targets": {PROJECT_ID: {"hosting": {}}}}
    
    if "targets" not in fb_rc:
        fb_rc["targets"] = {PROJECT_ID: {"hosting": {}}}
    if PROJECT_ID not in fb_rc["targets"]:
        fb_rc["targets"][PROJECT_ID] = {"hosting": {}}
        
    targets = fb_rc["targets"][PROJECT_ID]["hosting"]
    targets["main"] = [PROJECT_ID]
 
    print("Syncing infrastructure from registry...")
    for product in registry_data.get("products", []):
        site_id = product["id"]
        target_name = product["subdomain"]
        
        # Add to firebase.json
        new_hosting.append({
            "target": target_name,
            "public": target_name,
            "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
            "rewrites": [
                {
                    "source": "/dashboard/**",
                    "destination": "/dashboard/index.html"
                },
                {
                    "source": "**",
                    "destination": "/index.html"
                }
            ],
            "headers": [
                {
                    "source": "**/*.@(js|css|png|jpg|jpeg|gif|svg|woff|woff2)",
                    "headers": [
                        {
                            "key": "Cache-Control",
                            "value": "max-age=31536000"
                        }
                    ]
                },
                {
                    "source": "**/*.html",
                    "headers": [
                        {
                            "key": "Cache-Control",
                            "value": "no-cache"
                        }
                    ]
                }
            ]
        })
        
        # Add to .firebaserc
        targets[target_name] = [site_id]
        
        # Sync translation and accessibility assets
        sync_assets(target_name)
        
        print(f"✓ Configured and synced assets for {site_id} -> {target_name}.lx8labs.com")

    fb_json["hosting"] = new_hosting
    
    with open(FIREBASE_JSON_FILE, "w") as f:
        json.dump(fb_json, f, indent=2)
    
    with open(FIREBASERC_FILE, "w") as f:
        json.dump(fb_rc, f, indent=2)
        
    print("\nSuccessfully updated firebase.json and .firebaserc")

def print_manual_dns_instructions(registry_data):
    print("\n" + "="*60)
    print("ACTION REQUIRED: DNS & FIREBASE CONSOLE LINKING")
    print("="*60)
    print("Because custom domain linking requires domain verification,")
    print("you must do the following in the Firebase Console:")
    print(f"URL: https://console.firebase.google.com/project/{PROJECT_ID}/hosting/sites\n")
    
    print(f"{'Site ID':<20} | {'Custom Domain':<25} | {'Status'}")
    print("-" * 60)
    for product in registry_data.get("products", []):
        site_id = product["id"]
        domain = f"{product['subdomain']}.lx8labs.com"
        print(f"{site_id:<20} | {domain:<25} | Needs linking")
        
    print("\nFor each site above:")
    print("  1. Click 'Add Custom Domain'")
    print("  2. Enter the Custom Domain name")
    print("  3. Firebase will provide IP addresses (e.g., 199.36.158.100)")
    print("  4. Add those as 'A' records in your Google Domains dashboard")
    print("="*60)

if __name__ == "__main__":
    registry = load_registry()
    if registry:
        update_firebase_config(registry)
        print_manual_dns_instructions(registry)
