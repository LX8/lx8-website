import urllib.request
import urllib.error
import yaml
import sys
import ssl

REGISTRY_FILE = "lx8_registry.yaml"

def test_url(url):
    # Disable SSL verification for verification checking if DNS/certs are still propagating
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (SRE Domain Verification)'}
        )
        with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
            status = response.status
            # Check for standard i18n scripts in body
            html = response.read().decode('utf-8', errors='ignore')
            has_engine = "/i18n/engine.js" in html
            has_fb = "firebase-init.js" in html
            return f"🟢 ONLINE (HTTP {status}) - i18n Engine: {'✓' if has_engine else '✗'}, Telemetry: {'✓' if has_fb else '✗'}"
    except urllib.error.HTTPError as e:
        return f"🟡 HTTP ERROR {e.code}"
    except urllib.error.URLError as e:
        return f"🔴 RESOLUTION FAILED ({e.reason})"
    except Exception as e:
        return f"🔴 ERROR ({str(e)})"

def main():
    print("==================================================")
    print("      Lx8 Labs Subdomain & Site Verification      ")
    print("==================================================\n")
    
    try:
        with open(REGISTRY_FILE, "r") as f:
            registry = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: {REGISTRY_FILE} not found.")
        sys.exit(1)
        
    # 1. Test Main Website
    main_url = "https://lx8labs.com"
    print(f"Testing Central OS Target:")
    print(f"  {main_url:<35} -> {test_url(main_url)}")
    print("-" * 50)
    
    # 2. Test Subdomains
    print("Testing Product Subdomains:")
    for product in registry.get("products", []):
        subdomain = product["subdomain"]
        url = f"https://{subdomain}.lx8labs.com"
        print(f"  {url:<35} -> {test_url(url)}")
    print("==================================================")

if __name__ == "__main__":
    main()
