from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
from .notification_views import notification_config

router = DefaultRouter()
router.register("domains", views.DomainAssetViewSet, basename="domain")
router.register("hosting", views.HostingServiceViewSet, basename="hosting")
router.register("ai-subscriptions", views.AISubscriptionViewSet, basename="ai-subscription")
urlpatterns = router.urls + [
    path("health/", views.health),
    path("projects/", views.projects),
    path("projects/scan/", views.scan_projects),
    path("events/", views.events),
    path("events/create/", views.create_event),
    path("focus/", views.focus),
    path("focus/start/", views.focus_start),
    path("focus/end/", views.focus_end),
    path("notifications/test/", views.notification_test),
    path("notifications/config/", notification_config),
    path("snapshots/", views.snapshots),
    path("renewals/", views.renewals),
    path("infrastructure/check/", views.check_infrastructure),
]
