import json
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class StreamlitTests(unittest.TestCase):
    def test_artifact_dashboard_and_zero_effect_scenario(self):
        before = (ROOT / "artifacts/results.json").read_bytes()
        app = AppTest.from_file(
            str(ROOT / "streamlit_app.py"), default_timeout=30
        ).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.metric), 4)
        self.assertEqual(app.metric[1].value, "0.859")
        app.slider[0].set_value(0).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("0 contacts selected" in m.value for m in app.markdown))
        self.assertEqual(before, (ROOT / "artifacts/results.json").read_bytes())
