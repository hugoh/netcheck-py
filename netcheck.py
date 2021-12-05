#!/usr/bin/env python3
import argparse
import logging
import subprocess
import sys
import time

import requests


class InternetChecker:
    def __init__(self, url, every, down_after, logfile, on_disconnect):
        self.online = False
        self.failed_checks = 0
        self.url = url
        self.every = every
        self.down_after = down_after
        self.on_disconnect = on_disconnect
        self.status_changed = True
        self.setup_logger(logfile)
        self.logger.info(
            "Started: monitoring %s every %ds; %d failures = disconnect",
            url,
            every,
            down_after,
        )

    def setup_logger(self, logfile):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s %(filename)s[%(process)d] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        self.logger.addHandler(stdout_handler)
        if logfile:
            self.logger.info("Logging to %s", logfile)
            try:
                output_file_handler = logging.FileHandler(logfile)
                output_file_handler.setFormatter(formatter)
                self.logger.addHandler(output_file_handler)
            except FileNotFoundError as err:
                self.logger.error("Cannot setup logging to file: %s", err)

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
        self.logger.info("%s the Internet", msg)
        if not self.online and self.on_disconnect:
            try:
                self.logger.info(
                    "Running command on disconnect: %s", self.on_disconnect
                )
                subprocess.run(self.on_disconnect, check=True)
            except (subprocess.SubprocessError, FileNotFoundError) as err:
                self.logger.error(err)
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
    parser.add_argument("--logfile", type=str, help="File to log information to")
    parser.add_argument(
        "--on-disconnect", type=str, help="Command to execute on disconnect"
    )
    args = parser.parse_args()

    ic = InternetChecker(
        args.url, args.every, args.down_after, args.logfile, args.on_disconnect
    )
    ic.run()
