# -*- coding: utf-8 -*-
import os
from pathlib import Path

def guess_default_chrome_profile_win() -> Path:
    home = Path.home()
    base = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
    return base / "Google" / "Chrome" / "User Data" / "Default"
