from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_driver():
    return MagicMock()


@pytest.fixture
def scraping_pipeline(mock_driver):
    with (
        patch("pipetasks.scraping.pipeline.ChromeDriverManager"),
        patch("pipetasks.scraping.pipeline.ChromeDriver", return_value=mock_driver),
    ):
        from pipetasks.scraping.pipeline import ScrapingPipeline

        yield ScrapingPipeline()
