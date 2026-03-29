import time
from unittest.mock import MagicMock, patch

import pytest
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By


def test_scraping_pipeline_has_timeout(scraping_pipeline):
    assert scraping_pipeline.TIMEOUT is not None and scraping_pipeline.TIMEOUT > 0


def test_scraping_pipeline_get_respects_timeout(scraping_pipeline):
    url = "https://google.com"

    start = time.monotonic()
    scraping_pipeline.get(url)
    elapsed = time.monotonic() - start
    assert elapsed >= scraping_pipeline.TIMEOUT
    scraping_pipeline.driver.get.assert_called_once_with(url)


def test_find_element_without_scope(scraping_pipeline):
    mock_element = MagicMock()

    with patch("pipetasks.scraping.pipeline.WebDriverWait") as mock_wait:
        mock_wait.return_value.until.return_value = mock_element
        result = scraping_pipeline.find_element(By.ID, "submit-btn")
        mock_wait.assert_called_once_with(
            scraping_pipeline.driver,
            scraping_pipeline.TIMEOUT,
        )
        assert result == mock_element


def test_find_element_with_scope(scraping_pipeline):
    mock_scope = MagicMock()
    mock_element = MagicMock()
    mock_scope.find_element.return_value = mock_element
    result = scraping_pipeline.find_element(By.ID, "submit-btn", on=mock_scope)
    mock_scope.find_element.assert_called_once_with(By.ID, "submit-btn")
    assert result == mock_element


def test_find_elements_without_scope(scraping_pipeline):
    mock_elements = [MagicMock(), MagicMock()]

    with patch("pipetasks.scraping.pipeline.WebDriverWait") as mock_wait:
        mock_wait.return_value.until.return_value = mock_elements
        result = scraping_pipeline.find_elements(By.CLASS_NAME, "item")
        mock_wait.assert_called_once_with(
            scraping_pipeline.driver,
            scraping_pipeline.TIMEOUT,
        )
        assert result == mock_elements


def test_find_elements_with_scope(scraping_pipeline):
    mock_scope = MagicMock()
    mock_elements = [MagicMock(), MagicMock()]
    mock_scope.find_elements.return_value = mock_elements
    result = scraping_pipeline.find_elements(By.CLASS_NAME, "item", on=mock_scope)
    mock_scope.find_elements.assert_called_once_with(By.CLASS_NAME, "item")
    assert result == mock_elements


def test_scraping_pipeline_click_without_scope(scraping_pipeline):
    mock_element = MagicMock()

    with (
        patch.object(
            scraping_pipeline,
            "find_element",
            return_value=mock_element,
        ),
        patch("pipetasks.scraping.pipeline.WebDriverWait") as mock_wait,
    ):
        mock_wait.return_value.until.return_value = mock_element
        scraping_pipeline.click(By.ID, "submit-btn")
        scraping_pipeline.find_element.assert_called_once_with(
            By.ID,
            "submit-btn",
            on=None,
            timeout=scraping_pipeline.TIMEOUT,
        )
        mock_element.click.assert_called_once()


def test_scraping_pipeline_click_with_scope(scraping_pipeline):
    mock_scope = MagicMock()
    mock_element = MagicMock()

    with (
        patch.object(
            scraping_pipeline,
            "find_element",
            return_value=mock_element,
        ) as mock_find,
        patch("pipetasks.scraping.pipeline.WebDriverWait") as mock_wait,
    ):
        mock_wait.return_value.until.return_value = mock_element
        scraping_pipeline.click(By.ID, "submit-btn", on=mock_scope)
        mock_find.assert_called_once_with(
            By.ID,
            "submit-btn",
            on=mock_scope,
            timeout=scraping_pipeline.TIMEOUT,
        )
        mock_element.click.assert_called_once()


def test_scraping_pipeline_click_with_try_again(scraping_pipeline):
    mock_element = MagicMock()

    with (
        patch.object(
            scraping_pipeline,
            "find_element",
            return_value=mock_element,
        ),
        patch("pipetasks.scraping.pipeline.WebDriverWait") as mock_wait,
    ):
        mock_wait.return_value.until.side_effect = [
            StaleElementReferenceException,
            mock_element,
        ]
        scraping_pipeline.click(
            By.ID,
            "submit-btn",
            retry_kwargs={
                "stop_max_attempt_number": 3,
                "retry_on_exception": lambda e: isinstance(
                    e, StaleElementReferenceException
                ),
            },
        )
        assert mock_wait.return_value.until.call_count == 2
        mock_element.click.assert_called_once()


def test_scraping_pipeline_click_with_retry_unhandled_exception(scraping_pipeline):
    mock_element = MagicMock()

    with (
        patch.object(
            scraping_pipeline,
            "find_element",
            return_value=mock_element,
        ),
        patch("pipetasks.scraping.pipeline.WebDriverWait") as mock_wait,
        pytest.raises(TimeoutException),
    ):
        mock_wait.return_value.until.side_effect = TimeoutException
        scraping_pipeline.click(
            By.ID,
            "submit-btn",
            retry_kwargs={
                "stop_max_attempt_number": 3,
                "retry_on_exception": lambda e: isinstance(
                    e, StaleElementReferenceException
                ),
            },
        )


def test_scraping_pipeline_click_with_retry_exhausted(scraping_pipeline):
    mock_element = MagicMock()

    with (
        patch.object(
            scraping_pipeline,
            "find_element",
            return_value=mock_element,
        ),
        patch("pipetasks.scraping.pipeline.WebDriverWait") as mock_wait,
        pytest.raises(StaleElementReferenceException),
    ):
        mock_wait.return_value.until.side_effect = StaleElementReferenceException
        scraping_pipeline.click(
            By.ID,
            "submit-btn",
            retry_kwargs={
                "stop_max_attempt_number": 3,
                "retry_on_exception": lambda e: isinstance(
                    e, StaleElementReferenceException
                ),
            },
        )

    assert mock_wait.return_value.until.call_count == 3


def test_find_any_element_matches_first_xpath(scraping_pipeline):
    mock_element = MagicMock()

    with patch.object(
        scraping_pipeline,
        "find_element",
        return_value=mock_element,
    ) as mock_find:
        result = scraping_pipeline.find_any_element_of(
            "//div[@id='a']",
            "//div[@id='b']",
        )
        assert result == mock_element
        assert mock_find.call_count == 1


def test_rfind_any_element_matches_second_xpath(scraping_pipeline):
    mock_element = MagicMock()

    with patch.object(
        scraping_pipeline,
        "find_element",
        side_effect=[TimeoutException, mock_element],
    ) as mock_find:
        result = scraping_pipeline.find_any_element_of(
            "//div[@id='a']",
            "//div[@id='b']",
        )
        assert result == mock_element
        assert mock_find.call_count == 2


def test_find_any_element_raises_when_no_xpath_matches(scraping_pipeline):
    with patch.object(
        scraping_pipeline,
        "find_element",
        side_effect=TimeoutException,
    ) as mock_find:
        with pytest.raises(NoSuchElementException):
            scraping_pipeline.find_any_element_of(
                "//div[@id='a']",
                "//div[@id='b']",
            )
        assert mock_find.call_count == 2
