import unittest

from main import _build_sms, is_action_required


class ActionDetectionTests(unittest.TestCase):
    def test_detects_action_language_in_subject_or_body(self):
        self.assertTrue(is_action_required("Action required: confirm details", ""))
        self.assertTrue(
            is_action_required("Account update", "Please submit the form by Friday.")
        )

    def test_ignores_email_without_action_language(self):
        self.assertFalse(
            is_action_required("Your weekly reading list", "Here are this week's articles.")
        )

    def test_weekly_sms_reports_empty_inbox_scan(self):
        from datetime import datetime

        message = _build_sms([], datetime(2026, 11, 23))
        self.assertIn("no action-required emails found", message)


if __name__ == "__main__":
    unittest.main()
