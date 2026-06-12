import logging
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

import backend.db as db
import backend.email_service as email_service

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Styled HTML Templates ──────────────────────────────────────────────

STYLE_HEAD = """
<head>
    <meta charset="utf-8">
    <title>FlowDesk - Ticket Resolution</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;800;900&display=swap');
        
        body {
            font-family: 'Space Grotesk', sans-serif;
            background-color: #050C1A;
            background-image:
                radial-gradient(ellipse 60% 40% at 15% 60%, rgba(0,229,255,0.04) 0%, transparent 70%),
                radial-gradient(ellipse 50% 50% at 85% 15%, rgba(124,77,255,0.06) 0%, transparent 70%),
                linear-gradient(160deg, #050C1A 0%, #062233 50%, #073D50 100%);
            color: #E0E6F4;
            height: 100vh;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        .card {
            background: linear-gradient(155deg, rgba(14,22,48,0.9) 0%, rgba(10,16,34,0.95) 100%);
            border-radius: 24px;
            padding: 3rem 2rem;
            max-width: 480px;
            width: 90%;
            text-align: center;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05);
            position: relative;
            overflow: hidden;
            animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .icon-container {
            width: 80px;
            height: 80px;
            margin: 0 auto 1.5rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        .icon-success {
            background: rgba(76, 217, 123, 0.12);
            border: 1px solid rgba(76, 217, 123, 0.3);
            color: #4CD97B;
            box-shadow: 0 0 20px rgba(76, 217, 123, 0.2);
        }

        .icon-error {
            background: rgba(255, 77, 109, 0.12);
            border: 1px solid rgba(255, 77, 109, 0.3);
            color: #FF4D6D;
            box-shadow: 0 0 20px rgba(255, 77, 109, 0.2);
        }

        h1 {
            font-size: 1.75rem;
            font-weight: 800;
            margin-bottom: 0.75rem;
            letter-spacing: -0.02em;
            line-height: 1.2;
        }

        h1.success { color: #4CD97B; }
        h1.error { color: #FF4D6D; }

        p {
            font-size: 0.95rem;
            color: rgba(224,230,244,0.65);
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }

        .ticket-info {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 12px;
            padding: 1rem;
            margin: 1.5rem 0;
            border: 1px solid rgba(255, 255, 255, 0.04);
            text-align: left;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            font-size: 0.88rem;
        }
        .info-row:last-child {
            margin-bottom: 0;
        }

        .info-label {
            color: #8A94B0;
        }

        .info-value {
            font-weight: 600;
            color: #C8D0E8;
        }

        .branding {
            font-size: 0.72rem;
            color: #4A5470;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            margin-top: 2rem;
            font-weight: 600;
        }
    </style>
</head>
"""

SUCCESS_HTML = f"""
<!DOCTYPE html>
<html>
{STYLE_HEAD}
<body>
    <div class="card">
        <div class="icon-container icon-success">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
        </div>
        <h1 class="success">Ticket Resolved</h1>
        <p>Thank you. The campus issue has been marked as resolved. An automated notification has been dispatched to the student.</p>
        
        <div class="ticket-info">
            <div class="info-row">
                <span class="info-label">Ticket ID:</span>
                <span class="info-value">#{{ticket_id}}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Title:</span>
                <span class="info-value">{{title}}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Department:</span>
                <span class="info-value">{{department}}</span>
            </div>
        </div>

        <div class="branding">⚡ FlowDesk</div>
    </div>
</body>
</html>
"""

ERROR_HTML = f"""
<!DOCTYPE html>
<html>
{STYLE_HEAD}
<body>
    <div class="card">
        <div class="icon-container icon-error">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </div>
        <h1 class="error">Validation Failed</h1>
        <p>{{error_message}}</p>
        
        <div class="branding">⚡ FlowDesk</div>
    </div>
</body>
</html>
"""

# ── Routes ─────────────────────────────────────────────────────────────

@router.get("/api/tickets/complete", response_class=HTMLResponse)
async def complete_ticket(token: str = Query(..., description="Secure resolution token")) -> HTMLResponse:
    """FastAPI endpoint clicked by department representatives to resolve a ticket."""
    if not token.strip():
        return HTMLResponse(
            content=ERROR_HTML.replace("{error_message}", "Resolution token is missing or empty."),
            status_code=400
        )

    # Fetch ticket details by token
    ticket = db.get_ticket_by_validation_token(token)
    if not ticket:
        return HTMLResponse(
            content=ERROR_HTML.replace("{error_message}", "This resolution link is invalid, expired, or has already been used."),
            status_code=400
        )

    ticket_id = ticket["ticket_id"]
    
    try:
        # Resolve ticket in DB
        db.resolve_ticket_by_token(ticket_id)
        
        # Try to send email to student
        user = db.get_user_by_telegram_id(ticket["telegram_id"])
        student_email = user.get("verified_email") if user else None
        
        if student_email:
            email_service.send_student_resolution_notification(ticket, student_email)
            logger.info(f"Student notification email queued for ticket #{ticket_id} to {student_email}")
        else:
            logger.warning(f"No verified email found for user {ticket['telegram_id']} (Ticket #{ticket_id}). Skipping student email.")
        
        # Return success page
        html = SUCCESS_HTML.format(
            ticket_id=ticket_id,
            title=ticket["title"],
            department=ticket.get("department_name") or ticket.get("assigned_dept") or "Support"
        )
        return HTMLResponse(content=html, status_code=200)

    except Exception as exc:
        logger.exception(f"Error while completing ticket #{ticket_id} via token link")
        return HTMLResponse(
            content=ERROR_HTML.replace("{error_message}", f"Internal system error during ticket resolution: {exc}"),
            status_code=500
        )
