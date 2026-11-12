from rest_framework import serializers
from .models import Project, DevEvent, FocusSession
class ProjectSerializer(serializers.ModelSerializer):
 class Meta: model=Project; fields='__all__'
class EventSerializer(serializers.ModelSerializer):
 class Meta: model=DevEvent; fields='__all__'
class FocusSerializer(serializers.ModelSerializer):
 class Meta: model=FocusSession; fields='__all__'
