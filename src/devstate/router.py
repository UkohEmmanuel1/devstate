from .models import EventIn, Priority
from .database import Database
from .notifications import PhoneNotifier
from .config import Settings

NTFY_PRIORITY = {Priority.P0:5, Priority.P1:4, Priority.P2:3, Priority.P3:2, Priority.P4:1}

class EventRouter:
    def __init__(self, db: Database, notifier: PhoneNotifier, config: Settings):
        self.db, self.notifier, self.config = db, notifier, config

    async def dispatch(self, event: EventIn):
        event_id = self.db.add_event(event.model_dump())
        threshold = Priority[self.config.notify_min_priority.upper()]
        sent = False
        if event.priority <= threshold:
            try:
                sent = await self.notifier.send("DevState · " + event.title,
                    f"{event.source}: {event.message}".strip(), NTFY_PRIORITY[event.priority],
                    event.tags or ["computer"])
            except Exception as exc:
                return {"id":event_id,"stored":True,"notified":False,"notification_error":str(exc)}
        return {"id":event_id,"stored":True,"notified":sent}
