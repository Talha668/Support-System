from django.core.management.base import BaseCommand
from apps.support.models import Ticket
from apps.support.services.notification_service import NotificationService






class Command(BaseCommand):
    help = 'Check for SLA breaches and send notifications'
    
    def handle(self, *args, **kwargs):
        # Check all active tickets
        active_tickets = Ticket.objects.filter(status__in=['open', 'in_progress', 'pending'])
        
        breach_count = 0
        warning_count = 0
        
        for ticket in active_tickets:
            # Check if already breached
            if ticket.check_sla_status():
                if not ticket.sla_breached:  # New breach
                    NotificationService.notify_sla_breach(ticket)
                    breach_count += 1
            
            # Check for warnings (nearing deadline)
            if not ticket.sla_breached:
                remaining = ticket.get_time_until_response_deadline()
                if remaining and remaining.total_seconds() < 7200:  # Less than 2 hours
                    NotificationService.notify_sla_warning(ticket)
                    warning_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'SLA check complete: {breach_count} breaches, {warning_count} warnings'
        ))