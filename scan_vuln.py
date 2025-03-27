__Name__ = "Collector"
__Description__ = "Collect XSS vulnerable parameters from entire domain."
__Author__ = "Md. Nur Habib"
__Version__ = "1.0.0"

# Import modules
from multiprocessing import Manager
import os
import sys
import argparse
import requests
import warnings
import urllib.parse
import socket
import multiprocessing

warnings.filterwarnings("ignore")

# Argument parser
parser = argparse.ArgumentParser(description="=============== Help Menu ===============")
parser.add_argument("function", help="pull or check")
parser.add_argument("--host", help="Domain/Host Name")
parser.add_argument("--threads", type=int, help="The number of threads", default=5)
parser.add_argument("--with-subs", choices=["yes", "no"], help="yes or no", default="yes")
parser.add_argument("--loadfile", help="File location")
parser.add_argument("--outputfile", help="Saving Path")

args = parser.parse_args()


def waybackurlsFunction(host, with_subs):
    url = f"http://web.archive.org/cdx/search/cdx?url=*.{host}/*&output=list&fl=original&collapse=urlkey" if with_subs == "yes" else f"http://web.archive.org/cdx/search/cdx?url={host}/*&output=list&fl=original&collapse=urlkey"
    
    response = requests.get(url)
    
    if args.outputfile:
        with open(args.outputfile, "a") as f:
            f.write(response.text.strip() + "\n")
    
    print(response.text.strip())


def checkGivenDomainNameFunction(url):
    global timeOutGlobalVariable
    if not url:
        return

    url = url.replace(":80/", "/").replace(":443/", "/")
    if not url.startswith("http"):
        url = f"http://{url}"

    domainName = urllib.parse.urlparse(url).netloc.split(":")[0]
    if domainName in timeOutGlobalVariable:
        return

    try:
        response = requests.head(url, verify=False, timeout=0.25)
    except requests.exceptions.Timeout:
        timeOutGlobalVariable.append(domainName)
        return
    except requests.exceptions.ConnectionError:
        timeOutGlobalVariable.append(domainName)
        return

    if response.status_code == 404:
        return

    cLength = response.headers.get("Content-Length", "Unknown")
    cType = response.headers.get("Content-Type", "Unknown")

    if response.status_code in range(300, 400) and "Location" in response.headers:
        redirected_url = response.headers["Location"]
        result = ", ".join([url, str(response.status_code), cLength, cType, redirected_url])
    else:
        result = ", ".join([url, str(response.status_code), cLength, cType])

    print(result)
    
    if args.outputfile:
        with open(args.outputfile, "a") as f:
            f.write(result + "\n")


def checkGivenDomainNameFunctionValidDomain(endpoints):
    validDomains, invalidDomains, validEndpoints = [], [], []
    
    for endpoint in endpoints:
        endpoint = endpoint.strip().strip('"').strip("'")
        try:
            parsedUrl = urllib.parse.urlparse(endpoint)
            domainName = parsedUrl.netloc.split(":")[0]
            if domainName in validDomains:
                validEndpoints.append(endpoint)
                continue
            elif domainName in invalidDomains:
                continue
            try:
                socket.gethostbyname(domainName)
                validDomains.append(domainName)
                validEndpoints.append(endpoint)
            except:
                invalidDomains.append(domainName)
        except:
            continue
    return validEndpoints


def writerFunction(fileToWrite):
    while True:
        line = writeQueueVariable.get(True)
        if line is None:
            break
        fileToWrite.write(line)


# Multiprocessing setup
manager = multiprocessing.Manager()
timeOutGlobalVariable = manager.list()
writeQueueVariable = manager.Queue()
pool = multiprocessing.Pool(args.threads)

if args.function == "pull":
    if args.host:
        print("\nFetching URLs, This may take some time. Please wait...\n")
        waybackurlsFunction(args.host, args.with_subs)
    elif args.loadfile:
        with open(args.loadfile, "r") as f:
            for line in f.readlines():
                waybackurlsFunction(line.strip(), args.with_subs)

elif args.function == "check":
    if args.loadfile:
        try:
            if args.outputfile:
                outputfile = open(args.outputfile, "a", buffering=1)
                p = multiprocessing.Process(target=writerFunction, args=(outputfile,))
                p.start()

            with open(args.loadfile, "r") as f:
                endpoints = checkGivenDomainNameFunctionValidDomain(f.readlines())

            pool.map(checkGivenDomainNameFunction, endpoints)

            if args.outputfile:
                writeQueueVariable.put(None)
                p.join()
                outputfile.close()

        except IOError:
            print("Error: File not found!")
            sys.exit(1)
        except KeyboardInterrupt:
            print("Killing processes.")
            pool.terminate()
            sys.exit(1)
        except Exception as error:
            print(f"An error occurred: {error}")

    elif not sys.stdin.isatty():
        try:
            if args.outputfile:
                outputfile = open(args.outputfile, "a", buffering=1)
                p = multiprocessing.Process(target=writerFunction, args=(outputfile,))
                p.start()

            endpoints = checkGivenDomainNameFunctionValidDomain(sys.stdin.readlines())
            pool.map(checkGivenDomainNameFunction, endpoints)

            if args.outputfile:
                writeQueueVariable.put(None)
                p.join()
                outputfile.close()

        except IOError:
            print("Error: File not found!")
            sys.exit(1)
        except KeyboardInterrupt:
            print("Killing processes.")
            pool.terminate()
            sys.exit(1)
        except Exception as error:
            print(f"An error occurred: {error}")

    else:
        print("Please specify a file.")
        sys.exit(1)

