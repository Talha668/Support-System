from django.core.mail import send_mail
from django.conf import settings
from apps.support.models import TicketHistory






class NotificationService:
    """Service for sending notifications"""
    
    @staticmethod
    def notify_ticket_assignment(ticket, agent):
        """Notify agent of new ticket assignment"""
        subject = f"New Ticket Assigned: {ticket.id}"
        message = f"""
        Ticket {ticket.id} has been assigned to you.
        
        Title: {ticket.title}
        Priority: {ticket.get_priority_display()}
        Customer: {ticket.customer_name}
        SLA Deadline: {ticket.sla_response_deadline}
        
        Please respond within SLA timeframe.
        """
        
        NotificationService._send_notification(agent, subject, message)
        NotificationService._create_notification_log(ticket, agent, 'assignment')
    
    @staticmethod
    def notify_sla_warning(ticket):
        """Send SLA breach warning"""
        if not ticket.assigned_to:
            return
        
        hours_remaining = ticket.get_time_until_response_deadline()
        if hours_remaining:
            hours = hours_remaining.total_seconds() / 3600
            
            if hours <= 1:
                urgency = "CRITICAL"
            elif hours <= 2:
                urgency = "URGENT"
            else:
                urgency = "WARNING"
            
            subject = f"{urgency}: SLA Breach Imminent - Ticket {ticket.id}"
            message = f"""
            {urgency} WARNING
            
            Ticket {ticket.id} will breach SLA in {hours:.1f} hours.
            
            Title: {ticket.title}
            Current Status: {ticket.get_status_display()}
            SLA Deadline: {ticket.sla_response_deadline}
            
            Please take immediate action.
            """
            
            NotificationService._send_notification(ticket.assigned_to, subject, message)
            NotificationService._create_notification_log(ticket, ticket.assigned_to, 'sla_warning')
    
    @staticmethod
    def notify_sla_breach(ticket):
        """Notify of SLA breach"""
        if ticket.assigned_to:
            subject = f"SLA BREACHED - Ticket {ticket.id}"
            message = f"""
            SLA has been breached for Ticket {ticket.id}.
            
            Title: {ticket.title}
            Breach Reason: {ticket.sla_breach_reason}
            
            This ticket has been flagged and may be escalated.
            """
            
            NotificationService._send_notification(ticket.assigned_to, subject, message)
            NotificationService._create_notification_log(ticket, ticket.assigned_to, 'sla_breach')
        
        # Notify team manager
        if ticket.assigned_team:
            NotificationService._notify_team_managers(ticket)
    
    @staticmethod
    def notify_escalation(ticket, escalation_team):
        """Notify of ticket escalation"""
        subject = f"TICKET ESCALATED - {ticket.id}"
        message = f"""
        Ticket {ticket.id} has been escalated.
        
        Title: {ticket.title}
        Priority: {ticket.get_priority_display()}
        Escalation Level: {ticket.escalation_level}
        
        It has been assigned to {escalation_team.name}.
        """
        
        # Notify escalation team members
        agents = escalation_team.agents.filter(status='online')
        for agent in agents:
            NotificationService._send_notification(agent, subject, message)
        
        NotificationService._create_notification_log(ticket, None, 'escalation')
    
    @staticmethod
    def _send_notification(agent, subject, message):
        """Send notification via email"""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[agent.user.email],
                fail_silently=True,
            )
        except Exception as e:
            # Log the error
            print(f"Failed to send notification to {agent}: {str(e)}")
    
    @staticmethod
    def _create_notification_log(ticket, agent, notification_type):
        """Create notification log entry"""
        TicketHistory.objects.create(
            ticket=ticket,
            action=notification_type,
            performed_by=agent,
            comment=f"Notification sent: {notification_type}"
        )
    
    @staticmethod
    def _notify_team_managers(ticket):
        """Notify all managers in the team"""
        from apps.accounts.models import User
        
        managers = User.objects.filter(
            role='manager',
            agent_profile__team=ticket.assigned_team
        )
        
        subject = f"SLA Breach in Your Team - Ticket {ticket.id}"
        message = f"""
        A ticket in your team has breached SLA.
        
        Ticket ID: {ticket.id}
        Assigned to: {ticket.assigned_to.user.get_full_name() if ticket.assigned_to else 'Unassigned'}
        Customer: {ticket.customer_name}
        """
        
        for manager in managers:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[manager.email],
                fail_silently=True,
            )