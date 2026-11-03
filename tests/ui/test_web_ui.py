import pytest


@pytest.mark.ui
def test_web_ui_loads_submits_and_validates(settings):
    if not settings.run_ui_tests:
        pytest.skip("Set RUN_UI_TESTS=true and start the sample app to run Playwright tests")
    playwright = pytest.importorskip("playwright.sync_api")

    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch()
        page = browser.new_page()
        page.goto(settings.ui_base_url)
        assert page.get_by_role("heading", name="Knowledge Base Assistant").is_visible()

        page.get_by_label("Question").fill("What is the return window?")
        page.get_by_role("button", name="Ask").click()
        page.locator("#answer").wait_for()
        assert "30 days" in page.locator("#answer").inner_text()

        page.get_by_label("Question").fill("")
        page.locator("#ask-form").evaluate("form => form.noValidate = true")
        page.get_by_role("button", name="Ask").click()
        assert "Please enter" in page.get_by_role("alert").inner_text()
        browser.close()
