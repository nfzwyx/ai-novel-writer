"""AI 小说创作助手 - Streamlit Web UI"""

import streamlit as st
import os
import json
import re
from datetime import datetime
from novel_generator import (
    generate_novel_outline,
    generate_chapter_content,
    polish_text,
    continue_writing,
)

# ── 页面配置 ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI 小说创作助手",
    page_icon="✍️",
    layout="wide",
)

# ── 初始化 session_state ──────────────────────────────────
if "novel" not in st.session_state:
    st.session_state.novel = None  # 小说大纲数据
if "chapters" not in st.session_state:
    st.session_state.chapters = {}  # {chapter_number: content}
if "current_chapter" not in st.session_state:
    st.session_state.current_chapter = 1
if "genre" not in st.session_state:
    st.session_state.genre = "玄幻"
if "api_configured" not in st.session_state:
    st.session_state.api_configured = False

# ── 侧边栏：API 配置 ─────────────────────────────────────
with st.sidebar:
    st.title("✍️ AI 小说创作助手")
    st.divider()

    st.subheader("⚙️ API 配置")
    api_key = st.text_input(
        "API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="支持 OpenAI / DeepSeek / 其他兼容 API",
    )
    api_base = st.text_input(
        "API Base URL（可选）",
        value=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        help="DeepSeek 填 https://api.deepseek.com/v1",
    )
    model_name = st.text_input(
        "模型名称",
        value=os.getenv("MODEL_NAME", "gpt-4o"),
        help="DeepSeek 填 deepseek-chat",
    )

    if api_key:
        st.session_state.api_configured = True
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_BASE_URL"] = api_base
        os.environ["MODEL_NAME"] = model_name
        st.success("✅ API 已配置")
    else:
        st.warning("⚠️ 请先配置 API Key")
        st.caption("获取 Key 后填入上方输入框")

    st.divider()

    # 导航
    st.subheader("📂 导航")
    page = st.radio(
        "选择功能",
        ["🏠 新建小说", "📋 大纲管理", "📝 章节写作", "✨ 文本润色", "💾 导出小说"],
    )

# ── 调用 AI 的通用函数 ────────────────────────────────────
def call_ai(prompt: str, max_tokens: int = 4096) -> str:
    """调用配置好的 AI 模型"""
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
        resp = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "gpt-4o"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.8,
        )
        return resp.choices[0].message.content
    except Exception as e:
        st.error(f"AI 调用失败：{e}")
        return ""


# ── 页面 1：新建小说 ──────────────────────────────────────
if page == "🏠 新建小说":
    st.title("🏠 新建小说项目")

    col1, col2 = st.columns([2, 1])

    with col1:
        genre = st.selectbox(
            "选择题材",
            ["玄幻", "都市", "科幻", "历史", "武侠", "言情", "悬疑", "恐怖", "其他"],
        )
        if genre == "其他":
            genre = st.text_input("请输入题材名称")

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
        elif not st.session_state.api_configured:
            st.warning("请先在侧边栏配置 API Key！")
        else:
            with st.spinner("AI 正在构思大纲，请稍候…"):
                outline_data = generate_novel_outline(theme, genre, num_chapters)
                prompt = outline_data["prompt"]

                result = call_ai(prompt, max_tokens=4096)

                # 尝试解析 JSON
                try:
                    # 提取 JSON（可能有 markdown 代码块包裹）
                    json_match = re.search(r"```json\s*(.*?)\s*```", result, re.DOTALL)
                    if json_match:
                        result = json_match.group(1)
                    novel_data = json.loads(result)
                    st.session_state.novel = novel_data
                    st.session_state.chapters = {}
                    st.session_state.genre = genre
                    st.success("✅ 大纲生成成功！请切换到「大纲管理」查看")
                    st.rerun()
                except json.JSONDecodeError:
                    st.error("大纲解析失败，请重试。原始输出：")
                    st.text(result[:500])

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

    if not st.session_state.novel:
        st.info("📭 请先生成小说大纲！")
        st.stop()

    novel = st.session_state.novel
    chapters_outline = novel.get("chapters", [])
    total = len(chapters_outline)

    # 章节选择器
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

    # 获取/生成章节内容
    content_key = f"content_{ch_num}"
    if content_key not in st.session_state:
        st.session_state[content_key] = st.session_state.chapters.get(str(ch_num), "")

    # 生成按钮
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("✨ 生成本章内容", type="primary"):
            if not st.session_state.api_configured:
                st.warning("请先配置 API Key！")
            else:
                with st.spinner("AI 正在写作，请稍候…"):
                    ch_info = chapters_outline[int(ch_num) - 1] if ch_num <= total else {"title": f"第{ch_num}章", "summary": ""}
                    prev_text = ""
                    for i in range(1, ch_num):
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
                    result = call_ai(prompt, max_tokens=4096)
                    if result:
                        st.session_state[content_key] = result
                        st.session_state.chapters[str(ch_num)] = result
                        st.rerun()

    with col_btn2:
        if st.button("➡️ 续写当前内容"):
            if not st.session_state.api_configured:
                st.warning("请先配置 API Key！")
            else:
                current = st.session_state.get(content_key, "")
                if current:
                    with st.spinner("AI 正在续写…"):
                        prompt = continue_writing(current)
                        result = call_ai(prompt, max_tokens=2048)
                        if result:
                            new_content = current + "\n\n" + result
                            st.session_state[content_key] = new_content
                            st.session_state.chapters[str(ch_num)] = new_content
                            st.rerun()

    with col_btn3:
        target_words = st.number_input("目标字数", min_value=500, value=2000, step=500)

    # 编辑区
    st.subheader("✏️ 编辑区")
    edited = st.text_area(
        "章节正文",
        value=st.session_state.get(content_key, ""),
        height=500,
        label_visibility="collapsed",
    )
    st.session_state[content_key] = edited
    st.session_state.chapters[str(ch_num)] = edited

    # 字数统计
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
        elif not st.session_state.api_configured:
            st.warning("请先配置 API Key！")
        else:
            with st.spinner("AI 正在润色…"):
                prompt = polish_text(source_text, custom_instruction)
                result = call_ai(prompt, max_tokens=4096)
                if result:
                    st.subheader("✅ 润色结果")
                    st.text_area("润色后", value=result, height=300, label_visibility="collapsed")

# ── 页面 5：导出小说 ──────────────────────────────────────
elif page == "💾 导出小说":
    st.title("💾 导出小说")

    if not st.session_state.novel:
        st.info("📭 请先生成小说大纲！")
        st.stop()

    novel = st.session_state.novel
    chapters = st.session_state.chapters

    st.subheader(f"📕 {novel.get('title', '未命名小说')}")

    # 汇总预览
    full_text = f"# {novel.get('title', '未命名小说')}\n\n"
    full_text += f"## 简介\n{novel.get('summary', '')}\n\n"

    full_text += "## 角色介绍\n"
    for c in novel.get("characters", []):
        full_text += f"**{c['name']}**（{c.get('role', '角色')}）：{c.get('description', '')}\n\n"

    full_text += "---\n\n"
    for ch_num in sorted(chapters.keys(), key=lambda x: int(x)):
        ch_content = chapters[ch_num]
        if ch_content.strip():
            ch_info = next((c for c in novel.get("chapters", []) if str(c["number"]) == str(ch_num)), None)
            title = ch_info["title"] if ch_info else f"第{ch_num}章"
            full_text += f"# 第{ch_num}章 {title}\n\n{ch_content}\n\n---\n\n"

    # 统计
    total_words = len(full_text)
    written_chapters = sum(1 for v in chapters.values() if v.strip())
    st.info(f"已写 {written_chapters} 章，共约 {total_words} 字")

    st.text_area("预览", value=full_text[:3000] + ("…" if len(full_text) > 3000 else ""), height=300)

    # 下载按钮
    st.download_button(
        label="📥 下载为 TXT 文件",
        data=full_text,
        file_name=f"{novel.get('title', 'novel')}.txt",
        mime="text/plain",
    )

    # 保存为本地文件
    if st.button("💾 保存到工作区"):
        output_path = f"novel_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        st.success(f"✅ 已保存到工作区：`{output_path}`")
