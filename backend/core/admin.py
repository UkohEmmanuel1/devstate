from django.contrib import admin
from .models import Project, DevEvent, FocusSession
admin.site.register(Project); admin.site.register(DevEvent); admin.site.register(FocusSession)
