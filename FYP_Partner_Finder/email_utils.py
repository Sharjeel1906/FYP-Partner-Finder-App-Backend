import threading
import time
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def send_email_async(subject, body_text, recipient_email, body_html=None):

    def task():
        try:
            time.sleep(0.3)
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body_text,  # plain text fallback
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            if body_html:
                msg.attach_alternative(body_html, "text/html")
            msg.send(fail_silently=False)

        except Exception as e:
            print("EMAIL ERROR:", e)

    thread = threading.Thread(target=task, daemon=True)
    thread.start()