"""
简历自动填写工具 - 主入口

用法:
    python main.py --resume <简历文件路径> --url <招聘页面URL>
"""
import argparse
import sys
from pathlib import Path
from loguru import logger

from config.settings import settings, PROJECT_ROOT
from resume_parser import ResumeParser, ResumeInfo
from automation import BrowserAutomation, SmartFormFiller


def setup_logger():
    """配置日志"""
    log_path = PROJECT_ROOT / "logs"
    log_path.mkdir(exist_ok=True)
    
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level="INFO"
    )
    logger.add(
        log_path / "auto_fill_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )


def parse_resume(file_path: str) -> ResumeInfo:
    """解析简历"""
    parser = ResumeParser()
    resume = parser.parse(file_path)
    
    logger.info(f"简历解析完成:")
    logger.info(f"  姓名: {resume.name}")
    logger.info(f"  性别: {resume.gender}")
    logger.info(f"  手机: {resume.phone}")
    logger.info(f"  邮箱: {resume.email}")
    logger.info(f"  教育经历: {len(resume.education)} 条")
    logger.info(f"  工作经历: {len(resume.work_experience)} 条")
    
    return resume


def auto_fill(url: str, resume: ResumeInfo, headless: bool = False, user_data_dir: str = None, executable_path: str = None):
    """
    自动填写招聘表单
    
    Args:
        url: 招聘页面URL
        resume: 简历信息
        headless: 是否无头模式
        user_data_dir: 浏览器用户数据目录(保持登录状态)
        executable_path: 自定义浏览器路径
    """
    logger.info(f"开始自动填写: {url}")
    
    with BrowserAutomation(
        headless=headless,
        slow_mo=settings.slow_mo,
        screenshot_path=str(PROJECT_ROOT / settings.screenshot_path),
        user_data_dir=user_data_dir,
        executable_path=executable_path,
    ) as browser:
        # 访问目标页面
        browser.goto(url)
        
        # 等待页面加载
        browser.page.wait_for_load_state("networkidle")
        
        # 使用智能填写器
        filler = SmartFormFiller(browser.page, resume)
        filled_count = filler.fill_all_forms()
        
        # 截图保存结果
        browser.screenshot("fill_result")
        
        logger.info(f"自动填写完成，共填写 {filled_count} 个字段")
        
        # 等待用户确认（非无头模式）
        if not headless:
            input("\n按回车键继续提交，或按 Ctrl+C 取消...")
        
        return filled_count


def interactive_mode():
    """交互模式"""
    print("=" * 50)
    print("       简历自动填写工具")
    print("=" * 50)
    
    # 1. 输入简历路径
    while True:
        resume_path = input("\n请输入简历文件路径: ").strip()
        if Path(resume_path).exists():
            break
        print(f"文件不存在: {resume_path}")
    
    # 2. 解析简历
    print("\n正在解析简历...")
    try:
        resume = parse_resume(resume_path)
    except Exception as e:
        print(f"简历解析失败: {e}")
        return
    
    # 3. 显示解析结果
    print(f"\n解析结果:")
    print(f"  姓名: {resume.name or '未识别'}")
    print(f"  性别: {resume.gender or '未识别'}")
    print(f"  手机: {resume.phone or '未识别'}")
    print(f"  邮箱: {resume.email or '未识别'}")
    print(f"  现居地: {resume.location or '未识别'}")
    
    confirm = input("\n是否继续? (y/n): ").strip().lower()
    if confirm != 'y':
        return
    
    # 4. 输入招聘页面URL
    url = input("\n请输入招聘页面URL: ").strip()
    if not url:
        print("URL 不能为空")
        return
    
    # 5. 是否保持登录状态
    user_data_dir = None
    keep_login = input("是否保持浏览器登录状态? (y/n): ").strip().lower()
    if keep_login == 'y':
        user_data_dir = str(PROJECT_ROOT / "browser_data")
    
    # 6. 自定义浏览器路径
    executable_path = None
    use_custom_browser = input("是否使用自定义浏览器? (y/n): ").strip().lower()
    if use_custom_browser == 'y':
        executable_path = input("请输入浏览器路径 (如 C:/Program Files/Google/Chrome/Application/chrome.exe): ").strip()
    
    # 7. 开始自动填写
    print("\n正在打开浏览器...")
    try:
        auto_fill(url, resume, headless=False, user_data_dir=user_data_dir, executable_path=executable_path)
    except Exception as e:
        logger.error(f"自动填写失败: {e}")
        return
    
    print("\n完成!")


def main():
    """主函数"""
    setup_logger()
    
    parser = argparse.ArgumentParser(
        description="简历自动填写工具 - 自动解析简历并填写招聘表单"
    )
    parser.add_argument(
        "--resume", "-r",
        help="简历文件路径 (支持 PDF/Word/TXT)"
    )
    parser.add_argument(
        "--url", "-u",
        help="招聘页面 URL"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="无头模式运行（不显示浏览器窗口）"
    )
    parser.add_argument(
        "--keep-login",
        action="store_true",
        help="保持浏览器登录状态"
    )
    parser.add_argument(
        "--browser-path",
        help="自定义浏览器路径 (如 C:/Program Files/Google/Chrome/Application/chrome.exe)"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="交互模式运行"
    )
    
    args = parser.parse_args()
    
    # 交互模式
    if args.interactive or (not args.resume and not args.url):
        interactive_mode()
        return
    
    # 命令行模式
    if not args.resume or not args.url:
        print("请提供简历路径和URL，或使用 -i 进入交互模式")
        print("用法: python main.py -r <简历路径> -u <招聘页面URL>")
        return
    
    # 解析简历
    resume = parse_resume(args.resume)
    
    # 设置用户数据目录
    user_data_dir = None
    if args.keep_login:
        user_data_dir = str(PROJECT_ROOT / "browser_data")
    
    # 自动填写
    auto_fill(args.url, resume, headless=args.headless, user_data_dir=user_data_dir, executable_path=args.browser_path)


if __name__ == "__main__":
    main()
