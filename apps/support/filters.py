import django_filters
from .models import Ticket





class TicketFilter(django_filters.FilterSet):
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    priority_in = django_filters.BaseInFilter(field_name='priority')
    status_in = django_filters.BaseInFilter(field_name='status')
    
    class Meta:
        model = Ticket
        fields = {
            'status': ['exact'],
            'priority': ['exact'],
            'customer_tier': ['exact'],
            'channel': ['exact'],
            'issue_type': ['exact'],
            'assigned_to': ['exact'],
            'assigned_team': ['exact'],
            'escalated': ['exact'],
            'sla_breached': ['exact'],
        }