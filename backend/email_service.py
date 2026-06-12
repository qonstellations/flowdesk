import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import backend.db as db

logger = logging.getLogger(__name__)

def get_email_config() -> dict:
    return {
        "host": os.getenv("SMTP_HOST", "").strip(),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", "").strip(),
        "from": os.getenv("SMTP_FROM", "noreply@flowdesk.edu").strip(),
        "base_url": os.getenv("BASE_URL", "http://localhost:8000").strip().rstrip("/"),
    }

def _send_email(to_email: str, subject: str, html_content: str) -> bool:
    config = get_email_config()
    
    # If no SMTP user or host is configured, fall back to a mock delivery
    if not config["host"] or not config["user"]:
        logger.warning(
            f"[MOCK EMAIL] To: {to_email}\nSubject: {subject}\n"
            "Configure SMTP_HOST and SMTP_USER in .env to send real emails."
        )
        # Write the mock email details to a local file for developers to verify the HTML easily
        mock_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mock_emails")
        os.makedirs(mock_dir, exist_ok=True)
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{to_email.replace('@', '_').replace('.', '_')}.html"
        with open(os.path.join(mock_dir, filename), "w", encoding="utf-8") as f:
            f.write(f"<!-- To: {to_email} -->\n<!-- Subject: {subject} -->\n{html_content}")
        logger.info(f"[MOCK EMAIL] Written to data/mock_emails/{filename}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = config["from"] or config["user"]
        msg["To"] = to_email
        msg.attach(MIMEText(html_content, "html"))

        # Connect to SMTP
        server = smtplib.SMTP(config["host"], config["port"], timeout=10)
        server.ehlo()
        # Start TLS if port is 587
        if config["port"] == 587:
            server.starttls()
            server.ehlo()
        
        if config["password"]:
            server.login(config["user"], config["password"])
            
        server.sendmail(msg["From"], [to_email], msg.as_string())
        server.quit()
        logger.info(f"Email successfully sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
        return False

def send_department_completion_link(ticket: dict, token: str) -> bool:
    """Send verification/completion email to department."""
    config = get_email_config()
    dept_name = ticket.get("department_name") or ticket.get("assigned_dept") or "Support"
    dept_email = ticket.get("department_email") or ticket.get("escalation_contact") or ""
    
    if not dept_email:
        # Check if we can fetch department details to get the email
        dept_id = ticket.get("department_id")
        if dept_id:
            dept = db.get_department(dept_id)
            if dept:
                dept_email = dept.get("escalation_contact") or ""
                
    if not dept_email:
        logger.warning(f"No escalation email found for department '{dept_name}' on Ticket #{ticket['ticket_id']}. Falling back to test email.")
        # Use a fallback email for testing
        dept_email = "pp398444@gmail.com"

    # Construct the completion link
    completion_link = f"{config['base_url']}/api/tickets/complete?token={token}"

    subject = f"[FlowDesk] Action Required: Ticket #{ticket['ticket_id']} - {ticket['title']}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 8px; border: 1px solid #e1e4e8; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
            .header {{ border-bottom: 2px solid #00E5FF; padding-bottom: 15px; margin-bottom: 20px; }}
            .logo {{ font-size: 24px; font-weight: 800; color: #073D50; text-transform: uppercase; letter-spacing: -1px; }}
            .title {{ font-size: 18px; font-weight: 700; margin-top: 0; color: #222; }}
            .details-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .details-table td {{ padding: 10px; border-bottom: 1px solid #f0f0f0; }}
            .details-table td.label {{ font-weight: 600; color: #5A6480; width: 30%; }}
            .btn-container {{ text-align: center; margin: 30px 0; }}
            .btn {{ background-color: #00E5FF; color: #050C1A; padding: 12px 24px; font-weight: bold; text-decoration: none; border-radius: 6px; font-size: 16px; box-shadow: 0 4px 6px rgba(0,229,255,0.2); display: inline-block; }}
            .footer {{ font-size: 12px; color: #8A94B0; border-top: 1px solid #e1e4e8; padding-top: 15px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <span class="logo">⚡ FlowDesk</span>
            </div>
            <h2 class="title">New Ticket Assigned to {dept_name}</h2>
            <p>Dear Department Representative,</p>
            <p>A campus complaint has been assigned to your department and requires your attention. Please review the details below:</p>
            
            <table class="details-table">
                <tr>
                    <td class="label">Ticket ID</td>
                    <td>#{ticket['ticket_id']}</td>
                </tr>
                <tr>
                    <td class="label">Subject</td>
                    <td><strong>{ticket['title']}</strong></td>
                </tr>
                <tr>
                    <td class="label">Description</td>
                    <td>{ticket['description']}</td>
                </tr>
                <tr>
                    <td class="label">Location</td>
                    <td>{ticket['location']}</td>
                </tr>
                <tr>
                    <td class="label">Priority</td>
                    <td>{ticket['priority']}</td>
                </tr>
            </table>

            <p>Once you have finished the necessary repairs or resolved the issue, please click the button below to mark this ticket as resolved in the system:</p>
            
            <div class="btn-container">
                <a href="{completion_link}" class="btn">Mark Ticket Resolved</a>
            </div>

            <p style="font-size: 13px; color: #FF8C00;">⚠️ <em>Note: This link is secure, unique to this issue, and can only be clicked once.</em></p>
            
            <div class="footer">
                This is an automated notification from FlowDesk. Please do not reply directly to this email.
            </div>
        </div>
    </body>
    </html>
    """
    return _send_email(dept_email, subject, html_content)


def send_student_resolution_notification(ticket: dict, student_email: str) -> bool:
    """Send confirmation email to the student who submitted the ticket."""
    subject = f"[FlowDesk] Ticket #{ticket['ticket_id']} Resolved - {ticket['title']}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 8px; border: 1px solid #e1e4e8; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
            .header {{ border-bottom: 2px solid #4CD97B; padding-bottom: 15px; margin-bottom: 20px; }}
            .logo {{ font-size: 24px; font-weight: 800; color: #073D50; text-transform: uppercase; letter-spacing: -1px; }}
            .title {{ font-size: 18px; font-weight: 700; margin-top: 0; color: #222; }}
            .details-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .details-table td {{ padding: 10px; border-bottom: 1px solid #f0f0f0; }}
            .details-table td.label {{ font-weight: 600; color: #5A6480; width: 30%; }}
            .status-badge {{ color: #4CD97B; font-weight: bold; font-size: 16px; }}
            .footer {{ font-size: 12px; color: #8A94B0; border-top: 1px solid #e1e4e8; padding-top: 15px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <span class="logo">⚡ FlowDesk</span>
            </div>
            <h2 class="title" style="color: #4CD97B;">Your Issue Has Been Resolved</h2>
            <p>Dear Student,</p>
            <p>We are pleased to inform you that your complaint has been resolved by the assigned department. Here are the ticket details:</p>
            
            <table class="details-table">
                <tr>
                    <td class="label">Ticket ID</td>
                    <td>#{ticket['ticket_id']}</td>
                </tr>
                <tr>
                    <td class="label">Subject</td>
                    <td><strong>{ticket['title']}</strong></td>
                </tr>
                <tr>
                    <td class="label">Description</td>
                    <td>{ticket['description']}</td>
                </tr>
                <tr>
                    <td class="label">Status</td>
                    <td><span class="status-badge">Resolved ✓</span></td>
                </tr>
            </table>

            <p>Thank you for using FlowDesk to report and improve our campus environment. If you believe the issue was not fully resolved, please contact General Admin or submit a new report.</p>
            
            <div class="footer">
                This is an automated notification from FlowDesk. Please do not reply directly to this email.
            </div>
        </div>
    </body>
    </html>
    """
    return _send_email(student_email, subject, html_content)
