import pytest
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver

from pipetasks.scraping.pipeline import ScrapingPipeline


@pytest.mark.integration
def test_scraping_pipeline_has_driver():
    scraping_pipeline = ScrapingPipeline()
    assert isinstance(
        scraping_pipeline.driver,
        ChromeDriver,
    )
