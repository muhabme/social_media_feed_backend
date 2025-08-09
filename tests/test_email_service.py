import pytest
from django.core import mail
from django.test import TestCase, override_settings


@pytest.mark.django_db
class EmailServiceTests(TestCase):
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_otp_email(self):
        """Test that OTP emails are sent correctly via locmem backend."""
        # Ensure outbox is empty at start
        mail.outbox.clear()

        # Send test email
        from django.core.mail import send_mail

        send_mail(
            subject="Your OTP Code",
            message="Your verification code is 123456",
            from_email="test@example.com",
            recipient_list=["user@example.com"],
            fail_silently=False,
        )

        # Check email was sent
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert email.subject == "Your OTP Code"
        assert "123456" in email.body
        assert email.to == ["user@example.com"]
