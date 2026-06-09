"""
AI 小说创作助手 - 核心生成模块
使用 WorkBuddy 内置 AI 能力生成小说内容
"""

import json
import re


def generate_novel_outline(theme: str, genre: str, num_chapters: int = 10) -> dict:
    """
    生成小说大纲

    Args:
        theme: 小说主题/设定
        genre: 题材（玄幻/都市/科幻/历史等）
        num_chapters: 章节数量

    Returns:
        包含 title, summary, characters, chapters 的字典
    """
    prompt = f"""
你是一个专业的小说大纲设计师。请根据以下信息，生成一个完整的小说大纲。

【题材】{genre}
【主题设定】{theme}
【章节数】约{num_chapters}章

请按以下 JSON 格式输出（不要输出任何其他内容）：

```json
{{
  "title": "小说标题",
  "summary": "整体故事简介（200字以内）",
  "characters": [
    {{"name": "角色名", "role": "主角/配角", "description": "角色简介"}},
    ...
  ],
  "chapters": [
    {{"number": 1, "title": "第1章标题", "summary": "本章内容概要"}},
    ...
  ]
}}
```

要求：
1. 故事有起承转合，情节紧凑
2. 角色鲜明，有成长弧线
3. 章节概要逻辑连贯
4. 输出纯 JSON，不要多余文字
"""
    # 注意：实际调用时需接入 AI 生成
    # 这里返回结构示例，实际内容由 AI 填充
    return {
        "prompt": prompt,
        "genre": genre,
        "theme": theme,
        "num_chapters": num_chapters,
    }


def generate_chapter_content(
    novel_title: str,
    chapter_title: str,
    chapter_summary: str,
    previous_content: str = "",
    characters: list = None,
    genre: str = "",
    word_count: int = 2000,
) -> str:
    """
    生成单章内容

    Args:
        novel_title: 小说标题
        chapter_title: 本章标题
        chapter_summary: 本章概要
        previous_content: 前文内容（用于保持连贯）
        characters: 角色列表
        genre: 题材
        word_count: 目标字数

    Returns:
        本章正文内容
    """
    char_desc = ""
    if characters:
        char_desc = "【主要角色】\n" + "\n".join(
            f"- {c['name']}：{c.get('description', '')}" for c in characters[:5]
        )

    prev_summary = ""
    if previous_content:
        prev_summary = f"【前文梗概】\n{previous_content[-500:] if len(previous_content) > 500 else previous_content}"

    prompt = f"""
你是一个专业的{genre}小说作家。请撰写以下章节的正文内容。

【小说标题】{novel_title}
【本章标题】{chapter_title}
【本章概要】{chapter_summary}
{char_desc}
{prev_summary}

要求：
1. 正文不少于{word_count}字
2. 语言流畅，符合{genre}题材风格
3. 情节与概要保持一致
4. 有对话、有描写、有情节推进
5. 直接输出正文，不要标题和解释

开始写作：
"""
    return prompt


def polish_text(text: str, instruction: str = "请润色以下文本，使其更加流畅生动") -> str:
    """润色/改写文本"""
    prompt = f"""
{instruction}

【原文】
{text}

【输出要求】
直接输出润色后的文本，不要多余解释。
"""
    return prompt


def continue_writing(
    current_text: str, plot_direction: str = "", word_count: int = 1000
) -> str:
    """续写功能"""
    prompt = f"""
请继续续写以下小说内容。

【已有内容】
{current_text[-1000:] if len(current_text) > 1000 else current_text}

【情节走向提示】
{plot_direction if plot_direction else "请根据现有情节自然延续"}

要求：
1. 续写约{word_count}字
2. 与上文风格保持一致
3. 情节自然推进
4. 直接输出续写内容
"""
    return prompt
