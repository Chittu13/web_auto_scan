import os
import re
import subprocess
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# ANSI color codes
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
RESET = "\033[0m"
BOLD = "\033[1m"

def create_directory(path):
    os.makedirs("result", exist_ok=True)
    os.makedirs(path, exist_ok=True)

def extract_domain(url):
    parsed = urlparse(url)
    domain = parsed.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain

def run_nmap(domain, output_path):
    try:
        result = subprocess.run(["nmap", "-sV", "--open", domain], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        result = e

    output = result.stdout
    filtered_output = []

    host_info = re.search(r"Nmap scan report for (.+)", output)
    if host_info:
        filtered_output.append(host_info.group(1))

    rdns_info = re.search(r"rDNS record for .+", output)
    if rdns_info:
        filtered_output.append(rdns_info.group(0))

    port_section = re.findall(r"(\d+/tcp\s+open\s+\S+\s+[^\n]+)", output)
    if port_section:
        filtered_output.append("PORT   STATE SERVICE VERSION")
        filtered_output.extend(port_section)

    with open(output_path, "w") as f:
        for line in filtered_output:
            print(f"{GREEN}{line}{RESET}")
            f.write(line + "\n")

def run_command_and_save(command, output_path):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        result = e

    with open(output_path, "w") as f:
        for line in result.stdout.splitlines():
            f.write(line + "\n")
            if any(x in line for x in ["[", "---", "==="]):
                print(f"{BOLD}{GREEN}{line}{RESET}")
            else:
                print(f"{CYAN}{line}{RESET}")

def get_html(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return response.text
    except requests.RequestException:
        return ""

def normalize_url(base_url, found_url):
    return found_url if found_url.startswith("http") else urljoin(base_url, found_url)

def extract_endpoints(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    tags = soup.find_all(["a", "form", "script", "link", "img"])
    links = set()

    for tag in tags:
        for attr in ["href", "src", "action"]:
            if tag.has_attr(attr):
                links.add(normalize_url(base_url, tag[attr]))

    return sorted(links)

def extract_js_files(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    js_files = set()

    for script in soup.find_all("script", src=True):
        src = script['src']
        if src.endswith(".js"):
            js_files.add(normalize_url(base_url, src))

    return sorted(js_files)

def run_endpoint_logic(url, output_path):
    html = get_html(url)
    if not html:
        print(f"{YELLOW}[!] Failed to fetch website content.{RESET}")
        return

    endpoints = extract_endpoints(html, url)
    js_files = extract_js_files(html, url)

    with open(output_path, "w") as f:
        print(f"{GREEN}\n[+] Unique Endpoints Found:{RESET}")
        f.write("[+] Unique Endpoints Found:\n")
        for endpoint in endpoints:
            print(f"{CYAN}{endpoint}{RESET}")
            f.write(endpoint + "\n")

        print(f"{GREEN}\n[+] JavaScript Files Found:{RESET}")
        f.write("\n[+] JavaScript Files Found:\n")
        for js in js_files:
            print(f"{CYAN}{js}{RESET}")
            f.write(js + "\n")

# ✅ Subdomain Enumeration without real-time showing
def run_subdomain_enumeration(domain, result_dir):
    print(f"{GREEN}\n[+] Running Subdomain Enumeration...{RESET}")

    # 1. Run subfinder
    subfinder_cmd = f"subfinder -d {domain} -all -silent"
    subfinder_result = subprocess.run(subfinder_cmd, shell=True, capture_output=True, text=True)
    subdomains1 = subfinder_result.stdout.strip().splitlines()

    # 2. Run assetfinder
    assetfinder_cmd = f"assetfinder --subs-only {domain}"
    assetfinder_result = subprocess.run(assetfinder_cmd, shell=True, capture_output=True, text=True)
    subdomains2 = assetfinder_result.stdout.strip().splitlines()

    # 3. Merge all found subdomains
    all_subdomains = sorted(set(subdomains1 + subdomains2))

    if not all_subdomains:
        print(f"{YELLOW}[!] No subdomains found.{RESET}")
        return

    print(f"{CYAN}\n[+] Checking subdomain status...{RESET}")

    alive_subdomains = []
    dead_subdomains = []

    # 🌟 Just silently check
    for sub in all_subdomains:
        url = f"http://{sub}"
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            if response.status_code == 200:
                alive_subdomains.append(f"{sub} [Status: {response.status_code}]")
            else:
                dead_subdomains.append(f"{sub} [Status: {response.status_code}]")
        except requests.RequestException:
            dead_subdomains.append(f"{sub} [No Response]")

    subdomain_file = os.path.join(result_dir, "subdomains.txt")
    with open(subdomain_file, "w") as f:
        f.write("[+] Alive Subdomains:\n")
        for item in alive_subdomains:
            f.write(item + "\n")
        f.write("\n[+] Dead Subdomains:\n")
        for item in dead_subdomains:
            f.write(item + "\n")

    # 🎯 Final count output only
    print(f"\n{CYAN}[+] Total Subdomains Found: {len(all_subdomains)}{RESET}")
    print(f"{GREEN}[+] Alive Subdomains: {len(alive_subdomains)}{RESET}")
    print(f"{RED}[+] Dead Subdomains: {len(dead_subdomains)}{RESET}")
    print(f"{GREEN}[+] Subdomain scan saved to {subdomain_file}{RESET}")

def run_scan_vuln(url, output_path):
    print(f"{GREEN}\n[+] Running Vulnerability Scanner...{RESET}")
    run_command_and_save(f"python3 scan_vuln.py pull --host {url}", output_path)

def main():
    try:
        url = input(f"{CYAN}Enter the target URL (e.g., http://example.com): {RESET}").strip()
        domain = extract_domain(url)
        if not domain:
            print(f"{YELLOW}[!] Invalid domain.{RESET}")
            return

        result_dir = os.path.join("result", domain)
        create_directory(result_dir)

        run_subdomain_enumeration(domain, result_dir)

        print(f"\n{GREEN}[+] Running Nmap on {domain}...{RESET}")
        run_nmap(domain, os.path.join(result_dir, "nmap.txt"))

        print(f"\n{GREEN}[+] Running WhatWeb on {url}...{RESET}")
        run_command_and_save(f"whatweb {url}", os.path.join(result_dir, "whatweb.txt"))

        print(f"\n{GREEN}[+] Extracting Endpoints from {url}...{RESET}")
        run_endpoint_logic(url, os.path.join(result_dir, "endpoint.txt"))

        run_scan_vuln(url, os.path.join(result_dir, "scan_vuln.txt"))

        print(f"\n{GREEN}[✔] All tasks completed.{RESET}")

    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] Skipping current step...{RESET}")

if __name__ == "__main__":
    main()

