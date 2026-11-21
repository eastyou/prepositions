"""单元测试：词表、规范化、查词、练习生成与答案判定。"""

from __future__ import annotations

import re
import unittest

from prepositions.model import (
    MAX_QUIZ_COUNT,
    PREPOSITIONS,
    SCENES,
    build_sentence,
    check_answer,
    list_words,
    lookup,
    make_quiz,
    normalize,
    scene_for,
)


class PrepositionDataTests(unittest.TestCase):
    def test_preposition_count(self) -> None:
        self.assertEqual(len(PREPOSITIONS), 12)

    def test_word_order(self) -> None:
        expected = [
            "in",
            "on",
            "under",
            "behind",
            "in front of",
            "next to",
            "between",
            "above",
            "below",
            "over",
            "near",
            "inside",
        ]
        self.assertEqual(list_words(), expected)

    def test_preposition_fields(self) -> None:
        for item in PREPOSITIONS:
            with self.subTest(word=item.get("word")):
                self.assertEqual(
                    set(item), {"word", "meaning", "note", "position"}
                )
                for field in ("word", "meaning", "note", "position"):
                    self.assertIsInstance(item[field], str)
                    self.assertTrue(str(item[field]).strip())

    def test_positions_are_unique(self) -> None:
        positions = [str(item["position"]) for item in PREPOSITIONS]
        self.assertEqual(len(set(positions)), 12)

    def test_scene_count(self) -> None:
        self.assertGreaterEqual(len(SCENES), 8)

    def test_scene_fields(self) -> None:
        for scene in SCENES:
            with self.subTest(answer=scene.get("answer")):
                self.assertEqual(set(scene), {"sentence", "answer", "position"})
                for field in ("sentence", "answer", "position"):
                    self.assertIsInstance(scene[field], str)
                    self.assertTrue(str(scene[field]).strip())

    def test_scene_answers_and_positions(self) -> None:
        words = set(list_words())
        positions = {str(item["position"]) for item in PREPOSITIONS}
        for scene in SCENES:
            with self.subTest(answer=scene["answer"]):
                self.assertIn(scene["answer"], words)
                self.assertIn(scene["position"], positions)

    def test_scene_sentences_contain_answer(self) -> None:
        for scene in SCENES:
            sentence = str(scene["sentence"])
            answer = str(scene["answer"])
            with self.subTest(answer=answer):
                self.assertTrue(sentence.startswith("The ball is"))
                self.assertTrue(sentence.endswith("."))
                pattern = r"\b%s\b" % re.escape(answer)
                self.assertIsNotNone(re.search(pattern, sentence, re.IGNORECASE))


class NormalizeTests(unittest.TestCase):
    def test_lowercase_and_strip(self) -> None:
        self.assertEqual(normalize("  IN  "), "in")

    def test_collapse_internal_whitespace(self) -> None:
        self.assertEqual(normalize("In   Front\tOf"), "in front of")
        self.assertEqual(normalize("next\n to"), "next to")

    def test_non_string_raises_type_error(self) -> None:
        for value in (None, 12, 3.5, [], b"in"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    normalize(value)  # type: ignore[arg-type]

    def test_empty_or_blank_raises_value_error(self) -> None:
        for value in ("", "   ", "\t\n"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize(value)


class LookupTests(unittest.TestCase):
    def test_lookup_returns_entry(self) -> None:
        item = lookup("in")
        self.assertEqual(item["word"], "in")
        self.assertEqual(item["meaning"], "在……里面")

    def test_lookup_normalizes_case_and_spaces(self) -> None:
        item = lookup("  In   Front   Of  ")
        self.assertEqual(item["word"], "in front of")
        self.assertEqual(lookup("NEXT TO")["word"], "next to")

    def test_unknown_word_raises(self) -> None:
        with self.assertRaises(ValueError):
            lookup("beyond")

    def test_non_string_raises(self) -> None:
        with self.assertRaises(TypeError):
            lookup(None)  # type: ignore[arg-type]

    def test_returned_entry_is_a_copy(self) -> None:
        item = lookup("on")
        item["meaning"] = "被修改"
        self.assertEqual(lookup("on")["meaning"], "在……上面")


class ListWordsTests(unittest.TestCase):
    def test_list_order_and_length(self) -> None:
        words = list_words()
        self.assertEqual(len(words), 12)
        self.assertEqual(words[0], "in")
        self.assertEqual(words[-1], "inside")

    def test_returns_new_list(self) -> None:
        words = list_words()
        words.append("beyond")
        self.assertEqual(len(list_words()), 12)


class MakeQuizTests(unittest.TestCase):
    def test_length_and_required_fields(self) -> None:
        items = make_quiz(8, 3)
        self.assertEqual(len(items), 8)
        for item in items:
            with self.subTest(question=item.get("question")):
                for field in ("question", "answer", "options", "explanation"):
                    self.assertIn(field, item)

    def test_options_are_four_unique_words(self) -> None:
        words = set(list_words())
        for item in make_quiz(12, 5):
            options = item["options"]
            self.assertIsInstance(options, list)
            self.assertEqual(len(options), 4)
            self.assertEqual(len(set(options)), 4)
            for option in options:
                self.assertIn(option, words)

    def test_answer_is_in_options_and_blank(self) -> None:
        for item in make_quiz(12, 11):
            with self.subTest(answer=item["answer"]):
                self.assertIn(item["answer"], item["options"])
                self.assertIn("____", str(item["question"]))
                pattern = r"\b%s\b" % re.escape(str(item["answer"]))
                self.assertIsNone(
                    re.search(pattern, str(item["question"]), re.IGNORECASE)
                )

    def test_explanation_mentions_sentence_and_answer(self) -> None:
        for item in make_quiz(6, 2):
            explanation = str(item["explanation"])
            self.assertIn(str(item["sentence"]), explanation)
            self.assertIn(str(item["answer"]), explanation)

    def test_same_seed_is_reproducible(self) -> None:
        self.assertEqual(make_quiz(8, 3), make_quiz(8, 3))

    def test_different_seeds_differ(self) -> None:
        self.assertNotEqual(make_quiz(8, 1), make_quiz(8, 2))

    def test_boundary_counts(self) -> None:
        self.assertEqual(len(make_quiz(1, 0)), 1)
        self.assertEqual(len(make_quiz(MAX_QUIZ_COUNT, 9)), MAX_QUIZ_COUNT)

    def test_count_out_of_range(self) -> None:
        for count in (0, -1, MAX_QUIZ_COUNT + 1):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    make_quiz(count, 0)

    def test_count_must_be_int(self) -> None:
        for count in (8.0, "8", None, True):
            with self.subTest(count=count):
                with self.assertRaises(TypeError):
                    make_quiz(count, 0)  # type: ignore[arg-type]

    def test_seed_must_be_int(self) -> None:
        for seed in (3.0, "3", None, False):
            with self.subTest(seed=seed):
                with self.assertRaises(TypeError):
                    make_quiz(3, seed)  # type: ignore[arg-type]

    def test_answers_and_positions_are_valid(self) -> None:
        positions = {str(item["position"]) for item in PREPOSITIONS}
        words = set(list_words())
        for item in make_quiz(20, 4):
            self.assertIn(item["answer"], words)
            self.assertIn(item["position"], positions)


class CheckAnswerTests(unittest.TestCase):
    def test_ignores_case_and_spaces(self) -> None:
        for answer, expected in (
            ("in", "in"),
            (" In ", "in"),
            ("IN FRONT OF", "in front of"),
            ("in   front    of", "In Front Of"),
        ):
            with self.subTest(answer=answer):
                self.assertTrue(check_answer(answer, expected))

    def test_wrong_or_empty_answer_is_false(self) -> None:
        self.assertFalse(check_answer("on", "in"))
        self.assertFalse(check_answer("", "in"))
        self.assertFalse(check_answer("in", ""))

    def test_non_string_raises(self) -> None:
        with self.assertRaises(TypeError):
            check_answer(None, "in")  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            check_answer("in", 3)  # type: ignore[arg-type]


class SceneTests(unittest.TestCase):
    def test_scene_for_known_word(self) -> None:
        scene = scene_for("under")
        self.assertEqual(scene["position"], "under")
        self.assertIn("under", str(scene["sentence"]))

    def test_scene_for_normalizes_input(self) -> None:
        self.assertEqual(scene_for("  IN   FRONT   OF  ")["position"], "front")

    def test_unknown_word_raises(self) -> None:
        with self.assertRaises(ValueError):
            scene_for("beyond")

    def test_non_string_raises(self) -> None:
        with self.assertRaises(TypeError):
            scene_for(None)  # type: ignore[arg-type]

    def test_scene_is_a_copy(self) -> None:
        scene = scene_for("in")
        scene["sentence"] = "changed"
        self.assertEqual(scene_for("in")["sentence"], "The ball is in the box.")

    def test_build_sentence(self) -> None:
        self.assertEqual(build_sentence("in"), "The ball is in the box.")
        self.assertEqual(
            build_sentence(" in   front   of "), "The ball is in front of the box."
        )

    def test_build_sentence_rejects_bad_input(self) -> None:
        with self.assertRaises(ValueError):
            build_sentence("beyond")
        with self.assertRaises(TypeError):
            build_sentence(1)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
