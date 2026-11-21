"""单元测试：命令行退出码、标准输出/错误与文件输出。"""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from typing import Sequence, Tuple

from prepositions.cli import main


def _run(args: Sequence[str]) -> Tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(args))
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def test_info_success(self) -> None:
        code, out, err = _run(["info", "in"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("介词：in", out)
        self.assertIn("释义：在……里面", out)
        self.assertIn("The ball is in the box.", out)

    def test_info_normalizes_input(self) -> None:
        code, out, _ = _run(["info", "  IN  "])
        self.assertEqual(code, 0)
        self.assertIn("介词：in", out)

    def test_info_unknown_returns_two(self) -> None:
        code, out, err = _run(["info", "beyond"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("错误："))
        self.assertIn("未知介词", err)

    def test_list_prints_all_words(self) -> None:
        code, out, err = _run(["list"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("共 12 个方位介词。", out)
        self.assertIn("in front of", out)
        self.assertIn("next to", out)

    def test_scene_writes_html_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "scene.html")
            code, out, _ = _run(["scene", "in front of", "-o", path])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(path))
            with open(path, encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("<svg", content)
            self.assertIn("盒子", content)
            self.assertIn("已生成场景页", out)

    def test_scene_creates_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "a", "b", "scene.html")
            code, _, _ = _run(["scene", "next to", "-o", path])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(path))

    def test_scene_unknown_returns_two_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "scene.html")
            code, _, err = _run(["scene", "beyond", "-o", path])
            self.assertEqual(code, 2)
            self.assertIn("未知介词", err)
            self.assertFalse(os.path.exists(path))

    def test_quiz_writes_file_without_answers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "quiz.html")
            code, out, _ = _run(
                ["quiz", "--count", "2", "--seed", "3", "-o", path]
            )
            self.assertEqual(code, 0)
            with open(path, encoding="utf-8") as handle:
                content = handle.read()
            self.assertEqual(content.count('<li class="q">'), 2)
            self.assertNotIn('class="answer"', content)
            self.assertIn("共 2 题", out)

    def test_quiz_answers_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "quiz-answers.html")
            code, _, _ = _run(
                ["quiz", "--count", "3", "--seed", "4", "-o", path, "--answers"]
            )
            self.assertEqual(code, 0)
            with open(path, encoding="utf-8") as handle:
                content = handle.read()
            self.assertEqual(content.count('class="answer"'), 3)
            self.assertIn("参考答案", content)

    def test_quiz_count_out_of_range_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for count in ("0", "51"):
                path = os.path.join(tmp, "quiz-%s.html" % count)
                with self.subTest(count=count):
                    code, out, err = _run(
                        ["quiz", "--count", count, "-o", path]
                    )
                    self.assertEqual(code, 2)
                    self.assertEqual(out, "")
                    self.assertIn("错误：", err)
                    self.assertFalse(os.path.exists(path))

    def test_quiz_count_not_int_exits_with_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            err = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(err):
                with self.assertRaises(SystemExit) as ctx:
                    main(
                        [
                            "quiz",
                            "--count",
                            "abc",
                            "-o",
                            os.path.join(tmp, "quiz.html"),
                        ]
                    )
            self.assertEqual(ctx.exception.code, 2)

    def test_quiz_seed_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = os.path.join(tmp, "first.html")
            second = os.path.join(tmp, "second.html")
            _run(["quiz", "--count", "4", "--seed", "99", "-o", first])
            _run(["quiz", "--count", "4", "--seed", "99", "-o", second])
            with open(first, encoding="utf-8") as handle:
                first_text = handle.read()
            with open(second, encoding="utf-8") as handle:
                second_text = handle.read()
            self.assertEqual(first_text, second_text)

    def test_demo_writes_all_scenes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "scenes.html")
            code, out, _ = _run(["demo", "-o", path])
            self.assertEqual(code, 0)
            with open(path, encoding="utf-8") as handle:
                content = handle.read()
            self.assertEqual(content.count('class="card"'), 12)
            self.assertIn("共 12 个方位介词", content)
            self.assertIn("已生成场景图页", out)

    def test_unknown_command_exits_with_two(self) -> None:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                main(["unknown"])
        self.assertEqual(ctx.exception.code, 2)

    def test_missing_output_exits_with_two(self) -> None:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                main(["quiz"])
        self.assertEqual(ctx.exception.code, 2)

    def test_help_exits_with_zero(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                main(["--help"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("prepositions", out.getvalue())
        self.assertIn("方位介词", out.getvalue())


if __name__ == "__main__":
    unittest.main()
