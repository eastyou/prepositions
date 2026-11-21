"""渲染：球与盒子的 SVG 场景图，以及自包含的可打印 HTML 页面。"""

from __future__ import annotations

import html
from collections.abc import Mapping as MappingABC
from collections.abc import Sequence as SequenceABC
from typing import Dict, List, Mapping, Sequence

from .model import PREPOSITIONS, lookup, scene_for

_POSITION_META: Dict[str, Dict[str, object]] = {
    str(item["position"]): item for item in PREPOSITIONS
}

_CSS = """
@page { size: A4; margin: 16mm; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  margin: 0;
  background: #e9edf3;
  color: #1f2937;
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
    "Noto Sans SC", Arial, sans-serif;
  line-height: 1.6;
}
.sheet {
  width: 210mm;
  min-height: 297mm;
  margin: 16px auto;
  padding: 16mm;
  background: #fff;
  box-shadow: 0 2px 16px rgba(15, 23, 42, 0.12);
}
.sheet-head { border-bottom: 2px solid #2f6fed; padding-bottom: 10px; margin-bottom: 14px; }
h1 { margin: 0 0 6px; font-size: 22pt; color: #1e3a8a; }
.meta { margin: 0; color: #475569; font-size: 10.5pt; }
.badge {
  display: inline-block;
  margin-top: 8px;
  padding: 2px 10px;
  border-radius: 999px;
  background: #dcfce7;
  color: #166534;
  font-size: 10pt;
}
.questions { list-style: none; margin: 0; padding: 0; }
.q { padding: 10px 0 12px; border-bottom: 1px dashed #cbd5e1; page-break-inside: avoid; }
.q:last-child { border-bottom: 0; }
.q-head { font-size: 12pt; font-weight: 600; }
.num { color: #2f6fed; margin-right: 4px; }
.thumb { margin: 6px 0; }
.scene-svg {
  width: 132px;
  height: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fbfaf7;
}
.options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 18px;
  list-style: none;
  margin: 6px 0 0;
  padding: 0;
  font-size: 11pt;
}
.options li { min-width: 110px; }
.key {
  display: inline-block;
  width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  border-radius: 50%;
  background: #eef2ff;
  color: #3730a3;
  font-size: 9pt;
  margin-right: 4px;
}
.answer {
  margin-top: 6px;
  padding: 6px 10px;
  background: #ecfdf5;
  border-left: 3px solid #10b981;
  color: #065f46;
  font-size: 10.5pt;
}
.sheet-foot { margin-top: 14px; color: #64748b; font-size: 9.5pt; text-align: center; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.card {
  border: 1px solid #dbe3ee;
  border-radius: 10px;
  padding: 8px;
  background: #fff;
  page-break-inside: avoid;
}
.card h2 { margin: 0; font-size: 13pt; color: #1e3a8a; }
.card .meaning { font-size: 9.5pt; color: #475569; font-weight: 400; }
.card .thumb { margin: 4px 0; }
.card .scene-svg { width: 100%; }
.card .sentence { margin: 2px 0; font-size: 9.5pt; font-weight: 600; }
.card .note { margin: 0; font-size: 8.5pt; color: #64748b; }
.card .tag {
  display: inline-block;
  margin-top: 4px;
  padding: 0 6px;
  border-radius: 999px;
  background: #eef2ff;
  color: #3730a3;
  font-size: 8pt;
}
.focus { max-width: 460px; margin: 0 auto; }
.focus .card { padding: 14px; }
.focus .card h2 { font-size: 20pt; }
.focus .card .sentence { font-size: 12pt; }
.focus .card .note { font-size: 10.5pt; }
@media print {
  body { background: #fff; }
  .sheet { width: auto; min-height: 0; margin: 0; padding: 0; box-shadow: none; }
}
"""


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _require_title(title: str) -> str:
    if not isinstance(title, str):
        raise TypeError("标题必须是字符串，收到 %s" % type(title).__name__)
    cleaned = title.strip()
    if not cleaned:
        raise ValueError("标题不能为空")
    return cleaned


def _box(x: float, y: float, width: float = 100.0, height: float = 62.0,
         opacity: float = 1.0) -> str:
    return (
        '<rect class="box" x="%g" y="%g" width="%g" height="%g" rx="5" '
        'fill="#f3d4a0" fill-opacity="%g" stroke="#a16207" stroke-width="3"/>'
        % (x, y, width, height, opacity)
    )


def _ball(cx: float, cy: float) -> str:
    return (
        '<circle class="ball" cx="%g" cy="%g" r="13" fill="#2f6fed" '
        'stroke="#1e3a8a" stroke-width="2"/>'
        '<circle cx="%g" cy="%g" r="4" fill="#bfdbfe" opacity="0.9"/>'
        % (cx, cy, cx - 4, cy - 4)
    )


def _scene_parts(position: str) -> List[str]:
    """按位置键摆放盒子与球，返回按绘制顺序排列的 SVG 片段。"""
    if position == "in":
        return [_box(110, 104, opacity=0.55), _ball(160, 142)]
    if position == "inside":
        return [_box(110, 104, opacity=0.45), _ball(160, 146)]
    if position == "on":
        return [_box(110, 104), _ball(160, 91)]
    if position == "under":
        return [_box(110, 86, height=60), _ball(160, 174)]
    if position == "behind":
        return [_ball(160, 100), _box(110, 104)]
    if position == "front":
        return [_box(110, 104), _ball(160, 168)]
    if position == "next_to":
        return [_box(88, 112, width=90, height=56), _ball(218, 140)]
    if position == "between":
        return [
            _box(44, 104, width=72, height=62),
            _box(204, 104, width=72, height=62),
            _ball(160, 135),
        ]
    if position == "above":
        return [_box(110, 124), _ball(160, 58)]
    if position == "below":
        return [_box(110, 66), _ball(160, 190)]
    if position == "over":
        return [
            _box(110, 128),
            _ball(160, 58),
            '<path class="arc" d="M 208 122 Q 244 92 178 70" fill="none" '
            'stroke="#b45309" stroke-width="2" stroke-dasharray="4 4"/>'
            '<path class="arrow" d="M 178 70 L 190 76 L 186 63 Z" fill="#b45309"/>',
        ]
    if position == "near":
        return [
            _box(110, 104),
            '<circle class="near-ring" cx="250" cy="140" r="26" fill="none" '
            'stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4 4"/>',
            _ball(250, 140),
        ]
    raise ValueError("未知场景位置：%s" % position)


def scene_svg(position: str) -> str:
    """生成某个空间位置的球与盒子 SVG。"""
    if not isinstance(position, str):
        raise TypeError("场景位置必须是字符串，收到 %s" % type(position).__name__)
    key = " ".join(position.split()).lower()
    if not key:
        raise ValueError("场景位置不能为空")
    try:
        meta = _POSITION_META[key]
    except KeyError:
        raise ValueError("未知场景位置：%s" % key) from None

    word = str(meta["word"])
    meaning = str(meta["meaning"])
    svg_id = "scene-%s" % key
    parts = "".join(_scene_parts(key))
    return (
        '<svg class="scene-svg" xmlns="http://www.w3.org/2000/svg" '
        'viewBox="0 0 320 220" width="320" height="220" role="img" '
        'aria-labelledby="%s-title %s-desc">'
        '<title id="%s-title">%s · %s</title>'
        '<desc id="%s-desc">%s表示「%s」，画面展示球与盒子的位置关系。</desc>'
        '<rect x="0" y="0" width="320" height="220" fill="#fbfaf7"/>'
        '<text class="caption" x="160" y="24" text-anchor="middle" '
        'font-size="14" font-weight="700" fill="#1e3a8a">%s · %s</text>'
        "%s"
        '<text class="legend" x="12" y="212" font-size="11" fill="#475569">'
        "● 球 ball　▭ 盒子 box</text>"
        "</svg>"
        % (
            svg_id,
            svg_id,
            svg_id,
            _escape(word),
            _escape(meaning),
            svg_id,
            _escape(word),
            _escape(meaning),
            _escape(word),
            _escape(meaning),
            parts,
        )
    )


def _prepare_item(item: Mapping[str, object], index: int) -> Dict[str, object]:
    """校验并规范化一道题的输入，避免渲染时出现越界或缺失字段。"""
    if not isinstance(item, MappingABC):
        raise ValueError("第 %d 题格式不正确：应为字典" % index)
    for field in ("question", "answer", "options", "explanation"):
        if field not in item:
            raise ValueError("第 %d 题缺少字段：%s" % (index, field))

    question = item["question"]
    answer = item["answer"]
    explanation = item["explanation"]
    if not isinstance(question, str) or not question.strip():
        raise ValueError("第 %d 题的题干不能为空" % index)
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("第 %d 题的答案不能为空" % index)
    if not isinstance(explanation, str):
        raise ValueError("第 %d 题的解析必须是字符串" % index)

    raw_options = item["options"]
    if isinstance(raw_options, (str, bytes)) or not isinstance(
        raw_options, SequenceABC
    ):
        raise ValueError("第 %d 题的选项必须是列表" % index)
    options: List[str] = []
    for value in raw_options:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("第 %d 题的选项必须是非空字符串" % index)
        options.append(value.strip())
    if len(options) != 4:
        raise ValueError("第 %d 题必须提供 4 个选项" % index)

    normalized = [" ".join(value.split()).lower() for value in options]
    if len(set(normalized)) != len(normalized):
        raise ValueError("第 %d 题的选项不能重复" % index)
    key = " ".join(answer.split()).lower()
    if key not in normalized:
        raise ValueError("第 %d 题的答案必须出现在选项中" % index)

    position = item.get("position")
    if position is not None:
        if not isinstance(position, str):
            raise ValueError("第 %d 题的场景位置必须是字符串" % index)
        position_key = " ".join(position.split()).lower()
        if position_key not in _POSITION_META:
            raise ValueError("第 %d 题使用未知场景位置：%s" % (index, position_key))
        position = position_key

    return {
        "question": question.strip(),
        "answer": answer.strip(),
        "options": options,
        "explanation": explanation.strip(),
        "position": position,
    }


def _page(safe_title: str, body: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n"
        "<style>%s</style>\n"
        "</head>\n"
        "<body>\n"
        "%s\n"
        "</body>\n"
        "</html>\n" % (safe_title, _CSS, body)
    )


def worksheet_html(
    items: Sequence[Mapping[str, object]],
    title: str,
    show_answers: bool = False,
) -> str:
    """生成 A4 可打印的四选一练习页；show_answers 为真时输出答案版。"""
    cleaned_title = _require_title(title)
    if not isinstance(show_answers, bool):
        raise TypeError("show_answers 必须是布尔值，收到 %s" % type(show_answers).__name__)
    if isinstance(items, (str, bytes)) or not isinstance(items, SequenceABC):
        raise TypeError("题目列表必须是列表或元组")
    if not items:
        raise ValueError("题目列表不能为空")

    prepared: List[Dict[str, object]] = []
    for index, item in enumerate(items, start=1):
        prepared.append(_prepare_item(item, index))

    blocks: List[str] = []
    for index, item in enumerate(prepared, start=1):
        options = item["options"]
        assert isinstance(options, list)
        option_rows = "".join(
            '<li><span class="key">%s</span>%s</li>' % (letter, _escape(option))
            for letter, option in zip("ABCD", options)
        )
        thumb = ""
        if isinstance(item["position"], str):
            thumb = '<div class="thumb">%s</div>' % scene_svg(str(item["position"]))
        answer_block = ""
        if show_answers:
            detail = _escape(str(item["explanation"]))
            if detail:
                detail = "　<span>%s</span>" % detail
            answer_block = (
                '<div class="answer"><strong>答案：</strong>%s%s</div>'
                % (_escape(str(item["answer"])), detail)
            )
        blocks.append(
            '<li class="q">'
            '<div class="q-head"><span class="num">%d.</span>%s</div>'
            "%s"
            '<ul class="options">%s</ul>'
            "%s"
            "</li>"
            % (index, _escape(str(item["question"])), thumb, option_rows, answer_block)
        )

    badge = '<span class="badge">参考答案</span>' if show_answers else ""
    body = (
        '<main class="sheet">'
        '<header class="sheet-head">'
        "<h1>%s</h1>"
        '<p class="meta">姓名：__________　班级：__________　日期：__________</p>'
        "%s"
        "</header>"
        '<ol class="questions">%s</ol>'
        '<footer class="sheet-foot">共 %d 题 · 看图选择正确的方位介词</footer>'
        "</main>"
        % (
            _escape(cleaned_title),
            badge,
            "".join(blocks),
            len(prepared),
        )
    )
    return _page(_escape(cleaned_title), body)


def _scene_card(word: str) -> str:
    info = lookup(word)
    scene = scene_for(word)
    return (
        '<article class="card">'
        "<h2>%s <span class=\"meaning\">%s</span></h2>"
        '<div class="thumb">%s</div>'
        '<p class="sentence">%s</p>'
        '<p class="note">%s</p>'
        '<span class="tag">%s</span>'
        "</article>"
        % (
            _escape(str(info["word"])),
            _escape(str(info["meaning"])),
            scene_svg(str(scene["position"])),
            _escape(str(scene["sentence"])),
            _escape(str(info["note"])),
            _escape(str(info["position"])),
        )
    )


def scenes_html(title: str) -> str:
    """生成包含全部方位介词场景图的 A4 页面。"""
    cleaned_title = _require_title(title)
    cards = "".join(_scene_card(str(item["word"])) for item in PREPOSITIONS)
    body = (
        '<main class="sheet">'
        '<header class="sheet-head">'
        "<h1>%s</h1>"
        '<p class="meta">共 %d 个方位介词 · 观察球与盒子的位置关系</p>'
        "</header>"
        '<section class="grid">%s</section>'
        '<footer class="sheet-foot">英语方位介词与场景图 · 可打印 A4 页面</footer>'
        "</main>"
        % (_escape(cleaned_title), len(PREPOSITIONS), cards)
    )
    return _page(_escape(cleaned_title), body)


def scene_html(word: str, title: str) -> str:
    """生成单个介词的场景说明页。"""
    cleaned_title = _require_title(title)
    info = lookup(word)
    word_value = str(info["word"])
    body = (
        '<main class="sheet">'
        '<header class="sheet-head">'
        "<h1>%s</h1>"
        '<p class="meta">%s · %s</p>'
        "</header>"
        '<section class="focus">%s</section>'
        "</main>"
        % (
            _escape(cleaned_title),
            _escape(word_value),
            _escape(str(info["meaning"])),
            _scene_card(word_value),
        )
    )
    return _page(_escape(cleaned_title), body)
