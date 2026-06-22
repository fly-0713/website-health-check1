"""CI 专用入口 - 规避 main.py 中的 Windows-only API（如 os.startfile）

CI 环境用法：
    python ci_run.py                          # 运行全部测试（无头模式）
    python ci_run.py -k login                 # 只运行 login 用例
    python ci_run.py -m smoke                 # 只运行 smoke 标记

本地开发仍推荐使用 main.py。
"""

import os
import subprocess
import sys

import pytest

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 确保项目根目录在 sys.path 中
sys.path.insert(0, PROJECT_ROOT)

# 产物路径
ALLURE_RESULTS = os.path.join(PROJECT_ROOT, "report", "allure_results")
ALLURE_REPORT = os.path.join(PROJECT_ROOT, "report", "allure_report")
HTML_REPORT = os.path.join(PROJECT_ROOT, "report", "html", "report.html")

os.makedirs(ALLURE_RESULTS, exist_ok=True)
os.makedirs(os.path.dirname(HTML_REPORT), exist_ok=True)

# pytest 参数：强制无头模式 + Allure + HTML 报告
pytest_args = [
    "testcases/",
    "-v",
    "--tb=short",
    "--headless",
    f"--alluredir={ALLURE_RESULTS}",
    f"--html={HTML_REPORT}",
    "--self-contained-html",
]

# 支持从命令行透传额外参数（如 -k / -m）
pytest_args += sys.argv[1:]

# 执行测试
exit_code = pytest.main(pytest_args)

# 生成 Allure HTML 报告
allure_cmd = os.environ.get("ALLURE_CMD", "allure")
try:
    subprocess.run(
        [allure_cmd, "generate", ALLURE_RESULTS, "-o", ALLURE_REPORT, "--clean"],
        check=False,
    )
except FileNotFoundError:
    print(f"[警告] allure 命令未找到（{allure_cmd}），跳过 Allure 报告生成")

sys.exit(exit_code)
