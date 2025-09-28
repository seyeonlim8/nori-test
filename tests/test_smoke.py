def test_homepage_loads(driver, base_url):
    try:
        driver.get(base_url)
        assert driver.title != ""
    finally:
        driver.quit()