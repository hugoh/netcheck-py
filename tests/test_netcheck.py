import time
import unittest
import unittest.mock

import netcheck


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.down_after = 3
        self.ic = netcheck.InternetChecker("", 1, self.down_after, "", "", "", -1)

    def test_is_connected_unknown(self):
        with self.assertRaises(ValueError, msg="Unknown status"):
            self.ic.is_connected()

    def test_is_connected_success(self):
        self.ic.record_success()
        self.assertTrue(self.ic.is_connected(), msg="Connected after success")

    def test_is_connected_failure(self):
        for i in range(self.down_after - 1):
            self.ic.record_failure()
            self.assertTrue(self.ic.is_connected(), msg="Still connected after failure")
        self.ic.record_failure()
        self.assertFalse(self.ic.is_connected(), msg="Disconnected")
        self.ic.record_success()
        self.assertTrue(self.ic.is_connected(), msg="Reconnected after success")

    def test_command_run(self):
        RERUN_EVERY = 2
        ic = netcheck.InternetChecker("", 1, 1, "", "", "", RERUN_EVERY)
        ic.run_on_disconnect_command = unittest.mock.Mock(side_effect=CommandRun)
        with self.assertRaises(CommandRun, msg="Command run on disconnect"):
            ic.record_failure()
        ic._InternetChecker__record_on_disconnect_command_run()
        ic.record_failure()
        time.sleep(RERUN_EVERY)
        with self.assertRaises(CommandRun, msg="Command run after disconnect"):
            ic.record_failure()
        ic.record_success()
        with self.assertRaises(CommandRun, msg="Command run on disconnect"):
            ic.record_failure()


class CommandRun(Exception):
    pass


if __name__ == "__main__":
    unittest.main()
