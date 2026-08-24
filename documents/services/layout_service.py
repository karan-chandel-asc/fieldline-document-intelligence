import re
from pathlib import Path

import pymupdf
from django.conf import settings

from fieldline.logger import logger


class LayoutService:
    """Render PDF pages, collect word boxes, and align extracted values to them."""

    def analyze(self, document):
        file_path = document.file.path
        pages = []
        words = []
        text_parts = []
        try:
            pdf = pymupdf.open(file_path)
        except Exception as e:
            logger.error(f"Could not open PDF for layout: {e}")
            return {"text": "", "pages": [], "words": []}

        out_dir = Path(settings.MEDIA_ROOT) / "documents" / str(document.job_id) / "pages" / str(document.id)
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            for index, page in enumerate(pdf):
                page_no = index + 1
                rect = page.rect
                width = rect.width or 1
                height = rect.height or 1
                pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1.6, 1.6), alpha=False)
                rel_path = f"documents/{document.job_id}/pages/{document.id}/page-{page_no:03d}.png"
                pixmap.save(str(Path(settings.MEDIA_ROOT) / rel_path))
                pages.append(
                    {
                        "page": page_no,
                        "path": rel_path.replace("\\", "/"),
                        "width": pixmap.width,
                        "height": pixmap.height,
                    }
                )
                page_text = (page.get_text("text") or "").strip()
                if page_text:
                    text_parts.append(page_text)
                for item in page.get_text("words") or []:
                    x0, y0, x1, y1, raw = item[:5]
                    token = str(raw or "").strip()
                    if not token:
                        continue
                    words.append(
                        {
                            "page": page_no,
                            "text": token,
                            "bbox": [
                                round(100 * float(x0) / width, 3),
                                round(100 * float(y0) / height, 3),
                                round(100 * (float(x1) - float(x0)) / width, 3),
                                round(100 * (float(y1) - float(y0)) / height, 3),
                            ],
                        }
                    )
        finally:
            pdf.close()

        return {
            "text": "\n\n".join(text_parts).strip(),
            "pages": pages,
            "words": words,
        }

    def match_fields(self, words, extracted):
        data = extracted if isinstance(extracted, dict) else {}
        meta = {}
        for key, value in data.items():
            if key == "line_items" or isinstance(value, (list, dict)):
                continue
            if value in (None, ""):
                meta[key] = {"matched": False, "conf": 0.2, "page": None, "bbox": None}
                continue
            hit = self._best_span(str(value), words)
            if hit:
                meta[key] = hit
            else:
                meta[key] = {"matched": False, "conf": 0.45, "page": None, "bbox": None}
        return meta

    def _best_span(self, value, words):
        if not words:
            return None
        numeric = self._normalize_number(value)
        tokens = self._tokens(value)
        by_page = {}
        for word in words:
            by_page.setdefault(word["page"], []).append(word)

        best = None
        for page, group in by_page.items():
            exact = self._token_window(group, tokens) if tokens else None
            if exact:
                return {
                    "matched": True,
                    "conf": 0.96,
                    "page": page,
                    "bbox": self._union(exact),
                }
            if numeric:
                number_hit = self._number_window(group, numeric)
                if number_hit:
                    candidate = {
                        "matched": True,
                        "conf": 0.9,
                        "page": page,
                        "bbox": self._union(number_hit),
                    }
                    best = candidate
        return best

    def _token_window(self, group, needles):
        if not needles:
            return None
        stream = []
        for idx, word in enumerate(group):
            for token in self._tokens(word["text"]):
                stream.append((token, idx))
        length = len(needles)
        if length > len(stream):
            return None
        for start in range(len(stream) - length + 1):
            window = stream[start : start + length]
            if [item[0] for item in window] == needles:
                first = window[0][1]
                last = window[-1][1]
                return group[first : last + 1]
        return None

    def _number_window(self, group, target):
        for start in range(len(group)):
            chunk = ""
            for end in range(start, min(start + 4, len(group))):
                chunk += group[end]["text"]
                if self._normalize_number(chunk) == target:
                    return group[start : end + 1]
        return None

    def _union(self, span):
        left = min(word["bbox"][0] for word in span)
        top = min(word["bbox"][1] for word in span)
        right = max(word["bbox"][0] + word["bbox"][2] for word in span)
        bottom = max(word["bbox"][1] + word["bbox"][3] for word in span)
        return [
            round(left, 3),
            round(top, 3),
            round(max(right - left, 0.8), 3),
            round(max(bottom - top, 0.8), 3),
        ]

    def _tokens(self, value):
        return re.findall(r"[a-z0-9]+", str(value).lower())

    def _normalize_number(self, value):
        cleaned = re.sub(r"[^\d.]", "", str(value))
        if not cleaned or not re.search(r"\d", cleaned):
            return ""
        if cleaned.count(".") > 1:
            parts = cleaned.split(".")
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        if "." in cleaned:
            cleaned = cleaned.rstrip("0").rstrip(".")
        return cleaned
