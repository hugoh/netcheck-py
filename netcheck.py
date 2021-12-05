#!/usr/bin/env python3
import argparse
import logging
import subprocess
import sys
import time

import requests

TIMEOUT = 10


class InternetChecker:
    def __init__(
        self, url, every, down_after, logfile, on_disconnect, rerun_command_every
    ):
        self.failed_checks = -1
        self.url = url
        self.every = every
        self.down_after = down_after
        self.on_disconnect = on_disconnect
        self.rerun_command_every = rerun_command_every
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
        if self.failed_checks != 0:
            self.failed_checks = 0
            self.record_change()

    def record_failure(self):
        self.failed_checks = max(self.failed_checks, 0) + 1
        logging.info("Failed URL check; fail count = %d", self.failed_checks)
        if self.failed_checks == self.down_after:
            self.record_change()
            self.run_on_disconnect_command()
        elif self.failed_checks > self.down_after:
            if self.rerun_command_every > 0:
                time_since_last_command_run = (
                    (self.failed_checks - self.down_after) * self.every
                ) % self.rerun_command_every
                if time_since_last_command_run < self.every:
                    self.run_on_disconnect_command()

    def record_change(self):
        if self.failed_checks == 0:
            msg = "Connected to"
        else:
            msg = "Disconnected from"
        self.logger.info("%s the Internet", msg)

    def run_on_disconnect_command(self):
        if self.on_disconnect:
            try:
                self.logger.info(
                    "Running command on disconnect: %s", self.on_disconnect
                )
                subprocess.run(self.on_disconnect, check=True)
            except (subprocess.SubprocessError, FileNotFoundError) as err:
                self.logger.error(err)

    def run(self):
        while True:
            try:
                req = requests.get(self.url, timeout=TIMEOUT)
                req.raise_for_status()
                self.record_success()
            except requests.exceptions.HTTPError:
                self.record_failure()
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
    parser.add_argument(
        "--rerun-command-every",
        type=int,
        default=0,
        help="rerun on-disconnect command every N seconds",
    )
    args = parser.parse_args()

    ic = InternetChecker(
        args.url,
        args.every,
        args.down_after,
        args.logfile,
        args.on_disconnect,
        args.rerun_command_every,
    )
    ic.run()
