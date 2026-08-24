import tempfile
from pathlib import Path
from types import SimpleNamespace

from django.test import SimpleTestCase, override_settings

from documents.services.layout_service import LayoutService


class LayoutMatchTests(SimpleTestCase):
    def test_matches_vendor_invoice_and_amount(self):
        words = [
            {"page": 1, "text": "Harbor", "bbox": [10, 10, 12, 3]},
            {"page": 1, "text": "Freight", "bbox": [23, 10, 12, 3]},
            {"page": 1, "text": "Lines", "bbox": [36, 10, 10, 3]},
            {"page": 1, "text": "INV-10482", "bbox": [70, 10, 15, 3]},
            {"page": 1, "text": "4,280.00", "bbox": [70, 80, 12, 3]},
        ]
        meta = LayoutService().match_fields(
            words,
            {
                "vendor": "Harbor Freight Lines",
                "invoice_id": "INV-10482",
                "total": "4280.00",
            },
        )
        self.assertTrue(meta["vendor"]["matched"])
        self.assertTrue(meta["invoice_id"]["matched"])
        self.assertTrue(meta["total"]["matched"])
        self.assertEqual(meta["vendor"]["page"], 1)
        self.assertEqual(len(meta["vendor"]["bbox"]), 4)

    def test_unmatched_value_stays_unlocated(self):
        meta = LayoutService().match_fields(
            [{"page": 1, "text": "Invoice", "bbox": [10, 10, 12, 3]}],
            {"vendor": "Not On This Page"},
        )
        self.assertFalse(meta["vendor"]["matched"])
        self.assertIsNone(meta["vendor"]["bbox"])


class LayoutAnalyzeTests(SimpleTestCase):
    def test_renders_page_image_and_aligns_words(self):
        import pymupdf

        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "media"
            media.mkdir()
            pdf_path = Path(tmp) / "inv.pdf"
            pdf = pymupdf.open()
            page = pdf.new_page()
            page.insert_text((72, 72), "Harbor Freight Lines")
            page.insert_text((72, 110), "INV-10482")
            page.insert_text((72, 150), "4280.00")
            pdf.save(pdf_path)
            pdf.close()

            document = SimpleNamespace(
                file=SimpleNamespace(path=str(pdf_path)),
                job_id=1,
                id=9,
            )
            with override_settings(MEDIA_ROOT=media):
                result = LayoutService().analyze(document)

            self.assertTrue(result["pages"])
            self.assertTrue((media / result["pages"][0]["path"]).exists())
            blob = " ".join(word["text"] for word in result["words"])
            self.assertIn("Harbor", blob)
            meta = LayoutService().match_fields(
                result["words"],
                {"vendor": "Harbor Freight Lines", "invoice_id": "INV-10482"},
            )
            self.assertTrue(meta["vendor"]["matched"])
            self.assertTrue(meta["invoice_id"]["matched"])
