import base64
import hashlib
import json
import random
import secrets
import string
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from oauth2_provider.models import get_application_model
from rest_framework import status
from rest_framework.test import APIClient

from .models import Customer
from .views import CustomerAPIView

Application = get_application_model()


class CustomerTestCase(TestCase):
    def setUp(self):
        # Set up test OAuth2 client credentials and other required data
        self.client_id = secrets.token_urlsafe(16)
        self.client_secret = secrets.token_urlsafe(50)

        # Create a test OAuth2 application
        self.application = Application.objects.create(
            name="Test Application",
            client_id=self.client_id,
            client_secret=self.client_secret,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris="http://localhost:8000/o/callback",
            algorithm=Application.RS256_ALGORITHM,
        )

        # Set up data for creating a superuser
        self.superuser_data = {
            "username": "admin",
            "password": "adminpassword",  # pragma: allowlist secret
            "email": "admin@example.com",
        }

        # Generate code verifier and challenge for PKCE
        code_verifier = "".join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(random.randint(43, 128))
        )
        code_verifier = base64.urlsafe_b64encode(code_verifier.encode("utf-8"))
        self.verifier = code_verifier.decode("utf-8")

        code_challenge = hashlib.sha256(code_verifier).digest()
        code_challenge = (
            base64.urlsafe_b64encode(code_challenge).decode("utf-8").replace("=", "")
        )
        self.challenge = code_challenge

        # Create a superuser for testing
        self.user = User.objects.create_superuser(
            username=self.superuser_data["username"],
            email=self.superuser_data["email"],
            password=self.superuser_data["password"],
        )
        self.client = APIClient(raise_request_exception=True)

        # Test the OAuth2 authorization code flow
        self.client.login(
            username=self.superuser_data["username"],
            password=self.superuser_data["password"],
        )

        authorization_url = reverse("oauth2_provider:authorize")
        response = self.client.get(
            authorization_url,
            {
                "response_type": "code",
                "code_challenge": self.challenge,
                "code_challenge_method": "S256",
                "client_id": self.application.client_id,
                "redirect_uri": self.application.redirect_uris.split()[0],
                "scope": "openid",
            },
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("oauth2_provider:authorize"),
            {
                "response_type": "code",
                "code_challenge": self.challenge,
                "code_challenge_method": "S256",
                "client_id": self.application.client_id,
                "redirect_uri": self.application.redirect_uris.split()[0],
                "scope": "openid",
                "allow": True,
            },
        )
        self.assertEqual(response.status_code, 302)

        redirect_url = response.url
        parsed_url = urlparse(redirect_url)
        query_parameters = parse_qs(parsed_url.query)
        authorization_code = query_parameters.get("code", [])

        # Simulate callback URL response
        callback_url = reverse("oauth_open_id_callback")
        response = self.client.get(
            callback_url,
            {
                "code": authorization_code[0],
                "state": secrets.token_urlsafe(50),
            },
        )
        self.assertEqual(response.status_code, 200)

        # Request an access token
        token_data = {
            "grant_type": "authorization_code",
            "code": authorization_code[0],
            "redirect_uri": self.application.redirect_uris.split()[0],
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code_verifier": self.verifier,
        }

        token_url = reverse("oauth2_provider:token")
        response = self.client.post(token_url, token_data)
        self.assertEqual(response.status_code, 200)

        token_info = json.loads(response.content)
        self.access_token = token_info.get("access_token")
        self.assertIsNotNone(self.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_customer_str_representation(self):
        ("""Test Customer model __str__ method to achieve 100%"
            "coverage on models.py""")
        customer = Customer.objects.create(
            first_name="John", last_name="Doe", phone_number="0700000000"
        )
        self.assertEqual(str(customer), "John Doe")

    def test_create_customer(self):
        data = {
            "first_name": "Steve",
            "last_name": "Harvey",
            "phone_number": "0712345678",
        }
        response = self.client.post("/api/v1/customers/", data)
        response_info = json.loads(response.content)
        self.assertEqual(response_info["status"], 201)
        self.assertTrue(Customer.objects.filter(first_name="Steve").exists())

    def test_create_customer_validation_error(self):
        data = {
            "last_name": "Perez",
            "phone_number": "0724567890",
        }
        response = self.client.post("/api/v1/customers/", data)
        response_info = json.loads(response.content)
        self.assertEqual(response_info["status"], status.HTTP_400_BAD_REQUEST)
        self.assertIn("first_name", response_info["results"])

    @patch.object(CustomerAPIView, "serializer_class")
    def test_create_customer_exception_handling(self, mock_serializer):
        # Cause the class instantiation inside self.serializer_class(data=...)
        # to raise an Exception
        mock_serializer.side_effect = Exception("Database error")

        data = {
            "first_name": "Steve",
            "last_name": "Harvey",
            "phone_number": "0712345678",
        }
        response = self.client.post("/api/v1/customers/", data)
        response_info = json.loads(response.content)

        self.assertEqual(response_info["status"], 400)
        self.assertEqual(response_info["results"]["error"], "Database error")

    def test_read_customer(self):
        customer = Customer.objects.create(
            first_name="Jesicca",
            last_name="Pearson",
            phone_number="0711223344",
        )
        response = self.client.get(f"/api/v1/customers/{customer.id}/")
        response_info = json.loads(response.content)
        self.assertEqual(response_info["status"], 200)
        self.assertEqual(response_info["results"]["first_name"], "Jesicca")

    def test_list_customers(self):
        Customer.objects.bulk_create(
            [
                Customer(
                    first_name="Jesicca",
                    last_name="Knowles",
                    phone_number="0711223344",
                ),
                Customer(
                    first_name="Moses",
                    last_name="Green",
                    phone_number="0723443521",
                ),
            ]
        )
        response = self.client.get("/api/v1/customers/")
        response_info = json.loads(response.content)
        self.assertEqual(response_info["status"], 200)
        self.assertEqual(len(response_info["results"]), 2)

    def test_update_customer(self):
        customer = Customer.objects.create(
            first_name="Mike", last_name="Ross", phone_number="0798765432"
        )
        updated_data = {
            "first_name": "Louis",
            "last_name": "Litt",
            "phone_number": "0722333444",
        }
        response = self.client.patch(
            f"/api/v1/customers/{customer.id}/", updated_data, format="json"
        )
        response_info = json.loads(response.content)
        self.assertEqual(response_info["status"], 200)

        customer.refresh_from_db()
        self.assertEqual(customer.first_name, "Louis")

    def test_update_customer_validation_error(self):
        customer = Customer.objects.create(
            first_name="John",
            last_name="Crown",
            phone_number="0755123456",
        )
        invalid_data = {
            "first_name": "",
            "last_name": "Crown",
            "phone_number": "0753125678",
        }
        response = self.client.patch(
            f"/api/v1/customers/{customer.id}/", invalid_data, format="json"
        )
        response_info = json.loads(response.content)
        self.assertEqual(response_info["status"], status.HTTP_400_BAD_REQUEST)
        self.assertIn("first_name", response_info["results"])

    def test_delete_customer(self):
        customer = Customer.objects.create(
            first_name="Steve", last_name="Harvey", phone_number="0712345678"
        )
        response = self.client.delete(f"/api/v1/customers/{customer.id}/")
        response_info = json.loads(response.content)
        self.assertEqual(response_info["status"], 204)
        self.assertFalse(Customer.objects.filter(id=customer.id).exists())

    def test_delete_customer_not_found(self):
        response = self.client.delete("/api/v1/customers/99999/")
        response_info = json.loads(response.content)
        self.assertEqual(response_info["status"], 400)

    @patch.object(CustomerAPIView, "serializer_class")
    def test_read_customer_exception_handling(self, mock_serializer):
        customer = Customer.objects.create(
            first_name="Jessica",
            last_name="Pearson",
            phone_number="0711223344",
        )

        mock_serializer.side_effect = Exception("Customer serialization error")

        response = self.client.get(f"/api/v1/customers/{customer.id}/")

        response_info = json.loads(response.content)

        self.assertEqual(response_info["status"], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_info["results"]["error"], "Customer serialization error"
        )

    @patch.object(CustomerAPIView, "serializer_class")
    def test_patch_customer_exception_handling(self, mock_serializer):
        """Triggers lines 89-90 in views.py"""
        mock_serializer.side_effect = Exception("Database error updating customer")
        customer = Customer.objects.create(
            first_name="Test", last_name="User", phone_number="0700000000"
        )

        response = self.client.patch(
            f"/api/v1/customers/{customer.id}/",
            {"first_name": "Updated"},
            format="json",
        )
        response_info = json.loads(response.content)

        self.assertEqual(response_info["status"], 400)
        self.assertEqual(
            response_info["results"]["error"],
            "Database error updating customer",
        )
