import time
from typing import Any

from retrying import Retrying
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from undetected_chromedriver import Chrome, ChromeOptions

from pipetasks.pipeline import Pipeline


class ScrapingPipeline(Pipeline):
    TIMEOUT = 0.5
    CHROME_VERSION = None

    def __init__(  # type: ignore[no-untyped-def]
        self,
        headless: bool = True,
        *args,
        **kwargs,
    ):
        self.driver = self.__init_driver(headless=headless)
        super().__init__(*args, **kwargs)

    def __init_driver(
        self,
        headless: bool = True,
    ) -> Chrome:
        chrome_options = ChromeOptions()
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--lang=es-AR")

        return Chrome(
            options=chrome_options,
            headless=headless,
            use_subprocess=True,
            version_main=self.CHROME_VERSION,
        )

    def __del__(self) -> None:
        try:
            self.driver.quit()
        except Exception:
            pass

    def sleep(self, seconds: float | None = None) -> None:
        secs = seconds if seconds else self.TIMEOUT
        time.sleep(secs)

    def __timeout(self, seconds: float | None = None) -> float:
        return seconds if seconds is not None else self.TIMEOUT

    def get(self, dns: str) -> None:
        self.driver.get(dns)
        self.sleep()

    def find_element(
        self,
        by: str,
        value: str,
        on: WebElement | None = None,
        timeout: float | None = None,
    ) -> WebElement:
        if on:
            return on.find_element(by, value)
        else:
            return WebDriverWait(
                self.driver,
                self.__timeout(timeout),
            ).until(EC.presence_of_element_located((by, value)))

    def find_elements(
        self,
        by: str,
        value: str,
        on: WebElement | None = None,
        timeout: float | None = None,
    ) -> list[WebElement]:
        if on:
            return on.find_elements(by, value)
        else:
            return WebDriverWait(
                self.driver,
                self.__timeout(timeout),
            ).until(EC.presence_of_all_elements_located((by, value)))

    def click(
        self,
        by: str,
        value: str,
        on: WebElement | None = None,
        timeout: float | None = None,
        retry_kwargs: dict[str, Any] | None = None,
    ) -> None:
        def _do_click() -> None:
            wait_timeout = self.__timeout(timeout)
            element = self.find_element(
                by,
                value,
                on=on,
                timeout=wait_timeout,
            )
            WebDriverWait(self.driver, wait_timeout).until(
                EC.element_to_be_clickable(element)
            ).click()
            self.sleep()

        if retry_kwargs is not None:
            Retrying(**retry_kwargs).call(_do_click)
        else:
            _do_click()

    def find_any_element_of(
        self,
        *xpaths: str,
        timeout: float | None = None,
    ) -> WebElement:
        wait_timeout = self.__timeout(timeout)
        for xpath in xpaths:
            try:
                return self.find_element(
                    By.XPATH,
                    xpath,
                    timeout=wait_timeout,
                )
            except TimeoutException:
                continue
        raise NoSuchElementException("No se encontró el elemento deseado.") from None
