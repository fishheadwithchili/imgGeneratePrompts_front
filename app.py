import gradio as gr
import pandas as pd
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
import os
import json
from PIL import Image
import io

from api_client import api_client
from config import *


def format_timestamp(timestamp_str: str) -> str:
    """格式化时间戳"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp_str


def safe_get(data: Dict, key: str, default: Any = "") -> Any:
    """安全获取字典值"""
    return data.get(key, default) if data else default


def check_api_connection():
    """检查API连接状态"""
    health = api_client.health_check()
    db_status = api_client.db_status_check()
    
    if 'error' in health:
        return f"❌ API连接失败: {health['error']}", "error"
    elif 'error' in db_status:
        return f"❌ 数据库连接失败: {db_status['error']}", "error"
    else:
        return "✅ API和数据库连接正常", "success"


# ============ 仪表板功能 ============
def load_dashboard_data():
    """加载仪表板数据"""
    try:
        # 获取统计信息
        prompt_stats = api_client.get_prompt_stats()
        tag_stats = api_client.get_tag_stats()
        recent_prompts = api_client.get_recent_prompts(5)
        
        if 'error' in prompt_stats:
            return f"获取统计信息失败: {prompt_stats['error']}", "", ""
        
        # 格式化统计信息
        stats_info = f"""
        ## 📊 系统统计
        
        **提示词统计:**
        - 总数: {safe_get(prompt_stats.get('data', {}), 'total_prompts', 0)}
        - 公开: {safe_get(prompt_stats.get('data', {}), 'public_prompts', 0)}
        - 私有: {safe_get(prompt_stats.get('data', {}), 'private_prompts', 0)}
        
        **标签统计:**
        - 总数: {safe_get(tag_stats.get('data', {}), 'total_tags', 0)}
        """
        
        # 格式化最近提示词
        recent_info = "## 🕒 最近提示词\n\n"
        if 'error' not in recent_prompts and recent_prompts.get('data'):
            for prompt in recent_prompts['data'][:5]:
                created_at = format_timestamp(prompt.get('created_at', ''))
                prompt_text = prompt.get('prompt_text', '')[:50] + '...' if len(prompt.get('prompt_text', '')) > 50 else prompt.get('prompt_text', '')
                recent_info += f"- **{created_at}**: {prompt_text}\n"
        else:
            recent_info += "暂无数据"
        
        connection_status, status_type = check_api_connection()
        
        return stats_info, recent_info, connection_status
        
    except Exception as e:
        return f"加载仪表板数据失败: {str(e)}", "", f"❌ 连接错误: {str(e)}"


# ============ 提示词管理功能 ============
def create_prompt_with_image(
    image_file, prompt_text: str, negative_prompt: str, model_name: str,
    is_public: bool, style_desc: str, usage_scenario: str, 
    atmosphere_desc: str, expressive_intent: str, structure_analysis: str, 
    tag_names: str
):
    """创建带图片的提示词"""
    if not prompt_text.strip():
        return "❌ 请输入提示词文本", None
    
    try:
        # 准备数据
        prompt_data = {
            'prompt_text': prompt_text,
            'negative_prompt': negative_prompt,
            'model_name': model_name,
            'is_public': is_public,
            'style_description': style_desc,
            'usage_scenario': usage_scenario,
            'atmosphere_description': atmosphere_desc,
            'expressive_intent': expressive_intent,
            'structure_analysis': structure_analysis,
            'tag_names': tag_names
        }
        
        if image_file is not None:
            # 上传图片并创建提示词
            with open(image_file, 'rb') as f:
                result = api_client.upload_and_create_prompt(f, prompt_data)
        else:
            # 仅创建提示词
            result = api_client.create_prompt(prompt_data)
        
        if 'error' in result:
            return f"❌ 创建失败: {result['error']}", None
        else:
            return "✅ 创建成功", load_prompts_data()
    
    except Exception as e:
        return f"❌ 创建失败: {str(e)}", None


def load_prompts_data(page: int = 1, keyword: str = "", model_name: str = "", is_public: Optional[bool] = None, tag_names: str = ""):
    """加载提示词数据"""
    try:
        filters = {}
        if keyword:
            filters['keyword'] = keyword
        if model_name:
            filters['model_name'] = model_name
        if is_public is not None:
            filters['is_public'] = is_public
        if tag_names:
            filters['tag_names'] = tag_names
        
        result = api_client.get_prompts(page=page, page_size=DEFAULT_PAGE_SIZE, **filters)
        
        if 'error' in result:
            return pd.DataFrame(), f"❌ 加载失败: {result['error']}"
        
        data = result.get('data', [])
        if not data:
            return pd.DataFrame(), "暂无数据"
        
        # 转换为DataFrame
        rows = []
        for item in data:
            tags = ', '.join([tag['name'] for tag in item.get('tags', [])])
            rows.append({
                'ID': item.get('id'),
                '创建时间': format_timestamp(item.get('created_at', '')),
                '提示词': item.get('prompt_text', '')[:100] + '...' if len(item.get('prompt_text', '')) > 100 else item.get('prompt_text', ''),
                '模型': item.get('model_name', ''),
                '公开': '是' if item.get('is_public') else '否',
                '标签': tags,
                '风格': item.get('style_description', '')[:30] + '...' if len(item.get('style_description', '')) > 30 else item.get('style_description', '')
            })
        
        df = pd.DataFrame(rows)
        
        # 分页信息
        pagination = result.get('pagination', {})
        page_info = f"第 {pagination.get('page', 1)} 页，共 {pagination.get('total_pages', 1)} 页，总计 {pagination.get('total', 0)} 条记录"
        
        return df, page_info
    
    except Exception as e:
        return pd.DataFrame(), f"❌ 加载失败: {str(e)}"


def get_prompt_detail(prompt_id: int):
    """获取提示词详情"""
    if not prompt_id:
        return "", "", "", "", False, "", "", "", "", "", ""
    
    try:
        result = api_client.get_prompt(prompt_id)
        if 'error' in result:
            return f"❌ 获取失败: {result['error']}", "", "", "", False, "", "", "", "", "", ""
        
        data = result.get('data', {})
        tags = ', '.join([tag['name'] for tag in data.get('tags', [])])
        
        return (
            data.get('prompt_text', ''),
            data.get('negative_prompt', ''),
            data.get('model_name', ''),
            data.get('image_url', ''),
            data.get('is_public', False),
            data.get('style_description', ''),
            data.get('usage_scenario', ''),
            data.get('atmosphere_description', ''),
            data.get('expressive_intent', ''),
            data.get('structure_analysis', ''),
            tags
        )
    
    except Exception as e:
        return f"❌ 获取失败: {str(e)}", "", "", "", False, "", "", "", "", "", ""


def update_prompt_detail(
    prompt_id: int, prompt_text: str, negative_prompt: str, model_name: str,
    is_public: bool, style_desc: str, usage_scenario: str, 
    atmosphere_desc: str, expressive_intent: str, structure_analysis: str, 
    tag_names: str
):
    """更新提示词"""
    if not prompt_id:
        return "❌ 请先选择要更新的提示词", None
    
    try:
        update_data = {
            'prompt_text': prompt_text,
            'negative_prompt': negative_prompt,
            'model_name': model_name,
            'is_public': is_public,
            'style_description': style_desc,
            'usage_scenario': usage_scenario,
            'atmosphere_description': atmosphere_desc,
            'expressive_intent': expressive_intent,
            'structure_analysis': structure_analysis,
            'tag_names': tag_names.split(',') if tag_names else []
        }
        
        result = api_client.update_prompt(prompt_id, update_data)
        
        if 'error' in result:
            return f"❌ 更新失败: {result['error']}", None
        else:
            return "✅ 更新成功", load_prompts_data()
    
    except Exception as e:
        return f"❌ 更新失败: {str(e)}", None


def delete_prompt_by_id(prompt_id: int):
    """删除提示词"""
    if not prompt_id:
        return "❌ 请输入要删除的提示词ID", None
    
    try:
        result = api_client.delete_prompt(prompt_id)
        
        if 'error' in result:
            return f"❌ 删除失败: {result['error']}", None
        else:
            return "✅ 删除成功", load_prompts_data()
    
    except Exception as e:
        return f"❌ 删除失败: {str(e)}", None


def check_prompt_duplicate(prompt_text: str):
    """检查提示词重复"""
    if not prompt_text.strip():
        return "请输入要检查的提示词文本"
    
    try:
        result = api_client.check_duplicate(prompt_text)
        
        if 'error' in result:
            return f"❌ 检查失败: {result['error']}"
        
        data = result.get('data', {})
        is_duplicate = data.get('is_duplicate', False)
        count = data.get('count', 0)
        
        if is_duplicate:
            return f"⚠️ 发现 {count} 条重复提示词"
        else:
            return "✅ 未发现重复提示词"
    
    except Exception as e:
        return f"❌ 检查失败: {str(e)}"


# ============ 标签管理功能 ============
def load_tags_data():
    """加载标签数据"""
    try:
        result = api_client.get_all_tags()
        
        if 'error' in result:
            return pd.DataFrame(), f"❌ 加载失败: {result['error']}"
        
        data = result.get('data', [])
        if not data:
            return pd.DataFrame(), "暂无标签数据"
        
        # 转换为DataFrame
        rows = []
        for item in data:
            rows.append({
                'ID': item.get('id'),
                '标签名称': item.get('name', ''),
                '创建时间': format_timestamp(item.get('created_at', ''))
            })
        
        df = pd.DataFrame(rows)
        return df, f"共 {len(rows)} 个标签"
    
    except Exception as e:
        return pd.DataFrame(), f"❌ 加载失败: {str(e)}"


def create_new_tag(tag_name: str):
    """创建新标签"""
    if not tag_name.strip():
        return "❌ 请输入标签名称", None
    
    try:
        result = api_client.create_tag({'name': tag_name.strip()})
        
        if 'error' in result:
            return f"❌ 创建失败: {result['error']}", None
        else:
            return "✅ 标签创建成功", load_tags_data()
    
    except Exception as e:
        return f"❌ 创建失败: {str(e)}", None


def delete_tag_by_id(tag_id: int):
    """删除标签"""
    if not tag_id:
        return "❌ 请输入要删除的标签ID", None
    
    try:
        result = api_client.delete_tag(tag_id)
        
        if 'error' in result:
            return f"❌ 删除失败: {result['error']}", None
        else:
            return "✅ 标签删除成功", load_tags_data()
    
    except Exception as e:
        return f"❌ 删除失败: {str(e)}", None


def search_tags_by_keyword(keyword: str):
    """搜索标签"""
    try:
        result = api_client.search_tags(keyword)
        
        if 'error' in result:
            return pd.DataFrame(), f"❌ 搜索失败: {result['error']}"
        
        data = result.get('data', [])
        if not data:
            return pd.DataFrame(), "未找到匹配的标签"
        
        # 转换为DataFrame
        rows = []
        for item in data:
            rows.append({
                'ID': item.get('id'),
                '标签名称': item.get('name', ''),
                '创建时间': format_timestamp(item.get('created_at', ''))
            })
        
        df = pd.DataFrame(rows)
        return df, f"找到 {len(rows)} 个匹配标签"
    
    except Exception as e:
        return pd.DataFrame(), f"❌ 搜索失败: {str(e)}"


# ============ 搜索功能 ============
def search_prompts_by_tags_func(tag_names: str, page: int = 1):
    """根据标签搜索提示词"""
    if not tag_names.strip():
        return pd.DataFrame(), "❌ 请输入要搜索的标签名称"
    
    try:
        tags_list = [tag.strip() for tag in tag_names.split(',') if tag.strip()]
        result = api_client.search_prompts_by_tags(tags_list, page=page, page_size=DEFAULT_PAGE_SIZE)
        
        if 'error' in result:
            return pd.DataFrame(), f"❌ 搜索失败: {result['error']}"
        
        data = result.get('data', [])
        if not data:
            return pd.DataFrame(), "未找到匹配的提示词"
        
        # 转换为DataFrame
        rows = []
        for item in data:
            tags = ', '.join([tag['name'] for tag in item.get('tags', [])])
            rows.append({
                'ID': item.get('id'),
                '创建时间': format_timestamp(item.get('created_at', '')),
                '提示词': item.get('prompt_text', '')[:100] + '...' if len(item.get('prompt_text', '')) > 100 else item.get('prompt_text', ''),
                '模型': item.get('model_name', ''),
                '公开': '是' if item.get('is_public') else '否',
                '标签': tags
            })
        
        df = pd.DataFrame(rows)
        
        # 分页信息
        pagination = result.get('pagination', {})
        page_info = f"第 {pagination.get('page', 1)} 页，共 {pagination.get('total_pages', 1)} 页，总计 {pagination.get('total', 0)} 条记录"
        
        return df, page_info
    
    except Exception as e:
        return pd.DataFrame(), f"❌ 搜索失败: {str(e)}"


# ============ 创建Gradio界面 ============
def create_app():
    """创建Gradio应用"""
    
    # 自定义CSS样式
    custom_css = """
    .gradio-container {
        font-family: 'Microsoft YaHei', Arial, sans-serif;
    }
    .tab-nav {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
    """
    
    with gr.Blocks(css=custom_css, title="图像生成提示词管理系统", theme=gr.themes.Soft()) as app:
        
        gr.Markdown(
            """
            # 🎨 图像生成提示词管理系统
            
            欢迎使用图像生成提示词管理系统！这是一个功能强大的工具，帮助你管理和组织AI图像生成的提示词。
            """,
            elem_classes=["center"]
        )
        
        with gr.Tabs():
            
            # ============ 仪表板标签页 ============
            with gr.Tab("📊 仪表板"):
                gr.Markdown("### 系统概览")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        stats_display = gr.Markdown("正在加载统计信息...")
                    with gr.Column(scale=1):
                        recent_display = gr.Markdown("正在加载最近提示词...")
                
                connection_status = gr.Markdown("正在检查连接状态...")
                refresh_dashboard_btn = gr.Button("🔄 刷新仪表板", variant="primary")
                
                # 事件绑定
                refresh_dashboard_btn.click(
                    fn=load_dashboard_data,
                    outputs=[stats_display, recent_display, connection_status]
                )
                
                # 页面加载时自动刷新
                app.load(
                    fn=load_dashboard_data,
                    outputs=[stats_display, recent_display, connection_status]
                )
            
            # ============ 提示词管理标签页 ============
            with gr.Tab("📝 提示词管理"):
                
                with gr.Tabs():
                    # 创建提示词子标签页
                    with gr.Tab("➕ 创建提示词"):
                        gr.Markdown("### 创建新的提示词")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                prompt_text_input = gr.Textbox(
                                    label="提示词文本 *", 
                                    placeholder="输入你的提示词...",
                                    lines=3
                                )
                                negative_prompt_input = gr.Textbox(
                                    label="负面提示词", 
                                    placeholder="输入负面提示词...",
                                    lines=2
                                )
                                
                                with gr.Row():
                                    model_name_input = gr.Textbox(
                                        label="模型名称", 
                                        placeholder="例如: SDXL, Midjourney"
                                    )
                                    is_public_input = gr.Checkbox(label="设为公开", value=False)
                                
                                with gr.Row():
                                    style_desc_input = gr.Textbox(
                                        label="风格描述", 
                                        placeholder="描述图像风格..."
                                    )
                                    usage_scenario_input = gr.Textbox(
                                        label="使用场景", 
                                        placeholder="描述适用场景..."
                                    )
                                
                                with gr.Row():
                                    atmosphere_desc_input = gr.Textbox(
                                        label="氛围描述", 
                                        placeholder="描述画面氛围..."
                                    )
                                    expressive_intent_input = gr.Textbox(
                                        label="表现意图", 
                                        placeholder="描述表现意图..."
                                    )
                                
                                structure_analysis_input = gr.Textbox(
                                    label="结构分析", 
                                    placeholder="分析提示词结构...",
                                    lines=2
                                )
                                tag_names_input = gr.Textbox(
                                    label="标签", 
                                    placeholder="用逗号分隔多个标签: 动漫,风景,科幻"
                                )
                            
                            with gr.Column(scale=1):
                                image_upload = gr.File(
                                    label="上传图片 (可选)",
                                    file_types=["image"],
                                    type="filepath"
                                )
                                create_btn = gr.Button("🎨 创建提示词", variant="primary", size="lg")
                                create_status = gr.Markdown("")
                        
                        # 重复检查功能
                        gr.Markdown("### 🔍 重复检查")
                        with gr.Row():
                            duplicate_check_input = gr.Textbox(
                                label="检查重复提示词", 
                                placeholder="输入要检查的提示词文本..."
                            )
                            check_duplicate_btn = gr.Button("检查重复")
                        duplicate_result = gr.Markdown("")
                    
                    # 查看和管理提示词子标签页
                    with gr.Tab("📋 查看提示词"):
                        gr.Markdown("### 提示词列表")
                        
                        # 筛选器
                        with gr.Row():
                            keyword_filter = gr.Textbox(label="关键词搜索", placeholder="搜索提示词内容...")
                            model_filter = gr.Textbox(label="模型筛选", placeholder="筛选模型...")
                            public_filter = gr.Dropdown(
                                label="公开筛选", 
                                choices=[("全部", None), ("公开", True), ("私有", False)],
                                value=None
                            )
                            tag_filter = gr.Textbox(label="标签筛选", placeholder="用逗号分隔标签...")
                        
                        with gr.Row():
                            search_prompts_btn = gr.Button("🔍 搜索提示词", variant="secondary")
                            refresh_prompts_btn = gr.Button("🔄 刷新列表", variant="secondary")
                        
                        prompts_table = gr.Dataframe(
                            headers=["ID", "创建时间", "提示词", "模型", "公开", "标签", "风格"],
                            datatype=["number", "str", "str", "str", "str", "str", "str"],
                            interactive=False,
                            wrap=True
                        )
                        prompts_info = gr.Markdown("")
                    
                    # 编辑提示词子标签页
                    with gr.Tab("✏️ 编辑提示词"):
                        gr.Markdown("### 编辑提示词详情")
                        
                        prompt_id_input = gr.Number(label="提示词ID", precision=0)
                        load_prompt_btn = gr.Button("📥 加载提示词详情", variant="secondary")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                edit_prompt_text = gr.Textbox(label="提示词文本", lines=3)
                                edit_negative_prompt = gr.Textbox(label="负面提示词", lines=2)
                                
                                with gr.Row():
                                    edit_model_name = gr.Textbox(label="模型名称")
                                    edit_is_public = gr.Checkbox(label="设为公开")
                                
                                with gr.Row():
                                    edit_style_desc = gr.Textbox(label="风格描述")
                                    edit_usage_scenario = gr.Textbox(label="使用场景")
                                
                                with gr.Row():
                                    edit_atmosphere_desc = gr.Textbox(label="氛围描述")
                                    edit_expressive_intent = gr.Textbox(label="表现意图")
                                
                                edit_structure_analysis = gr.Textbox(label="结构分析", lines=2)
                                edit_tag_names = gr.Textbox(label="标签 (用逗号分隔)")
                            
                            with gr.Column(scale=1):
                                edit_image_url = gr.Textbox(label="图片URL", interactive=False)
                                with gr.Row():
                                    update_btn = gr.Button("💾 更新提示词", variant="primary")
                                    delete_btn = gr.Button("🗑️ 删除提示词", variant="stop")
                        
                        edit_status = gr.Markdown("")
            
            # ============ 标签管理标签页 ============
            with gr.Tab("🏷️ 标签管理"):
                
                with gr.Tabs():
                    # 查看标签子标签页
                    with gr.Tab("📋 查看标签"):
                        gr.Markdown("### 标签列表")
                        
                        refresh_tags_btn = gr.Button("🔄 刷新标签列表", variant="secondary")
                        tags_table = gr.Dataframe(
                            headers=["ID", "标签名称", "创建时间"],
                            datatype=["number", "str", "str"],
                            interactive=False
                        )
                        tags_info = gr.Markdown("")
                    
                    # 创建标签子标签页
                    with gr.Tab("➕ 创建标签"):
                        gr.Markdown("### 创建新标签")
                        
                        with gr.Row():
                            new_tag_name = gr.Textbox(
                                label="标签名称", 
                                placeholder="输入新标签名称...",
                                scale=3
                            )
                            create_tag_btn = gr.Button("🏷️ 创建标签", variant="primary", scale=1)
                        
                        create_tag_status = gr.Markdown("")
                    
                    # 删除标签子标签页
                    with gr.Tab("🗑️ 删除标签"):
                        gr.Markdown("### 删除标签")
                        
                        with gr.Row():
                            delete_tag_id = gr.Number(
                                label="标签ID", 
                                precision=0,
                                scale=3
                            )
                            delete_tag_btn = gr.Button("🗑️ 删除标签", variant="stop", scale=1)
                        
                        delete_tag_status = gr.Markdown("")
                    
                    # 搜索标签子标签页
                    with gr.Tab("🔍 搜索标签"):
                        gr.Markdown("### 搜索标签")
                        
                        with gr.Row():
                            tag_search_keyword = gr.Textbox(
                                label="搜索关键词", 
                                placeholder="输入搜索关键词...",
                                scale=3
                            )
                            search_tags_btn = gr.Button("🔍 搜索", variant="secondary", scale=1)
                        
                        search_tags_table = gr.Dataframe(
                            headers=["ID", "标签名称", "创建时间"],
                            datatype=["number", "str", "str"],
                            interactive=False
                        )
                        search_tags_info = gr.Markdown("")
            
            # ============ 高级搜索标签页 ============
            with gr.Tab("🔍 高级搜索"):
                gr.Markdown("### 根据标签搜索提示词")
                
                with gr.Row():
                    search_tag_names = gr.Textbox(
                        label="搜索标签", 
                        placeholder="输入标签名称，用逗号分隔: 动漫,风景",
                        scale=3
                    )
                    search_by_tags_btn = gr.Button("🔍 搜索", variant="primary", scale=1)
                
                search_results_table = gr.Dataframe(
                    headers=["ID", "创建时间", "提示词", "模型", "公开", "标签"],
                    datatype=["number", "str", "str", "str", "str", "str"],
                    interactive=False,
                    wrap=True
                )
                search_results_info = gr.Markdown("")
        
        # ============ 事件绑定 ============
        
        # 创建提示词事件
        create_btn.click(
            fn=create_prompt_with_image,
            inputs=[
                image_upload, prompt_text_input, negative_prompt_input, model_name_input,
                is_public_input, style_desc_input, usage_scenario_input, 
                atmosphere_desc_input, expressive_intent_input, structure_analysis_input, 
                tag_names_input
            ],
            outputs=[create_status, prompts_table]
        )
        
        # 重复检查事件
        check_duplicate_btn.click(
            fn=check_prompt_duplicate,
            inputs=[duplicate_check_input],
            outputs=[duplicate_result]
        )
        
        # 搜索提示词事件
        search_prompts_btn.click(
            fn=lambda keyword, model, is_public, tags: load_prompts_data(1, keyword, model, is_public, tags),
            inputs=[keyword_filter, model_filter, public_filter, tag_filter],
            outputs=[prompts_table, prompts_info]
        )
        
        # 刷新提示词列表事件
        refresh_prompts_btn.click(
            fn=lambda: load_prompts_data(),
            outputs=[prompts_table, prompts_info]
        )
        
        # 加载提示词详情事件
        load_prompt_btn.click(
            fn=get_prompt_detail,
            inputs=[prompt_id_input],
            outputs=[
                edit_prompt_text, edit_negative_prompt, edit_model_name, edit_image_url,
                edit_is_public, edit_style_desc, edit_usage_scenario, 
                edit_atmosphere_desc, edit_expressive_intent, edit_structure_analysis, 
                edit_tag_names
            ]
        )
        
        # 更新提示词事件
        update_btn.click(
            fn=update_prompt_detail,
            inputs=[
                prompt_id_input, edit_prompt_text, edit_negative_prompt, edit_model_name,
                edit_is_public, edit_style_desc, edit_usage_scenario, 
                edit_atmosphere_desc, edit_expressive_intent, edit_structure_analysis, 
                edit_tag_names
            ],
            outputs=[edit_status, prompts_table]
        )
        
        # 删除提示词事件
        delete_btn.click(
            fn=delete_prompt_by_id,
            inputs=[prompt_id_input],
            outputs=[edit_status, prompts_table]
        )
        
        # 标签管理事件
        refresh_tags_btn.click(
            fn=load_tags_data,
            outputs=[tags_table, tags_info]
        )
        
        create_tag_btn.click(
            fn=create_new_tag,
            inputs=[new_tag_name],
            outputs=[create_tag_status, tags_table]
        )
        
        delete_tag_btn.click(
            fn=delete_tag_by_id,
            inputs=[delete_tag_id],
            outputs=[delete_tag_status, tags_table]
        )
        
        search_tags_btn.click(
            fn=search_tags_by_keyword,
            inputs=[tag_search_keyword],
            outputs=[search_tags_table, search_tags_info]
        )
        
        # 高级搜索事件
        search_by_tags_btn.click(
            fn=search_prompts_by_tags_func,
            inputs=[search_tag_names],
            outputs=[search_results_table, search_results_info]
        )
        
        # 页面加载时自动刷新数据
        app.load(
            fn=load_prompts_data,
            outputs=[prompts_table, prompts_info]
        )
        
        app.load(
            fn=load_tags_data,
            outputs=[tags_table, tags_info]
        )
    
    return app


# ============ 主程序入口 ============
if __name__ == "__main__":
    # 检查API连接
    print("正在检查API连接...")
    status, _ = check_api_connection()
    print(status)
    
    # 创建并启动应用
    app = create_app()
    
    print(f"启动图像生成提示词管理系统...")
    print(f"后端API地址: {API_BASE_URL}")
    print(f"前端地址: http://{GRADIO_SERVER_NAME}:{GRADIO_SERVER_PORT}")
    
    app.launch(
        server_name=GRADIO_SERVER_NAME,
        server_port=GRADIO_SERVER_PORT,
        share=GRADIO_SHARE,
        inbrowser=True
    )
