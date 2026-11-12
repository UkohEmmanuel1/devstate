from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DEVSTATE_", env_file=".env", extra="ignore")
    host: str = "127.0.0.1"
    port: int = 8765
    db_path: Path = Path("./data/devstate.db")
    projects_dirs: str = ""
    recovery_dir: Path = Path("./data/recovery")
    ntfy_server: str = "https://ntfy.sh"
    ntfy_topic: str = ""
    ntfy_token: str = ""
    notify_min_priority: str = "P1"

    @property
    def project_roots(self) -> list[Path]:
        return [Path(p.strip()).expanduser() for p in self.projects_dirs.split(";") if p.strip()]

settings = Settings()
