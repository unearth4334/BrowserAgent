from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable, Literal
import os

from playwright.sync_api import sync_playwright, Browser as PWBrowser, Page, Error as PlaywrightError

from .actions import (
    Action, Navigate, Click, Type, WaitForSelector, WaitForUser, 
    ExtractLinks, ExtractHTML, ExecuteJS, UploadFile, SelectOption, SetSlider
)
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
    browser_type: Literal["chromium", "firefox", "webkit"] = "chromium"
    launch_timeout: int = 15000  # milliseconds
    navigation_timeout: int = 30000  # milliseconds
    default_wait: Literal["load", "domcontentloaded", "networkidle"] = "load"
    extra_launch_args: list[str] = field(default_factory=list)
    screenshot_on_error: bool = False
    screenshot_dir: str = "/tmp/browser-agent-screenshots"

    _playwright: Optional[object] = field(default=None, init=False)
    _browser: Optional[PWBrowser] = field(default=None, init=False)
    _page: Optional[Page] = field(default=None, init=False)
    _extracted_links: list[str] = field(default_factory=list, init=False)
    _extracted_html: str = field(default="", init=False)

    def start(self) -> None:
        if self._browser is not None:
            return

        logger.info(
            "Starting Playwright browser (type=%s, headless=%s)",
            self.browser_type,
            self.headless,
        )
        
        try:
            self._playwright = sync_playwright().start()
            
            # Select browser type
            if self.browser_type == "chromium":
                browser_type = self._playwright.chromium
            elif self.browser_type == "firefox":
                browser_type = self._playwright.firefox
            elif self.browser_type == "webkit":
                browser_type = self._playwright.webkit
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")

            launch_args: dict = {
                "headless": self.headless,
                "timeout": self.launch_timeout,
            }
            
            if self.executable_path:
                launch_args["executable_path"] = self.executable_path
            
            # Add extra launch args for Docker/headless environments
            if self.extra_launch_args:
                launch_args["args"] = self.extra_launch_args
            elif self.headless and self.browser_type == "chromium":
                # Default args for headless Chromium in containerized environments
                launch_args["args"] = [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]

            self._browser = browser_type.launch(**launch_args)
            
            # Create page with timeouts
            self._page = self._browser.new_page()
            self._page.set_default_timeout(self.navigation_timeout)
            self._page.set_default_navigation_timeout(self.navigation_timeout)
            
            logger.info("Browser started successfully")
            
        except PlaywrightError as e:
            logger.error("Failed to start browser: %s", e)
            logger.error(
                "Ensure Playwright browsers are installed: playwright install %s",
                self.browser_type,
            )
            raise
        except Exception as e:
            logger.error("Unexpected error starting browser: %s", e)
            raise

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
        
        try:
            if isinstance(action, Navigate):
                page.goto(action.url, wait_until=self.default_wait)
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
            elif isinstance(action, ExecuteJS):
                # Execute JavaScript in page context
                result = page.evaluate(action.code)
                logger.info("Executed JS, result: %s", result)
            elif isinstance(action, UploadFile):
                # Upload file to input element
                page.set_input_files(action.selector, action.file_path)
                logger.info("Uploaded file %s to %s", action.file_path, action.selector)
            elif isinstance(action, SelectOption):
                # Select option from dropdown
                page.select_option(action.selector, action.value)
                logger.info("Selected option %s in %s", action.value, action.selector)
            elif isinstance(action, SetSlider):
                # Set slider value using JavaScript
                page.evaluate(
                    f"document.querySelector('{action.selector}').value = {action.value};"
                    f"document.querySelector('{action.selector}').dispatchEvent(new Event('input'));"
                    f"document.querySelector('{action.selector}').dispatchEvent(new Event('change'));"
                )
                logger.info("Set slider %s to value %s", action.selector, action.value)
            else:  # pragma: no cover - safety
                raise ValueError(f"Unknown action type {action}")
        except Exception as e:
            logger.error("Error performing action %s: %s", action, e)
            if self.screenshot_on_error:
                self._take_error_screenshot(action)
            raise
    
    def _take_error_screenshot(self, action: Action) -> None:
        """Take a screenshot when an error occurs."""
        if self._page is None:
            return
        
        try:
            os.makedirs(self.screenshot_dir, exist_ok=True)
            timestamp = __import__("time").strftime("%Y%m%d_%H%M%S")
            action_type = action.__class__.__name__
            filename = f"{self.screenshot_dir}/error_{action_type}_{timestamp}.png"
            self._page.screenshot(path=filename)
            logger.info("Error screenshot saved to: %s", filename)
        except Exception as e:
            logger.warning("Failed to take error screenshot: %s", e)
    
    def get_extracted_links(self) -> list[str]:
        """Return the list of extracted links from the last ExtractLinks action."""
        return self._extracted_links.copy()
    
    def get_extracted_html(self) -> str:
        """Return the extracted HTML from the last ExtractHTML action."""
        return self._extracted_html
