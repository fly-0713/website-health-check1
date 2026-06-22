"""主程序入口 - 运行所有测试用例

用法：
    python main.py                          # 运行所有测试用例（自动生成 Allure + HTML 报告）
    python main.py --headless               # 无头模式运行
    python main.py -k login                 # 只运行名称包含 login 的用例
    python main.py -m smoke                 # 只运行 smoke 标记的用例
    python main.py --open                   # 运行后自动打开 Allure 报告
    python main.py --no-clean               # 运行前不清理旧产物
"""

import argparse
import os
import shutil
import subprocess
import sys

import pytest

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 确保 allure 命令可用
_ALLURE_BIN_DIR = os.path.join(os.path.dirname(PROJECT_ROOT), "allure-2.24.1", "bin")
if os.path.exists(_ALLURE_BIN_DIR) and _ALLURE_BIN_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _ALLURE_BIN_DIR + os.pathsep + os.environ.get("PATH", "")


def _find_allure_cmd() -> str:
    """查找 allure 可执行文件路径，找不到则返回 'allure'"""
    # 1. 已知安装路径
    known_path = os.path.join(_ALLURE_BIN_DIR, "allure.bat")
    if os.path.exists(known_path):
        return known_path
    # 2. 系统 PATH 中查找
    import shutil
    found = shutil.which("allure")
    return found if found else "allure"

# 各产物目录
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "screenshots")
HTML_REPORT_DIR = os.path.join(PROJECT_ROOT, "report", "html")
ALLURE_RESULTS_DIR = os.path.join(PROJECT_ROOT, "report", "allure_results")
ALLURE_REPORT_DIR = os.path.join(PROJECT_ROOT, "report", "allure_report")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="UI 自动化测试主程序")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="无头模式运行（不显示浏览器窗口）",
    )
    parser.add_argument(
        "-k",
        default=None,
        help="只运行名称匹配的用例（支持关键字表达式）",
    )
    parser.add_argument(
        "-m",
        default=None,
        help="只运行指定标记的用例（如 smoke、regression）",
    )
    parser.add_argument(
        "--tb",
        default="short",
        choices=["long", "short", "line", "no"],
        help="回溯信息格式（默认 short）",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="运行结束后自动打开 Allure 报告",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="运行前不清理旧日志、截图、报告",
    )
    args, remaining = parser.parse_known_args()
    return args, remaining


def clean_old_artifacts():
    """运行前清理旧的截图、报告（日志用追加模式，不清理）"""
    dirs_to_clean = [SCREENSHOT_DIR, ALLURE_RESULTS_DIR, HTML_REPORT_DIR]
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
    print(f"[清理] 已清除旧产物: screenshots / report")


def build_pytest_args(args, remaining):
    """构建 pytest 参数列表"""
    pytest_args = [
        "testcases/",
        "-v",
        f"--tb={args.tb}",
    ]

    # HTML 报告
    os.makedirs(HTML_REPORT_DIR, exist_ok=True)
    html_path = os.path.join(HTML_REPORT_DIR, "report.html")
    pytest_args.append(f"--html={html_path}")
    pytest_args.append("--self-contained-html")

    # Allure 报告（默认生成）
    os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)
    pytest_args.append(f"--alluredir={ALLURE_RESULTS_DIR}")

    # 无头模式
    if args.headless:
        pytest_args.append("--headless")

    # 关键字过滤
    if args.k:
        pytest_args.extend(["-k", args.k])

    # 标记过滤
    if args.m:
        pytest_args.extend(["-m", args.m])

    # 追加其他参数
    pytest_args.extend(remaining)

    return pytest_args


def generate_allure_report():
    """运行结束后自动生成 Allure HTML 报告"""
    if not os.path.exists(ALLURE_RESULTS_DIR):
        print("[警告] Allure 数据目录不存在，跳过报告生成")
        return False

    allure_cmd = _find_allure_cmd()
    try:
        result = subprocess.run(
            [allure_cmd, "generate", ALLURE_RESULTS_DIR, "-o", ALLURE_REPORT_DIR, "--clean"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print(f"[报告] Allure 报告已生成: {ALLURE_REPORT_DIR}")
            return True
        else:
            print(f"[警告] Allure 报告生成失败: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        print("[警告] 未找到 allure 命令")
        print(f"[提示] Allure 数据已生成到: {ALLURE_RESULTS_DIR}")
        print("[提示] 请安装 Allure CLI 后执行: allure generate report/allure_results -o report/allure_report --clean")
        return False


def open_allure_report(args):
    """打开 Allure 报告"""
    allure_cmd = _find_allure_cmd()

    # 优先尝试 allure serve（启动本地服务，实时查看）
    if os.path.exists(ALLURE_RESULTS_DIR):
        try:
            subprocess.run(
                [allure_cmd, "serve", ALLURE_RESULTS_DIR],
                check=False,
            )
            return
        except FileNotFoundError:
            pass

    # 回退：尝试打开已生成的静态报告
    index_path = os.path.join(ALLURE_REPORT_DIR, "index.html")
    if os.path.exists(index_path):
        os.startfile(index_path)
        print(f"[报告] 已打开 Allure 报告: {index_path}")
    else:
        # 最后回退：打开 HTML 报告
        html_path = os.path.join(HTML_REPORT_DIR, "report.html")
        if os.path.exists(html_path):
            os.startfile(html_path)
            print(f"[报告] 已打开 HTML 报告: {html_path}")


def main():
    args, remaining = parse_args()

    # 1. 运行前清理旧产物
    if not args.no_clean:
        clean_old_artifacts()

    # 2. 获取 logger
    from common.logger import logger as test_logger
    from common.config import config

    test_logger.info("=" * 50)
    test_logger.info("开始运行 UI 自动化测试")
    test_logger.info(f"运行参数: headless={args.headless}, k={args.k}, m={args.m}, env={config.base_url}")
    test_logger.info("=" * 50)

    # 3. 执行测试
    pytest_args = build_pytest_args(args, remaining)
    exit_code = pytest.main(pytest_args)

    # 4. 自动生成 Allure 报告
    generate_allure_report()

    # 5. 输出结果
    test_logger.info("=" * 50)
    if exit_code == 0:
        test_logger.info("所有测试用例通过！")
    else:
        test_logger.warning(f"测试运行结束，退出码: {exit_code}")
    test_logger.info("=" * 50)

    # 6. 自动打开报告
    if args.open:
        open_allure_report(args)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
