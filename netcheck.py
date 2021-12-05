#!/usr/bin/env python3
import argparse
import logging
import subprocess
import time
import requests


class InternetChecker:
    def __init__(self, url, every, down_after, on_disconnect):
        self.online = False
        self.failed_checks = 0
        self.url = url
        self.every = every
        self.down_after = down_after
        self.on_disconnect = on_disconnect
        self.status_changed = True
        logging.basicConfig(
            format="%(asctime)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
            level=logging.INFO,
        )

    def record_success(self):
        if not self.online:
            self.online = True
            self.status_changed = True
        self.failed_checks = 0

    def record_failure(self):
        self.failed_checks = self.failed_checks + 1
        logging.info("Failed URL check; fail count = %d", self.failed_checks)
        if self.online and self.failed_checks == self.down_after:
            self.online = False
            self.status_changed = True

    def process_change(self):
        if self.online:
            msg = "Connected to"
        else:
            msg = "Disconnected from"
        logging.info("%s the Internet", msg)
        if self.on_disconnect:
            try:
                subprocess.run(self.on_disconnect, check=True)
                logging.info("Ran %s", self.on_disconnect)
            except (subprocess.SubprocessError, FileNotFoundError) as err:
                logging.error(err)
        self.status_changed = False

    def run(self):
        while True:
            try:
                req = requests.get(self.url)
                req.raise_for_status()
                self.record_success()
            except requests.exceptions.HTTPError:
                self.record_failure()
            if self.status_changed:
                self.process_change()
            time.sleep(self.every)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Internet connectivity")
    parser.add_argument(
        "--url",
        type=str,
        default="http://connectivitycheck.gstatic.com/generate_204",
        help="URL to fetch to check",
    )
    parser.add_argument(
        "--every", type=int, default=120, help="how often to check for connectivity"
    )
    parser.add_argument(
        "--down-after",
        type=int,
        default=2,
        help="number of failures before considering the connection down",
    )
    parser.add_argument(
        "--on-disconnect", type=str, help="Command to execute on disconnect"
    )
    args = parser.parse_args()

    ic = InternetChecker(args.url, args.every, args.down_after, args.on_disconnect)
    ic.run()
