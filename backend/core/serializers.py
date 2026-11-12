from rest_framework import serializers
from .models import Project, DevEvent, FocusSession
class ProjectSerializer(serializers.ModelSerializer):
 class Meta: model=Project; fields='__all__'
class EventSerializer(serializers.ModelSerializer):
 class Meta: model=DevEvent; fields='__all__'
class FocusSerializer(serializers.ModelSerializer):
 class Meta: model=FocusSession; fields='__all__'

from .models import DomainAsset, HostingService, AISubscription

class DomainAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DomainAsset
        fields = "__all__"
        read_only_fields = ("last_dns_check", "dns_status", "observed_dns", "created_at")

class HostingServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostingService
        fields = "__all__"
        read_only_fields = ("last_checked_at", "last_http_status")

class AISubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AISubscription
        fields = "__all__"
        read_only_fields = ("created_at",)
