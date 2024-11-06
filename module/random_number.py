"""
功能-生成一个1-100的随机数
"""
import random


class FunctionModule:
    """
    FunctionModule 类，实现线程安全的单例模式。
    """

    _instance = None
    # 命令标识，用于标注什么样的命令开头会调用这个功能模块
    # 如@机器人 测试2 或者如@机器人 test2就会触发这个模块
    _command_sign = ["随机数", "生成随机数"]
    # 如果未激活那么不会使用
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

    def get_command_sign(self):
        """
        返回当前模块的命令标识
        """
        return self._command_sign

    @staticmethod
    def get_simple_description():
        """
        返回简单的功能描述
        """
        return "生成随机数功能"

    @staticmethod
    def get_detail_description():
        """
        返回详细的功能描述
        """
        return "生成一个1到100之间的随机整数并返回。"

    @staticmethod
    def process_messages(_, __):
        """
        根据发消息人的昵称和发消息的内容，制作回复
        """
        random_number = random.randint(1, 100)
        reply_string = f"你生成的随机数是：{random_number}"
        return reply_string
