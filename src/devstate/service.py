from datetime import datetime,timedelta,timezone
from .config import Settings
from .database import Database
from .models import EventIn,Priority
from .notifications import PhoneNotifier
from .router import EventRouter
from .sessions import scan_projects

class DevStateService:
    def __init__(self,config:Settings):
        self.config=config
        self.db=Database(config.db_path)
        self.notifier=PhoneNotifier(config)
        self.router=EventRouter(self.db,self.notifier,config)
        self.focus_started_at=None
        self.focus_ends_at=None

    async def emit(self,source,title,message,priority=Priority.P2):
        return await self.router.dispatch(EventIn(source=source,title=title,message=message,priority=priority))

    def snapshot(self):
        snapshots=scan_projects(self.config.project_roots)
        self.config.recovery_dir.mkdir(parents=True,exist_ok=True)
        for item in snapshots:
            payload=item.model_dump(mode="json")
            self.db.add_snapshot(item.name,payload)
            safe="".join(c if c.isalnum() or c in "-_" else "_" for c in item.name)
            paths="\n".join(f"- `{p}`" for p in item.dirty_paths) or "- Clean working tree"
            (self.config.recovery_dir/f"{safe}-latest.md").write_text(
                f"# Recovery: {item.name}\n\n- Path: `{item.path}`\n- Branch: `{item.branch}`\n"
                f"- Commit: `{item.commit or 'unborn'}`\n- Captured: {item.captured_at.isoformat()}\n\n"
                f"## Uncommitted paths\n{paths}\n\n## Resume note\n"
                "Inspect the current working tree before changing files. No Git refs or files were modified.\n",encoding="utf-8")
        return [s.model_dump(mode="json") for s in snapshots]

    async def start_focus(self,hours=6):
        if not 1<=hours<=12: raise ValueError("Focus duration must be between 1 and 12 hours")
        self.focus_started_at=datetime.now(timezone.utc)
        self.focus_ends_at=self.focus_started_at+timedelta(hours=hours)
        await self.emit("focus","Engineering block started",f"Focus ends at {self.focus_ends_at.isoformat()}",Priority.P1)
        return {"active":True,"started_at":self.focus_started_at,"ends_at":self.focus_ends_at}

    async def end_focus(self):
        snapshots=self.snapshot()
        self.focus_started_at=self.focus_ends_at=None
        await self.emit("focus","Engineering block ended",f"Saved {len(snapshots)} repository snapshots.",Priority.P1)
        return {"active":False,"snapshots_saved":len(snapshots)}
