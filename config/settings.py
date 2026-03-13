"""
全局配置
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    # 简历文件路径
    resume_path: str = "data/resume"
    
    # 浏览器配置
    headless: bool = False  # 是否无头模式
    slow_mo: int = 100  # 操作延迟(ms)
    browser_path: str = "C:/Program Files/Google/Chrome/Application/chrome.exe"  # 自定义浏览器路径 (留空使用 Playwright 自带)
    
    # 截图保存路径
    screenshot_path: str = "logs/screenshots"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

settings = Settings()
