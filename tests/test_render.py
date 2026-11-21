"""单元测试：SVG 场景图与 HTML 页面的结构、转义和边界。"""

from __future__ import annotations

import unittest
from typing import Dict

from prepositions.model import PREPOSITIONS, list_words, make_quiz
from prepositions.render import scene_html, scene_svg, scenes_html, worksheet_html


def _custom_item(**overrides: object) -> Dict[str, object]:
    item = {
        "question": "The ball is ____ the box.",
        "answer": "in",
        "options": ["in", "on", "under", "near"],
        "explanation": "in 表示在内部。",
    }
    item.update(overrides)
    return item


class SceneSvgTests(unittest.TestCase):
    def test_all_positions_produce_valid_svg(self) -> None:
        for entry in PREPOSITIONS:
            position = str(entry["position"])
            with self.subTest(position=position):
                svg = scene_svg(position)
                self.assertTrue(svg.startswith("<svg"))
                self.assertTrue(svg.endswith("</svg>"))
                self.assertIn('role="img"', svg)
                self.assertIn("<title", svg)
                self.assertIn("viewBox=\"0 0 320 220\"", svg)

    def test_labels_and_caption(self) -> None:
        svg = scene_svg("front")
        self.assertIn("球", svg)
        self.assertIn("盒子", svg)
        self.assertIn("in front of", svg)
        self.assertIn("在……前面", svg)

    def test_normalizes_and_is_deterministic(self) -> None:
        self.assertEqual(scene_svg("  IN  "), scene_svg("in"))
        self.assertEqual(scene_svg("next_to"), scene_svg("next_to"))

    def test_unknown_or_empty_position_raises(self) -> None:
        for position in ("", "   ", "flying", "next to"):
            with self.subTest(position=position):
                with self.assertRaises(ValueError):
                    scene_svg(position)

    def test_non_string_raises(self) -> None:
        with self.assertRaises(TypeError):
            scene_svg(None)  # type: ignore[arg-type]

    def test_layout_markers(self) -> None:
        between = scene_svg("between")
        self.assertEqual(between.count('class="box"'), 2)

        behind = scene_svg("behind")
        self.assertLess(behind.index('class="ball"'), behind.index('class="box"'))

        inside = scene_svg("in")
        self.assertLess(inside.index('class="box"'), inside.index('class="ball"'))

        self.assertIn('class="arc"', scene_svg("over"))
        self.assertIn('class="near-ring"', scene_svg("near"))

    def test_every_scene_is_distinct(self) -> None:
        scenes = {
            scene_svg(str(entry["position"])) for entry in PREPOSITIONS
        }
        self.assertEqual(len(scenes), 12)


class WorksheetTests(unittest.TestCase):
    def test_basic_worksheet_content(self) -> None:
        items = make_quiz(3, 7)
        page = worksheet_html(items, "方位介词练习")
        self.assertIn("方位介词练习", page)
        self.assertIn("The ball is", page)
        self.assertEqual(page.count('<li class="q">'), 3)
        self.assertIn("@page", page)
        self.assertIn("A4", page)
        self.assertNotIn("<script", page)
        self.assertNotIn('<link', page)
        self.assertNotIn('src="http', page)

    def test_options_use_ab_cd_letters(self) -> None:
        page = worksheet_html(make_quiz(1, 1), "练习")
        for letter in "ABCD":
            self.assertIn('<span class="key">%s</span>' % letter, page)

    def test_answers_hidden_and_shown(self) -> None:
        items = make_quiz(2, 3)
        hidden = worksheet_html(items, "练习")
        self.assertNotIn('class="answer"', hidden)
        self.assertNotIn("参考答案", hidden)

        shown = worksheet_html(items, "练习（答案版）", show_answers=True)
        self.assertEqual(shown.count('class="answer"'), 2)
        self.assertIn("参考答案", shown)
        self.assertIn("答案：", shown)

    def test_escapes_title_and_question(self) -> None:
        title = '<script>alert("x")</script>'
        question = "<b>危险</b> ____ the box."
        page = worksheet_html(
            [_custom_item(question=question)], title, show_answers=True
        )
        self.assertIn("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;", page)
        self.assertNotIn("<script>alert", page)
        self.assertIn("&lt;b&gt;危险&lt;/b&gt;", page)
        self.assertNotIn("<b>危险", page)

    def test_rejects_empty_items(self) -> None:
        with self.assertRaises(ValueError):
            worksheet_html([], "练习")

    def test_rejects_non_sequence_items(self) -> None:
        for items in ("abc", 123, None):
            with self.subTest(items=items):
                with self.assertRaises(TypeError):
                    worksheet_html(items, "练习")  # type: ignore[arg-type]

    def test_rejects_bad_title(self) -> None:
        with self.assertRaises(ValueError):
            worksheet_html(make_quiz(1, 0), "   ")
        with self.assertRaises(TypeError):
            worksheet_html(make_quiz(1, 0), 123)  # type: ignore[arg-type]

    def test_rejects_non_bool_flag(self) -> None:
        with self.assertRaises(TypeError):
            worksheet_html(make_quiz(1, 0), "练习", show_answers="yes")  # type: ignore[arg-type]

    def test_rejects_malformed_items(self) -> None:
        broken = _custom_item()
        del broken["answer"]
        with self.subTest(case="missing"):
            with self.assertRaises(ValueError):
                worksheet_html([broken], "练习")

        cases = (
            _custom_item(options=["in", "IN", "on", "under"]),
            _custom_item(options=["on", "under", "near", "above"]),
            _custom_item(options=["in", "on", "under"]),
            _custom_item(question="   "),
            _custom_item(position="flying"),
        )
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(ValueError):
                    worksheet_html([case], "练习")

    def test_item_without_position_renders_without_svg(self) -> None:
        page = worksheet_html([_custom_item()], "练习")
        self.assertNotIn("<svg", page)
        self.assertIn("The ball is", page)


class ScenesHtmlTests(unittest.TestCase):
    def test_contains_all_words_and_cards(self) -> None:
        page = scenes_html("方位介词场景图")
        for word in list_words():
            self.assertIn(word, page)
        self.assertEqual(page.count('class="card"'), 12)
        self.assertEqual(page.count("<svg"), 12)
        self.assertIn("@page", page)
        self.assertIn("A4", page)
        self.assertNotIn("<script", page)

    def test_escapes_title(self) -> None:
        page = scenes_html('<script>"场景"</script>')
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>", page)

    def test_rejects_bad_title(self) -> None:
        with self.assertRaises(ValueError):
            scenes_html("")
        with self.assertRaises(TypeError):
            scenes_html(None)  # type: ignore[arg-type]


class SceneHtmlTests(unittest.TestCase):
    def test_single_scene_page(self) -> None:
        page = scene_html("in front of", "单场景")
        self.assertIn("单场景", page)
        self.assertIn("in front of", page)
        self.assertIn("在……前面", page)
        self.assertIn("<svg", page)

    def test_unknown_word_raises(self) -> None:
        with self.assertRaises(ValueError):
            scene_html("beyond", "单场景")

    def test_bad_title_and_word_types(self) -> None:
        with self.assertRaises(ValueError):
            scene_html("in", "   ")
        with self.assertRaises(TypeError):
            scene_html(None, "单场景")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
