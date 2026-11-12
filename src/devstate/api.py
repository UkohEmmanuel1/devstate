from fastapi import FastAPI,HTTPException
from .config import settings
from .models import EventIn,Priority
from .service import DevStateService

service=DevStateService(settings)
app=FastAPI(title="DevState",version="0.1.0",description="Local-first developer workspace orchestrator")

@app.get("/health")
def health():
    return {"status":"ok","phone_notifications_configured":service.notifier.enabled}

@app.get("/projects")
def projects(): return service.snapshot()

@app.post("/snapshots")
def snapshots(): return {"projects":service.snapshot()}

@app.get("/events")
def events(limit:int=50): return service.db.recent_events(max(1,min(limit,200)))

@app.post("/events")
async def create_event(event:EventIn): return await service.router.dispatch(event)

@app.post("/notifications/test")
async def test_notification():
    if not service.notifier.enabled:
        raise HTTPException(409,"Configure DEVSTATE_NTFY_TOPIC in .env first")
    try:
        sent=await service.notifier.send("DevState · Test","Your phone notification channel is connected.",4,["white_check_mark"])
        return {"accepted_by_ntfy":sent,"message":"Check your phone's ntfy app."}
    except Exception as exc:
        raise HTTPException(502,f"Notification provider error: {exc}") from exc

@app.post("/focus/start")
async def focus_start(hours:int=6):
    try: return await service.start_focus(hours)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc

@app.post("/focus/end")
async def focus_end(): return await service.end_focus()

@app.get("/focus")
def focus():
    return {"active":service.focus_started_at is not None,"started_at":service.focus_started_at,"ends_at":service.focus_ends_at}
