import gradio as gr
import pandas as pd
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
import os
import json

from api_client import api_client
from config import *

# --- 新增的配置项 ---
# !! 重要：请根据您Go后端项目的实际位置修改此路径
BACKEND_PROJECT_PATH = "D:/projects/GolandProjects/imgGeneratePrompts"


# --- 辅助函数 ---
def format_timestamp(ts):
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return ts


def safe_get(d, key, default=""):
    return d.get(key, default) if isinstance(d, dict) else default


def parse_structure_analysis(item):
    analysis = item.get('structure_analysis')
    if isinstance(analysis, str):
        try:
            item['structure_analysis'] = json.loads(analysis) if analysis else {}
        except:
            item['structure_analysis'] = {}
    elif not isinstance(analysis, dict):
        item['structure_analysis'] = {}
    return item


# --- 数据加载与API交互 ---
def check_api_connection():
    health = api_client.health_check()
    db_status = api_client.db_status_check()
    if 'error' in health: return f"❌ API连接失败: {health['error']}"
    if 'error' in db_status: return f"❌ 数据库连接失败: {db_status['error']}"
    return "✅ API和数据库连接正常"


def load_dashboard_data():
    stats = api_client.get_prompt_stats()
    tags = api_client.get_tag_stats()
    recent = api_client.get_recent_prompts(5)
    stats_data = safe_get(stats, 'data', {})
    tags_data = safe_get(tags, 'data', {})
    stats_info = f"""## 📊 系统统计\n**提示词:** {safe_get(stats_data, 'total_prompts', 0)} 总数 | {safe_get(stats_data, 'public_prompts', 0)} 公开\n**标签:** {safe_get(tags_data, 'total_tags', 0)} 总数"""
    recent_info = "## 🕒 最近提示词\n\n"
    if 'error' not in recent and isinstance(safe_get(recent, 'data'), list):
        for p in recent['data']:
            recent_info += f"- **{format_timestamp(p.get('created_at'))}**: {p.get('prompt_text', '')[:50]}...\n"
    return stats_info, recent_info, check_api_connection()


def create_prompt_with_images(input_images, output_image, prompt_text, *fields):
    """通用创建函数"""
    if not prompt_text.strip():
        return "❌ 提示词文本不能为空", None, None
    try:
        prompt_data = {
            'prompt_text': prompt_text, 'negative_prompt': fields[0], 'model_name': fields[1],
            'is_public': fields[2], 'style_description': fields[3], 'usage_scenario': fields[4],
            'atmosphere_description': fields[5], 'expressive_intent': fields[6],
            'structure_analysis': fields[7], 'tag_names': fields[8]
        }
        files_to_upload = {
            'input_images': input_images if input_images else [],
            'output_image': output_image
        }
        result = api_client.upload_and_create_prompt_multi(files_to_upload, prompt_data)
        if 'error' in result:
            return f"❌ 创建失败: {result['error']}", None, None
        df, info = load_prompts_data()
        return "✅ 创建成功!", df, info
    except Exception as e:
        return f"❌ 发生意外错误: {str(e)}", None, None


def smart_generate_prompt(input_images, output_image, prompt_text, model_name):
    if not prompt_text.strip() or not output_image:
        return "❌ 请提供输出图片和基础提示词", "", "", "", "", "", "", ""
    try:
        files_paths = {
            'input_images': input_images if input_images else [],
            'output_image': output_image
        }
        result = api_client.analyze_prompt(files_paths, {'prompt_text': prompt_text, 'model_name': model_name or ''})
        if 'error' in result:
            return f"❌ 分析失败: {result['error']}", "", "", "", "", "", "", ""
        data = result.get('data', {})
        analysis = data.get('structure_analysis', {})
        analysis_str = json.dumps(analysis, ensure_ascii=False, indent=2) if analysis else ""
        return ("✅ 智能生成完成!", data.get('negative_prompt', ''), data.get('style_description', ''),
                data.get('usage_scenario', ''), data.get('atmosphere_description', ''),
                data.get('expressive_intent', ''),
                analysis_str, ', '.join(data.get('tag_names', [])))
    except Exception as e:
        return f"❌ 分析失败: {str(e)}", "", "", "", "", "", "", ""


def load_prompts_data(page: int = 1, keyword: str = "", model_name: str = "", is_public: Optional[bool] = None,
                      tag_names: str = ""):
    try:
        filters = {'keyword': keyword, 'model_name': model_name, 'is_public': is_public, 'tag_names': tag_names}
        result = api_client.get_prompts(page=page, page_size=DEFAULT_PAGE_SIZE, **filters)
        if 'error' in result: return pd.DataFrame(), f"❌ 加载失败: {result['error']}"
        pagination_data = result.get('data', {})
        items = pagination_data.get('items', [])
        if not items: return pd.DataFrame(), "当前页无数据"
        rows = []
        for item in items:
            item = parse_structure_analysis(item)
            tags = ', '.join([tag['name'] for tag in item.get('tags', [])])
            rows.append({
                'ID': item.get('id'), '创建时间': format_timestamp(item.get('created_at', '')),
                '提示词': item.get('prompt_text', '')[:100] + '...', '模型': item.get('model_name', ''),
                '公开': '是' if item.get('is_public') else '否', '输出图': '✓' if item.get('output_image_url') else '✗',
                '参考图': f"{len(item.get('input_image_urls', []))}张", '标签': tags
            })
        df = pd.DataFrame(rows)
        page_info = f"第 {pagination_data.get('page', 1)} 页 / 共 {pagination_data.get('total_pages', 1)} 页 (总计 {pagination_data.get('total', 0)} 条)"
        return df, page_info
    except Exception as e:
        return pd.DataFrame(), f"❌ 加载失败: {str(e)}"


def get_prompt_detail(prompt_id: int):
    """获取提示词详情，并修复图片路径以便Gradio显示"""
    print(f"\n--- DEBUG: 调用 get_prompt_detail, ID: {prompt_id} ---")

    if not prompt_id:
        print("--- DEBUG: prompt_id 为空, 返回默认值。")
        return "请先输入ID", "", "", "", "", [], False, "", "", "", "", "", ""

    try:
        result = api_client.get_prompt(prompt_id)
        if 'error' in result:
            print(f"--- DEBUG: API返回错误: {result['error']}")
            return f"❌ 获取失败: {result['error']}", "", "", "", "", [], False, "", "", "", "", "", ""

        data = parse_structure_analysis(result.get('data', {}))
        tags = ', '.join([t['name'] for t in data.get('tags', [])])
        analysis_str = json.dumps(data.get('structure_analysis', {}), ensure_ascii=False, indent=2)

        # --- 核心修复：使用正确的后端项目路径 ---
        base_path = BACKEND_PROJECT_PATH
        print(f"--- DEBUG: 使用的基础路径 (base_path): '{base_path}'")

        def build_path(relative_url):
            if not relative_url:
                return ""
            # relative_url 是 '/uploads/image.jpg'
            # lstrip后是 'uploads/image.jpg'
            # os.path.join(base_path, ...) 会正确拼接
            # os.path.normpath 会转换为 D:\...\uploads\image.jpg
            abs_path = os.path.normpath(os.path.join(base_path, relative_url.lstrip('/\\')))
            print(f"--- DEBUG: 相对URL '{relative_url}' -> 绝对路径 '{abs_path}'")
            return abs_path

        output_image_absolute_path = build_path(data.get('output_image_url', ''))
        input_image_absolute_paths = [build_path(url) for url in data.get('input_image_urls', []) if url]

        final_return_values = (
            f"✅ 已加载ID: {prompt_id}",
            data.get('prompt_text', ''), data.get('negative_prompt', ''), data.get('model_name', ''),
            output_image_absolute_path, input_image_absolute_paths,
            data.get('is_public', False), data.get('style_description', ''), data.get('usage_scenario', ''),
            data.get('atmosphere_description', ''), data.get('expressive_intent', ''), analysis_str, tags
        )
        print(f"--- DEBUG: 准备返回给Gradio的数据: {final_return_values}")
        return final_return_values

    except Exception as e:
        import traceback
        print("\n--- FATAL ERROR in get_prompt_detail ---");
        traceback.print_exc();
        print("--- END ERROR ---")
        return f"❌ 前端处理失败: {e}", "", "", "", "", [], False, "", "", "", "", "", ""


def update_prompt_detail(prompt_id, *fields):
    if not prompt_id: return "❌ 请先选择要更新的提示词", None, None
    try:
        update_data = {'prompt_text': fields[0], 'negative_prompt': fields[1], 'model_name': fields[2],
                       'is_public': fields[3], 'style_description': fields[4], 'usage_scenario': fields[5],
                       'atmosphere_description': fields[6], 'expressive_intent': fields[7],
                       'structure_analysis': fields[8], 'tag_names': [t.strip() for t in fields[9].split(',')]}
        result = api_client.update_prompt(prompt_id, update_data)
        if 'error' in result: return f"❌ 更新失败: {result['error']}", None, None
        df, info = load_prompts_data()
        return "✅ 更新成功", df, info
    except Exception as e:
        return f"❌ 更新失败: {str(e)}", None, None


def delete_prompt_by_id(prompt_id: int):
    if not prompt_id: return "❌ 请输入要删除的ID", None, None
    result = api_client.delete_prompt(prompt_id)
    if 'error' in result: return f"❌ 删除失败: {result['error']}", None, None
    df, info = load_prompts_data()
    return "✅ 删除成功", df, info


def load_tags_data():
    result = api_client.get_all_tags()
    if 'error' in result: return pd.DataFrame(), f"❌ 加载失败: {result['error']}"
    data = result.get('data', [])
    rows = [{'ID': r.get('id'), '标签名称': r.get('name'), '创建时间': format_timestamp(r.get('created_at'))} for r in
            data]
    return pd.DataFrame(rows), f"共 {len(rows)} 个标签"


def create_new_tag(name):
    if not name.strip(): return "❌ 名称不能为空", None, None
    result = api_client.create_tag({'name': name.strip()})
    if 'error' in result: return f"❌ 创建失败: {result['error']}", None, None
    df, info = load_tags_data()
    return "✅ 创建成功", df, info


def delete_tag_by_id(tag_id):
    if not tag_id: return "❌ ID不能为空", None, None
    result = api_client.delete_tag(tag_id)
    if 'error' in result: return f"❌ 删除失败: {result['error']}", None, None
    df, info = load_tags_data()
    return "✅ 删除成功", df, info


# --- Gradio UI 界面 ---
def create_app():
    with gr.Blocks(title="图像生成提示词管理系统 V4.2", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🎨 图像生成提示词管理系统 V4.2")
        with gr.Tabs():
            with gr.Tab("📊 仪表板"):
                with gr.Row():
                    stats_display = gr.Markdown("加载中...")
                    recent_display = gr.Markdown("加载中...")
                connection_status = gr.Markdown("加载中...")
                refresh_dashboard_btn = gr.Button("🔄 刷新仪表板")

            with gr.Tab("📝 提示词管理"):
                with gr.Tabs():
                    with gr.Tab("🤖 智能生成"):
                        with gr.Row():
                            with gr.Column(scale=1):
                                sm_output_img = gr.File(label="输出结果图 (必须)", file_types=["image"],
                                                        type="filepath")
                                sm_input_imgs = gr.File(label="输入参考图 (可选)", file_count="multiple",
                                                        file_types=["image"], type="filepath")
                            with gr.Column(scale=2):
                                sm_prompt = gr.Textbox(label="基础提示词 *", lines=3)
                                sm_model = gr.Textbox(label="模型名称 (可选)")
                                sm_gen_btn = gr.Button("🤖 智能生成", variant="primary")
                                sm_status = gr.Markdown()
                        gr.Markdown("---")
                        gr.Markdown("### 生成结果 (请审核并保存)")
                        sm_neg_prompt = gr.Textbox(label="负面提示词", lines=2)
                        sm_style = gr.Textbox(label="风格描述")
                        sm_usage = gr.Textbox(label="使用场景")
                        sm_atmosphere = gr.Textbox(label="氛围描述")
                        sm_intent = gr.Textbox(label="表现意图")
                        sm_analysis = gr.Textbox(label="结构分析 (JSON)", lines=2)
                        sm_tags = gr.Textbox(label="标签 (逗号分隔)")
                        sm_public = gr.Checkbox(label="设为公开", value=True)
                        sm_save_btn = gr.Button("💾 保存提示词", variant="primary")
                        sm_save_status = gr.Markdown()

                    with gr.Tab("➕ 手动创建"):
                        with gr.Row():
                            with gr.Column(scale=2):
                                man_prompt = gr.Textbox(label="提示词文本 *", lines=3)
                                man_neg_prompt = gr.Textbox(label="负面提示词", lines=2)
                                man_model = gr.Textbox(label="模型名称")
                                man_public = gr.Checkbox(label="设为公开", value=True)
                                man_style = gr.Textbox(label="风格描述")
                                man_usage = gr.Textbox(label="使用场景")
                                man_atmosphere = gr.Textbox(label="氛围描述")
                                man_intent = gr.Textbox(label="表现意图")
                                man_analysis = gr.Textbox(label="结构分析 (JSON)", placeholder='例如: {"主体": "猫"}')
                                man_tags = gr.Textbox(label="标签 (逗号分隔)")
                            with gr.Column(scale=1):
                                man_output_img = gr.File(label="上传输出图片 (可选)", file_types=["image"],
                                                         type="filepath")
                                man_input_imgs = gr.File(label="上传参考图片 (可选)", file_count="multiple",
                                                         file_types=["image"], type="filepath")
                                man_save_btn = gr.Button("💾 保存提示词", variant="primary")
                                man_save_status = gr.Markdown()

                    with gr.Tab("📋 查看与编辑"):
                        with gr.Row():
                            keyword_filter = gr.Textbox(label="关键词")
                            model_filter = gr.Textbox(label="模型")
                            public_filter = gr.Dropdown(label="公开",
                                                        choices=[("全部", None), ("是", True), ("否", False)],
                                                        value=None)
                            tag_filter = gr.Textbox(label="标签")
                        search_btn = gr.Button("🔍 搜索")
                        prompts_table = gr.Dataframe(
                            headers=["ID", "创建时间", "提示词", "模型", "公开", "输出图", "参考图", "标签"],
                            interactive=False, wrap=True)
                        prompts_info = gr.Markdown()
                        gr.Markdown("---")
                        with gr.Row():
                            prompt_id_input = gr.Number(label="输入ID进行编辑", precision=0)
                            load_btn = gr.Button("📥 加载")
                        edit_status = gr.Markdown()
                        edit_fields = [
                            gr.Textbox(label="提示词", lines=3), gr.Textbox(label="负面提示词", lines=2),
                            gr.Textbox(label="模型"), gr.Checkbox(label="公开"),
                            gr.Textbox(label="风格"), gr.Textbox(label="场景"),
                            gr.Textbox(label="氛围"), gr.Textbox(label="意图"),
                            gr.Textbox(label="结构分析 (JSON)", lines=3), gr.Textbox(label="标签 (逗号分隔)")
                        ]
                        edit_output_url = gr.Textbox(label="输出图URL", interactive=False)
                        edit_input_gallery = gr.Gallery(label="输入参考图", columns=4, height="auto",
                                                        object_fit="contain")
                        with gr.Row():
                            update_btn = gr.Button("💾 更新", variant="primary")
                            delete_btn = gr.Button("🗑️ 删除", variant="stop")
                        update_delete_status = gr.Markdown()

            with gr.Tab("🏷️ 标签管理"):
                with gr.Tabs():
                    with gr.Tab("📋 查看"):
                        refresh_tags_btn = gr.Button("🔄 刷新")
                        tags_table = gr.Dataframe(headers=["ID", "标签名称", "创建时间"], interactive=False)
                        tags_info = gr.Markdown()
                    with gr.Tab("➕➖ 创建与删除"):
                        with gr.Row():
                            with gr.Column():
                                new_tag_name = gr.Textbox(label="新标签名称")
                                create_tag_btn = gr.Button("创建", variant="primary")
                                create_tag_status = gr.Markdown()
                            with gr.Column():
                                delete_tag_id = gr.Number(label="要删除的标签ID", precision=0)
                                delete_tag_btn = gr.Button("删除", variant="stop")
                                delete_tag_status = gr.Markdown()

        # --- 事件绑定 ---
        all_man_fields = [man_neg_prompt, man_model, man_public, man_style, man_usage, man_atmosphere, man_intent,
                          man_analysis, man_tags]
        all_sm_fields = [sm_neg_prompt, sm_public, sm_style, sm_usage, sm_atmosphere, sm_intent, sm_analysis, sm_tags]
        all_edit_fields = [prompt_id_input] + edit_fields

        refresh_dashboard_btn.click(load_dashboard_data, outputs=[stats_display, recent_display, connection_status])

        # 智能生成流程
        sm_gen_btn.click(
            smart_generate_prompt,
            [sm_input_imgs, sm_output_img, sm_prompt, sm_model],
            [sm_status, sm_neg_prompt, sm_style, sm_usage, sm_atmosphere, sm_intent, sm_analysis, sm_tags]
        )
        sm_save_btn.click(
            lambda i, o, p, m, *f: create_prompt_with_images(i, o, p, *(f[:1] + [m] + f[1:])),
            [sm_input_imgs, sm_output_img, sm_prompt, sm_model] + all_sm_fields,
            [sm_save_status, prompts_table, prompts_info]
        )

        # 手动创建流程
        man_save_btn.click(
            lambda i, o, p, *f: create_prompt_with_images(i, o, p, *f),
            [man_input_imgs, man_output_img, man_prompt] + all_man_fields,
            [man_save_status, prompts_table, prompts_info]
        )

        # 查看与编辑流程
        search_btn.click(
            lambda k, m, p, t: load_prompts_data(1, k, m, p, t),
            [keyword_filter, model_filter, public_filter, tag_filter],
            [prompts_table, prompts_info]
        )
        load_btn.click(
            get_prompt_detail,
            [prompt_id_input],
            [edit_status, edit_fields[0], edit_fields[1], edit_fields[2],
             edit_output_url, edit_input_gallery, edit_fields[3], edit_fields[4],
             edit_fields[5], edit_fields[6], edit_fields[7], edit_fields[8],
             edit_fields[9]]
        )
        update_btn.click(update_prompt_detail, all_edit_fields, [update_delete_status, prompts_table, prompts_info])
        delete_btn.click(delete_prompt_by_id, [prompt_id_input], [update_delete_status, prompts_table, prompts_info])

        # 标签管理流程
        refresh_tags_btn.click(load_tags_data, outputs=[tags_table, tags_info])
        create_tag_btn.click(create_new_tag, [new_tag_name], [create_tag_status, tags_table, tags_info])
        delete_tag_btn.click(delete_tag_by_id, [delete_tag_id], [delete_tag_status, tags_table, tags_info])

        app.load(load_dashboard_data, outputs=[stats_display, recent_display, connection_status])
        app.load(load_prompts_data, outputs=[prompts_table, prompts_info])
        app.load(load_tags_data, outputs=[tags_table, tags_info])
    return app


if __name__ == "__main__":
    app = create_app()
    # --- 核心修复：使用新的配置变量 ---
    allowed_path = os.path.normpath(os.path.join(BACKEND_PROJECT_PATH, "uploads"))
    print(f"INFO: Allowing Gradio to access path: {allowed_path}")

    app.launch(
        server_name=GRADIO_SERVER_NAME,
        server_port=GRADIO_SERVER_PORT,
        share=GRADIO_SHARE,
        inbrowser=True,
        allowed_paths=[allowed_path]
    )

