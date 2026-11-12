import httpx
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import AISubscription,DomainAsset,HostingService,DevEvent
from core.views import notify

class Command(BaseCommand):
    help="Notify account owners about upcoming renewals."
    def handle(self,*args,**options):
        now=timezone.now();sources=[("AI subscription",AISubscription.objects.filter(active=True,renews_at__isnull=False),"renews_at",None),("Domain",DomainAsset.objects.filter(expires_at__isnull=False),"expires_at",30),("Hosting",HostingService.objects.filter(renewal_at__isnull=False),"renewal_at",14)];due=sent=0
        for label,qs,field,default in sources:
            for item in qs.select_related("owner"):
                renewal=getattr(item,field);days=(renewal-now).total_seconds()/86400;threshold=item.reminder_days if default is None else default
                if days>threshold:continue
                due+=1;name=getattr(item,"provider",None) or getattr(item,"domain_name",None) or item.name;title=f"{label} renewal: {name}"
                if DevEvent.objects.filter(owner=item.owner,source="renewal-monitor",title=title,created_at__date=timezone.localdate()).exists():continue
                message=f"{name} is due in {max(0,int(days))} day(s), on {timezone.localtime(renewal).strftime('%Y-%m-%d %H:%M %Z')}."
                DevEvent.objects.create(owner=item.owner,source="renewal-monitor",title=title,message=message,priority=1)
                try:sent+=int(notify(item.owner,title,message,2))
                except httpx.HTTPError as exc:self.stderr.write(f"Notification failed for account {item.owner_id}: {exc}")
        self.stdout.write(self.style.SUCCESS(f"Checked renewals. {due} due, {sent} notifications sent."))
