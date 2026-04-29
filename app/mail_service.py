import imaplib
import os
import smtplib
from datetime import datetime
from email import message_from_bytes
from email.header import decode_header, make_header
from email.message import EmailMessage as StdEmailMessage
from email.utils import getaddresses, parsedate_to_datetime

from cryptography.fernet import Fernet, InvalidToken

from .extensions import db
from .models import EmailAttachment, EmailMessage


SYNC_LIMIT = 50


class MailConfigurationError(RuntimeError):
    pass


class MailSyncError(RuntimeError):
    pass


def credentials_key_configured():
    return bool(os.environ.get("EMAIL_CREDENTIALS_KEY"))


def get_fernet():
    key = os.environ.get("EMAIL_CREDENTIALS_KEY")
    if not key:
        raise MailConfigurationError(
            "EMAIL_CREDENTIALS_KEY non configurata. Imposta una chiave Fernet valida "
            "prima di salvare password, sincronizzare o inviare email."
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:
        raise MailConfigurationError("EMAIL_CREDENTIALS_KEY non e una chiave Fernet valida.") from exc


def encrypt_password(password):
    if not password:
        return None
    return get_fernet().encrypt(password.encode()).decode()


def decrypt_password(account):
    if not account.password_encrypted:
        raise MailConfigurationError("Password account email non configurata.")
    try:
        return get_fernet().decrypt(account.password_encrypted.encode()).decode()
    except InvalidToken as exc:
        raise MailConfigurationError(
            "Password email non decifrabile con EMAIL_CREDENTIALS_KEY corrente."
        ) from exc


def decode_mime_header(value):
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def parse_message_datetime(value):
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed and parsed.tzinfo:
            return parsed.astimezone().replace(tzinfo=None)
        return parsed
    except Exception:
        return None


def addresses_to_string(headers):
    addresses = getaddresses(headers)
    return ", ".join(
        email or name for name, email in addresses if (email or name)
    )


def decode_part_payload(part):
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def extract_bodies_and_attachments(parsed_message):
    text_parts = []
    html_parts = []
    attachments = []

    if not parsed_message.is_multipart():
        content_type = parsed_message.get_content_type()
        if content_type == "text/plain":
            text_parts.append(decode_part_payload(parsed_message))
        elif content_type == "text/html":
            html_parts.append(decode_part_payload(parsed_message))
        return "\n\n".join(text_parts).strip(), "\n\n".join(html_parts).strip(), attachments

    for part in parsed_message.walk():
        content_disposition = (part.get("Content-Disposition") or "").lower()
        content_type = part.get_content_type()
        filename = decode_mime_header(part.get_filename())

        if filename or "attachment" in content_disposition:
            payload = part.get_payload(decode=True) or b""
            attachments.append(
                {
                    "filename": filename or "allegato",
                    "content_type": content_type,
                    "size": len(payload),
                }
            )
            continue

        if content_type == "text/plain":
            text_parts.append(decode_part_payload(part))
        elif content_type == "text/html":
            html_parts.append(decode_part_payload(part))

    return "\n\n".join(text_parts).strip(), "\n\n".join(html_parts).strip(), attachments


def parsed_message_to_model(account, uid, raw_message, folder="INBOX"):
    parsed = message_from_bytes(raw_message)
    body_text, body_html, attachments = extract_bodies_and_attachments(parsed)
    message = EmailMessage(
        account_id=account.id,
        message_id=(parsed.get("Message-ID") or "").strip() or None,
        imap_uid=str(uid),
        folder=folder,
        subject=decode_mime_header(parsed.get("Subject")) or "(senza oggetto)",
        from_address=addresses_to_string(parsed.get_all("From", [])),
        to_addresses=addresses_to_string(parsed.get_all("To", [])),
        cc_addresses=addresses_to_string(parsed.get_all("Cc", [])),
        reply_to=addresses_to_string(parsed.get_all("Reply-To", [])) or None,
        body_text=body_text or None,
        body_html=body_html or None,
        direction="inbound",
        is_read=False,
        received_at=parse_message_datetime(parsed.get("Date")),
    )
    message.attachments = [
        EmailAttachment(
            filename=attachment["filename"],
            content_type=attachment["content_type"],
            size=attachment["size"],
        )
        for attachment in attachments
    ]
    return message


def sync_inbox(account, limit=SYNC_LIMIT):
    password = decrypt_password(account)
    client = None
    imported = 0
    skipped = 0

    try:
        if account.imap_use_ssl:
            client = imaplib.IMAP4_SSL(account.imap_host, account.imap_port)
        else:
            client = imaplib.IMAP4(account.imap_host, account.imap_port)
        client.login(account.username, password)
        status, _ = client.select("INBOX")
        if status != "OK":
            raise MailSyncError("Impossibile aprire la cartella INBOX.")

        status, data = client.uid("search", None, "ALL")
        if status != "OK" or not data:
            raise MailSyncError("Ricerca messaggi IMAP non riuscita.")

        uids = data[0].split()[-limit:]
        for uid_bytes in uids:
            uid = uid_bytes.decode()
            exists = EmailMessage.query.filter_by(
                account_id=account.id,
                folder="INBOX",
                imap_uid=uid,
            ).first()
            if exists:
                skipped += 1
                continue

            status, fetch_data = client.uid("fetch", uid, "(RFC822)")
            if status != "OK" or not fetch_data:
                skipped += 1
                continue

            raw_message = None
            for item in fetch_data:
                if isinstance(item, tuple):
                    raw_message = item[1]
                    break
            if not raw_message:
                skipped += 1
                continue

            db.session.add(parsed_message_to_model(account, uid, raw_message))
            imported += 1

        account.last_sync_at = datetime.utcnow()
        db.session.commit()
        return {"imported": imported, "skipped": skipped}
    except (MailConfigurationError, MailSyncError):
        db.session.rollback()
        raise
    except Exception as exc:
        db.session.rollback()
        raise MailSyncError(f"Errore sync IMAP: {exc}") from exc
    finally:
        if client is not None:
            try:
                client.logout()
            except Exception:
                pass


def send_email(account, to_addresses, subject, body, cc_addresses=None, reply_to_message=None):
    password = decrypt_password(account)
    message = StdEmailMessage()
    message["From"] = account.email_address
    message["To"] = to_addresses
    if cc_addresses:
        message["Cc"] = cc_addresses
    message["Subject"] = subject
    if reply_to_message and reply_to_message.message_id:
        message["In-Reply-To"] = reply_to_message.message_id
        message["References"] = reply_to_message.message_id
    message.set_content(body or "")

    try:
        with smtplib.SMTP(account.smtp_host, account.smtp_port, timeout=30) as smtp:
            if account.smtp_use_tls:
                smtp.starttls()
            smtp.login(account.username, password)
            smtp.send_message(message)
    except Exception as exc:
        raise MailSyncError(f"Errore invio SMTP: {exc}") from exc

    return EmailMessage(
        account_id=account.id,
        message_id=message.get("Message-ID"),
        folder="SENT",
        subject=subject,
        from_address=account.email_address,
        to_addresses=to_addresses,
        cc_addresses=cc_addresses,
        body_text=body,
        direction="outbound",
        is_read=True,
        sent_at=datetime.utcnow(),
    )
