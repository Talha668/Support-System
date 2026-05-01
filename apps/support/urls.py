from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views




router = DefaultRouter()
router.register(r'teams', views.TeamViewSet)
router.register(r'agents', views.AgentViewSet)
router.register(r'sla-rules', views.SLARuleViewSet)
router.register(r'tickets', views.TicketViewSet)
router.register(r'ticket-history', views.TicketHistoryViewSet)
router.register(r'business-hours', views.BusinessHoursViewSet)
router.register(r'escalation-rules', views.EscalationRuleViewSet)


urlpatterns = [
    path('', include(router.urls)),
]