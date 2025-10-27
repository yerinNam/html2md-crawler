# -*- coding: utf-8 -*-
import asyncio
from .cli import build_settings_from_args
from .runner import run

def main():
    settings = build_settings_from_args()
    asyncio.run(run(settings))

if __name__ == "__main__":
    main()
