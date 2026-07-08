"""CI 专用入口 - 规避 main.py 中的 Windows-only API（如 os.startfile）

CI 环境用法：
    python ci_run.py                          # 运行全部测试（无头模式）
    python ci_run.py -k login                 # 只运行 login 用例
    python ci_run.py -m smoke                 # 只运行 smoke 标记

本地开发仍推荐使用 main.py。
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CI 运行入口脚本
支持通过命令行参数运行 pytest 测试
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from common.logger import logger


def main():
    parser = argparse.ArgumentParser(description="运行 UI 自动化测试")
    parser.add_argument(
        "test_path",
        nargs="?",
        default="testcases/",
        help="测试文件或目录路径（默认: testcases/）"
    )
    parser.add_argument(
        "-m", "--markers",
        help="pytest -m 标记表达式"
    )
    parser.add_argument(
        "-k", "--keyword",
        help="pytest -k 关键字表达式"
    )
    parser.add_argument(
        "--alluredir",
        default="report/allure_results",
        help="Allure 结果输出目录"
    )
    parser.add_argument(
        "--maxfail",
        type=int,
        default=5,
        help="最大失败次数后停止（默认: 5）"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    # 构建 pytest 命令
    cmd = [
        sys.executable,
        "-m", "pytest",
        args.test_path,
        f"--alluredir={args.alluredir}",
        f"--maxfail={args.maxfail}",
        "--tb=short",
    ]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    if args.keyword:
        cmd.extend(["-k", args.keyword])
    
    # 设置环境变量
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    
    logger.info(f"执行命令: {' '.join(cmd)}")
    logger.info(f"测试路径: {args.test_path}")
    logger.info(f"Allure 输出目录: {args.alluredir}")
    
    # 执行测试
    result = subprocess.run(cmd, env=env)
    
    # 返回退出码
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()