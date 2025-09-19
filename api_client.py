import requests
import json
from typing import Optional, List, Dict, Any, Tuple
from config import API_PREFIX, API_BASE_URL


class APIClient:
    """API客户端类，用于与后端API通信"""
    
    def __init__(self):
        self.base_url = API_PREFIX
        self.uploads_url = f"{API_BASE_URL}/uploads"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求的通用方法"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "success": False}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "success": False}
    
    def _make_upload_request(self, endpoint: str, files: Dict, data: Dict) -> Dict[str, Any]:
        """上传文件的特殊请求方法"""
        url = f"{self.base_url}{endpoint}"
        try:
            # 移除Content-Type头，让requests自动设置multipart/form-data
            headers = {k: v for k, v in self.session.headers.items() if k.lower() != 'content-type'}
            response = requests.post(url, files=files, data=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "success": False}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "success": False}

    # ============ 健康检查相关 ============
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except:
            return {"error": "API服务器无法连接", "success": False}
    
    def db_status_check(self) -> Dict[str, Any]:
        """数据库状态检查"""
        try:
            response = requests.get(f"{API_BASE_URL}/db-status", timeout=5)
            response.raise_for_status()
            return response.json()
        except:
            return {"error": "数据库连接失败", "success": False}

    # ============ 提示词相关接口 ============
    def create_prompt(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建提示词"""
        return self._make_request('POST', '/prompts/', json=prompt_data)
    
    def upload_and_create_prompt(self, image_file, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """上传图片并创建提示词"""
        files = {'image': image_file}
        return self._make_upload_request('/prompts/upload', files=files, data=prompt_data)
    
    def get_prompt(self, prompt_id: int) -> Dict[str, Any]:
        """获取单个提示词"""
        return self._make_request('GET', f'/prompts/{prompt_id}')
    
    def update_prompt(self, prompt_id: int, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新提示词"""
        return self._make_request('PUT', f'/prompts/{prompt_id}', json=prompt_data)
    
    def delete_prompt(self, prompt_id: int) -> Dict[str, Any]:
        """删除提示词"""
        return self._make_request('DELETE', f'/prompts/{prompt_id}')
    
    def get_prompts(self, page: int = 1, page_size: int = 10, **filters) -> Dict[str, Any]:
        """获取提示词列表"""
        params = {'page': page, 'page_size': page_size}
        params.update({k: v for k, v in filters.items() if v is not None and v != ''})
        return self._make_request('GET', '/prompts/', params=params)
    
    def get_public_prompts(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """获取公开提示词列表"""
        params = {'page': page, 'page_size': page_size}
        return self._make_request('GET', '/prompts/public', params=params)
    
    def get_recent_prompts(self, limit: int = 10) -> Dict[str, Any]:
        """获取最近的提示词"""
        params = {'limit': limit}
        return self._make_request('GET', '/prompts/recent', params=params)
    
    def get_prompt_stats(self) -> Dict[str, Any]:
        """获取提示词统计信息"""
        return self._make_request('GET', '/prompts/stats')
    
    def search_prompts_by_tags(self, tags: List[str], page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """根据标签搜索提示词"""
        params = {
            'tags': ','.join(tags),
            'page': page,
            'page_size': page_size
        }
        return self._make_request('GET', '/prompts/search/tags', params=params)
    
    def check_duplicate(self, prompt_text: str) -> Dict[str, Any]:
        """检查重复提示词"""
        params = {'prompt_text': prompt_text}
        return self._make_request('GET', '/prompts/check-duplicate', params=params)

    # ============ 标签相关接口 ============
    def create_tag(self, tag_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建标签"""
        return self._make_request('POST', '/tags/', json=tag_data)
    
    def get_tag(self, tag_id: int) -> Dict[str, Any]:
        """获取单个标签"""
        return self._make_request('GET', f'/tags/{tag_id}')
    
    def get_all_tags(self) -> Dict[str, Any]:
        """获取所有标签"""
        return self._make_request('GET', '/tags/')
    
    def search_tags(self, keyword: str = '') -> Dict[str, Any]:
        """搜索标签"""
        params = {'keyword': keyword} if keyword else {}
        return self._make_request('GET', '/tags/search', params=params)
    
    def delete_tag(self, tag_id: int) -> Dict[str, Any]:
        """删除标签"""
        return self._make_request('DELETE', f'/tags/{tag_id}')
    
    def get_tag_stats(self) -> Dict[str, Any]:
        """获取标签统计信息"""
        return self._make_request('GET', '/tags/stats')


# 创建全局API客户端实例
api_client = APIClient()
