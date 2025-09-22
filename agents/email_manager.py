import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(sender_email, password, recipient_emails, subject, body):
    if isinstance(recipient_emails, str):
        recipient_emails = [recipient_emails]  # single → list

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipient_emails)  # multiple recipients
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient_emails, msg.as_string())
        server.quit()
        return f"✅ Email sent successfully to {len(recipient_emails)} recipient(s)."
    except Exception as e:
        return f"❌ Failed to send email: {e}"

