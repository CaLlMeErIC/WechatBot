"""
查询豆子功能模块
"""

from utils.bean_actions import BeanManager  # 假设 BeanManager 类保存在 bean_manager.py 文件中


class FunctionModule:
    """
    FunctionModule 类，实现查询自己豆子的功能。
    """

    _instance = None
    # 命令标识，用于标注什么样的命令会调用这个功能模块
    # 如 @机器人 查询豆子 或者 @机器人 我的豆子 就会触发这个模块
    _command_sign = ["查豆子", "我的豆子"]
    _reply_string = None
    # 模块激活状态
    is_active = True

    def __new__(cls):
        """
        线程安全的单例实现。
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
            print("初始化 FunctionModule 实例（查询豆子）")
            self.bean_manager = BeanManager()

    def get_command_sign(self):
        """
        返回当前模块的命令标识
        """
        return self._command_sign

    def process_messages(self, sender_nickname, content):
        """
        根据发消息人的昵称和消息内容，处理查询豆子的请求。

        Args:
            sender_nickname (str): 发送者的昵称。
            content (str): 消息内容。

        Returns:
            str: 回复消息。
        """
        # 获取用户的豆子数量
        total_beans = self.bean_manager.get_bean_count(sender_nickname)
        self._reply_string = f"{sender_nickname}，您当前的豆子总数是：{total_beans}。"
        return self.get_reply()

    @staticmethod
    def get_simple_description():
        """
        返回简单的功能描述
        """
        return "查询自己当前的豆子数量。"

    @staticmethod
    def get_detail_description():
        """
        返回详细的功能描述
        """
        return ("【查询豆子功能说明】\n"
                "您可以通过发送“查询豆子”或“我的豆子”来查看您当前拥有的豆子数量。\n"
                "豆子可用于参与平台的各种活动，快来看看您拥有多少豆子吧！")

    def get_reply(self):
        """
        返回最终的回复内容
        """
        return self._reply_string

    def close(self):
        """
        关闭资源，例如数据库连接。
        """
        self.bean_manager.close_connection()
