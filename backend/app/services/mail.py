from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app


def _send(to_email: str, subject: str, html_body: str) -> None:
    server = current_app.config.get('MAIL_SERVER')
    username = current_app.config.get('MAIL_USERNAME')
    password = current_app.config.get('MAIL_PASSWORD')

    if not all([server, username, password]):
        current_app.logger.warning('Mail not configured — skipping send to %s: %s', to_email, subject)
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = username
    msg['To'] = to_email
    msg.attach(MIMEText(html_body, 'html'))

    with smtplib.SMTP(server, 587) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.sendmail(username, to_email, msg.as_string())


def send_verification_email(to_email: str, display_name: str, raw_token: str) -> None:
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
    link = f'{frontend_url}/verify-email?token={raw_token}'
    html = (
        f'<p>Hi {display_name},</p>'
        f'<p>Click the link below to verify your FinTrack account. '
        f'This link expires in 24 hours.</p>'
        f'<p><a href="{link}">{link}</a></p>'
        f'<p>If you did not create an account, ignore this email.</p>'
    )
    _send(to_email, 'Verify your FinTrack account', html)


def send_password_reset_email(to_email: str, display_name: str, raw_token: str) -> None:
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
    link = f'{frontend_url}/reset-password?token={raw_token}'
    html = (
        f'<p>Hi {display_name},</p>'
        f'<p>We received a request to reset your FinTrack password. '
        f'Click the link below — it expires in 15 minutes.</p>'
        f'<p><a href="{link}">{link}</a></p>'
        f'<p>If you did not request this, ignore this email. Your password has not changed.</p>'
    )
    _send(to_email, 'Reset your FinTrack password', html)
