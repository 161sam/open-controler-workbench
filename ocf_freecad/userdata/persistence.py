from __future__ import annotations

import json
import os
from pathlib import Path

from ocf_freecad.userdata.store import UserDataStore

DEFAULT_USERDATA_DIRNAME = ".ocf_userdata"
DEFAULT_FILENAME = "userdata.json"


class UserDataPersistence:
    def __init__(self, base_dir: str | None = None, filename: str = DEFAULT_FILENAME) -> None:
        self.base_dir = Path(base_dir or _default_base_dir())
        self.filename = filename

    @property
    def path(self) -> Path:
        return self.base_dir / self.filename

    def load(self) -> UserDataStore:
        try:
            content = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return UserDataStore()
        except OSError:
            return UserDataStore()
        if not content.strip():
            return UserDataStore()
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return UserDataStore()
        return UserDataStore.from_dict(data)

    def save(self, store: UserDataStore) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(store.to_dict(), indent=2, sort_keys=True)
        self.path.write_text(payload + "\n", encoding="utf-8")


def _default_base_dir() -> str:
    configured = os.environ.get("OCF_USERDATA_DIR")
    if configured:
        return configured
    xdg = os.environ.get("XDG_STATE_HOME")
    if xdg:
        return str(Path(xdg) / "open-controller-freecad")
    return str(Path.cwd() / DEFAULT_USERDATA_DIRNAME)
