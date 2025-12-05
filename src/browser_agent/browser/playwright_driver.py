from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable

from playwright.sync_api import sync_playwright, Browser as PWBrowser, Page

from .actions import Action, Navigate, Click, Type, WaitForSelector, WaitForUser, ExtractLinks, ExtractHTML
from .observation import PageObservation, ButtonInfo, InputInfo
from ..logging_utils import get_logger

logger = get_logger(__name__)


@runtime_checkable
class BrowserController(Protocol):
    """Abstract browser controller interface."""

    def start(self) -> None:  # pragma: no cover - interface only
        ...

    def stop(self) -> None:  # pragma: no cover - interface only
        ...

    def get_observation(self) -> PageObservation:
        ...

    def perform(self, action: Action) -> None:
        ...


@dataclass
class PlaywrightBrowserController:
    """Playwright-based implementation of BrowserController."""

    executable_path: Optional[str] = None
    headless: bool = True

    _playwright: Optional[object] = field(default=None, init=False)
    _browser: Optional[PWBrowser] = field(default=None, init=False)
    _page: Optional[Page] = field(default=None, init=False)
    _extracted_links: list[str] = field(default_factory=list, init=False)
    _extracted_html: str = field(default="", init=False)

    def start(self) -> None:
        if self._browser is not None:
            return

        logger.info("Starting Playwright browser (headless=%s)", self.headless)
        self._playwright = sync_playwright().start()
        browser_type = self._playwright.chromium

        launch_args: dict = {"headless": self.headless}
        if self.executable_path:
            launch_args["executable_path"] = self.executable_path

        self._browser = browser_type.launch(**launch_args)
        self._page = self._browser.new_page()
        logger.info("Browser started")

    def stop(self) -> None:
        logger.info("Stopping browser")
        if self._page:
            self._page.close()
            self._page = None
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def get_observation(self) -> PageObservation:
        assert self._page is not None, "Browser not started"
        page = self._page

        buttons: list[ButtonInfo] = []
        for el in page.query_selector_all("button, input[type=submit]"):
            try:
                text = el.inner_text().strip()
            except Exception:
                text = ""
            selector = el.evaluate(
                "el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '')"
            )
            buttons.append(ButtonInfo(selector=selector, text=text))

        inputs: list[InputInfo] = []
        for el in page.query_selector_all(
            "input[type=text], input:not([type]), textarea"
        ):
            selector = el.evaluate(
                "el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '')"
            )
            name = el.get_attribute("name")
            value = el.get_attribute("value")
            inputs.append(InputInfo(selector=selector, name=name, value=value))

        obs = PageObservation(
            url=page.url,
            title=page.title(),
            buttons=buttons,
            inputs=inputs,
            raw_html=None,
        )
        logger.debug("Observation: %s", obs)
        return obs

    def perform(self, action: Action) -> None:
        assert self._page is not None, "Browser not started"
        page = self._page

        logger.info("Performing action: %s", action)
        if isinstance(action, Navigate):
            page.goto(action.url, wait_until="load")
        elif isinstance(action, Click):
            page.click(action.selector)
        elif isinstance(action, Type):
            page.fill(action.selector, action.text)
            if action.press_enter:
                page.press(action.selector, "Enter")
        elif isinstance(action, WaitForSelector):
            page.wait_for_selector(action.selector, timeout=action.timeout_ms)
        elif isinstance(action, WaitForUser):
            logger.info("Waiting for user: %s", action.message)
            input(action.message)
        elif isinstance(action, ExtractLinks):
            # Extract links matching the pattern
            elements = page.query_selector_all(action.pattern)
            self._extracted_links = []
            for el in elements:
                href = el.get_attribute("href")
                if href:
                    self._extracted_links.append(href)
            logger.info("Extracted %d links matching pattern: %s", len(self._extracted_links), action.pattern)
        elif isinstance(action, ExtractHTML):
            # Extract HTML content matching the selector
            element = page.query_selector(action.selector)
            if element:
                self._extracted_html = element.inner_html()
                logger.info("Extracted HTML from selector: %s (%d chars)", action.selector, len(self._extracted_html))
            else:
                self._extracted_html = ""
                logger.warning("No element found matching selector: %s", action.selector)
        else:  # pragma: no cover - safety
            raise ValueError(f"Unknown action type {action}")
    
    def get_extracted_links(self) -> list[str]:
        """Return the list of extracted links from the last ExtractLinks action."""
        return self._extracted_links.copy()
    
    def get_extracted_html(self) -> str:
        """Return the extracted HTML from the last ExtractHTML action."""
        return self._extracted_html
