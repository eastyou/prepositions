# prepositions

[![CI](https://github.com/eastyou/prepositions/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/prepositions/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

面向英语课堂的方位介词与场景图工具：12 个常用方位介词、球与盒子的空间关系、可复现的四选一练习，以及自包含的 A4 可打印页面。

## 功能

- 收录 in / on / under / behind / in front of / next to / between / above / below / over / near / inside 共 12 个方位介词
- 每个介词都有中文释义、用法提示和对应的球与盒子场景
- 查词自动忽略大小写与多余空格，未知介词给出中文错误提示
- 12 个场景句，按介词生成 SVG 位置图，覆盖里外、上下、前后、旁边、之间等关系
- `make_quiz` 生成四选一练习，选项唯一、答案固定，同一随机种子结果完全可复现
- 练习页与场景图页均为内联 CSS 的单文件 HTML，支持 A4 打印与答案版
- 全部使用 Python 标准库，零第三方依赖

## 安装

```bash
pip install -e .
```

也可以不安装，直接在仓库根目录运行 `python -m prepositions`。

## 使用

```bash
# 查看单个介词
prepositions info "in front of"

# 列出全部介词
prepositions list

# 生成单个场景的可打印页面
prepositions scene "next to" -o examples/next-to.html

# 生成 8 道四选一练习（含答案）
prepositions quiz --count 8 --seed 3 -o examples/worksheet.html --answers

# 生成全部场景图
prepositions demo -o examples/scenes.html
```

`quiz` 的 `--count` 取值范围是 1 ~ 50，`--seed` 控制随机顺序；不传 `--answers` 时输出学生版练习页。

## 作为库使用

```python
from prepositions import check_answer, lookup, make_quiz, scene_svg

assert lookup("  IN  ")["word"] == "in"
assert lookup("in   front   of")["meaning"] == "在……前面"
assert check_answer("In Front Of", "in front of") is True

first = make_quiz(8, 3)
second = make_quiz(8, 3)
assert first == second
assert len(first[0]["options"]) == 4
assert first[0]["answer"] in first[0]["options"]

assert "<svg" in scene_svg("between")
assert 'class="box"' in scene_svg("in")
```

## 示例

- [examples/worksheet.html](examples/worksheet.html)：8 道四选一练习的答案版，含场景缩略图与解析
- [examples/scenes.html](examples/scenes.html)：12 个方位介词的场景图与用法说明

两个页面都内联 CSS，直接用浏览器打开即可打印为 A4。

## 测试

```bash
python -m unittest discover -s tests -v
```

共 79 项单元测试，覆盖词表完整性、规范化、查词、场景映射、练习确定性与选项去重、SVG 片段、HTML 转义、命令行退出码与文件输出。CI 在 Linux、macOS、Windows 上运行 Python 3.9 ~ 3.13。

## 许可

MIT © 2026 eastyou
