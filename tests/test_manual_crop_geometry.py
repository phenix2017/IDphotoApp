import unittest

from process_photo import (
    PhotoSpec,
    default_manual_crop_rect,
    manual_crop_metrics,
    manual_crop_suggestions,
)


class ManualCropGeometryTests(unittest.TestCase):
    def setUp(self):
        self.spec = PhotoSpec(
            name="Test",
            width_in=2.0,
            height_in=2.0,
            head_height_ratio=0.56,
            eye_line_from_bottom_ratio=0.66,
            background_rgb=(255, 255, 255),
            top_margin_ratio=0.08,
        )

    def test_default_crop_stays_inside_image(self):
        rect = default_manual_crop_rect(
            image_shape=(1000, 800, 3),
            face_bbox=(300, 180, 180, 220),
            eye_point=(390, 260),
            spec=self.spec,
        )
        x1, y1, x2, y2 = rect
        self.assertGreaterEqual(x1, 0)
        self.assertGreaterEqual(y1, 0)
        self.assertLessEqual(x2, 800)
        self.assertLessEqual(y2, 1000)
        self.assertEqual(x2 - x1, y2 - y1)

    def test_manual_crop_metrics_are_near_targets_for_default_rect(self):
        face_bbox = (300, 180, 180, 220)
        eye_point = (390, 260)
        rect = default_manual_crop_rect((1000, 800, 3), face_bbox, eye_point, self.spec)
        metrics = manual_crop_metrics(rect, face_bbox, eye_point, self.spec)
        self.assertLess(abs(metrics["actual_eye_ratio"] - metrics["target_eye_ratio"]), 0.08)
        self.assertLess(metrics["actual_center_offset_ratio"], 0.02)

    def test_suggestions_report_valid_framing_for_default_rect(self):
        face_bbox = (300, 180, 180, 220)
        eye_point = (390, 260)
        rect = default_manual_crop_rect((1000, 800, 3), face_bbox, eye_point, self.spec)
        metrics = manual_crop_metrics(rect, face_bbox, eye_point, self.spec)
        self.assertIn("Framing is within", manual_crop_suggestions(metrics)[0])


if __name__ == "__main__":
    unittest.main()
