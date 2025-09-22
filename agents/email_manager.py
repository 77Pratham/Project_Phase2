import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(sender_email, password, recipient_email, subject, body, smtp_server="smtp.gmail.com", port=465):
    """
    Send an email using Gmail SMTP.
    """
    try:
        # Create email
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Secure connection
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        return f"Email sent to {recipient_email} ✅"

    except Exception as e:
        return f"Error sending email: {e}"
