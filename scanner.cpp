#include <iostream>
#include <cstdlib>
#include <cstdio>
#include <sstream>
#include <string>
#include <regex>
#include <unistd.h> // Add this for access() and F_OK

using namespace std;

// Function to extract domain from URL
std::string extractDomain(const std::string& url) {
    std::string domain = url;

    // Check if the URL starts with http:// or https://
    if (domain.find("http://") == 0) {
        domain = domain.substr(7); // Remove "http://"
    } else if (domain.find("https://") == 0) {
        domain = domain.substr(8); // Remove "https://"
    }

    // Remove "www." if present
    if (domain.find("www.") == 0) {
        domain = domain.substr(4); // Remove "www."
    }

    // Extract only the domain name (before any "/")
    size_t pos = domain.find('/');
    if (pos != std::string::npos) {
        domain = domain.substr(0, pos);
    }

    return domain;
}

// Function to run Nmap and filter the output
void runNmap(const std::string& domain) {
    std::string command = "nmap -sV --open " + domain + " 2>&1"; // Run nmap command with version detection
    FILE* fp = popen(command.c_str(), "r");
    if (fp == nullptr) {
        std::cerr << "Failed to run nmap command." << std::endl;
        return;
    }

    char buffer[128];
    std::string nmap_output;

    // Read output from nmap command
    while (fgets(buffer, sizeof(buffer), fp) != nullptr) {
        nmap_output += buffer;
    }

    fclose(fp);

    // Use regex to find the relevant PORT STATE SERVICE VERSION lines
    std::regex pattern(R"((\d+/tcp)\s+(open)\s+(\S+)\s+([\S\s]+))"); // Regex to capture port, state, service, version
    std::smatch matches;

    // Print the header
    std::cout << "\033[32mPORT   STATE SERVICE VERSION\033[0m" << std::endl; // Green color

    // Search for matches in the nmap output
    std::string::const_iterator search_start(nmap_output.cbegin());
    bool found = false; // Flag to check if we find any matches
    while (std::regex_search(search_start, nmap_output.cend(), matches, pattern)) {
        // Print the matched line in green
        std::cout << "\033[32m" << matches[1] << " " << matches[2] << " " << matches[3] << " " << matches[4] << "\033[0m" << std::endl;
        search_start = matches.suffix().first; // Move to next match
        found = true;
    }

    // If no open ports found
    if (!found) {
        std::cout << "\033[32mNo open ports found.\033[0m" << std::endl;
    }
}

// Function to run WhatWeb
void runWhatWeb(const std::string& url) {
    std::string command = "whatweb " + url + " 2>&1"; // Run whatweb command
    FILE* fp = popen(command.c_str(), "r");
    if (fp == nullptr) {
        std::cerr << "Failed to run whatweb command." << std::endl;
        return;
    }

    char buffer[128];
    std::string whatweb_output;

    // Read output from whatweb command
    while (fgets(buffer, sizeof(buffer), fp) != nullptr) {
        whatweb_output += buffer;
    }

    fclose(fp);

    // Print the raw WhatWeb output
    std::cout << "Raw WhatWeb Output:\n" << whatweb_output << std::endl;
}

// Function to compile and run endpoint.cpp
void runEndpoint(const std::string& url) {
    // Check if the endpoint binary exists
    if (access("./endpoint", F_OK) != 0) {
        std::cout << "Compiling endpoint.cpp..." << std::endl;
        std::string compileCommand = "g++ endpoint.cpp -o endpoint -lcurl";
        system(compileCommand.c_str());
    }

    // Run the endpoint program with the URL as input
    std::string endpointCommand = "./endpoint " + url;
    std::cout << "Running Endpoint Extraction on " << url << "..." << std::endl;
    system(endpointCommand.c_str());
}

// Function to run scan_vuln.py
void runScanVuln(const std::string& url) {
    std::string command = "python3 scan_vuln.py pull --host " + url;
    std::cout << "Running scan_vuln.py on " << url << "..." << std::endl;
    system(command.c_str());
}

int main() {
    std::string url;
    std::cout << "Enter the target URL (e.g., http://example.com): ";
    std::getline(std::cin, url);

    // Extract domain from the URL
    std::string domain = extractDomain(url);

    if (!domain.empty()) {
        // Run Nmap and filter the results
        std::cout << "\nRunning Nmap on " << domain << "...\n" << std::endl;
        runNmap(domain);

        // Run WhatWeb with the provided URL
        std::cout << "\nRunning WhatWeb on " << url << "...\n" << std::endl;
        runWhatWeb(url);

        // After completing, run endpoint.cpp
        runEndpoint(url);

        // Finally, run scan_vuln.py
        runScanVuln(url);
    } else {
        std::cerr << "Invalid domain extracted from the URL." << std::endl;
    }

    return 0;
}
