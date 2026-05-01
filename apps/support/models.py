from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
import uuid






class Team(models.Model):
    """Support teams"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Agent(models.Model):
    """Support agents"""
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('busy', 'Busy'),
        ('break', 'On Break'),
    ]
    
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='agent_profile')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, related_name='agents')
    employee_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    active_tickets = models.IntegerField(default=0)
    max_capacity = models.IntegerField(default=10)
    skills = models.JSONField(default=list)
    average_rating = models.FloatField(default=0.0)
    total_tickets_resolved = models.IntegerField(default=0)
    joined_date = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.team.name if self.team else 'No Team'})"
    
    def update_active_tickets_count(self):
        """Update the active ticket count"""
        self.active_tickets = self.assigned_tickets.filter(
            status__in=['open', 'in_progress']
        ).count()
        self.save(update_fields=['active_tickets'])
    
    def can_take_more_tickets(self):
        """Check if agent can take more tickets"""
        return self.active_tickets < self.max_capacity

class SLARule(models.Model):
    """Service Level Agreement rules"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    TIER_CHOICES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    customer_tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    response_hours = models.IntegerField(help_text="Hours to first response")
    resolution_hours = models.IntegerField(help_text="Hours to resolution")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['customer_tier', 'priority']
        ordering = ['customer_tier', 'priority']
    
    def __str__(self):
        return f"{self.get_customer_tier_display()} - {self.get_priority_display()}: {self.response_hours}h/{self.resolution_hours}h"

class BusinessHours(models.Model):
    """Business hours configuration"""
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    day_of_week = models.IntegerField(choices=DAY_CHOICES, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_working_day = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['day_of_week']
    
    def __str__(self):
        return f"{self.get_day_of_week_display()}: {self.start_time} - {self.end_time}"

class Ticket(models.Model):
    """Support tickets"""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    TIER_CHOICES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    CHANNEL_CHOICES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('chat', 'Live Chat'),
        ('web', 'Web Form'),
        ('api', 'API'),
    ]
    
    ISSUE_TYPE_CHOICES = [
        ('technical', 'Technical Issue'),
        ('billing', 'Billing'),
        ('integration', 'Integration'),
        ('onboarding', 'Onboarding'),
        ('account', 'Account Management'),
        ('other', 'Other'),
    ]
    
    # Core fields
    id = models.CharField(max_length=20, primary_key=True)
    title = models.CharField(max_length=500)
    description = models.TextField()
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField(blank=True)
    customer_tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    
    # Status and assignment
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    assigned_to = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    assigned_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='team_tickets')
    
    # Classification
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    issue_type = models.CharField(max_length=20, choices=ISSUE_TYPE_CHOICES)
    tags = models.JSONField(default=list)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # SLA tracking
    sla_response_deadline = models.DateTimeField(null=True, blank=True)
    sla_resolution_deadline = models.DateTimeField(null=True, blank=True)
    sla_breached = models.BooleanField(default=False)
    sla_breach_reason = models.TextField(blank=True)
    
    # Metrics
    response_time_minutes = models.IntegerField(null=True, blank=True)
    resolution_time_minutes = models.IntegerField(null=True, blank=True)
    satisfaction_score = models.IntegerField(null=True, blank=True)
    
    # Escalation
    escalated = models.BooleanField(default=False)
    escalation_level = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['customer_tier', 'priority']),
            models.Index(fields=['sla_response_deadline']),
        ]
    
    def __str__(self):
        return f"{self.id} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"T-{uuid.uuid4().hex[:6].upper()}"
        
        # Calculate SLA deadlines on creation
        if not self.sla_response_deadline:
            self.calculate_sla_deadlines()
        
        # Update timestamps based on status changes
        if self.status == 'in_progress' and not self.first_response_at:
            self.first_response_at = timezone.now()
        
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
            self.calculate_resolution_time()
        
        if self.status == 'closed' and not self.closed_at:
            self.closed_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Update agent's active ticket count
        if self.assigned_to:
            self.assigned_to.update_active_tickets_count()
    
    def calculate_sla_deadlines(self):
        """Calculate SLA deadlines based on tier and priority"""
        try:
            sla_rule = SLARule.objects.get(
                customer_tier=self.customer_tier,
                priority=self.priority,
                is_active=True
            )
            
            # Calculate response deadline
            self.sla_response_deadline = self.calculate_business_deadline(
                self.created_at, 
                sla_rule.response_hours
            )
            
            # Calculate resolution deadline
            self.sla_resolution_deadline = self.calculate_business_deadline(
                self.created_at,
                sla_rule.resolution_hours
            )
        except SLARule.DoesNotExist:
            # Default fallback
            self.sla_response_deadline = self.created_at + timedelta(hours=72)
            self.sla_resolution_deadline = self.created_at + timedelta(hours=168)
    
    def calculate_business_deadline(self, start_time, hours_to_add):
        """Calculate deadline considering business hours"""
        if not BusinessHours.objects.filter(is_working_day=True).exists():
            return start_time + timedelta(hours=hours_to_add)
        
        current_time = start_time
        hours_added = 0
        
        while hours_added < hours_to_add:
            current_time += timedelta(hours=1)
            
            # Get business hours for current day
            try:
                day_hours = BusinessHours.objects.get(
                    day_of_week=current_time.weekday(),
                    is_working_day=True
                )
                
                # Check if current time is within business hours
                current_time_only = current_time.time()
                if day_hours.start_time <= current_time_only <= day_hours.end_time:
                    hours_added += 1
            except BusinessHours.DoesNotExist:
                # Skip non-working days
                continue
        
        return current_time
    
    def calculate_resolution_time(self):
        """Calculate resolution time in minutes"""
        if self.created_at and self.resolved_at:
            delta = self.resolved_at - self.created_at
            self.resolution_time_minutes = int(delta.total_seconds() / 60)
            
            # Consider only business hours
            if BusinessHours.objects.filter(is_working_day=True).exists():
                business_minutes = 0
                current = self.created_at
                while current < self.resolved_at:
                    try:
                        day_hours = BusinessHours.objects.get(
                            day_of_week=current.weekday(),
                            is_working_day=True
                        )
                        day_start = current.replace(
                            hour=day_hours.start_time.hour,
                            minute=day_hours.start_time.minute,
                            second=0
                        )
                        day_end = current.replace(
                            hour=day_hours.end_time.hour,
                            minute=day_hours.end_time.minute,
                            second=0
                        )
                        
                        if day_start <= current <= day_end:
                            business_minutes += 1
                    except BusinessHours.DoesNotExist:
                        pass
                    current += timedelta(minutes=1)
                
                self.response_time_minutes = business_minutes
    
    def check_sla_status(self):
        """Check if SLA has been breached"""
        if self.status in ['open', 'in_progress', 'pending']:
            now = timezone.now()
            
            if self.sla_response_deadline and now > self.sla_response_deadline:
                self.sla_breached = True
                self.sla_breach_reason = f"Response SLA breached. Deadline was {self.sla_response_deadline}"
                self.save(update_fields=['sla_breached', 'sla_breach_reason'])
                return True
            
            if self.sla_resolution_deadline and now > self.sla_resolution_deadline:
                self.sla_breached = True
                self.sla_breach_reason = f"Resolution SLA breached. Deadline was {self.sla_resolution_deadline}"
                self.save(update_fields=['sla_breached', 'sla_breach_reason'])
                return True
        
        return False
    
    def assign_to_agent(self, agent):
        """Assign ticket to an agent"""
        if not agent.can_take_more_tickets():
            raise ValidationError(f"Agent {agent} has reached maximum capacity")
        
        self.assigned_to = agent
        self.assigned_team = agent.team
        
        if self.status == 'open':
            self.status = 'in_progress'
        
        self.save()
        return True
    
    def get_time_until_response_deadline(self):
        """Get remaining time until response deadline"""
        if self.sla_response_deadline and self.status in ['open', 'in_progress', 'pending']:
            remaining = self.sla_response_deadline - timezone.now()
            return max(remaining, timedelta(0))
        return None
    
    def get_time_until_resolution_deadline(self):
        """Get remaining time until resolution deadline"""
        if self.sla_resolution_deadline and self.status in ['open', 'in_progress', 'pending']:
            remaining = self.sla_resolution_deadline - timezone.now()
            return max(remaining, timedelta(0))
        return None

class TicketHistory(models.Model):
    """Track all changes to tickets"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('assigned', 'Assigned'),
        ('status_changed', 'Status Changed'),
        ('priority_changed', 'Priority Changed'),
        ('comment_added', 'Comment Added'),
        ('escalated', 'Escalated'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    performed_by = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Ticket histories'
    
    def __str__(self):
        return f"{self.ticket.id} - {self.action} at {self.created_at}"

class TicketComment(models.Model):
    """Comments on tickets"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Agent, on_delete=models.CASCADE)
    comment = models.TextField()
    is_internal = models.BooleanField(default=True)
    attachments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author} on {self.ticket.id}"

class EscalationRule(models.Model):
    """Rules for automatic ticket escalation"""
    CONDITION_CHOICES = [
        ('response_time', 'Response Time Exceeded'),
        ('resolution_time', 'Resolution Time Exceeded'),
        ('priority', 'Priority Level'),
        ('customer_tier', 'Customer Tier'),
    ]
    
    name = models.CharField(max_length=200)
    condition_type = models.CharField(max_length=50, choices=CONDITION_CHOICES)
    condition_value = models.JSONField()
    escalation_team = models.ForeignKey(Team, on_delete=models.CASCADE)
    escalation_level = models.IntegerField(default=1)
    notification_template = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class WorkSchedule(models.Model):
    """Agent work schedules"""
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=BusinessHours.DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_working = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['agent', 'day_of_week']
    
    def __str__(self):
        return f"{self.agent} - {self.get_day_of_week_display()}"