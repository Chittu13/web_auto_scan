#include <iostream>
#include <string>
#include <vector>
#include <set>
#include <regex>
#include <curl/curl.h>

using namespace std;

// Callback function for libcurl
size_t WriteCallback(void *contents, size_t size, size_t nmemb, string *output) {
    size_t totalSize = size * nmemb;
    output->append((char *)contents, totalSize);
    return totalSize;
}

// Function to fetch HTML content
string getHTML(const string &url) {
    CURL *curl = curl_easy_init();
    string response;

    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
        curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L); // Follow redirects
        curl_easy_setopt(curl, CURLOPT_USERAGENT, "Mozilla/5.0");
        curl_easy_perform(curl);
        curl_easy_cleanup(curl);
    }

    return response;
}

// Function to normalize URLs
string normalizeURL(const string &baseUrl, const string &foundUrl) {
    if (foundUrl.find("http") == 0 || foundUrl.find("//") == 0) {
        return foundUrl; // Already absolute URL
    }
    return baseUrl + foundUrl; // Convert relative to absolute
}

// Function to extract endpoints
vector<string> extractEndpoints(const string &html, const string &baseUrl) {
    set<string> uniqueEndpoints;
    regex pattern(R"((href|src|action)=["'](.*?)["'])");
    smatch match;

    string::const_iterator searchStart(html.cbegin());
    while (regex_search(searchStart, html.cend(), match, pattern)) {
        string url = normalizeURL(baseUrl, match[2]);
        uniqueEndpoints.insert(url);
        searchStart = match.suffix().first;
    }

    return vector<string>(uniqueEndpoints.begin(), uniqueEndpoints.end());
}

// Function to extract JavaScript files
vector<string> extractJSFiles(const string &html, const string &baseUrl) {
    set<string> jsFiles;
    regex pattern(R"(src=["'](.*?\.js(\?.*?)?)["'])"); // Improved regex to detect JS files correctly
    smatch match;

    string::const_iterator searchStart(html.cbegin());
    while (regex_search(searchStart, html.cend(), match, pattern)) {
        string jsFile = normalizeURL(baseUrl, match[1]);
        jsFiles.insert(jsFile);
        searchStart = match.suffix().first;
    }

    return vector<string>(jsFiles.begin(), jsFiles.end());
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        cerr << "[!] No target URL provided!" << endl;
        return 1;
    }

    string targetUrl = argv[1]; // Get the URL from the command-line argument

    // Get HTML content
    string html = getHTML(targetUrl);
    if (html.empty()) {
        cerr << "[!] Failed to fetch website content." << endl;
        return 1;
    }

    // Extract and display endpoints
    vector<string> endpoints = extractEndpoints(html, targetUrl);
    cout << "\n[+] Unique Endpoints Found:" << endl;
    for (const string &endpoint : endpoints) {
        cout << endpoint << endl;
    }

    // Extract and display JavaScript files
    vector<string> jsFiles = extractJSFiles(html, targetUrl);
    cout << "\n[+] JavaScript Files Found:" << endl;
    for (const string &jsFile : jsFiles) {
        cout << jsFile << endl;
    }

    return 0;
}
