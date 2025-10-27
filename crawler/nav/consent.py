# -*- coding: utf-8 -*-
from playwright.async_api import Page

CONSENT_BUTTON_XP = [
    "//button[contains(., '동의') or contains(., '허용') or contains(., '수락')]",
    "//button[contains(., 'Accept') or contains(., 'Agree') or contains(., 'Allow')]",
    "//div[contains(@class,'onetrust')]//button[.//text()[contains(.,'Accept') or contains(.,'동의')]]",
]

async def click_consent(page: Page):
    for xp in CONSENT_BUTTON_XP:
        try:
            btn = await page.wait_for_selector(f"xpath={xp}", timeout=1200)
            if btn:
                await btn.click()
                await page.wait_for_timeout(300)
        except Exception:
            pass
