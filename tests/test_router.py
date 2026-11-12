import pytest
from devstate.config import Settings
from devstate.database import Database
from devstate.models import EventIn,Priority
from devstate.router import EventRouter

class FakeNotifier:
    async def send(self,**kwargs): return True

@pytest.mark.asyncio
async def test_urgent_event_notifies_and_persists(tmp_path):
    cfg=Settings(db_path=tmp_path/"db.sqlite",notify_min_priority="P1")
    db=Database(cfg.db_path); router=EventRouter(db,FakeNotifier(),cfg)
    result=await router.dispatch(EventIn(source="ci",title="Build failed",priority=Priority.P1))
    assert result["stored"] and result["notified"]
    assert db.recent_events()[0]["title"]=="Build failed"

@pytest.mark.asyncio
async def test_low_priority_event_is_quiet(tmp_path):
    cfg=Settings(db_path=tmp_path/"db.sqlite",notify_min_priority="P1")
    db=Database(cfg.db_path); router=EventRouter(db,FakeNotifier(),cfg)
    result=await router.dispatch(EventIn(source="media",title="New clip",priority=Priority.P3))
    assert result["stored"] and not result["notified"]
