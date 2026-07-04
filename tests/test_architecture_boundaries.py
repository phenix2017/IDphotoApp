import os
import threading
import time
import unittest

from PIL import Image

from background_engine import selected_background_engine
from print_sheet import LayoutSpec, VERY_LIGHT_GUIDE_COLORS, build_print_sheet


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_background_engine_context_restores_environment(self):
        old_birefnet = os.environ.get("IDPHOTO_DISABLE_BIREFNET")
        old_rembg = os.environ.get("IDPHOTO_DISABLE_REMBG")

        with selected_background_engine("Basic (no AI model)"):
            self.assertEqual(os.environ.get("IDPHOTO_DISABLE_BIREFNET"), "1")
            self.assertEqual(os.environ.get("IDPHOTO_DISABLE_REMBG"), "1")

        self.assertEqual(os.environ.get("IDPHOTO_DISABLE_BIREFNET"), old_birefnet)
        self.assertEqual(os.environ.get("IDPHOTO_DISABLE_REMBG"), old_rembg)

    def test_background_engine_serializes_concurrent_sessions(self):
        """Streamlit runs each session in its own thread of one process, so two
        concurrent requests picking different engines must not interleave their
        env-var toggling — otherwise one session's inference can silently run
        under another session's engine choice."""
        order = []

        def worker(name, engine):
            with selected_background_engine(engine):
                order.append(f"{name}-enter")
                time.sleep(0.05)
                order.append(f"{name}-exit")

        t1 = threading.Thread(target=worker, args=("A", "Best quality (slower)"))
        t2 = threading.Thread(target=worker, args=("B", "Basic (no AI model)"))
        t1.start()
        time.sleep(0.01)
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(order, ["A-enter", "A-exit", "B-enter", "B-exit"])

    def test_print_sheet_guides_are_very_light(self):
        photo = Image.new("RGB", (600, 600), (250, 250, 250))
        sheet = build_print_sheet(
            photo,
            LayoutSpec(4, 6),
            dpi=300,
            margin_in=0.02,
            spacing_in=0.02,
            copies=2,
            draw_guides=True,
        )
        colors = sheet.getcolors(maxcolors=1000000)
        guide_colors = {
            color
            for _, color in colors
            if color not in {(255, 255, 255), (250, 250, 250)}
        }

        self.assertEqual(guide_colors, set(VERY_LIGHT_GUIDE_COLORS.values()))
        self.assertTrue(all(min(color) >= 232 for color in guide_colors))


if __name__ == "__main__":
    unittest.main()
