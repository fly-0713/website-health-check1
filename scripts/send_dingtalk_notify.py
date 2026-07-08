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
        "api_response_times": [],  # 🔥 新增：API 响应时间列表
        "status_code": 200,
        "error_type": "无",
        "test_status": "passed"
    }
    
    if not os.path.exists(allure_dir):
        print(f"⚠️ Allure 目录不存在: {allure_dir}")
        results["test_status"] = "failed"
        results["status_code"] = 404
        results["errors"] = ["Allure 目录不存在"]
        return results
    
    json_files = list(Path(allure_dir).glob("*.json"))
    if not json_files:
        print(f"⚠️ 没有找到 JSON 文件")
        results["test_status"] = "failed"
        results["status_code"] = 404
        results["errors"] = ["没有找到测试结果文件"]
        return results
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n📄 文件: {file_path.name}")
            
            if "status" not in data:
                print(f"   - ⚠️ 跳过：没有 status 字段")
                continue
            
            status = data.get("status", "").lower()
            print(f"   - status: '{status}'")
            
            # 🔥 从 data 中提取 API 响应时间（如果有）
            api_response_time = 0
            if "api_response_time" in data:
                api_response_time = data.get("api_response_time", 0)
                print(f"   - API 响应时间: {api_response_time:.3f}秒")
            
            # 判断是否失败
            is_failed = False
            
            # 从 statusDetails 或 message 提取错误
            error_msg = ""
            if "statusDetails" in data and data["statusDetails"]:
                error_msg = data["statusDetails"].get("message", "")
                if error_msg:
                    is_failed = True
            if not error_msg and "message" in data and data["message"]:
                error_msg = data["message"]
                is_failed = True
            
            if status == "failed" or status == "broken":
                is_failed = True
            elif status not in ["passed", "skipped"] and status:
                is_failed = True
            
            if is_failed:
                results["failed"] += 1
                results["test_status"] = "failed"
                if not error_msg:
                    error_msg = f"测试失败，状态: {status}"
                results["errors"].append(error_msg)
                print(f"   - ❌ 失败: {error_msg[:100]}")
            elif status == "passed":
                results["passed"] += 1
                print(f"   - ✅ 通过")
            elif status == "skipped":
                results["skipped"] += 1
                print(f"   - ⏭️ 跳过")
            else:
                results["failed"] += 1
                results["test_status"] = "failed"
                results["errors"].append(f"未知状态: {status}")
                print(f"   - ⚠️ 默认标记为失败")
            
            results["total"] += 1
            
            # 🔥 保存 API 响应时间
            if api_response_time > 0:
                results["api_response_times"].append(api_response_time)
            
            # 读取测试耗时
            duration_sec = 0
            if "time" in data and isinstance(data["time"], dict):
                duration_sec = data["time"].get("duration", 0) / 1000
            if duration_sec == 0 and "duration" in data:
                duration_sec = data["duration"] / 1000
            if duration_sec == 0 and "stop" in data and "start" in data:
                duration_sec = (data["stop"] - data["start"]) / 1000
            
            if duration_sec > 0:
                results["durations"].append(duration_sec)
                print(f"   - 测试耗时: {duration_sec:.2f}秒")
                
        except Exception as e:
            print(f"❌ 解析 Allure 文件失败 {file_path}: {e}")
            results["errors"].append(f"解析失败: {e}")
            results["test_status"] = "failed"
    
    # 计算平均值
    if results["durations"]:
        results["avg_duration"] = sum(results["durations"]) / len(results["durations"])
    else:
        results["avg_duration"] = 0
    
    if results["api_response_times"]:
        results["avg_api_response"] = sum(results["api_response_times"]) / len(results["api_response_times"])
    else:
        results["avg_api_response"] = 0
    
    # 设置状态码
    if results["failed"] > 0 or results["test_status"] == "failed":
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
    
    print(f"\n📊 统计结果:")
    print(f"   - 总用例: {results['total']}")
    print(f"   - 通过: {results['passed']}")
    print(f"   - 失败: {results['failed']}")
    print(f"   - 测试状态: {results['test_status']}")
    print(f"   - 平均测试耗时: {results['avg_duration']:.2f}秒")
    print(f"   - 平均API响应: {results.get('avg_api_response', 0):.3f}秒")
    
    return results


def send_dingtalk_notification(webhook: str, site_name: str, env: str, results: dict):
    """发送钉钉通知"""
    is_success = results.get("test_status") == "passed" and results["failed"] == 0
    status_text = "✅ 正常" if is_success else "❌ 异常"
    
    error_msg = "；".join(results["errors"][:3]) if results["errors"] else "无"
    if len(results["errors"]) > 3:
        error_msg += f" ... 共 {len(results['errors'])} 个失败"
    
    beijing_time = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
    
    # 格式化测试耗时
    if results['avg_duration'] > 0:
        duration_display = f"{results['avg_duration']:.2f} 秒"
    else:
        duration_display = "N/A"
    
    # 🔥 格式化 API 响应时间
    if results.get('avg_api_response', 0) > 0:
        api_response_display = f"{results['avg_api_response']:.3f} 秒"
    else:
        api_response_display = "未测量"
    
    # 🔥 新模板：包含测试耗时和服务器响应时间
    msg = f"""## {site_name}

| 项目 | 内容 |
|------|------|
| **检测时间** | {beijing_time} |
| **检测环境** | {env} |
| **检测状态** | **{status_text}** |
| **响应状态码** | {results['status_code']} |
| **测试耗时** | {duration_display} |
| **服务器响应** | {api_response_display} |
| **错误信息** | {error_msg} |
| **错误类型** | {results['error_type']} |
"""
    
    if results["errors"]:
        fail_details = "\n".join([f"- {e[:200]}" for e in results["errors"][:5]])
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
        results["failed"] = 1
        results["test_status"] = "failed"
        results["status_code"] = 404
        results["avg_duration"] = 0
        results["avg_api_response"] = 0
        results["error_type"] = "无测试执行"
        results["errors"] = ["未找到测试结果文件，请检查测试是否正常执行"]
    
    print(f"   - 总用例: {results['total']}")
    print(f"   - 通过: {results['passed']}")
    print(f"   - 失败: {results['failed']}")
    print(f"   - 测试状态: {results.get('test_status', 'unknown')}")
    print(f"   - 平均测试耗时: {results['avg_duration']:.2f} 秒")
    print(f"   - 平均API响应: {results.get('avg_api_response', 0):.3f} 秒")
    
    send_dingtalk_notification(webhook, site_name, env_name, results)
    
    with open(f"test_result_{allure_prefix}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {site_name} 通知处理完成")


if __name__ == "__main__":
    main()