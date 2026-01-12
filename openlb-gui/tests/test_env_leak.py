
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
from fastapi import Request

class TestEnvSanitization(unittest.TestCase):
    def setUp(self):
        self.mock_request = MagicMock(spec=Request)
        self.mock_request.client.host = "127.0.0.1"

    def test_build_case_sanitizes_env(self):
        """
        Verify that build_case sanitizes environment variables.
        """
        # Patch run_command_safe instead of subprocess.run
        with patch("main.run_command_safe", return_value=0) as mock_run:

            mock_lock = MagicMock()
            mock_lock.acquire.return_value = True

            with patch("main.validate_case_path", return_value="/tmp/safe/case"), \
                 patch("os.path.exists", return_value=True), \
                 patch("main.execution_lock", mock_lock):

                req = CommandRequest(case_path="some/case")
                build_case(req, self.mock_request)

                args, kwargs = mock_run.call_args
                env_passed = kwargs.get("env")
                # If env was passed as positional arg (it is 3rd arg in run_command_safe)
                if not env_passed and len(args) > 2:
                    env_passed = args[2]

                self.assertIsNotNone(env_passed, "Environment should be passed explicitly")
                self.assertNotIn("SECRET_API_KEY", env_passed, "SECRET_API_KEY should be stripped")
                self.assertIn("PATH", env_passed, "PATH should be preserved")
                self.assertIn("OLB_CUSTOM_VAR", env_passed, "OLB_ variables should be preserved")

    def test_run_case_sanitizes_env(self):
        """
        Verify that run_case sanitizes environment variables.
        """
        # Patch run_command_safe instead of subprocess.run
        with patch("main.run_command_safe", return_value=0) as mock_run:

            mock_lock = MagicMock()
            mock_lock.acquire.return_value = True

            with patch("main.validate_case_path", return_value="/tmp/safe/case"), \
                 patch("os.path.exists", return_value=True), \
                 patch("main.execution_lock", mock_lock):

                req = CommandRequest(case_path="some/case")
                run_case(req, self.mock_request)

                args, kwargs = mock_run.call_args
                env_passed = kwargs.get("env")
                # If env was passed as positional arg (it is 3rd arg in run_command_safe)
                if not env_passed and len(args) > 2:
                    env_passed = args[2]

                self.assertIsNotNone(env_passed, "Environment should be passed explicitly")
                self.assertNotIn("SECRET_API_KEY", env_passed, "SECRET_API_KEY should be stripped")
                self.assertIn("PATH", env_passed, "PATH should be preserved")
                self.assertIn("OLB_CUSTOM_VAR", env_passed, "OLB_ variables should be preserved")

if __name__ == '__main__':
    unittest.main()
