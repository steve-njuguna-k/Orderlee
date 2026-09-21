from unittest.mock import patch

from django.db.utils import OperationalError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.services import send_sms, sender


class SendSMSTestCase(TestCase):
    @patch("core.services.sms.send")
    def test_send_sms_success(self, mock_sms_send):
        """Test sending an SMS with valid parameters and phone number."""
        mock_sms_send.return_value = {
            "SMSMessageData": {"Recipients": [{"statusCode": 101, "status": "Success"}]}
        }

        phone_number = "0714916889"
        customer_name = "John Snow"
        item = "Sneakers"
        quantity = 2
        total = "39.98"

        send_sms(customer_name, item, quantity, total, phone_number)

        expected_e164_phone = "+254714916889"
        expected_message = (
            "Hello John Snow, this is to inform you that your order "
            "of 2 Sneakers(s), "
            "for a total of Ksh. 39.98 is ready for pickup. Thank "
            "you for your service."
        )

        # Assert Africa's Talking SMS API was called with exact arguments
        mock_sms_send.assert_called_once_with(
            expected_message, [expected_e164_phone], sender
        )

    @patch("core.services.sms.send")
    def test_send_sms_api_exception(self, mock_sms_send):
        ("""Test that an exception from Africa's Talking SDK is"
            "caught and re-raised.""")
        mock_sms_send.side_effect = Exception("API connection timeout")

        phone_number = "0714916889"

        with self.assertRaises(Exception) as context:
            send_sms("Jane Doe", "Sweater", 1, "29.99", phone_number)

        self.assertIn(
            "An Error Occurred: API connection timeout", str(context.exception)
        )

    def test_send_sms_invalid_phone_number(self):
        """Test that passing an invalid phone number raises an exception."""
        invalid_phone_number = "not-a-phone-number"

        with self.assertRaises(Exception) as context:
            send_sms("Jane Doe", "Sweater", 1, "29.99", invalid_phone_number)

        self.assertIn("Invalid Phone Number", str(context.exception))

    @patch("core.services.sms.send")
    def test_send_sms_invalid_number_structure(self, mock_sms_send):
        ("""Test a phone number that parses without error but"
            "fails phonenumbers.is_valid_number().""")
        # "070000000" (9 digits total) is parsed by phonenumbers without
        # raising
        # NumberParseException, but evaluates to False for is_valid_number()
        invalid_structure_number = "070000000"

        with self.assertRaises(Exception) as context:
            send_sms("Jane Doe", "Sweater", 1, "29.99", invalid_structure_number)

        self.assertEqual(str(context.exception), "Invalid Phone Number")
        mock_sms_send.assert_not_called()


class HealthCheckTests(APITestCase):
    def setUp(self):
        # Update these URL names or paths to match your project's urls.py
        self.healthz_url = reverse("healthz")
        self.ready_url = reverse("ready")

    def test_healthz_returns_200_ok(self):
        """Test that the liveness probe returns HTTP 200 OK."""
        response = self.client.get(self.healthz_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})

    def test_ready_returns_200_when_database_is_healthy(self):
        ("""Test that readiness probe returns 200 OK when the"
            "database connection succeeds.""")
        response = self.client.get(self.ready_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok", "checks": {"database": "ok"}})

    @patch("django.db.connection.cursor")
    def test_ready_returns_503_when_database_fails(self, mock_cursor):
        ("""Test that readiness probe returns 503 Service"
            "Unavailable when DB raises OperationalError.""")
        mock_cursor.side_effect = OperationalError("Database connection failed")

        response = self.client.get(self.ready_url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(
            response.data, {"status": "error", "checks": {"database": "error"}}
        )
