from django.db.models import Count, Q, F
from apps.support.models import Agent, Ticket, Team


class TicketAssignmentService:
    """Service for intelligent ticket assignment"""
    
    @staticmethod
    def auto_assign_ticket(ticket):
        """Automatically assign ticket to best available agent"""
        
        # Get relevant team for ticket type
        team = TicketAssignmentService.get_team_for_issue_type(ticket.issue_type)
        
        if not team:
            team = Team.objects.filter(is_active=True).first()
        
        # Strategy 1: Skills-based assignment
        agent = TicketAssignmentService.assign_by_skills(ticket, team)
        if agent:
            return agent
        
        # Strategy 2: Workload-balanced assignment
        agent = TicketAssignmentService.assign_by_workload(team)
        if agent:
            return agent
        
        # Strategy 3: Round-robin assignment
        agent = TicketAssignmentService.assign_round_robin(team)
        if agent:
            return agent
        
        return None
    
    @staticmethod
    def get_team_for_issue_type(issue_type):
        """Map issue types to teams"""
        team_mapping = {
            'technical': 'Technical Escalations',
            'billing': 'Billing Ops',
            'integration': 'Integrations',
            'onboarding': 'Customer Success',
            'account': 'General Support',
        }
        
        team_name = team_mapping.get(issue_type, 'General Support')
        return Team.objects.filter(name=team_name, is_active=True).first()
    
    @staticmethod
    def assign_by_skills(ticket, team):
        """Assign based on agent skills matching ticket requirements"""
        required_skills = TicketAssignmentService.get_required_skills(ticket)
        
        available_agents = Agent.objects.filter(
            team=team,
            status='online',
            active_tickets__lt=F('max_capacity')
        )
        
        if required_skills:
            # Find agents with matching skills
            matching_agents = []
            for agent in available_agents:
                agent_skills = agent.skills or []
                matching_count = len(set(required_skills) & set(agent_skills))
                if matching_count > 0:
                    matching_agents.append((agent, matching_count))
            
            # Sort by match count and workload
            matching_agents.sort(key=lambda x: (-x[1], x[0].active_tickets))
            
            if matching_agents:
                best_agent = matching_agents[0][0]
                ticket.assign_to_agent(best_agent)
                return best_agent
        
        return None
    
    @staticmethod
    def get_required_skills(ticket):
        """Determine required skills based on ticket properties"""
        skills = []
        
        # Add skills based on issue type
        if ticket.issue_type == 'technical':
            skills.extend(['debugging', 'api', 'database', 'infrastructure'])
        elif ticket.issue_type == 'billing':
            skills.extend(['payments', 'accounting', 'subscriptions'])
        elif ticket.issue_type == 'integration':
            skills.extend(['api', 'webhooks', 'sdk', 'third-party'])
        elif ticket.issue_type == 'onboarding':
            skills.extend(['training', 'documentation', 'configuration'])
        
        # Add skills based on priority
        if ticket.priority in ['urgent', 'high']:
            skills.append('critical_incident')
        
        return list(set(skills))
    
    @staticmethod
    def assign_by_workload(team):
        """Assign to agent with least workload"""
        agent = Agent.objects.filter(
            team=team,
            status='online',
            active_tickets__lt=F('max_capacity')
        ).order_by('active_tickets').first()
        
        if agent:
            return agent
        return None
    
    @staticmethod
    def assign_round_robin(team):
        """Round-robin assignment"""
        # Get last assigned agent in this team
        last_ticket = Ticket.objects.filter(
            assigned_team=team
        ).order_by('-created_at').first()
        
        agents = list(Agent.objects.filter(
            team=team,
            status='online',
            active_tickets__lt=F('max_capacity')
        ).order_by('id'))
        
        if not agents:
            return None
        
        if last_ticket and last_ticket.assigned_to in agents:
            current_index = agents.index(last_ticket.assigned_to)
            next_index = (current_index + 1) % len(agents)
            return agents[next_index]
        
        return agents[0]
    
    @staticmethod
    def bulk_assign_unassigned_tickets():
        """Assign all unassigned open tickets"""
        unassigned_tickets = Ticket.objects.filter(
            assigned_to__isnull=True,
            status='open'
        )
        
        assigned_count = 0
        for ticket in unassigned_tickets:
            agent = TicketAssignmentService.auto_assign_ticket(ticket)
            if agent:
                assigned_count += 1
        
        return assigned_count
    
    @staticmethod
    def rebalance_workload(team):
        """Rebalance tickets across team agents"""
        agents = Agent.objects.filter(
            team=team,
            status='online'
        ).order_by('active_tickets')
        
        if not agents:
            return
        
        # Calculate average tickets per agent
        total_tickets = sum(agent.active_tickets for agent in agents)
        avg_tickets = total_tickets / len(agents)
        
        # Reassign from overloaded to underloaded agents
        overloaded = [a for a in agents if a.active_tickets > avg_tickets + 1]
        underloaded = [a for a in agents if a.active_tickets < avg_tickets]
        
        for source_agent in overloaded:
            while source_agent.active_tickets > avg_tickets and underloaded:
                target_agent = underloaded[0]
                
                # Find a ticket to reassign
                ticket = Ticket.objects.filter(
                    assigned_to=source_agent,
                    status='open'
                ).first()
                
                if ticket:
                    ticket.assign_to_agent(target_agent)
                else:
                    break
                
                if target_agent.active_tickets >= avg_tickets:
                    underloaded.pop(0)