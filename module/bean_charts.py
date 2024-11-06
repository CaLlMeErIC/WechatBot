"""
排行榜功能模块
"""

from utils.bean_actions import BeanManager  # 假设 BeanManager 类保存在 bean_manager.py 文件中


class FunctionModule:
    """
    FunctionModule 类，实现豆子排行榜功能。
    """

    _instance = None
    # 命令标识，用于标注什么样的命令开头会调用这个功能模块
    # 比如用户发送 "@机器人 排行榜" 或 "@机器人 查看排行榜" 会触发这个模块
    _command_sign = ["排行榜", "查看排行榜"]
    _reply_string = None
    # 模块激活状态
    is_active = True  # 设置为 True，表示模块被激活

    def __new__(cls):
        """
        单例实现。
        """
        if cls._instance is None:
            cls._instance = super(FunctionModule, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
        初始化方法。
        """
        if not hasattr(self, '_initialized'):
            self._initialized = True
            # 初始化操作
            self.bean_manager = BeanManager()

    def get_command_sign(self):
        """
        返回当前模块的命令标识
        """
        return self._command_sign

    def process_messages(self, sender_nickname, content):
        """
        根据发消息人的昵称和消息内容，处理排行榜的请求。

        Args:
            sender_nickname (str): 发送者的昵称。
            content (str): 消息内容。

        Returns:
            str: 回复消息。
        """
        # 获取豆子数量最多的前 10 名用户
        top_users = self.bean_manager.get_top_users(10)
        if top_users:
            reply_lines = ["📊 当前豆子排行榜："]
            for rank, (username, total_beans) in enumerate(top_users, start=1):
                reply_lines.append(f"第 {rank} 名：{username}，豆子数量：{total_beans}")
            return "\n".join(reply_lines)
        else:
            return "当前还没有用户领取豆子，快来成为第一个领取豆子的人吧！"

    @staticmethod
    def get_simple_description():
        """
        返回简单的功能描述
        """
        return "查看豆子排行榜，显示前 10 名用户的豆子数量。"

    @staticmethod
    def get_detail_description():
        """
        返回详细的功能描述
        """
        return ("【豆子排行榜功能说明】\n"
                "您可以通过发送“排行榜”或“查看排行榜”来查看豆子排行榜。\n"
                "排行榜显示拥有豆子数量最多的前 10 名用户。\n"
                "快来领取豆子，争当排行榜第一名吧！")

    def close(self):
        """
        关闭资源，例如数据库连接。
        """
        self.bean_manager.close_connection()


