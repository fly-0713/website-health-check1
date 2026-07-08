#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
发送钉钉通知脚本
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests


# 北京时间时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


def load_test_results(allure_dir: str) -> dict:
    """从 Allure 结果目录加载测试结果"""
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": [],
        "durations": [],
        "status_code": 200,
        "error_type": "无"
    }
    
    if not os.path.exists(allure_dir):
        print(f"⚠️ Allure 目录不存在: {allure_dir}")
        return results
    
    for file_path in Path(allure_dir).glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if data.get("status") == "passed":
                results["passed"] += 1
            elif data.get("status") == "failed":
                results["failed"] += 1
                status_details = data.get("statusDetails", {})
                error_msg = status_details.get("message", "未知错误")
                results["errors"].append(error_msg)
            elif data.get("status") in ["skipped", "broken"]:
                results["skipped"] += 1
            
            results["total"] += 1
            
            # 🔥 读取 duration（单位：毫秒，转换为秒）
            if "time" in data:
                duration_ms = data["time"].get("duration", 0)
                results["durations"].append(duration_ms / 1000)
                
        except Exception as e:
            print(f"解析 Allure 文件失败 {file_path}: {e}")
    
    # 计算平均响应时间
    if results["durations"]:
        results["avg_duration"] = sum(results["durations"]) / len(results["durations"])
    else:
        results["avg_duration"] = 0
    
    # 判断状态码
    if results["failed"] > 0:
        results["status_code"] = 500
    elif results["total"] == 0:
        results["status_code"] = 404
    else:
        results["status_code"] = 200
    
    # 分析错误类型
    if results["errors"]:
        first_error = results["errors"][0]
        if "TimeoutError" in first_error or "timeout" in first_error.lower():
            results["error_type"] = "超时错误"
        elif "定位" in first_error or "locator" in first_error.lower():
            results["error_type"] = "元素定位错误"
        elif "验证码" in first_error or "captcha" in first_error.lower():
            results["error_type"] = "验证码识别错误"
        elif "网络" in first_error or "connection" in first_error.lower():
            results["error_type"] = "网络连接错误"
        elif "assert" in first_error.lower():
            results["error_type"] = "断言失败"
        else:
            results["error_type"] = "业务逻辑错误"
    
    return results


def send_dingtalk_notification(webhook: str, site_name: str, env: str, results: dict):
    """发送钉钉通知"""
    is_success = results["failed"] == 0
    status_text = "✅ 正常" if is_success else "❌ 异常"
    
    error_msg = "；".join(results["errors"][:3]) if results["errors"] else "无"
    if len(results["errors"]) > 3:
        error_msg += f" ... 共 {len(results['errors'])} 个失败"
    
    # 🔥 使用北京时间
    beijing_time = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
    
    # 🔥 去掉"通过/总数"行，修改表格
    msg = f"""## {site_name}

| 项目 | 内容 |
|------|------|
| **检测时间** | {beijing_time} |
| **检测环境** | {env} |
| **检测状态** | **{status_text}** |
| **响应状态码** | {results['status_code']} |
| **响应时间** | {results['avg_duration']:.2f} 秒 |
| **错误信息** | {error_msg} |
| **错误类型** | {results['error_type']} |
"""
    
    # 如果有失败用例，添加失败详情
    if results["errors"]:
        fail_details = "\n".join([f"- {e[:100]}" for e in results["errors"][:5]])
        if len(results["errors"]) > 5:
            fail_details += f"\n- ... 共 {len(results['errors'])} 个失败"
        msg += f"\n**失败详情:**\n{fail_details}"
    
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"UI自动化测试报告 - {site_name}",
            "text": msg
        }
    }
    
    try:
        response = requests.post(webhook, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get("errcode") == 0:
            print(f"✅ {site_name} 钉钉通知发送成功")
        else:
            print(f"❌ {site_name} 钉钉返回错误: {result}")
    except Exception as e:
        print(f"❌ {site_name} 钉钉通知发送失败: {e}")


def main():
    webhook = os.environ.get("WEBHOOK")
    if not webhook:
        print("⚠️ 未配置 WEBHOOK 环境变量，跳过通知")
        sys.exit(0)
    
    site_name = os.environ.get("SITE_NAME", "未知站点")
    env_name = os.environ.get("ENV_NAME", "test")
    allure_prefix = os.environ.get("ALLURE_PREFIX", "default")
    allure_dir = f"report/allure_results_{allure_prefix}"
    
    print(f"📊 开始处理 {site_name} 的测试结果...")
    print(f"   - Allure 目录: {allure_dir}")
    print(f"   - 北京时间: {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = load_test_results(allure_dir)
    
    if results["total"] == 0:
        print("⚠️ 没有找到测试结果")
        results["total"] = 0
        results["passed"] = 0
        results["failed"] = 0
        results["status_code"] = 404
        results["avg_duration"] = 0
        results["error_type"] = "无测试执行"
        results["errors"] = ["未找到测试结果文件，请检查测试是否正常执行"]
    
    print(f"   - 总用例: {results['total']}")
    print(f"   - 通过: {results['passed']}")
    print(f"   - 失败: {results['failed']}")
    print(f"   - 平均响应时间: {results['avg_duration']:.2f} 秒")
    
    send_dingtalk_notification(webhook, site_name, env_name, results)
    
    with open(f"test_result_{allure_prefix}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {site_name} 通知处理完成")


if __name__ == "__main__":
    main()