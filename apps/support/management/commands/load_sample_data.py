import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from apps.support.models import Team, Agent, SLARule, Ticket, BusinessHours
from apps.accounts.models import User





class Command(BaseCommand):
    help = 'Load sample data from JSON files'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Loading sample data...')
        
        self.load_business_hours()
        self.load_teams_and_agents()
        self.load_sla_rules()
        self.load_tickets()
        
        self.stdout.write(self.style.SUCCESS('Sample data loaded successfully!'))
    
    def load_business_hours(self):
        """Create default business hours"""
        BusinessHours.objects.all().delete()
        
        business_hours = [
            (0, '09:00', '17:00', True),   # Monday
            (1, '09:00', '17:00', True),   # Tuesday
            (2, '09:00', '17:00', True),   # Wednesday
            (3, '09:00', '17:00', True),   # Thursday
            (4, '09:00', '17:00', True),   # Friday
            (5, '10:00', '14:00', True),   # Saturday
            (6, '00:00', '00:00', False),  # Sunday
        ]
        
        for day, start, end, working in business_hours:
            BusinessHours.objects.create(
                day_of_week=day,
                start_time=start,
                end_time=end,
                is_working_day=working
            )
        
        self.stdout.write('  ✓ Business hours created')
    
    def load_teams_and_agents(self):
        """Load teams and agents from agents.json"""
        data_path = Path('data/agents.json')
        
        if not data_path.exists():
            self.stdout.write(self.style.WARNING('  agents.json not found, skipping...'))
            return
        
        with open(data_path) as f:
            agents_data = json.load(f)
        
        for agent_data in agents_data:
            # Create or get team
            team, _ = Team.objects.get_or_create(
                name=agent_data['team'],
                defaults={'description': f'{agent_data["team"]} team'}
            )
            
            # Create user for agent
            email = f"{agent_data['name'].lower()}@support.com"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': agent_data['name'],
                    'last_name': '',
                    'role': 'agent',
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
            
            # Create agent profile
            Agent.objects.get_or_create(
                user=user,
                defaults={
                    'team': team,
                    'employee_id': f"EMP-{agent_data['name'][:3].upper()}-{Agent.objects.count() + 1:03d}",
                    'active_tickets': agent_data['activeTickets'],
                    'status': 'online',
                }
            )
        
        self.stdout.write(f'  ✓ {len(agents_data)} agents loaded')
    
    def load_sla_rules(self):
        """Load SLA rules from sla_rules.json"""
        data_path = Path('data/sla_rules.json')
        
        if not data_path.exists():
            self.stdout.write(self.style.WARNING('  sla_rules.json not found, skipping...'))
            return
        
        with open(data_path) as f:
            sla_data = json.load(f)
        
        for rule in sla_data:
            SLARule.objects.get_or_create(
                customer_tier=rule['customerTier'].lower(),
                priority=rule['priority'].lower(),
                defaults={
                    'response_hours': rule['hours'],
                    'resolution_hours': rule['hours'] * 2,  # Resolution time is double
                }
            )
        
        self.stdout.write(f'  ✓ {len(sla_data)} SLA rules loaded')
    
    def load_tickets(self):
        """Load tickets from tickets.json"""
        data_path = Path('data/tickets.json')
        
        if not data_path.exists():
            self.stdout.write(self.style.WARNING('  tickets.json not found, skipping...'))
            return
        
        with open(data_path) as f:
            tickets_data = json.load(f)
        
        loaded_count = 0
        for ticket_data in tickets_data:
            try:
                # Parse created_at with flexible format
                created_at = self.parse_date(ticket_data['createdAt'])
                
                # Find assigned agent if any
                assigned_agent = None
                if ticket_data.get('assignedTo'):
                    assigned_agent = Agent.objects.filter(
                        user__first_name=ticket_data['assignedTo']
                    ).first()
                
                # Create ticket
                ticket = Ticket.objects.create(
                    id=ticket_data['id'],
                    title=ticket_data['title'].strip(),
                    description=ticket_data['description'].strip(),
                    customer_name=ticket_data['customerName'].strip(),
                    customer_tier=ticket_data['customerTier'].lower().strip(),
                    status=ticket_data['status'],
                    priority=ticket_data['priority'].lower().strip(),
                    assigned_to=assigned_agent,
                    assigned_team=assigned_agent.team if assigned_agent else None,
                    channel=ticket_data['channel'],
                    issue_type=ticket_data['issueType'],
                    created_at=created_at,
                )
                
                loaded_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error loading ticket {ticket_data.get("id", "unknown")}: {str(e)}'))
        
        self.stdout.write(f'  ✓ {loaded_count} tickets loaded')
    
    def parse_date(self, date_str):
        """Parse date strings in various formats"""
        if not date_str:
            return timezone.now()
        
        formats = [
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y/%m/%d %H:%M:%S',
            '%m-%d-%Y %H:%M',
            '%Y-%m-%dT%H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.tzinfo is None:
                    return timezone.make_aware(dt)
                return dt
            except (ValueError, TypeError):
                continue
        
        return timezone.now()