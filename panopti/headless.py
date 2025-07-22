# panopti/headless.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class HeadlessBrowser:
    """Wrapper around a Playwright browser running in headless mode."""

    page: any
    browser: any
    ctx: any
    pw: any

    def close(self) -> None:
        try:
            if self.browser:
                self.browser.close()
        finally:
            if self.pw:
                self.pw.stop()


def launch(url: str, width: int = 1280, height: int = 720) -> HeadlessBrowser:
    """Launch a Chromium browser in headless mode and load the given URL.

    Parameters
    ----------
    url:
        The URL of the panopti server including query parameters.
    width:
        Browser viewport width.
    height:
        Browser viewport height.

    Returns
    -------
    HeadlessBrowser
        Object containing Playwright handles. Call ``close()`` when done.
    """

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - missing dependency
        msg = (
            "\n[Panopti] ERROR:\n"
            "Playwright is required for headless mode.\n"
            "See https://armanmaesumi.github.io/panopti/headless_rendering/ for more information.\n"
            "Exiting...\n"
        )
        raise RuntimeError(msg) from exc

    pw = sync_playwright().start()
    try:
        browser = pw.chromium.launch(headless=True)
    except Exception as exc:
        pw.stop()
        msg = (
            "\n[Panopti] ERROR:\n"
            "Failed to launch Chromium. You may need to run 'playwright install chromium' "
            "to install the headless Chromium shell. If you have already installed the Playwright's "
            "headless Chromium shell, then you may need to specify the environment variable "
            "'PLAYWRIGHT_BROWSERS_PATH' to the path where Chromium is installed.\n"
            "See https://armanmaesumi.github.io/panopti/headless_rendering/ for more information.\n"
            "Exiting...\n"
        )
        raise RuntimeError(msg) from exc

    ctx = browser.new_context(viewport={"width": width, "height": height})
    page = ctx.new_page()
    page.goto(url)

    return HeadlessBrowser(page=page, browser=browser, ctx=ctx, pw=pw)
