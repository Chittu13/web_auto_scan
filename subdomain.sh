#!/bin/bash

# Prompt user for the target URL
read -p "Enter target URL (e.g., https://www.example.com): " input_url

# Extract and normalize the domain: remove http(s), www, and trailing slashes
domain=$(echo "$input_url" | sed -E 's|https?://||' | sed -E 's|^www\.||' | sed -E 's|/.*||')

echo "[*] Extracted domain: $domain"

# Run subfinder
echo "[*] Running subfinder..."
sudo subfinder -d "$domain" -all -silent > subdomain1.txt

# Run assetfinder
echo "[*] Running assetfinder..."
sudo assetfinder --subs-only "$domain" > subdomain2.txt

# Merge and sort results
echo "[*] Merging and deduplicating results..."
sort -u subdomain1.txt subdomain2.txt > mainsubdomain.txt

# Count and display number of unique subdomains
count=$(wc -l < mainsubdomain.txt)
echo "[+] Results saved in mainsubdomain.txt"

# Delete temporary files
rm -f subdomain1.txt subdomain2.txt
echo "[+] Found $count unique subdomains for $domain"
