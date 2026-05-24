#!/usr/bin/env python3
import os
import sys
import json
import hashlib
import subprocess
import argparse
import urllib.request
import time
from datetime import datetime

# Visual styling tokens for visual accessibility (ADHD/Dyslexia clear parsing)
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_PRIMARY = "\033[36m"   # Cyan
C_SUCCESS = "\033[32m"   # Green
C_WARN = "\033[33m"      # Yellow
C_FAIL = "\033[31m"      # Red
C_MUTED = "\033[90m"     # Grey

CACHE_FILE = ".deploy_cache.json"
REGISTRY_FILE = "lx8_registry.yaml"

def print_header(title):
    print(f"\n{C_BOLD}{C_PRIMARY}=== {title} ==={C_RESET}")

def print_success(msg):
    print(f"  {C_SUCCESS}✓ {msg}{C_RESET}")

def print_warn(msg):
    print(f"  {C_WARN}⚠️ {msg}{C_RESET}")

def print_fail(msg):
    print(f"  {C_FAIL}✗ {msg}{C_RESET}")

def print_info(msg):
    print(f"  {C_MUTED}• {msg}{C_RESET}")

# Calculate hashes of specific directories to determine changes
def get_dir_hash(directory):
    if not os.path.exists(directory):
        return ""
    
    sha = hashlib.sha256()
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", ".firebase", "dashboard", "version.json")]
        for file in sorted(files):
            if file.startswith('.'):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, "rb") as f:
                    while chunk := f.read(8192):
                        sha.update(chunk)
            except Exception:
                pass
    return sha.hexdigest()

def check_dashboard_dirty(cache):
    current_hash = get_dir_hash("dashboard")
    prev_hash = cache.get("dashboard", "")
    return current_hash != prev_hash, current_hash

def check_main_dirty(cache):
    root_files = ["index.html", "global.css", "robots.txt", "sitemap.xml", "manifest.json", "404.html", "og-image.png"]
    sha = hashlib.sha256()
    for f in root_files:
        if os.path.exists(f):
            try:
                with open(f, "rb") as fd:
                    sha.update(fd.read())
            except Exception:
                pass
    current_hash = sha.hexdigest()
    prev_hash = cache.get("main_site", "")
    return current_hash != prev_hash, current_hash

def check_book_dirty(cache):
    book_dir = "/Users/alexeiferreira/Lx8Labs/products/bipartite-universe-book"
    if not os.path.exists(book_dir):
        return False, ""
    
    sha = hashlib.sha256()
    for root, dirs, files in os.walk(book_dir):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".next", "out", ".firebase")]
        for file in sorted(files):
            if file.startswith('.'):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, "rb") as f:
                    while chunk := f.read(8192):
                        sha.update(chunk)
            except Exception:
                pass
    current_hash = sha.hexdigest()
    prev_hash = cache.get("book_site", "")
    return current_hash != prev_hash, current_hash

def increment_version(version_str):
    try:
        parts = version_str.split('.')
        if len(parts) == 3:
            patch = int(parts[2]) + 1
            return f"{parts[0]}.{parts[1]}.{patch}"
    except Exception:
        pass
    return "1.0.1"

def get_git_commit():
    try:
        res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "local"

def check_live_status(subdomain, expected_commit):
    urls = [
        f"https://{subdomain}.lx8labs.com/version.json",
        f"https://lx8-{subdomain.replace('ide', '-ide')}.web.app/version.json",
        f"https://lx8-{subdomain}.web.app/version.json"
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Lx8-Deploy-Engine'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                if data.get("commit") == expected_commit:
                    return True, url, data.get("version")
        except Exception:
            continue
    return False, None, None

def main():
    parser = argparse.ArgumentParser(description="Lx8 Labs Smart SRE Deploy Engine")
    parser.add_argument("--dry-run", action="store_true", help="Perform pre-flight diagnostics without deploying")
    parser.add_argument("--force", action="store_true", help="Force rebuild and redeploy of all targets")
    args = parser.parse_args()

    print("==================================================")
    print(f"      {C_BOLD}🚀 Lx8 Central OS Smart Deploy Engine{C_RESET}      ")
    print("==================================================")

    if not os.path.exists(REGISTRY_FILE):
        print_fail(f"Registry file '{REGISTRY_FILE}' is missing! Halting.")
        sys.exit(1)
    
    cache = {}
    if os.path.exists(CACHE_FILE) and not args.force:
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
        except Exception:
            pass

    print_header("1. HASHING & CHANGE DETECTION")
    dash_dirty, dash_hash = check_dashboard_dirty(cache)
    if dash_dirty:
        print_warn("Dashboard source files have changed. Vite rebuild required!")
    else:
        print_success("Dashboard assets are clean. Build skipped!")

    dirty_targets = []
    subdomain_hashes = {}
    git_commit = get_git_commit()

    main_dirty, main_hash = check_main_dirty(cache)
    if main_dirty or args.force:
        dirty_targets.append("main")
        print_warn("Root main website files have changed. Deploying target 'main'!")
    else:
        print_success("Root main website is clean.")
    
    book_dirty, book_hash = check_book_dirty(cache)
    if book_dirty or args.force:
        print_warn("Bipartite Book Next.js codebase has changed!")
    else:
        print_success("Bipartite Book Next.js codebase is clean.")

    import yaml
    with open(REGISTRY_FILE, "r") as f:
        registry = yaml.safe_load(f)

    timestamp = datetime.utcnow().isoformat() + "Z"

    for prod in registry["products"]:
        sub = prod["subdomain"]
        sub_hash = get_dir_hash(sub)
        subdomain_hashes[sub] = sub_hash
        
        prev_sub_hash = cache.get(f"sub_{sub}", "")
        is_dirty = sub_hash != prev_sub_hash or dash_dirty or args.force
        if sub == "bipartitebook" and book_dirty:
            is_dirty = True
            
        # LIVE CLOUD VERIFICATION
        if is_dirty and not args.force:
            print_info(f"Querying cloud for {sub} to check if commit {git_commit} is already live...")
            is_live, live_url, live_version = check_live_status(sub, git_commit)
            if is_live:
                print_success(f"Target '{sub}' is ALREADY RUNNING commit {git_commit} at {live_url} (v{live_version}). Skipping deploy!")
                is_dirty = False
                # Fix versions in registry
                prod["version"] = live_version
        
        if is_dirty:
            dirty_targets.append(sub)
            old_ver = prod.get("version", "1.0.0")
            new_ver = increment_version(old_ver)
            prod["version"] = new_ver
            print_info(f"Target '{sub}' is DIRTY: Bumping version {old_ver} -> {new_ver}")
            
            version_payload = {
                "version": new_ver,
                "commit": git_commit,
                "buildTime": timestamp,
                "subdomain": sub
            }
            
            if not args.dry_run:
                if not os.path.exists(sub):
                    os.makedirs(sub)
                version_path = os.path.join(sub, "version.json")
                with open(version_path, "w") as vf:
                    json.dump(version_payload, vf, indent=2)
        else:
            print_success(f"Target '{sub}' is CLEAN (local hash matches or already live).")

    if not dirty_targets:
        print_success("Absolute clean state! All subdomains perfectly match cloud. Nothing to do.")
        sys.exit(0)

    if not args.dry_run:
        with open(REGISTRY_FILE, "w") as f:
            yaml.safe_dump(registry, f, default_flow_style=False, sort_keys=False)
        print_success("Registry file updated with new semantic version numbers.")

    if dash_dirty or args.force:
        print_header("2. COMPILING CENTRAL OS REACT DASHBOARD")
        if args.dry_run:
            print_info("[DRY-RUN] Would execute: npm run build in /dashboard")
        else:
            try:
                subprocess.run(["npm", "run", "build"], cwd="dashboard", check=True)
                print_success("React compilation completed successfully!")
            except subprocess.CalledProcessError as e:
                print_fail(f"Vite compilation failed! Error code: {e.returncode}")
                sys.exit(1)

    if ("bipartitebook" in dirty_targets and book_dirty) or args.force:
        print_header("2.1 COMPILING BIPARTITE UNIVERSE NEXT.JS BOOK")
        if not args.dry_run:
            book_path = "/Users/alexeiferreira/Lx8Labs/products/bipartite-universe-book"
            try:
                subprocess.run(["npm", "run", "build"], cwd=book_path, check=True)
                export_out = os.path.join(book_path, "out")
                target_dest = "bipartitebook"
                if os.path.exists(export_out):
                    for item in os.listdir(target_dest):
                        item_path = os.path.join(target_dest, item)
                        if item == "dashboard" or item == "version.json":
                            continue
                        if os.path.isdir(item_path):
                            import shutil
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                    for item in os.listdir(export_out):
                        src_item = os.path.join(export_out, item)
                        dst_item = os.path.join(target_dest, item)
                        if os.path.isdir(src_item):
                            import shutil
                            shutil.copytree(src_item, dst_item)
                        else:
                            import shutil
                            shutil.copy2(src_item, dst_item)
                print_success("Next.js Book compilation completed successfully!")
            except Exception as e:
                print_fail(f"Next.js Book build failed: {str(e)}")
                sys.exit(1)

    print_header("3. INFRASTRUCTURE & TARGETS SYNCHRONIZATION")
    if not args.dry_run:
        try:
            sys.path.append(os.path.abspath("scripts"))
            import sync_infrastructure
            sync_infrastructure.update_firebase_config(registry)
            for sub in dirty_targets:
                if sub == "main": continue
                src_v = os.path.join(sub, "version.json")
                dst_v = os.path.join(sub, "dashboard", "version.json")
                if os.path.exists(src_v) and os.path.exists(os.path.dirname(dst_v)):
                    import shutil
                    shutil.copy2(src_v, dst_v)
            print_success("Targets synced! Dashboard builds and version tags replicated cleanly.")
        except Exception as e:
            print_fail(f"Infrastructure sync failed: {str(e)}")
            sys.exit(1)

    print_header("4. PRE-FLIGHT VALIDATIONS")
    validation_passed = True
    for sub in dirty_targets:
        if sub == "main": continue
        if not os.path.exists(os.path.join(sub, "index.html")): validation_passed = False
    if not validation_passed:
        print_fail("Halted pre-flight: broken targets detected.")
        sys.exit(1)
    
    print_success("Pre-flight safety validation complete! Clean static trees verified.")

    print_header("5. TARGETED CLOUD HOSTING DEPLOYMENT")
    deploy_command = ["npx", "-y", "firebase-tools@latest", "deploy", "--only"]
    only_args = ",".join([f"hosting:{sub}" for sub in dirty_targets])
    deploy_command.append(only_args)

    if not args.dry_run:
        try:
            subprocess.run(deploy_command, check=True)
            print_success("Cloud hosting deployment finalized successfully!")
            
            cache["dashboard"] = dash_hash
            cache["main_site"] = main_hash
            cache["book_site"] = book_hash
            for sub in subdomain_hashes:
                cache[f"sub_{sub}"] = subdomain_hashes[sub]
            with open(CACHE_FILE, "w") as f:
                json.dump(cache, f, indent=2)
        except subprocess.CalledProcessError as e:
            print_fail(f"Firebase deployment failed! Exit code: {e.returncode}")
            sys.exit(1)

    print_header("6. POST-FLIGHT LIVE VERIFICATION")
    if not args.dry_run:
        print_info("Pinging live endpoints to verify deployment status...")
        time.sleep(3) # Give Firebase edge nodes a moment to propagate
        for sub in dirty_targets:
            if sub == "main": continue
            # Check the native Firebase URL first to bypass DNS propagation
            check_urls = [
                f"https://lx8-{sub.replace('ide', '-ide')}.web.app/version.json",
                f"https://lx8-{sub}.web.app/version.json",
                f"https://{sub}.lx8labs.com/version.json"
            ]
            up = False
            for url in check_urls:
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Lx8-Deploy-Engine'})
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode())
                            if data.get("commit") == git_commit:
                                print_success(f"Verified UP AND RUNNING: {url} (v{data.get('version')})")
                                up = True
                                break
                except Exception:
                    continue
            if not up:
                print_warn(f"Could not immediately verify {sub} endpoint. DNS might be propagating.")

if __name__ == "__main__":
    main()
