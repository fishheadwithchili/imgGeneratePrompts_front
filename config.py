# 配置文件
import os

# 后端API配置
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8080')
API_VERSION = 'v1'
API_PREFIX = f'{API_BASE_URL}/api/{API_VERSION}'

# Gradio配置
GRADIO_SERVER_NAME = os.getenv('GRADIO_SERVER_NAME', '0.0.0.0')
GRADIO_SERVER_PORT = int(os.getenv('GRADIO_SERVER_PORT', '7860'))
GRADIO_SHARE = os.getenv('GRADIO_SHARE', 'False').lower() == 'true'

# 文件上传配置
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']

# 分页配置
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
