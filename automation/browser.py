"""
浏览器自动化控制
"""
from typing import Optional, Callable, Any
from pathlib import Path
from loguru import logger
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext


class BrowserAutomation:
    """浏览器自动化控制类"""
    
    def __init__(
        self,
        headless: bool = False,
        slow_mo: int = 100,
        screenshot_path: str = "logs/screenshots",
        user_data_dir: Optional[str] = None,
    ):
        """
        初始化浏览器自动化
        
        Args:
            headless: 是否无头模式
            slow_mo: 操作延迟(ms)
            screenshot_path: 截图保存路径
            user_data_dir: 浏览器用户数据目录(保持登录状态)
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.screenshot_path = Path(screenshot_path)
        self.user_data_dir = user_data_dir
        
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
        # 创建截图目录
        self.screenshot_path.mkdir(parents=True, exist_ok=True)
    
    def start(self, browser_type: str = "chromium"):
        """启动浏览器"""
        logger.info(f"启动浏览器: {browser_type}")
        
        self._playwright = sync_playwright().start()
        
        # 选择浏览器类型
        browser_launcher = getattr(self._playwright, browser_type)
        
        # 启动浏览器
        if self.user_data_dir:
            # 使用持久化上下文，保持登录状态
            self._context = browser_launcher.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=["--start-maximized"],
                viewport={"width": 1920, "height": 1080},
            )
            self._page = self._context.new_page()
        else:
            self._browser = browser_launcher.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=["--start-maximized"],
            )
            self._context = self._browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            self._page = self._context.new_page()
        
        logger.info("浏览器启动成功")
        return self
    
    def close(self):
        """关闭浏览器"""
        if self._page:
            self._page.close()
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        
        logger.info("浏览器已关闭")
    
    @property
    def page(self) -> Page:
        """获取当前页面"""
        if not self._page:
            raise RuntimeError("浏览器未启动，请先调用 start()")
        return self._page
    
    def goto(self, url: str, wait_until: str = "networkidle"):
        """导航到指定URL"""
        logger.info(f"访问: {url}")
        self.page.goto(url, wait_until=wait_until)
        return self
    
    def click(self, selector: str, timeout: int = 10000):
        """点击元素"""
        logger.debug(f"点击: {selector}")
        self.page.click(selector, timeout=timeout)
        return self
    
    def fill(self, selector: str, value: str, timeout: int = 10000):
        """填充输入框"""
        logger.debug(f"填充 {selector}: {value}")
        self.page.fill(selector, value, timeout=timeout)
        return self
    
    def select(self, selector: str, value: str, timeout: int = 10000):
        """选择下拉框"""
        logger.debug(f"选择 {selector}: {value}")
        self.page.select_option(selector, value, timeout=timeout)
        return self
    
    def wait_for(self, selector: str, timeout: int = 30000):
        """等待元素出现"""
        self.page.wait_for_selector(selector, timeout=timeout)
        return self
    
    def screenshot(self, name: str) -> str:
        """截图"""
        path = self.screenshot_path / f"{name}.png"
        self.page.screenshot(path=path)
        logger.info(f"截图已保存: {path}")
        return str(path)
    
    def wait_and_click(self, selector: str, timeout: int = 30000):
        """等待并点击"""
        self.wait_for(selector, timeout)
        self.click(selector)
        return self
    
    def wait_and_fill(self, selector: str, value: str, timeout: int = 30000):
        """等待并填充"""
        self.wait_for(selector, timeout)
        self.fill(selector, value)
        return self
    
    def execute_script(self, script: str) -> Any:
        """执行 JavaScript"""
        return self.page.evaluate(script)
    
    def get_text(self, selector: str) -> str:
        """获取元素文本"""
        return self.page.text_content(selector) or ""
    
    def get_value(self, selector: str) -> str:
        """获取输入框值"""
        return self.page.input_value(selector)
    
    def is_visible(self, selector: str) -> bool:
        """检查元素是否可见"""
        return self.page.is_visible(selector)
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
