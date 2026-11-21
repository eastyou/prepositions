"""prepositions 命令行入口。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .model import build_sentence, list_words, lookup, make_quiz
from .render import scene_html, scenes_html, worksheet_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prepositions", description="英语方位介词与场景图工具"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    info = sub.add_parser("info", help="查看某个方位介词的释义与例句")
    info.add_argument("word", help="介词，例如 in 或 in front of")

    sub.add_parser("list", help="列出全部方位介词")

    scene = sub.add_parser("scene", help="生成单个场景的可打印 HTML 页面")
    scene.add_argument("word", help="介词，例如 next to")
    scene.add_argument("-o", "--output", required=True, help="输出 HTML 路径")

    quiz = sub.add_parser("quiz", help="生成四选一练习页")
    quiz.add_argument("--count", type=int, default=8, help="题目数量（1-50），默认 8")
    quiz.add_argument("--seed", type=int, default=0, help="随机种子，默认 0")
    quiz.add_argument("-o", "--output", required=True, help="输出 HTML 路径")
    quiz.add_argument("--answers", action="store_true", help="输出含答案的版本")

    demo = sub.add_parser("demo", help="生成全部场景图页面")
    demo.add_argument("-o", "--output", required=True, help="输出 HTML 路径")

    return parser


def _run(args: argparse.Namespace) -> int:
    if args.command == "info":
        item = lookup(args.word)
        print("介词：%s" % item["word"])
        print("释义：%s" % item["meaning"])
        print("用法：%s" % item["note"])
        print("例句：%s" % build_sentence(args.word))
        print("场景位置：%s" % item["position"])
        return 0
    if args.command == "list":
        words = list_words()
        for index, word in enumerate(words, start=1):
            item = lookup(word)
            print("%2d. %-12s %s" % (index, word, item["meaning"]))
        print("共 %d 个方位介词。" % len(words))
        return 0
    if args.command == "scene":
        info = lookup(args.word)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            scene_html(args.word, "方位介词场景：%s" % info["word"]),
            encoding="utf-8",
        )
        print("已生成场景页：%s" % output)
        return 0
    if args.command == "quiz":
        items = make_quiz(args.count, args.seed)
        title = "方位介词练习（答案版）" if args.answers else "方位介词练习"
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            worksheet_html(items, title, show_answers=args.answers),
            encoding="utf-8",
        )
        print("已生成练习页：%s（共 %d 题）" % (output, len(items)))
        return 0
    if args.command == "demo":
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(scenes_html("方位介词场景图"), encoding="utf-8")
        print("已生成场景图页：%s" % output)
        return 0
    raise ValueError("未知命令：%s" % args.command)


def _ensure_utf8_console() -> None:
    """Windows 控制台默认编码可能无法输出中文，尽量切换为 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            continue


def main(argv: Optional[Sequence[str]] = None) -> int:
    _ensure_utf8_console()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except (TypeError, ValueError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
