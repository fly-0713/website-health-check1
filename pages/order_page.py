"""计划订单页面对象"""

from playwright.sync_api import Page, Locator, expect

from common.logger import logger
from pages.base_page import BasePage


class OrderPage(BasePage):
    """计划订单页面对象"""

    # 页面 URL 关键路径
    ORDER_URL_KEYWORD = "/plan/index"

    def __init__(self, page: Page):
        super().__init__(page)
        # 左侧菜单定位器
        self._menu_plan = page.locator(".el-sub-menu__title, .el-menu-item").filter(has_text="计划管理")
        self._menu_order = page.locator(".el-menu-item").filter(has_text="计划订单")

        # 搜索区域定位器
        self._order_no_input = page.get_by_placeholder("计划编号")
        self._search_button = page.get_by_role("button", name="搜索")

    def navigate_to_order(self):
        """从首页导航到计划订单页面：点击计划管理 → 点击计划订单"""
        logger.info("导航到计划订单页面")
        self._menu_plan.first.click()
        self.page.wait_for_timeout(500)
        self._menu_order.first.click()
        # 等待页面加载
        self._order_no_input.wait_for(state="visible", timeout=self.timeout)
        logger.info(f"已进入计划订单页面, URL: {self.page.url}")

    def search_order(self, order_no: str):
        """输入计划编号并点击搜索"""
        logger.info(f"搜索计划编号: {order_no}")
        self.click_and_fill(self._order_no_input, order_no)
        self.click(self._search_button)
        # 等待搜索结果加载完成
        self._wait_for_search_complete()

    def is_table_empty(self) -> bool:
        """判断表格数据是否为空"""
        try:
            # 优先检查 Element UI 空数据占位块
            empty_block = self.page.locator(".el-table__empty-block")
            if empty_block.is_visible():
                empty_text = self.page.locator(".el-table__empty-text").inner_text()
                logger.info(f"表格为空，提示: {empty_text}")
                return True
            # 检查表格数据行数（排除合计行等）
            rows = self.page.locator(".el-table__body-wrapper tbody tr").all()
            data_rows = [r for r in rows if r.is_visible()]
            is_empty = len(data_rows) == 0
            logger.info(f"表格可见行数: {len(data_rows)}, 是否为空: {is_empty}")
            return is_empty
        except Exception as e:
            logger.warning(f"判断表格是否为空时异常: {e}")
            return True

    def _get_column_index(self, header_text: str) -> int:
        """通过表头文本获取列索引（1-based）

        在 el-table 的头部中查找包含指定文本的列，返回其位置。
        这样即使表格列顺序变化或有隐藏列，也能正确定位。
        """
        headers = self.page.locator(".el-table__header-wrapper th").all()
        for i, th in enumerate(headers):
            if th.is_visible() and header_text in th.inner_text():
                logger.info(f"表头 '{header_text}' 在第 {i+1} 列")
                return i + 1
        logger.warning(f"未找到表头 '{header_text}'")
        return -1

    def get_order_numbers(self) -> list:
        """获取表格中所有计划编号"""
        order_numbers = []
        try:
            # 通过表头"计划编号"动态定位列，不再硬编码列号
            col_index = self._get_column_index("计划编号")
            if col_index == -1:
                logger.error("无法定位计划编号列")
                return order_numbers
            cells = self.page.locator(f".el-table__body-wrapper tbody tr td:nth-child({col_index})").all()
            for cell in cells:
                if cell.is_visible():
                    text = cell.inner_text().strip()
                    if text:
                        order_numbers.append(text)
        except Exception as e:
            logger.warning(f"获取计划编号列表异常: {e}")
        logger.info(f"计划编号列表: {order_numbers}")
        return order_numbers

    def _wait_for_search_complete(self):
        """等待搜索请求完成（Loading出现再消失）"""
        loading = self.page.locator(".el-loading-mask")
        try:
            # 等待 Loading 出现（说明请求已发出）
            loading.wait_for(state="visible", timeout=3000)
        except Exception:
            pass
        try:
            # 等待 Loading 消失（说明请求已完成）
            loading.wait_for(state="hidden", timeout=10000)
        except Exception:
            pass
        # 额外等待表格渲染
        self.page.wait_for_timeout(500)
