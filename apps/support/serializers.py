from rest_framework import serializers
from .models import (
    Team, Agent, SLARule, Ticket, TicketHistory, 
    TicketComment, BusinessHours, EscalationRule
)







class TeamSerializer(serializers.ModelSerializer):
    agent_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = '__all__'
    
    def get_agent_count(self, obj):
        return obj.agents.count()

class AgentSerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()
    workload_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Agent
        fields = '__all__'
    
    def get_user_full_name(self, obj):
        return obj.user.get_full_name()
    
    def get_team_name(self, obj):
        return obj.team.name if obj.team else None
    
    def get_workload_percentage(self, obj):
        if obj.max_capacity > 0:
            return round((obj.active_tickets / obj.max_capacity) * 100, 2)
        return 0

class SLARuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SLARule
        fields = '__all__'

class TicketHistorySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TicketHistory
        fields = '__all__'
    
    def get_performed_by_name(self, obj):
        return obj.performed_by.user.get_full_name() if obj.performed_by else None

class TicketCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TicketComment
        fields = '__all__'
    
    def get_author_name(self, obj):
        return obj.author.user.get_full_name()

class TicketSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()
    assigned_team_name = serializers.SerializerMethodField()
    sla_status = serializers.SerializerMethodField()
    time_until_response_deadline = serializers.SerializerMethodField()
    history = TicketHistorySerializer(many=True, read_only=True)
    comments = TicketCommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_assigned_to_name(self, obj):
        return obj.assigned_to.user.get_full_name() if obj.assigned_to else None
    
    def get_assigned_team_name(self, obj):
        return obj.assigned_team.name if obj.assigned_team else None
    
    def get_sla_status(self, obj):
        if obj.sla_breached:
            return 'breached'
        elif obj.sla_response_deadline:
            time_remaining = obj.get_time_until_response_deadline()
            if time_remaining and time_remaining.total_seconds() < 3600:  # Less than 1 hour
                return 'critical'
            elif time_remaining and time_remaining.total_seconds() < 7200:  # Less than 2 hours
                return 'warning'
            return 'ok'
        return 'unknown'
    
    def get_time_until_response_deadline(self, obj):
        remaining = obj.get_time_until_response_deadline()
        if remaining:
            return str(remaining)
        return None
    
    def validate_customer_tier(self, value):
        return value.lower().strip()
    
    def validate_priority(self, value):
        return value.lower().strip()
    
    def validate(self, data):
        # Clean up string fields
        for field in ['customer_name', 'title', 'description']:
            if field in data:
                data[field] = data[field].strip()
        return data

class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            'title', 'description', 'customer_name', 'customer_email',
            'customer_tier', 'priority', 'channel', 'issue_type', 'tags'
        ]

class TicketAssignmentSerializer(serializers.Serializer):
    agent_id = serializers.IntegerField(required=False)
    auto_assign = serializers.BooleanField(default=False)

class TicketStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Ticket.STATUS_CHOICES)
    comment = serializers.CharField(required=False, allow_blank=True)

class BusinessHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessHours
        fields = '__all__'

class EscalationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EscalationRule
        fields = '__all__'

class DashboardSerializer(serializers.Serializer):
    """Serializer for dashboard data"""
    total_tickets = serializers.IntegerField()
    open_tickets = serializers.IntegerField()
    in_progress_tickets = serializers.IntegerField()
    resolved_today = serializers.IntegerField()
    sla_breached = serializers.IntegerField()
    average_response_time = serializers.FloatField()
    compliance_rate = serializers.FloatField()
    tickets_by_priority = serializers.ListField()
    tickets_by_status = serializers.ListField()
    agent_performance = serializers.ListField()