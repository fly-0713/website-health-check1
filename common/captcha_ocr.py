"""验证码 OCR 识别工具

使用 ddddocr 对验证码图片进行识别。
用法：
    1. 通过图片字节流识别：recognize_from_bytes(image_bytes)
    2. 通过文件路径识别：recognize_from_file(file_path)
"""

import ddddocr

# 全局初始化 OCR 实例（避免每次调用重复加载模型）
_ocr = ddddocr.DdddOcr(show_ad=False)


def recognize_from_bytes(image_bytes: bytes) -> str:
    """通过图片字节流识别验证码

    Args:
        image_bytes: 图片的二进制数据

    Returns:
        识别出的验证码文本
    """
    return _ocr.classification(image_bytes)


def recognize_from_file(file_path: str) -> str:
    """通过文件路径识别验证码

    Args:
        file_path: 验证码图片文件路径

    Returns:
        识别出的验证码文本
    """
    with open(file_path, "rb") as f:
        return recognize_from_bytes(f.read())
