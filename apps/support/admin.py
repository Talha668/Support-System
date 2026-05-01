from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Team, Agent, SLARule, Ticket, TicketHistory, 
    TicketComment, BusinessHours, EscalationRule, WorkSchedule
)
from django.utils import timezone






@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'agent_count', 'created_at']
    search_fields = ['name']
    list_filter = ['is_active']
    
    def agent_count(self, obj):
        return obj.agents.count()
    agent_count.short_description = 'Agents'

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'get_user_name', 'team', 'status', 'active_tickets', 'average_rating']
    list_filter = ['status', 'team', 'joined_date']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'employee_id']
    actions = ['set_online', 'set_offline']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()
    get_user_name.short_description = 'Name'
    
    def set_online(self, request, queryset):
        queryset.update(status='online')
    set_online.short_description = 'Set selected agents as Online'
    
    def set_offline(self, request, queryset):
        queryset.update(status='offline')
    set_offline.short_description = 'Set selected agents as Offline'

@admin.register(SLARule)
class SLARuleAdmin(admin.ModelAdmin):
    list_display = ['customer_tier', 'priority', 'response_hours', 'resolution_hours', 'is_active']
    list_filter = ['customer_tier', 'priority', 'is_active']
    ordering = ['customer_tier', 'priority']

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'customer_name', 'status', 'priority', 
                   'assigned_to', 'sla_status_display', 'created_at']
    list_filter = ['status', 'priority', 'customer_tier', 'channel', 'issue_type', 'escalated']
    search_fields = ['id', 'title', 'customer_name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    actions = ['mark_resolved', 'mark_closed', 'auto_assign']
    
    def sla_status_display(self, obj):
        if obj.sla_breached:
            return format_html('<span style="color: red;">⚠ Breached</span>')
        
        remaining = obj.get_time_until_response_deadline()
        if remaining and remaining.total_seconds() < 3600:
            return format_html('<span style="color: orange;">⚠ Critical</span>')
        
        return format_html('<span style="color: green;">✓ OK</span>')
    sla_status_display.short_description = 'SLA Status'
    
    def mark_resolved(self, request, queryset):
        queryset.update(status='resolved', resolved_at=timezone.now())
    mark_resolved.short_description = 'Mark selected as Resolved'
    
    def mark_closed(self, request, queryset):
        queryset.update(status='closed', closed_at=timezone.now())
    mark_closed.short_description = 'Mark selected as Closed'
    
    def auto_assign(self, request, queryset):
        from .services.assignment_service import TicketAssignmentService
        count = 0
        for ticket in queryset.filter(assigned_to__isnull=True):
            agent = TicketAssignmentService.auto_assign_ticket(ticket)
            if agent:
                count += 1
        self.message_user(request, f'{count} tickets assigned successfully.')
    auto_assign.short_description = 'Auto-assign selected tickets'

@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'action', 'performed_by', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['ticket__id', 'comment']

@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']

@admin.register(BusinessHours)
class BusinessHoursAdmin(admin.ModelAdmin):
    list_display = ['day_of_week', 'start_time', 'end_time', 'is_working_day']
    list_editable = ['start_time', 'end_time', 'is_working_day']

@admin.register(EscalationRule)
class EscalationRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'condition_type', 'escalation_team', 'escalation_level', 'is_active']
    list_filter = ['condition_type', 'is_active']