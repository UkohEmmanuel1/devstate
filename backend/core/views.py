import os, subprocess
from pathlib import Path
from datetime import timedelta
import httpx
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Project, DevEvent, FocusSession
from .serializers import ProjectSerializer, EventSerializer, FocusSerializer

def notify(title, message, priority=3):
 if not settings.NTFY_TOPIC: return False
 headers={'Title':title,'Priority':str(max(1,min(5,5-priority)))}
 if settings.NTFY_TOKEN: headers['Authorization']='Bearer '+settings.NTFY_TOKEN
 response=httpx.post(settings.NTFY_SERVER+'/'+settings.NTFY_TOPIC,content=message.encode(),headers=headers,timeout=8); response.raise_for_status(); return True
@api_view(['GET'])
def health(request): return Response({'status':'ok','phone_notifications_configured':bool(settings.NTFY_TOPIC)})
@api_view(['GET'])
def projects(request): return Response(ProjectSerializer(Project.objects.all(),many=True).data)
@api_view(['GET'])
def events(request): return Response(EventSerializer(DevEvent.objects.all()[:100],many=True).data)
@api_view(['POST'])
def create_event(request):
 data=request.data.copy(); serializer=EventSerializer(data=data); serializer.is_valid(raise_exception=True); event=serializer.save(); sent=False
 if event.priority<=1 and settings.NTFY_TOPIC:
  try: sent=notify(event.title,event.message or event.source,event.priority)
  except httpx.HTTPError: sent=False
 return Response({**EventSerializer(event).data,'phone_notification_sent':sent},status=201)
@api_view(['GET'])
def focus(request):
 now=timezone.now()
 FocusSession.objects.filter(active=True,ends_at__lte=now).update(active=False,ended_at=now)
 session=FocusSession.objects.filter(active=True).first()
 return Response({'active':bool(session),**(FocusSerializer(session).data if session else {})})
@api_view(['POST'])
def focus_start(request):
 hours=int(request.query_params.get('hours',6))
 if not 1<=hours<=12: return Response({'detail':'hours must be between 1 and 12'},status=400)
 FocusSession.objects.filter(active=True).update(active=False,ended_at=timezone.now()); now=timezone.now(); session=FocusSession.objects.create(started_at=now,ends_at=now+timedelta(hours=hours)); return Response(FocusSerializer(session).data,status=201)
@api_view(['POST'])
def focus_end(request):
 now=timezone.now(); FocusSession.objects.filter(active=True).update(active=False,ended_at=now); return Response({'active':False,'ended_at':now})
@api_view(['POST'])
def notification_test(request):
 if not settings.NTFY_TOPIC: return Response({'detail':'Configure DEVSTATE_NTFY_TOPIC in backend/.env'},status=409)
 try: notify('DevState · Test','Your phone notification channel is connected.',2); return Response({'accepted_by_ntfy':True})
 except httpx.HTTPError as exc: return Response({'detail':str(exc)},status=502)
@api_view(['POST'])
def scan_projects(request):
 roots=[Path(p.strip()).expanduser() for p in os.getenv('DEVSTATE_PROJECTS_DIRS','').split(';') if p.strip()]; found=[]
 for root in roots:
  if not root.is_dir(): continue
  for path in [root,*[p for p in root.iterdir() if p.is_dir()]]:
   if not (path/'.git').exists(): continue
   try:
    def git(*args): return subprocess.check_output(['git','-C',str(path),*args],text=True,stderr=subprocess.DEVNULL).strip()
    dirty=git('status','--porcelain'); obj,_=Project.objects.update_or_create(path=str(path.resolve()),defaults={'name':path.name,'branch':git('branch','--show-current') or 'detached','commit':git('rev-parse','--short','HEAD'),'dirty_paths':[line[3:] for line in dirty.splitlines() if line.strip()]}); found.append(obj)
   except (OSError,subprocess.SubprocessError): pass
 return Response({'scanned':len(found),'projects':ProjectSerializer(found,many=True).data})
@api_view(['POST'])
def snapshots(request):
 from django.conf import settings as s
 import json
 directory=Path(os.getenv('DEVSTATE_RECOVERY_DIR',str(Path('data/recovery')))); directory.mkdir(parents=True,exist_ok=True)
 records=ProjectSerializer(Project.objects.all(),many=True).data; target=directory/('recovery-'+timezone.now().strftime('%Y%m%d-%H%M%S')+'.json'); target.write_text(json.dumps(records,indent=2),encoding='utf-8'); return Response({'saved':len(records),'file':str(target)})


from datetime import datetime, timezone as dt_timezone
import socket
import ssl
from urllib.parse import urlparse
from rest_framework import viewsets
from rest_framework.decorators import action
from .models import DomainAsset, HostingService, AISubscription
from .serializers import DomainAssetSerializer, HostingServiceSerializer, AISubscriptionSerializer

class DomainAssetViewSet(viewsets.ModelViewSet):
    queryset = DomainAsset.objects.all()
    serializer_class = DomainAssetSerializer

    @action(detail=True, methods=["post"])
    def check_dns(self, request, pk=None):
        item = self.get_object()
        observed = {}
        try:
            observed["A"] = sorted({entry[4][0] for entry in socket.getaddrinfo(item.domain_name, None, socket.AF_INET)})
            item.dns_status = "resolved"
            expected = item.expected_dns.get("A", [])
            if expected and not set(expected).issubset(set(observed["A"])):
                item.dns_status = "mismatch"
        except socket.gaierror as exc:
            item.dns_status = "failed"
            observed["error"] = str(exc)
        item.observed_dns = observed
        item.last_dns_check = timezone.now()
        item.save(update_fields=["dns_status", "observed_dns", "last_dns_check"])
        return Response(DomainAssetSerializer(item).data)

class HostingServiceViewSet(viewsets.ModelViewSet):
    queryset = HostingService.objects.all()
    serializer_class = HostingServiceSerializer

    @action(detail=True, methods=["post"])
    def check(self, request, pk=None):
        item = self.get_object()
        if not item.service_url:
            return Response({"detail": "Add a service URL before checking uptime."}, status=400)
        try:
            response = httpx.get(item.service_url, timeout=10, follow_redirects=True)
            item.last_http_status = response.status_code
            item.status = "active" if response.status_code < 500 else "paused"
        except httpx.HTTPError:
            item.last_http_status = None
            item.status = "paused"
        item.last_checked_at = timezone.now()
        item.save(update_fields=["last_http_status", "status", "last_checked_at"])
        return Response(HostingServiceSerializer(item).data)

class AISubscriptionViewSet(viewsets.ModelViewSet):
    queryset = AISubscription.objects.all()
    serializer_class = AISubscriptionSerializer

@api_view(["GET"])
def renewals(request):
    now = timezone.now()
    items = []
    for sub in AISubscription.objects.filter(active=True, renews_at__isnull=False):
        days = (sub.renews_at - now).total_seconds() / 86400
        items.append({"kind": "ai_subscription", "id": sub.id, "name": sub.provider, "renews_at": sub.renews_at, "days_remaining": max(0, round(days)), "due": days <= sub.reminder_days})
    for domain in DomainAsset.objects.filter(expires_at__isnull=False):
        days = (domain.expires_at - now).total_seconds() / 86400
        items.append({"kind": "domain", "id": domain.id, "name": domain.domain_name, "renews_at": domain.expires_at, "days_remaining": max(0, round(days)), "due": days <= 30})
    for host in HostingService.objects.filter(renewal_at__isnull=False):
        days = (host.renewal_at - now).total_seconds() / 86400
        items.append({"kind": "hosting", "id": host.id, "name": host.name, "renews_at": host.renewal_at, "days_remaining": max(0, round(days)), "due": days <= 14})
    return Response(sorted(items, key=lambda x: x["days_remaining"]))

@api_view(["POST"])
def check_infrastructure(request):
    domains = []
    for item in DomainAsset.objects.all():
        try:
            addresses = sorted({entry[4][0] for entry in socket.getaddrinfo(item.domain_name, None, socket.AF_INET)})
            item.observed_dns = {"A": addresses}
            expected = item.expected_dns.get("A", [])
            item.dns_status = "mismatch" if expected and not set(expected).issubset(set(addresses)) else "resolved"
        except socket.gaierror as exc:
            item.observed_dns = {"error": str(exc)}
            item.dns_status = "failed"
        item.last_dns_check = timezone.now()
        item.save(update_fields=["observed_dns", "dns_status", "last_dns_check"])
        domains.append({"domain": item.domain_name, "status": item.dns_status, "observed": item.observed_dns})
    hosts = []
    for item in HostingService.objects.exclude(service_url=""):
        try:
            response = httpx.get(item.service_url, timeout=10, follow_redirects=True)
            item.last_http_status = response.status_code
            item.status = "active" if response.status_code < 500 else "paused"
        except httpx.HTTPError:
            item.last_http_status = None
            item.status = "paused"
        item.last_checked_at = timezone.now()
        item.save(update_fields=["last_http_status", "status", "last_checked_at"])
        hosts.append({"name": item.name, "status": item.status, "http_status": item.last_http_status})
    return Response({"domains": domains, "hosting": hosts, "checked_at": timezone.now()})
