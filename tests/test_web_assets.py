import unittest
from pathlib import Path

from main import WEB_ASSETS, WEB_INDEX


class WebAssetTests(unittest.TestCase):
    def test_web_assets_exist(self):
        self.assertTrue(WEB_INDEX.is_file())
        self.assertTrue((WEB_ASSETS / "app.js").is_file())
        self.assertTrue((WEB_ASSETS / "styles.css").is_file())

    def test_html_references_asset_mount(self):
        html = WEB_INDEX.read_text(encoding="utf-8")

        self.assertIn("/web/assets/app.js", html)
        self.assertIn("/web/assets/styles.css", html)
        self.assertIn('data-tab="live"', html)
        self.assertIn('data-tab="training"', html)


if __name__ == "__main__":
    unittest.main()
