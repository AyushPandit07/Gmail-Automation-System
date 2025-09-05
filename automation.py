import time
import smtplib
import imaplib
import email
import json
import threading
from email.mime.text import MIMEText
import os


class GmailAutomation:
    def __init__(self):
        self.running = False
        self.leads = []
        self.sent_times = {}
        self.reply_counts = {}
        self.followup_counts = {}
        self.followup_interval = 5 * 60  # 5 minutes in seconds
        self.auto_reply_limit = 4
        self.followup_limit = 4
        self.messages = self.load_messages()

    def load_messages(self):
        try:
            with open("messages.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                # ✅ Ensure keys exist
                if "initial" not in data or "auto_replies" not in data or "follow_ups" not in data:
                    raise ValueError("messages.json must contain 'initial', 'auto_replies', and 'follow_ups'")
                return data
        except Exception as e:
            print(f"Error loading messages.json: {e}")
            return {"initial": {"subject": "Hello", "body": "Hi {name},"},
                    "auto_replies": ["Thanks {name}, reply #{i+1}"],
                    "follow_ups": ["Just checking in {name}"]}

    def validate_credentials(self, gmail_user, app_password):
        """Check Gmail login before starting automation."""
        try:
            # Validate SMTP
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(gmail_user, app_password)

            # Validate IMAP
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(gmail_user, app_password)
            mail.logout()
            return True
        except Exception as e:
            return str(e)

    def send_email(self, gmail_user, app_password, to_email, subject, message):
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = gmail_user
            msg['To'] = to_email

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(gmail_user, app_password)
                server.sendmail(gmail_user, [to_email], msg.as_string())
            return True
        except Exception as e:
            print(f"Error sending to {to_email}: {e}")
            return False

    def save_reply(self, sender, subject, body):
        """Save replies into replies.json"""
        reply_file = "replies.json"
        data = []
        if os.path.exists(reply_file):
            try:
                with open(reply_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = []

        entry = {
            "sender": sender,
            "subject": subject,
            "body": body,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        data.append(entry)

        with open(reply_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def check_replies(self, gmail_user, app_password):
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(gmail_user, app_password)
            mail.select("inbox")
            status, data = mail.search(None, '(UNSEEN)')
            if status != "OK":
                return []

            replies = []
            for num in data[0].split():
                status, msg_data = mail.fetch(num, '(RFC822)')
                if status != "OK":
                    continue
                msg = email.message_from_bytes(msg_data[0][1])
                from_email = email.utils.parseaddr(msg['From'])[1]

                # ✅ Extract subject and body
                subject = msg.get("Subject", "")
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode(errors="ignore")
                            except Exception:
                                body = ""
                            break
                else:
                    try:
                        body = msg.get_payload(decode=True).decode(errors="ignore")
                    except Exception:
                        body = ""

                # ✅ Save reply before auto reply
                if from_email in [lead[1] for lead in self.leads]:
                    self.save_reply(from_email, subject, body)
                    replies.append(from_email)

            mail.logout()
            return replies
        except Exception as e:
            print("Error checking replies:", e)
            return []

    def automation_loop(self, gmail_user, app_password, log_callback):
        while self.running:
            now = time.time()
            replies = self.check_replies(gmail_user, app_password)

            # Handle replies
            for r in replies:
                name = self.get_name_from_email(r)
                reply_num = self.reply_counts.get(r, 0)
                if reply_num < self.auto_reply_limit:
                    try:
                        message_text = self.messages["auto_replies"][reply_num].format(name=name)
                    except Exception:
                        message_text = f"Thank you {name}, this is auto reply #{reply_num + 1}"
                    if self.send_email(gmail_user, app_password, r, f"Re: {self.messages['initial']['subject']}", message_text):
                        self.reply_counts[r] = reply_num + 1
                        log_callback(f"✅ Auto-replied #{reply_num + 1} to {r}")

            # Handle follow-ups
            for name, email_addr in self.leads:
                if email_addr in replies:
                    continue
                if email_addr not in self.sent_times:
                    continue
                elapsed = now - self.sent_times[email_addr]
                followup_num = self.followup_counts.get(email_addr, 0)
                if elapsed >= self.followup_interval and followup_num < self.followup_limit:
                    try:
                        followup_text = self.messages["follow_ups"][followup_num].format(name=name)
                    except Exception:
                        followup_text = f"Hi {name}, just checking in (follow-up #{followup_num + 1})"
                    if self.send_email(gmail_user, app_password, email_addr,
                                    f"Follow-up: {self.messages['initial']['subject']}",
                                    followup_text):
                        self.sent_times[email_addr] = now
                        self.followup_counts[email_addr] = followup_num + 1
                        log_callback(f"📩 Sent follow-up #{followup_num + 1} to {email_addr}")

            time.sleep(10)

    def start(self, gmail_user, app_password, log_callback):
        # ✅ First validate credentials
        validation = self.validate_credentials(gmail_user, app_password)
        if validation is not True:
            log_callback(f"❌ Login failed: {validation}. Please try again with correct credentials.")
            self.running = False
            return  # 🚨 STOP here if login fails

        self.running = True
        log_callback("🚀 Automation started.")  # ✅ Log only after successful login

        # Send initial emails
        for name, email_addr in self.leads:
            message_text = self.messages["initial"]["body"].format(name=name)
            if self.send_email(gmail_user, app_password, email_addr,
                           self.messages["initial"]["subject"], message_text):
                self.sent_times[email_addr] = time.time()
                self.reply_counts[email_addr] = 0
                self.followup_counts[email_addr] = 0
                log_callback(f"✅ Sent initial email to {email_addr}")

        # Start background loop
        t = threading.Thread(
            target=self.automation_loop,
            args=(gmail_user, app_password, log_callback),
            daemon=True
        )
        t.start()

    def stop(self):
        self.running = False

    def get_name_from_email(self, email_addr):
        for name, e in self.leads:
            if e == email_addr:
                return name
        return ""
