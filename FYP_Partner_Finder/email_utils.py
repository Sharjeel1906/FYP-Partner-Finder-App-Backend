import threading
import time
from django.core.mail import send_mail
from django.conf import settings


def send_email_async(subject, body, recipient_email):

    def task():
        try:
            time.sleep(0.3)

            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [recipient_email],
                fail_silently=False,
            )

        except Exception as e:
            print("EMAIL ERROR:", e)

    thread = threading.Thread(target=task, daemon=True)
    thread.start()