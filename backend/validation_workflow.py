import logging
import secrets
import backend.db as db
import backend.email_service as email_service

logger = logging.getLogger(__name__)

def approve_ticket_by_admin(ticket_id: int) -> bool:
    """Approve a ticket as validated by the admin, generate a secure link token, and email the department."""
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        logger.error(f"Cannot approve ticket #{ticket_id}: Ticket not found.")
        return False
        
    # Generate secure random token
    token = secrets.token_urlsafe(24)
    
    try:
        # Save validation status and token in DB
        db.set_ticket_validation(ticket_id, admin_approved=1, validation_token=token)
        
        # Reload ticket to get full details (with department details)
        updated_ticket = db.get_ticket(ticket_id)
        
        # Send completion link email to department
        sent = email_service.send_department_completion_link(updated_ticket, token)
        if sent:
            logger.info(f"Ticket #{ticket_id} approved. Completion link emailed to department.")
            return True
        else:
            logger.error(f"Failed to send department completion link email for Ticket #{ticket_id}.")
            return False
            
    except Exception as e:
        logger.exception(f"Error during admin approval of Ticket #{ticket_id}: {e}")
        return False

def reject_ticket_by_admin(ticket_id: int) -> bool:
    """Mark a ticket as validation failed / rejected by the admin."""
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        logger.error(f"Cannot reject ticket #{ticket_id}: Ticket not found.")
        return False
        
    try:
        db.set_ticket_validation(ticket_id, admin_approved=-1, validation_token=None)
        logger.info(f"Ticket #{ticket_id} marked as validation failed by admin.")
        return True
    except Exception as e:
        logger.exception(f"Error during admin rejection of Ticket #{ticket_id}: {e}")
        return False
