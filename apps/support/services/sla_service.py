from django.utils import timezone
from datetime import timedelta
from apps.support.models import Ticket, SLARule, BusinessHours






class SLAService:
    """Service for SLA calculations and management"""
    
    @staticmethod
    def calculate_sla_metrics(start_date=None, end_date=None):
        """Calculate overall SLA metrics"""
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        tickets = Ticket.objects.filter(created_at__range=[start_date, end_date])
        
        total_tickets = tickets.count()
        breached_tickets = tickets.filter(sla_breached=True).count()
        resolved_tickets = tickets.filter(status='resolved').count()
        
        # Calculate compliance rate
        compliance_rate = 0
        if total_tickets > 0:
            compliance_rate = ((total_tickets - breached_tickets) / total_tickets) * 100
        
        # Average response and resolution times
        response_times = tickets.exclude(response_time_minutes=None).values_list('response_time_minutes', flat=True)
        resolution_times = tickets.exclude(resolution_time_minutes=None).values_list('resolution_time_minutes', flat=True)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        return {
            'total_tickets': total_tickets,
            'breached_tickets': breached_tickets,
            'resolved_tickets': resolved_tickets,
            'compliance_rate': round(compliance_rate, 2),
            'avg_response_time_minutes': round(avg_response_time, 2),
            'avg_resolution_time_minutes': round(avg_resolution_time, 2),
        }
    
    @staticmethod
    def get_tickets_nearing_sla(hours_threshold=2):
        """Get tickets that will breach SLA soon"""
        threshold_time = timezone.now() + timedelta(hours=hours_threshold)
        
        nearing_response = Ticket.objects.filter(
            status__in=['open', 'in_progress'],
            sla_response_deadline__lte=threshold_time,
            sla_response_deadline__gt=timezone.now(),
            sla_breached=False
        )
        
        nearing_resolution = Ticket.objects.filter(
            status__in=['open', 'in_progress'],
            sla_resolution_deadline__lte=threshold_time,
            sla_resolution_deadline__gt=timezone.now(),
            sla_breached=False
        )
        
        return {
            'nearing_response_deadline': nearing_response,
            'nearing_resolution_deadline': nearing_resolution,
            'count': nearing_response.count() + nearing_resolution.count()
        }
    
    @staticmethod
    def update_sla_rules_from_json(json_data):
        """Update SLA rules from JSON data"""
        updated_count = 0
        created_count = 0
        
        for rule_data in json_data:
            sla_rule, created = SLARule.objects.update_or_create(
                customer_tier=rule_data['customerTier'].lower(),
                priority=rule_data['priority'].lower(),
                defaults={
                    'response_hours': rule_data['hours'],
                    'resolution_hours': rule_data['hours'] * 2,  # Resolution time is double
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        return {'created': created_count, 'updated': updated_count}
    
    @staticmethod
    def check_business_hours(datetime_obj):
        """Check if datetime falls within business hours"""
        try:
            day_hours = BusinessHours.objects.get(
                day_of_week=datetime_obj.weekday(),
                is_working_day=True
            )
            time_only = datetime_obj.time()
            return day_hours.start_time <= time_only <= day_hours.end_time
        except BusinessHours.DoesNotExist:
            return False