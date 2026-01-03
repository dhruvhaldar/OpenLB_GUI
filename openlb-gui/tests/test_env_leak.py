
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add backend directory to sys.path to allow importing main
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))

# Mock environment variables to simulate leakage
os.environ["SECRET_API_KEY"] = "super_secret_value"
os.environ["OLB_CUSTOM_VAR"] = "should_be_passed"

from main import build_case, run_case, CommandRequest

class TestEnvSanitization(unittest.TestCase):
    def test_build_case_sanitizes_env(self):
        """
        Verify that build_case sanitizes environment variables.
        """
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.return_code = 0

            mock_lock = MagicMock()
            mock_lock.acquire.return_value = True

            with patch("main.validate_case_path", return_value="/tmp/safe/case"), \
                 patch("os.path.exists", return_value=True), \
                 patch("main.execution_lock", mock_lock):

                req = CommandRequest(case_path="some/case")
                build_case(req)

                args, kwargs = mock_run.call_args
                env_passed = kwargs.get("env")

                self.assertIsNotNone(env_passed, "Environment should be passed explicitly")
                self.assertNotIn("SECRET_API_KEY", env_passed, "SECRET_API_KEY should be stripped")
                self.assertIn("PATH", env_passed, "PATH should be preserved")
                self.assertIn("OLB_CUSTOM_VAR", env_passed, "OLB_ variables should be preserved")

    def test_run_case_sanitizes_env(self):
        """
        Verify that run_case sanitizes environment variables.
        """
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.return_code = 0

            mock_lock = MagicMock()
            mock_lock.acquire.return_value = True

            with patch("main.validate_case_path", return_value="/tmp/safe/case"), \
                 patch("os.path.exists", return_value=True), \
                 patch("main.execution_lock", mock_lock):

                req = CommandRequest(case_path="some/case")
                run_case(req)

                args, kwargs = mock_run.call_args
                env_passed = kwargs.get("env")

                self.assertIsNotNone(env_passed, "Environment should be passed explicitly")
                self.assertNotIn("SECRET_API_KEY", env_passed, "SECRET_API_KEY should be stripped")
                self.assertIn("PATH", env_passed, "PATH should be preserved")
                self.assertIn("OLB_CUSTOM_VAR", env_passed, "OLB_ variables should be preserved")

if __name__ == '__main__':
    unittest.main()
