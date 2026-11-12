from django.db import models
class Project(models.Model):
 name=models.CharField(max_length=120); path=models.TextField(unique=True); branch=models.CharField(max_length=255,blank=True,null=True); commit=models.CharField(max_length=64,blank=True,null=True); dirty_paths=models.JSONField(default=list); last_scanned_at=models.DateTimeField(auto_now=True)
 class Meta: ordering=['name']
class DevEvent(models.Model):
 source=models.CharField(max_length=80); title=models.CharField(max_length=160); message=models.TextField(blank=True); priority=models.PositiveSmallIntegerField(default=2); created_at=models.DateTimeField(auto_now_add=True)
 class Meta: ordering=['-created_at']
class FocusSession(models.Model):
 started_at=models.DateTimeField(); ends_at=models.DateTimeField(); ended_at=models.DateTimeField(null=True,blank=True); active=models.BooleanField(default=True)
 class Meta: ordering=['-started_at']
