from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q, Avg

from .models import (
    Team, Agent, SLARule, Ticket, TicketHistory, 
    TicketComment, BusinessHours, EscalationRule
)
from .serializers import (
    TeamSerializer, AgentSerializer, SLARuleSerializer,
    TicketSerializer, TicketCreateSerializer, TicketAssignmentSerializer,
    TicketStatusUpdateSerializer, TicketHistorySerializer, TicketCommentSerializer,
    BusinessHoursSerializer, EscalationRuleSerializer
)
from .services.sla_service import SLAService
from .services.assignment_service import TicketAssignmentService
from .services.notification_service import NotificationService
from .filters import TicketFilter









class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def agents(self, request, pk=None):
        team = self.get_object()
        agents = team.agents.all()
        serializer = AgentSerializer(agents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def tickets(self, request, pk=None):
        team = self.get_object()
        tickets = Ticket.objects.filter(assigned_team=team)
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        team = self.get_object()
        # Calculate team performance metrics
        tickets = Ticket.objects.filter(assigned_team=team)
        
        metrics = {
            'total_tickets': tickets.count(),
            'open_tickets': tickets.filter(status='open').count(),
            'resolved_tickets': tickets.filter(status='resolved').count(),
            'sla_compliance': tickets.exclude(sla_breached=True).count() / tickets.count() * 100 if tickets.count() > 0 else 0,
            'avg_resolution_time': tickets.filter(status='resolved').aggregate(avg=Avg('resolution_time_minutes'))['avg'],
        }
        
        return Response(metrics)

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def tickets(self, request, pk=None):
        agent = self.get_object()
        tickets = Ticket.objects.filter(assigned_to=agent)
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            tickets = tickets.filter(status=status_filter)
        
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        agent = self.get_object()
        
        tickets = Ticket.objects.filter(assigned_to=agent)
        resolved = tickets.filter(status='resolved')
        
        metrics = {
            'total_assigned': tickets.count(),
            'resolved': resolved.count(),
            'resolution_rate': round(resolved.count() / tickets.count() * 100, 2) if tickets.count() > 0 else 0,
            'sla_breached': tickets.filter(sla_breached=True).count(),
            'avg_resolution_time': resolved.aggregate(avg=Avg('resolution_time_minutes'))['avg'],
            'current_workload': agent.active_tickets,
            'max_capacity': agent.max_capacity,
        }
        
        return Response(metrics)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        agent = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in dict(Agent.STATUS_CHOICES):
            agent.status = new_status
            agent.save()
            return Response({'status': 'updated', 'new_status': new_status})
        
        return Response({'error': 'Invalid status'}, status=400)

class SLARuleViewSet(viewsets.ModelViewSet):
    queryset = SLARule.objects.all()
    serializer_class = SLARuleSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update SLA rules from JSON"""
        sla_service = SLAService()
        result = sla_service.update_sla_rules_from_json(request.data)
        return Response(result)

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TicketFilter
    search_fields = ['id', 'title', 'customer_name', 'description']
    ordering_fields = ['created_at', 'priority', 'status', 'sla_response_deadline']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TicketCreateSerializer
        return TicketSerializer
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign ticket to an agent"""
        ticket = self.get_object()
        serializer = TicketAssignmentSerializer(data=request.data)
        
        if serializer.is_valid():
            if serializer.validated_data.get('auto_assign'):
                agent = TicketAssignmentService.auto_assign_ticket(ticket)
                if agent:
                    NotificationService.notify_ticket_assignment(ticket, agent)
                    return Response({
                        'status': 'assigned',
                        'agent': AgentSerializer(agent).data
                    })
                return Response({'error': 'No available agents'}, status=400)
            else:
                agent_id = serializer.validated_data.get('agent_id')
                if agent_id:
                    agent = get_object_or_404(Agent, id=agent_id)
                    ticket.assign_to_agent(agent)
                    NotificationService.notify_ticket_assignment(ticket, agent)
                    return Response({'status': 'assigned', 'agent': AgentSerializer(agent).data})
        
        return Response(serializer.errors, status=400)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update ticket status"""
        ticket = self.get_object()
        serializer = TicketStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            old_status = ticket.status
            ticket.status = serializer.validated_data['status']
            ticket.save()
            
            # Create history entry
            TicketHistory.objects.create(
                ticket=ticket,
                action='status_changed',
                field_name='status',
                old_value=old_status,
                new_value=ticket.status,
                performed_by=request.user.agent_profile if hasattr(request.user, 'agent_profile') else None,
                comment=serializer.validated_data.get('comment', '')
            )
            
            return Response({'status': 'updated', 'new_status': ticket.get_status_display()})
        
        return Response(serializer.errors, status=400)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add comment to ticket"""
        ticket = self.get_object()
        serializer = TicketCommentSerializer(data=request.data)
        
        if serializer.is_valid():
            comment = serializer.save(
                ticket=ticket,
                author=request.user.agent_profile if hasattr(request.user, 'agent_profile') else None
            )
            
            # Create history entry
            TicketHistory.objects.create(
                ticket=ticket,
                action='comment_added',
                performed_by=request.user.agent_profile if hasattr(request.user, 'agent_profile') else None,
                comment=f"Comment added: {comment.comment[:100]}"
            )
            
            return Response(TicketCommentSerializer(comment).data, status=201)
        
        return Response(serializer.errors, status=400)
    
    @action(detail=True, methods=['post'])
    def escalate(self, request, pk=None):
        """Escalate ticket"""
        ticket = self.get_object()
        escalation_level = request.data.get('level', 1)
        
        ticket.escalated = True
        ticket.escalation_level = escalation_level
        ticket.priority = 'urgent'
        
        # Find escalation team
        try:
            rule = EscalationRule.objects.filter(
                condition_type='priority',
                is_active=True,
                escalation_level=escalation_level
            ).first()
            
            if rule:
                ticket.assigned_team = rule.escalation_team
                NotificationService.notify_escalation(ticket, rule.escalation_team)
        except EscalationRule.DoesNotExist:
            pass
        
        ticket.save()
        
        TicketHistory.objects.create(
            ticket=ticket,
            action='escalated',
            comment=f"Escalated to level {escalation_level}"
        )
        
        return Response({'status': 'escalated', 'level': escalation_level})
    
    @action(detail=False, methods=['get'])
    def my_tickets(self, request):
        """Get tickets assigned to current user"""
        if hasattr(request.user, 'agent_profile'):
            tickets = self.queryset.filter(assigned_to=request.user.agent_profile)
            serializer = self.get_serializer(tickets, many=True)
            return Response(serializer.data)
        return Response({'error': 'Not an agent'}, status=400)
    
    @action(detail=False, methods=['get'])
    def sla_breached(self, request):
        """Get all SLA breached tickets"""
        tickets = self.queryset.filter(sla_breached=True, status__in=['open', 'in_progress'])
        serializer = self.get_serializer(tickets, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unassigned(self, request):
        """Get all unassigned tickets"""
        tickets = self.queryset.filter(assigned_to__isnull=True, status='open')
        serializer = self.get_serializer(tickets, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_assign(self, request):
        """Bulk assign unassigned tickets"""
        count = TicketAssignmentService.bulk_assign_unassigned_tickets()
        return Response({'assigned_count': count})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get ticket statistics"""
        days = request.query_params.get('days', 30)
        start_date = timezone.now() - timezone.timedelta(days=int(days))
        
        stats = SLAService.calculate_sla_metrics(start_date)
        return Response(stats)

class TicketHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TicketHistory.objects.all()
    serializer_class = TicketHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        ticket_id = self.request.query_params.get('ticket_id')
        if ticket_id:
            queryset = queryset.filter(ticket_id=ticket_id)
        return queryset

class BusinessHoursViewSet(viewsets.ModelViewSet):
    queryset = BusinessHours.objects.all()
    serializer_class = BusinessHoursSerializer
    permission_classes = [IsAuthenticated]

class EscalationRuleViewSet(viewsets.ModelViewSet):
    queryset = EscalationRule.objects.all()
    serializer_class = EscalationRuleSerializer
    permission_classes = [IsAuthenticated]