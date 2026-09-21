import os

import africastalking as at
import phonenumbers
from dotenv import load_dotenv

load_dotenv()

username = os.environ.get("AT_USERNAME")
api_key = os.environ.get("AT_API_KEY")
sender = os.environ.get("AT_SMS_SHORTCODE")

at.initialize(username, api_key)
sms = at.SMS


def send_sms(customer_name, item, quantity, total, phone_number):
    try:
        parsed_phone_number = phonenumbers.parse(phone_number, "KE")
    except phonenumbers.NumberParseException:
        raise Exception("Invalid Phone Number")

    # Verify that the parsed number is a valid phone number
    if phonenumbers.is_valid_number(parsed_phone_number):
        validated_phone_number = phonenumbers.format_number(
            parsed_phone_number, phonenumbers.PhoneNumberFormat.E164
        )
        message = (
            f"Hello {customer_name}, this is to inform you that your order of "
            f"{quantity} {item}(s), for a total of Ksh. {total} is "
            "ready for pickup. "
            "Thank you for your service."
        )
        try:
            sms.send(message, [validated_phone_number], sender)
        except Exception as e:
            raise Exception(f"An Error Occurred: {e}")
    else:
        raise Exception("Invalid Phone Number")
