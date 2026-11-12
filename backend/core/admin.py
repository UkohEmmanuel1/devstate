from django.contrib import admin

from .models import (
    AISubscription,
    ClerkProfile,
    DevEvent,
    DomainAsset,
    FocusSession,
    HostingService,
    Project,
    RenewalNotice,
)

admin.site.register(ClerkProfile)
admin.site.register(Project)
admin.site.register(DevEvent)
admin.site.register(FocusSession)
admin.site.register(DomainAsset)
admin.site.register(HostingService)
admin.site.register(AISubscription)
admin.site.register(RenewalNotice)
