import requests
import json
import os
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
            response = self.session.request(method, url, timeout=10, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "success": False}
        except json.JSONDecodeError:
            return {"error": f"Invalid JSON response from server: {response.text[:200]}", "success": False}

    def _make_multipart_request(self, endpoint: str, files_list: List[Tuple[str, Any]], data: Dict) -> Dict[str, Any]:
        """处理 multipart/form-data 请求的通用方法"""
        url = f"{self.base_url}{endpoint}"
        try:
            headers = {k: v for k, v in self.session.headers.items() if k.lower() != 'content-type'}
            response = requests.post(url, files=files_list, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "success": False}
        except json.JSONDecodeError:
            return {"error": f"Invalid JSON response from server: {response.text[:200]}", "success": False}

    # ============ 提示词相关接口 ============
    def upload_and_create_prompt_multi(self, files_paths: Dict, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        上传多图片并创建提示词
        FIX: 彻底重构以正确处理文件路径列表并管理文件句柄
        """
        opened_files = []
        files_for_request = []
        try:
            # 处理输入图片 (多个)
            if 'input_images' in files_paths and files_paths['input_images']:
                for path in files_paths['input_images']:
                    if path:
                        f = open(path, 'rb')
                        opened_files.append(f)
                        # requests库需要一个元组: ('form_field_name', (filename, file_object))
                        # 重要的是，所有输入图片的 form_field_name 必须是同一个: 'input_images'
                        files_for_request.append(('input_images', (os.path.basename(path), f)))

            # 处理输出图片 (单个)
            if 'output_image' in files_paths and files_paths['output_image']:
                path = files_paths['output_image']
                f = open(path, 'rb')
                opened_files.append(f)
                files_for_request.append(('output_image', (os.path.basename(path), f)))

            # 如果没有任何文件被准备好上传，则调用常规的、不带图片的创建接口
            if not files_for_request:
                return self.create_prompt(prompt_data)

            return self._make_multipart_request('/prompts/upload', files_for_request, prompt_data)
        finally:
            # 确保所有打开的文件都被关闭，无论成功还是失败
            for f in opened_files:
                f.close()

    def create_prompt(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建提示词 (无图片)"""
        return self._make_request('POST', '/prompts/', json=prompt_data)

    def analyze_prompt(self, files_paths: Dict, analyze_data: Dict[str, Any]) -> Dict[str, Any]:
        """智能分析提示词（AI生成功能）"""
        opened_files = []
        files_for_request = []
        try:
            if 'input_images' in files_paths and files_paths['input_images']:
                for path in files_paths['input_images']:
                    if path:
                        f = open(path, 'rb')
                        opened_files.append(f)
                        files_for_request.append(('input_images', (os.path.basename(path), f)))

            if 'output_image' in files_paths and files_paths['output_image']:
                path = files_paths['output_image']
                f = open(path, 'rb')
                opened_files.append(f)
                files_for_request.append(('output_image', (os.path.basename(path), f)))

            return self._make_multipart_request('/prompts/analyze', files_for_request, analyze_data)
        finally:
            for f in opened_files:
                f.close()

    # --- 其他方法保持不变 ---
    def health_check(self) -> Dict[str, Any]:
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except:
            return {"error": "API服务器无法连接", "success": False}

    def db_status_check(self) -> Dict[str, Any]:
        try:
            response = requests.get(f"{API_BASE_URL}/db-status", timeout=5)
            response.raise_for_status()
            return response.json()
        except:
            return {"error": "数据库连接失败", "success": False}

    def get_prompt(self, prompt_id: int) -> Dict[str, Any]:
        return self._make_request('GET', f'/prompts/{prompt_id}')

    def update_prompt(self, prompt_id: int, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_request('PUT', f'/prompts/{prompt_id}', json=prompt_data)

    def delete_prompt(self, prompt_id: int) -> Dict[str, Any]:
        return self._make_request('DELETE', f'/prompts/{prompt_id}')

    def get_prompts(self, page: int = 1, page_size: int = 10, **filters) -> Dict[str, Any]:
        params = {'page': page, 'page_size': page_size}
        params.update({k: v for k, v in filters.items() if v is not None and v != ''})
        return self._make_request('GET', '/prompts/', params=params)

    def get_public_prompts(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        params = {'page': page, 'page_size': page_size}
        return self._make_request('GET', '/prompts/public', params=params)

    def get_recent_prompts(self, limit: int = 10) -> Dict[str, Any]:
        params = {'limit': limit}
        return self._make_request('GET', '/prompts/recent', params=params)

    def get_prompt_stats(self) -> Dict[str, Any]:
        return self._make_request('GET', '/prompts/stats')

    def search_prompts_by_tags(self, tags: List[str], page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        params = {'tags': ','.join(tags), 'page': page, 'page_size': page_size}
        return self._make_request('GET', '/prompts/search/tags', params=params)

    def check_duplicate(self, prompt_text: str) -> Dict[str, Any]:
        params = {'prompt_text': prompt_text}
        return self._make_request('GET', '/prompts/check-duplicate', params=params)

    def create_tag(self, tag_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_request('POST', '/tags/', json=tag_data)

    def get_tag(self, tag_id: int) -> Dict[str, Any]:
        return self._make_request('GET', f'/tags/{tag_id}')

    def get_all_tags(self) -> Dict[str, Any]:
        return self._make_request('GET', '/tags/')

    def search_tags(self, keyword: str = '') -> Dict[str, Any]:
        params = {'keyword': keyword} if keyword else {}
        return self._make_request('GET', '/tags/search', params=params)

    def delete_tag(self, tag_id: int) -> Dict[str, Any]:
        return self._make_request('DELETE', f'/tags/{tag_id}')

    def get_tag_stats(self) -> Dict[str, Any]:
        return self._make_request('GET', '/tags/stats')


api_client = APIClient()

