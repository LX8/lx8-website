#!/usr/bin/env python3
import os
import sys
import json
import hashlib
import subprocess
import argparse
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
    for root, _, files in os.walk(directory):
        # Exclude build output or dependency folders to avoid false dirty hits
        if "node_modules" in root or "dist" in root or ".firebase" in root or "dashboard" in root or "version.json" in root:
            continue
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
    for root, _, files in os.walk(book_dir):
        if "node_modules" in root or ".next" in root or "out" in root or ".firebase" in root:
            continue
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


# Increment patch version (e.g. 1.0.2 -> 1.0.3)
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

def main():
    parser = argparse.ArgumentParser(description="Lx8 Labs Smart SRE Deploy Engine")
    parser.add_argument("--dry-run", action="store_true", help="Perform pre-flight diagnostics without deploying")
    parser.add_argument("--force", action="store_true", help="Force rebuild and redeploy of all targets")
    args = parser.parse_args()

    print("==================================================")
    print(f"      {C_BOLD}🚀 Lx8 Central OS Smart Deploy Engine{C_RESET}      ")
    print("==================================================")

    # 1. Load Registry
    if not os.path.exists(REGISTRY_FILE):
        print_fail(f"Registry file '{REGISTRY_FILE}' is missing! Halting.")
        sys.exit(1)
    
    # Load deploy cache
    cache = {}
    if os.path.exists(CACHE_FILE) and not args.force:
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
        except Exception:
            pass

    # 2. Check if Dashboard requires a rebuild
    print_header("1. HASHING & CHANGE DETECTION")
    dash_dirty, dash_hash = check_dashboard_dirty(cache)
    
    if dash_dirty:
        print_warn("Dashboard source files have changed. Vite rebuild required!")
    else:
        print_success("Dashboard assets are clean. Build skipped!")

    # Calculate hashes for subdomains
    dirty_targets = []
    subdomain_hashes = {}

    # Check if root main website has changed
    main_dirty, main_hash = check_main_dirty(cache)
    if main_dirty or args.force:
        dirty_targets.append("main")
        print_warn("Root main website files have changed. Deploying target 'main'!")
    else:
        print_success("Root main website is clean.")
    
    # Check if Bipartite Book codebase has changed
    book_dirty, book_hash = check_book_dirty(cache)
    if book_dirty or args.force:
        print_warn("Bipartite Book Next.js codebase has changed!")
    else:
        print_success("Bipartite Book Next.js codebase is clean.")

    
    import yaml
    with open(REGISTRY_FILE, "r") as f:
        registry = yaml.safe_load(f)

    git_commit = get_git_commit()
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Bump versions and write version.json files locally
    for prod in registry["products"]:
        sub = prod["subdomain"]
        sub_hash = get_dir_hash(sub)
        subdomain_hashes[sub] = sub_hash
        
        prev_sub_hash = cache.get(f"sub_{sub}", "")
        is_dirty = sub_hash != prev_sub_hash or dash_dirty or args.force
        if sub == "bipartitebook" and book_dirty:
            is_dirty = True
        
        if is_dirty:
            dirty_targets.append(sub)
            
            # Increment version in memory
            old_ver = prod.get("version", "1.0.0")
            new_ver = increment_version(old_ver)
            prod["version"] = new_ver
            
            print_info(f"Target '{sub}' is DIRTY: Bumping version {old_ver} -> {new_ver}")
            
            # Generate version.json payload
            version_payload = {
                "version": new_ver,
                "commit": git_commit,
                "buildTime": timestamp,
                "subdomain": sub
            }
            
            # Write to subdomain directory
            if not args.dry_run:
                # Ensure directory exists
                if not os.path.exists(sub):
                    os.makedirs(sub)
                version_path = os.path.join(sub, "version.json")
                with open(version_path, "w") as vf:
                    json.dump(version_payload, vf, indent=2)
        else:
            print_success(f"Target '{sub}' is CLEAN (running version {prod.get('version', '1.0.0')})")

    if not dirty_targets:
        print_success("Absolute clean state! All subdomains perfectly match cloud. Nothing to do.")
        sys.exit(0)

    # Rewrite registry file with updated versions
    if not args.dry_run:
        with open(REGISTRY_FILE, "w") as f:
            yaml.safe_dump(registry, f, default_flow_style=False, sort_keys=False)
        print_success("Registry file updated with new semantic version numbers.")

    # 3. Compile React Dashboard
    if dash_dirty or args.force:
        print_header("2. COMPILING CENTRAL OS REACT DASHBOARD")
        if args.dry_run:
            print_info("[DRY-RUN] Would execute: npm run build in /dashboard")
        else:
            print_info("Running npm run build...")
            try:
                # Ensure node_modules exists
                if not os.path.exists(os.path.join("dashboard", "node_modules")):
                    print_warn("node_modules is missing! Performing npm install...")
                    subprocess.run(["npm", "install"], cwd="dashboard", check=True)
                
                # Build Vite React dashboard
                subprocess.run(["npm", "run", "build"], cwd="dashboard", check=True)
                print_success("React compilation completed successfully!")
            except subprocess.CalledProcessError as e:
                print_fail(f"Vite compilation failed! Error code: {e.returncode}")
                sys.exit(1)

    # 3.1 Compile Bipartite Universe Next.js Book
    if ("bipartitebook" in dirty_targets and book_dirty) or args.force:
        print_header("2.1 COMPILING BIPARTITE UNIVERSE NEXT.JS BOOK")
        if args.dry_run:
            print_info("[DRY-RUN] Would execute Next.js export build in products/bipartite-universe-book")
        else:
            book_path = "/Users/alexeiferreira/Lx8Labs/products/bipartite-universe-book"
            print_info(f"Running Next.js export build in {book_path}...")
            try:
                # Ensure node_modules exists
                if not os.path.exists(os.path.join(book_path, "node_modules")):
                    print_warn("Book node_modules is missing! Performing npm install...")
                    subprocess.run(["npm", "install"], cwd=book_path, check=True)
                
                # Build Next.js book
                subprocess.run(["npm", "run", "build"], cwd=book_path, check=True)
                
                # Copy export folder
                export_out = os.path.join(book_path, "out")
                target_dest = "bipartitebook"
                if os.path.exists(export_out):
                    print_info(f"Syncing Next.js export out/ folder to {target_dest}...")
                    # Clean existing files except dashboard/ and version.json
                    for item in os.listdir(target_dest):
                        item_path = os.path.join(target_dest, item)
                        if item == "dashboard" or item == "version.json":
                            continue
                        if os.path.isdir(item_path):
                            import shutil
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                            
                    # Copy static assets
                    for item in os.listdir(export_out):
                        src_item = os.path.join(export_out, item)
                        dst_item = os.path.join(target_dest, item)
                        if os.path.isdir(src_item):
                            import shutil
                            shutil.copytree(src_item, dst_item)
                        else:
                            import shutil
                            shutil.copy2(src_item, dst_item)
                            
                print_success("Next.js Book compilation and static export sync completed successfully!")
            except Exception as e:
                print_fail(f"Next.js Book build/sync failed: {str(e)}")
                sys.exit(1)


    # 4. Synchronize Subdomains & Infrastructure Targets
    print_header("3. INFRASTRUCTURE & TARGETS SYNCHRONIZATION")
    if args.dry_run:
        print_info("[DRY-RUN] Would run scripts/sync_infrastructure.py to regenerate hosting and replicate assets")
    else:
        print_info("Executing synchronization...")
        try:
            # Import and run the sync script
            sys.path.append(os.path.abspath("scripts"))
            import sync_infrastructure
            sync_infrastructure.update_firebase_config(registry)
            
            # Also copy subdomain version.json to subdomain/dashboard/version.json
            for sub in dirty_targets:
                if sub == "main":
                    continue
                src_v = os.path.join(sub, "version.json")
                dst_v = os.path.join(sub, "dashboard", "version.json")
                if os.path.exists(src_v) and os.path.exists(os.path.dirname(dst_v)):
                    import shutil
                    shutil.copy2(src_v, dst_v)
                    
            print_success("Targets synced! Dashboard builds and version tags replicated cleanly.")
        except Exception as e:
            print_fail(f"Infrastructure sync failed: {str(e)}")
            sys.exit(1)

    # 5. Pre-Flight Deploy Verifications (Halts on missing index.html to prevent cloud 404s)
    print_header("4. PRE-FLIGHT VALIDATIONS")
    validation_passed = True
    for sub in dirty_targets:
        if sub == "main":
            if not os.path.exists("index.html"):
                print_fail("Validation failed: Missing root main website 'index.html'!")
                validation_passed = False
            continue
        index_path = os.path.join(sub, "index.html")
        dash_path = os.path.join(sub, "dashboard", "index.html")
        v_path = os.path.join(sub, "version.json")
        
        if not os.path.exists(index_path):
            print_fail(f"Validation failed: Missing primary '{index_path}' landing page!")
            validation_passed = False
        if not os.path.exists(dash_path):
            print_fail(f"Validation failed: Missing copied dashboard '{dash_path}' assets!")
            validation_passed = False
        if not os.path.exists(v_path):
            print_fail(f"Validation failed: Missing version payload '{v_path}'!")
            validation_passed = False
            
    if not validation_passed:
        print_fail("Halted pre-flight: broken targets detected. Deploy aborted to protect active domains.")
        sys.exit(1)
    
    print_success("Pre-flight safety validation complete! Clean static trees verified.")

    # 6. Targeted Deployments
    print_header("5. TARGETED CLOUD HOSTING DEPLOYMENT")
    deploy_command = ["npx", "-y", "firebase-tools@latest", "deploy", "--only"]
    only_args = ",".join([f"hosting:{sub}" for sub in dirty_targets])
    deploy_command.append(only_args)

    if args.dry_run:
        print_info(f"[DRY-RUN] Would execute: {' '.join(deploy_command)}")
        print_success("Dry-run diagnostics completed with perfect metrics!")
    else:
        print_info(f"Executing Targeted Firebase Deploy for: {', '.join(dirty_targets)}...")
        try:
            subprocess.run(deploy_command, check=True)
            print_success("Cloud hosting deployment finalized successfully!")
            
            # Update Deploy Cache
            cache["dashboard"] = dash_hash
            cache["main_site"] = main_hash
            cache["book_site"] = book_hash
            for sub in subdomain_hashes:
                cache[f"sub_{sub}"] = subdomain_hashes[sub]
            
            with open(CACHE_FILE, "w") as f:
                json.dump(cache, f, indent=2)

            
            print_success("Deployment state cached successfully.")
        except subprocess.CalledProcessError as e:
            print_fail(f"Firebase deployment failed! Exit code: {e.returncode}")
            sys.exit(1)

if __name__ == "__main__":
    main()
