"""AI 小说创作助手 - Streamlit Web UI（无 API Key 版）
通过文件与 WorkBuddy 通信，由 WorkBuddy 内置 AI 直接生成内容。
"""

import streamlit as st
import os
import json
import re
import time
from datetime import datetime
from pathlib import Path

from novel_generator import (
    generate_novel_outline,
    generate_chapter_content,
    polish_text,
    continue_writing,
)

# ── 通信目录设置 ──────────────────────────────────────────
WORKBUDDY_DIR = Path.home() / ".workbuddy" / "ai_novel_writer"
WORKBUDDY_DIR.mkdir(parents=True, exist_ok=True)
PROMPT_FILE = WORKBUDDY_DIR / "prompt.txt"
RESPONSE_FILE = WORKBUDDY_DIR / "response.txt"
STATUS_FILE = WORKBUDDY_DIR / "status.txt"

# ── 页面配置 ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI 小说创作助手",
    page_icon="✍️",
    layout="wide",
)

# ── 初始化 session_state ──────────────────────────────────
if "novel" not in st.session_state:
    st.session_state.novel = None
if "chapters" not in st.session_state:
    st.session_state.chapters = {}
if "current_chapter" not in st.session_state:
    st.session_state.current_chapter = 1
if "genre" not in st.session_state:
    st.session_state.genre = "玄幻"
if "ai_prompt" not in st.session_state:
    st.session_state.ai_prompt = ""
if "ai_response" not in st.session_state:
    st.session_state.ai_response = ""
if "ai_pending" not in st.session_state:
    st.session_state.ai_pending = False
if "last_req_id" not in st.session_state:
    st.session_state.last_req_id = 0


# ── 侧边栏 ────────────────────────────────────────────────
with st.sidebar:
    st.title("✍️ AI 小说创作助手")
    st.caption("由 WorkBuddy AI 驱动，无需 API Key")
    st.divider()

    st.subheader("📂 导航")
    page = st.radio(
        "选择功能",
        ["🏠 新建小说", "📋 大纲管理", "📝 章节写作", "✨ 文本润色", "💾 导出小说"],
    )

    st.divider()
    st.caption(f"📁 通信目录：\n`{WORKBUDDY_DIR}`")


# ── 调用 AI：文件通信方式 ────────────────────────────────
def call_ai_via_file(prompt: str, max_tokens: int = 4096, timeout: int = 120) -> str:
    """通过文件与 WorkBuddy 通信，获取 AI 生成结果"""
    # 写入请求
    req_id = int(time.time())
    st.session_state.last_req_id = req_id
    st.session_state.ai_pending = True
    st.session_state.ai_prompt = prompt

    PROMPT_FILE.write_text(prompt, encoding="utf-8")
    STATUS_FILE.write_text(f"pending:{req_id}", encoding="utf-8")
    if RESPONSE_FILE.exists():
        RESPONSE_FILE.unlink()

    # 等待响应（在 Streamlit 中通过 rerun 轮询）
    st.session_state.ai_wait_start = time.time()
    st.session_state.ai_timeout = timeout
    st.rerun()


def check_ai_response() -> str | None:
    """检查是否有 AI 响应返回（在下次 rerun 时调用）"""
    if not st.session_state.get("ai_pending"):
        return st.session_state.get("ai_response", "")

    # 检查是否超时
    if time.time() - st.session_state.get("ai_wait_start", 0) > st.session_state.get("ai_timeout", 120):
        st.session_state.ai_pending = False
        return None  # 超时

    # 检查响应文件
    if RESPONSE_FILE.exists():
        status = STATUS_FILE.read_text(encoding="utf-8").strip() if STATUS_FILE.exists() else ""
        if status.startswith("done"):
            result = RESPONSE_FILE.read_text(encoding="utf-8")
            st.session_state.ai_pending = False
            st.session_state.ai_response = result
            if RESPONSE_FILE.exists():
                RESPONSE_FILE.unlink()
            return result

    # 还未完成，需要 rerun
    return None


def request_ai_and_wait(prompt: str, max_tokens: int = 4096) -> str:
    """请求 AI 并在当前 turn 通过文件等待结果（用于非 Streamlit 上下文）"""
    req_id = int(time.time())
    PROMPT_FILE.write_text(prompt, encoding="utf-8")
    STATUS_FILE.write_text(f"pending:{req_id}", encoding="utf-8")
    if RESPONSE_FILE.exists():
        RESPONSE_FILE.unlink()

    # 轮询等待（最多 120 秒）
    for _ in range(120):
        time.sleep(1)
        if RESPONSE_FILE.exists():
            status = STATUS_FILE.read_text(encoding="utf-8").strip() if STATUS_FILE.exists() else ""
            if status.startswith("done"):
                result = RESPONSE_FILE.read_text(encoding="utf-8")
                RESPONSE_FILE.unlink()
                return result
    return ""


# ── AI 请求面板（通用组件） ─────────────────────────────
def render_ai_panel():
    """渲染 AI 请求面板：显示 prompt + 等待区 + 响应粘贴区"""
    if not st.session_state.get("ai_pending"):
        return st.session_state.get("ai_response", "")

    st.info("🤖 **WorkBuddy AI 正在生成中…**\n\n"
            "请切换到 WorkBuddy 对话窗口，\n"
            "我会读取 prompt 并生成回复。")

    with st.expander("📄 当前 Prompt（可复制）", expanded=False):
        st.text_area(
            "复制以下内容发送给 WorkBuddy：",
            value=st.session_state.get("ai_prompt", ""),
            height=200,
            key="prompt_display",
            label_visibility="collapsed",
        )

    # 粘贴响应区
    st.subheader("📥 粘贴 AI 回复")
    pasted = st.text_area(
        "将 WorkBuddy 的回复粘贴到这里：",
        height=300,
        key="paste_response_area",
        label_visibility="collapsed",
    )

    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("✅ 确认收到回复", type="primary", use_container_width=True):
            if pasted.strip():
                # 写入响应文件以通知等待中的进程
                RESPONSE_FILE.write_text(pasted, encoding="utf-8")
                STATUS_FILE.write_text("done", encoding="utf-8")
                st.session_state.ai_response = pasted
                st.session_state.ai_pending = False
                st.rerun()
    with col_cancel:
        if st.button("❌ 取消", use_container_width=True):
            st.session_state.ai_pending = False
            if STATUS_FILE.exists():
                STATUS_FILE.write_text("cancelled", encoding="utf-8")
            st.rerun()

    # 自动轮询：检查响应文件是否已被写入（WorkBuddy 直接写入方式）
    if RESPONSE_FILE.exists():
        status = STATUS_FILE.read_text(encoding="utf-8").strip() if STATUS_FILE.exists() else ""
        if status.startswith("done") or not status.startswith("pending"):
            result = RESPONSE_FILE.read_text(encoding="utf-8")
            st.session_state.ai_response = result
            st.session_state.ai_pending = False
            if RESPONSE_FILE.exists():
                RESPONSE_FILE.unlink()
            st.rerun()

    st.stop()  # 暂停页面渲染，等待响应


# ── 页面 1：新建小说 ──────────────────────────────────────
if page == "🏠 新建小说":
    st.title("🏠 新建小说项目")

    # 如果正在等待 AI 响应，显示面板并暂停
    if st.session_state.get("ai_pending"):
        render_ai_panel()

    col1, col2 = st.columns([2, 1])

    with col1:
        genre = st.selectbox(
            "选择题材",
            ["玄幻", "都市", "科幻", "历史", "武侠", "言情", "悬疑", "恐怖", "其他"],
        )
        if genre == "其他":
            genre = st.text_input("请输入题材名称")
        st.session_state.genre = genre

        theme = st.text_area(
            "小说设定 / 灵感描述",
            placeholder="例：一个普通大学生偶然获得能看见鬼魂的能力，从此开始了阴阳两界的冒险……",
            height=120,
        )
        num_chapters = st.slider("预计章节数", 5, 50, 15)

    with col2:
        st.info(
            "💡 **提示**\n\n"
            "描述越详细，生成的大纲越精彩！\n\n"
            "可以包含：\n"
            "- 世界观设定\n"
            "- 主角人设\n"
            "- 核心冲突\n"
            "- 想要的元素"
        )

    if st.button("✨ 生成大纲", type="primary", use_container_width=True):
        if not theme.strip():
            st.warning("请先填写小说设定！")
        else:
            outline_data = generate_novel_outline(theme, genre, num_chapters)
            prompt = outline_data["prompt"]
            st.session_state.ai_prompt = prompt
            st.session_state.ai_pending = True
            st.session_state.ai_response = ""
            PROMPT_FILE.write_text(prompt, encoding="utf-8")
            STATUS_FILE.write_text(f"pending:{int(time.time())}", encoding="utf-8")
            if RESPONSE_FILE.exists():
                RESPONSE_FILE.unlink()
            st.rerun()

    # 如果刚收到响应，解析大纲
    if st.session_state.get("ai_response") and not st.session_state.get("ai_pending"):
        result = st.session_state.ai_response
        try:
            json_match = re.search(r"```json\s*(.*?)\s*```", result, re.DOTALL)
            if json_match:
                result = json_match.group(1)
            novel_data = json.loads(result)
            st.session_state.novel = novel_data
            st.session_state.chapters = {}
            st.session_state.genre = genre if 'genre' in dir() else st.session_state.genre
            st.success("✅ 大纲生成成功！请切换到「大纲管理」查看")
            st.session_state.ai_response = ""  # 清空
            st.rerun()
        except (json.JSONDecodeError, Exception) as e:
            st.error(f"大纲解析失败：{e}")
            st.text_area("原始 AI 输出（请检查格式）：", value=result, height=300)

# ── 页面 2：大纲管理 ──────────────────────────────────────
elif page == "📋 大纲管理":
    st.title("📋 小说大纲")

    if not st.session_state.novel:
        st.info("📭 还没有小说大纲，请先「新建小说」")
        st.stop()

    novel = st.session_state.novel

    st.subheader(novel.get("title", "未命名小说"))
    st.caption(f"题材：{st.session_state.genre}")

    with st.expander("📖 故事简介", expanded=True):
        st.write(novel.get("summary", "暂无简介"))

    with st.expander("👥 角色列表", expanded=True):
        chars = novel.get("characters", [])
        if chars:
            for c in chars:
                st.markdown(f"**{c['name']}**（`{c.get('role', '角色')}`）")
                st.caption(c.get("description", ""))
        else:
            st.caption("暂无角色信息")

    with st.expander("📑 章节大纲", expanded=True):
        chapters = novel.get("chapters", [])
        for ch in chapters:
            st.markdown(f"**第{ch['number']}章 {ch['title']}**")
            st.caption(ch.get("summary", ""))
            st.divider()

    if st.button("🗑️ 清除当前小说", use_container_width=True):
        st.session_state.novel = None
        st.session_state.chapters = {}
        st.rerun()

# ── 页面 3：章节写作 ──────────────────────────────────────
elif page == "📝 章节写作":
    st.title("📝 章节写作")

    if st.session_state.get("ai_pending"):
        render_ai_panel()

    if not st.session_state.novel:
        st.info("📭 请先生成小说大纲！")
        st.stop()

    novel = st.session_state.novel
    chapters_outline = novel.get("chapters", [])
    total = len(chapters_outline)

    col_sel, col_info = st.columns([1, 3])
    with col_sel:
        ch_num = st.number_input(
            "当前章节",
            min_value=1,
            max_value=max(total, 1),
            value=st.session_state.current_chapter,
        )
        st.session_state.current_chapter = int(ch_num)
    with col_info:
        if ch_num <= total:
            ch_info = chapters_outline[int(ch_num) - 1]
            st.caption(f"**{ch_info.get('title', '')}**")
            st.caption(ch_info.get("summary", ""))

    st.divider()

    content_key = f"content_{ch_num}"
    if content_key not in st.session_state:
        st.session_state[content_key] = st.session_state.chapters.get(str(ch_num), "")

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("✨ 生成本章内容", type="primary"):
            ch_info = (
                chapters_outline[int(ch_num) - 1]
                if ch_num <= total
                else {"title": f"第{ch_num}章", "summary": ""}
            )
            prev_text = ""
            for i in range(1, int(ch_num)):
                prev_text += st.session_state.chapters.get(str(i), "")

            chars = novel.get("characters", [])
            prompt = generate_chapter_content(
                novel.get("title", ""),
                ch_info.get("title", ""),
                ch_info.get("summary", ""),
                prev_text,
                chars,
                st.session_state.genre,
            )
            st.session_state.ai_prompt = prompt
            st.session_state.ai_pending = True
            st.session_state.ai_response = ""
            PROMPT_FILE.write_text(prompt, encoding="utf-8")
            STATUS_FILE.write_text(f"pending:{int(time.time())}", encoding="utf-8")
            if RESPONSE_FILE.exists():
                RESPONSE_FILE.unlink()
            st.rerun()

    with col_btn2:
        if st.button("➡️ 续写当前内容"):
            current = st.session_state.get(content_key, "")
            if current:
                prompt = continue_writing(current)
                st.session_state.ai_prompt = prompt
                st.session_state.ai_pending = True
                st.session_state.ai_response = ""
                PROMPT_FILE.write_text(prompt, encoding="utf-8")
                STATUS_FILE.write_text(f"pending:{int(time.time())}", encoding="utf-8")
                if RESPONSE_FILE.exists():
                    RESPONSE_FILE.unlink()
                st.rerun()

    with col_btn3:
        target_words = st.number_input("目标字数", min_value=500, value=2000, step=500)

    # 如果刚收到响应，更新章节内容
    if st.session_state.get("ai_response") and not st.session_state.get("ai_pending"):
        result = st.session_state.ai_response
        st.session_state[content_key] = result
        st.session_state.chapters[str(ch_num)] = result
        st.session_state.ai_response = ""
        st.rerun()

    st.subheader("✏️ 编辑区")
    edited = st.text_area(
        "章节正文",
        value=st.session_state.get(content_key, ""),
        height=500,
        label_visibility="collapsed",
    )
    st.session_state[content_key] = edited
    st.session_state.chapters[str(ch_num)] = edited

    word_count = len(edited)
    col_wc1, col_wc2 = st.columns([1, 4])
    with col_wc1:
        st.metric("当前字数", word_count)
    with col_wc2:
        progress = min(word_count / target_words, 1.0)
        st.progress(progress)
        st.caption(f"目标：{target_words} 字（完成 {progress*100:.0f}%）")

# ── 页面 4：文本润色 ──────────────────────────────────────
elif page == "✨ 文本润色":
    st.title("✨ 文本润色 / 改写")

    if st.session_state.get("ai_pending"):
        render_ai_panel()

    if not st.session_state.novel:
        st.info("📭 请先生成小说大纲！")
        st.stop()

    st.caption("粘贴需要润色的文本，选择润色风格")

    col1, col2 = st.columns(2)
    with col1:
        polish_mode = st.selectbox(
            "润色模式",
            ["流畅润色", "文笔提升", "对话优化", "情节紧凑化", "自定义指令"],
        )
    with col2:
        if polish_mode == "自定义指令":
            custom_instruction = st.text_input("自定义指令", placeholder="例：把这段改成更轻松幽默的风格")
        else:
            instruction_map = {
                "流畅润色": "请润色以下文本，使其语言更加流畅自然，修正语病和错别字",
                "文笔提升": "请提升以下文本的文学性，使用更优美的措辞和修辞手法",
                "对话优化": "请优化以下文本中的对话，使其更自然、符合角色性格",
                "情节紧凑化": "请删减冗余描写，使情节推进更加紧凑有力",
            }
            custom_instruction = instruction_map[polish_mode]
            st.caption(f"当前指令：{custom_instruction}")

    source_text = st.text_area("原文", height=300, placeholder="粘贴需要润色的文本…")

    if st.button("✨ 开始润色", type="primary"):
        if not source_text.strip():
            st.warning("请先粘贴原文！")
        else:
            prompt = polish_text(source_text, custom_instruction)
            st.session_state.ai_prompt = prompt
            st.session_state.ai_pending = True
            st.session_state.ai_response = ""
            PROMPT_FILE.write_text(prompt, encoding="utf-8")
            STATUS_FILE.write_text(f"pending:{int(time.time())}", encoding="utf-8")
            if RESPONSE_FILE.exists():
                RESPONSE_FILE.unlink()
            st.rerun()

    if st.session_state.get("ai_response") and not st.session_state.get("ai_pending"):
        result = st.session_state.ai_response
        st.subheader("✅ 润色结果")
        st.text_area("润色后", value=result, height=300, label_visibility="collapsed")
        st.session_state.ai_response = ""

# ── 页面 5：导出小说 ──────────────────────────────────────
elif page == "💾 导出小说":
    st.title("💾 导出小说")

    if not st.session_state.novel:
        st.info("📭 请先生成小说大纲！")
        st.stop()

    novel = st.session_state.novel
    chapters = st.session_state.chapters

    st.subheader(f"📕 {novel.get('title', '未命名小说')}")

    full_text = f"# {novel.get('title', '未命名小说')}\n\n"
    full_text += f"## 简介\n{novel.get('summary', '')}\n\n"

    full_text += "## 角色介绍\n"
    for c in novel.get("characters", []):
        full_text += f"**{c['name']}**（`{c.get('role', '角色')}`）：{c.get('description', '')}\n\n"

    full_text += "---\n\n"
    for ch_num in sorted(chapters.keys(), key=lambda x: int(x)):
        ch_content = chapters[ch_num]
        if ch_content.strip():
            ch_info = next((c for c in novel.get("chapters", []) if str(c["number"]) == str(ch_num)), None)
            title = ch_info["title"] if ch_info else f"第{ch_num}章"
            full_text += f"# 第{ch_num}章 {title}\n\n{ch_content}\n\n---\n\n"

    total_words = len(full_text)
    written_chapters = sum(1 for v in chapters.values() if v.strip())
    st.info(f"已写 {written_chapters} 章，共约 {total_words} 字")

    st.text_area("预览", value=full_text[:3000] + ("…" if len(full_text) > 3000 else ""), height=300)

    st.download_button(
        label="📥 下载为 TXT 文件",
        data=full_text,
        file_name=f"{novel.get('title', 'novel')}.txt",
        mime="text/plain",
    )

    if st.button("💾 保存到工作区"):
        output_path = f"novel_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        st.success(f"✅ 已保存到工作区：`{output_path}`")


# ── 底部：通信状态指示 ────────────────────────────────────
st.divider()
with st.container():
    col_a, col_b = st.columns([3, 1])
    with col_a:
        if STATUS_FILE.exists():
            status = STATUS_FILE.read_text(encoding="utf-8").strip()
            if status.startswith("pending"):
                st.caption("🟡 等待 WorkBuddy AI 响应中…")
            elif status.startswith("done"):
                st.caption("🟢 WorkBuddy AI 响应已就绪")
            else:
                st.caption("⚪ 就绪，等待新的生成请求")
        else:
            st.caption("⚪ 就绪，等待新的生成请求")
    with col_b:
        if st.button("🔄 刷新", help="手动刷新页面状态"):
            st.rerun()
