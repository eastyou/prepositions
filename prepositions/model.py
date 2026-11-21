"""数据模型：方位介词词表、球与盒子场景、练习生成。"""

from __future__ import annotations

import random
import re
from typing import Dict, List

MAX_QUIZ_COUNT = 50

PREPOSITIONS: List[Dict[str, object]] = [
    {
        "word": "in",
        "meaning": "在……里面",
        "note": "强调在某个空间的内部，常与封闭空间连用，如 in the box。",
        "position": "in",
    },
    {
        "word": "on",
        "meaning": "在……上面",
        "note": "表示在物体表面上并与之接触，如 on the table。",
        "position": "on",
    },
    {
        "word": "under",
        "meaning": "在……下面",
        "note": "表示在物体正下方，与 over 相对；under 更强调正下方。",
        "position": "under",
    },
    {
        "word": "behind",
        "meaning": "在……后面",
        "note": "表示在物体后方，视线通常被物体遮挡。",
        "position": "behind",
    },
    {
        "word": "in front of",
        "meaning": "在……前面",
        "note": "表示在物体前方，与 behind 相对，注意由三个单词组成。",
        "position": "front",
    },
    {
        "word": "next to",
        "meaning": "在……旁边",
        "note": "表示紧挨着某物，可与 beside 互换使用。",
        "position": "next_to",
    },
    {
        "word": "between",
        "meaning": "在……之间",
        "note": "表示在两者之间，通常要出现两个参照对象。",
        "position": "between",
    },
    {
        "word": "above",
        "meaning": "在……上方",
        "note": "表示位置高于某物，不一定在正上方，与 below 相对。",
        "position": "above",
    },
    {
        "word": "below",
        "meaning": "在……下方",
        "note": "表示位置低于某物，与 above 相对。",
        "position": "below",
    },
    {
        "word": "over",
        "meaning": "在……正上方",
        "note": "强调正上方或覆盖关系，也可表示越过某物。",
        "position": "over",
    },
    {
        "word": "near",
        "meaning": "在……附近",
        "note": "表示距离较近，但不一定紧挨着，与 far from 相对。",
        "position": "near",
    },
    {
        "word": "inside",
        "meaning": "在……内部",
        "note": "比 in 更强调完全处于内部，多用于封闭空间。",
        "position": "inside",
    },
]

SCENES: List[Dict[str, object]] = [
    {"sentence": "The ball is in the box.", "answer": "in", "position": "in"},
    {"sentence": "The ball is on the box.", "answer": "on", "position": "on"},
    {"sentence": "The ball is under the box.", "answer": "under", "position": "under"},
    {"sentence": "The ball is behind the box.", "answer": "behind", "position": "behind"},
    {
        "sentence": "The ball is in front of the box.",
        "answer": "in front of",
        "position": "front",
    },
    {
        "sentence": "The ball is next to the box.",
        "answer": "next to",
        "position": "next_to",
    },
    {
        "sentence": "The ball is between the two boxes.",
        "answer": "between",
        "position": "between",
    },
    {"sentence": "The ball is above the box.", "answer": "above", "position": "above"},
    {"sentence": "The ball is below the box.", "answer": "below", "position": "below"},
    {"sentence": "The ball is over the box.", "answer": "over", "position": "over"},
    {"sentence": "The ball is near the box.", "answer": "near", "position": "near"},
    {"sentence": "The ball is inside the box.", "answer": "inside", "position": "inside"},
]

_BY_WORD: Dict[str, Dict[str, object]] = {
    str(item["word"]): item for item in PREPOSITIONS
}
_SCENE_BY_WORD: Dict[str, Dict[str, object]] = {
    str(scene["answer"]): scene for scene in SCENES
}


def normalize(text: str) -> str:
    """去首尾空格、合并内部空白并转小写；类型或内容不合法时抛错。"""
    if not isinstance(text, str):
        raise TypeError("介词必须是字符串，收到 %s" % type(text).__name__)
    cleaned = " ".join(text.split()).lower()
    if not cleaned:
        raise ValueError("介词不能为空")
    return cleaned


def lookup(word: str) -> Dict[str, object]:
    """按介词查词条，支持大小写差异与多余空格。"""
    key = normalize(word)
    try:
        item = _BY_WORD[key]
    except KeyError:
        raise ValueError("未知介词：%s" % key) from None
    return dict(item)


def list_words() -> List[str]:
    """按固定顺序返回全部方位介词。"""
    return [str(item["word"]) for item in PREPOSITIONS]


def _as_int(value: object, label: str) -> int:
    """校验外部传入的整数参数，拒绝布尔值与浮点数。"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("%s必须是整数，收到 %s" % (label, type(value).__name__))
    return value


def _blank(sentence: str, answer: str) -> str:
    """把例句中的答案替换成下划线空格。"""
    pattern = re.compile(r"\b%s\b" % re.escape(answer), re.IGNORECASE)
    blanked, replaced = pattern.subn("____", sentence, count=1)
    if replaced != 1:
        raise ValueError("无法在例句中定位介词：%s" % answer)
    return blanked


def make_quiz(count: int, seed: int) -> List[Dict[str, object]]:
    """生成四选一练习题，同一 seed 结果可复现。"""
    total = _as_int(count, "题目数量")
    random_seed = _as_int(seed, "随机种子")
    if total < 1 or total > MAX_QUIZ_COUNT:
        raise ValueError("题目数量必须在 1 到 %d 之间" % MAX_QUIZ_COUNT)

    rng = random.Random(random_seed)
    indexes: List[int] = []
    while len(indexes) < total:
        block = list(range(len(SCENES)))
        rng.shuffle(block)
        indexes.extend(block)

    words = list_words()
    items: List[Dict[str, object]] = []
    for index in indexes[:total]:
        scene = SCENES[index]
        answer = str(scene["answer"])
        sentence = str(scene["sentence"])
        detail = _BY_WORD[answer]
        question = _blank(sentence, answer)
        distractors = rng.sample([word for word in words if word != answer], 3)
        options = distractors + [answer]
        rng.shuffle(options)
        explanation = "%s %s 表示「%s」。%s" % (
            sentence,
            answer,
            detail["meaning"],
            detail["note"],
        )
        items.append(
            {
                "question": question,
                "answer": answer,
                "options": options,
                "explanation": explanation,
                "sentence": sentence,
                "position": str(scene["position"]),
            }
        )
    return items


def check_answer(answer: str, expected: str) -> bool:
    """忽略大小写与多余空格地比较答案。"""
    if not isinstance(answer, str) or not isinstance(expected, str):
        raise TypeError("答案与标准答案都必须是字符串")
    left = " ".join(answer.split()).lower()
    right = " ".join(expected.split()).lower()
    return bool(left) and left == right


def scene_for(word: str) -> Dict[str, object]:
    """返回介词对应的球与盒子场景。"""
    key = normalize(word)
    try:
        scene = _SCENE_BY_WORD[key]
    except KeyError:
        raise ValueError("该介词暂无场景：%s" % key) from None
    return dict(scene)


def build_sentence(word: str) -> str:
    """返回介词的示例句。"""
    return str(scene_for(word)["sentence"])
