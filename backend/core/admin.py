from django.contrib import admin
from .models import Project, DevEvent, FocusSession
admin.site.register(Project); admin.site.register(DevEvent); admin.site.register(FocusSession)

from .models import DomainAsset, HostingService, AISubscription
admin.site.register(DomainAsset)
admin.site.register(HostingService)
admin.site.register(AISubscription)
