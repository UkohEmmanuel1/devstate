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
