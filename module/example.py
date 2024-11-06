"""
处理微信消息回复的模版模块
"""


class FunctionModule:
    """
    FunctionModule 类，实现线程安全的单例模式。
    """

    _instance = None
    # 命令标识，用于标注什么样的命令开头会调用这个功能模块
    # 如@机器人 测试1 或者如@机器人 test1就会触发这个模块
    _command_sign = ["测试1", "test1"]
    _reply_string = None
    # 如果未被激活就不会使用
    is_active = False

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
            print("初始化 FunctionModule 实例")

    def get_command_sign(self):
        """
        返回当前模块的命令标识
        """
        return self._command_sign

    def process_messages(self, sender_nickname, content):
        """
        根据发消息人的昵称和发消息的内容，制作回复
        """
        return self.get_reply()

    @staticmethod
    def get_simple_description():
        """
        返回简单的功能描述
        """
        return "这是测试1"

    @staticmethod
    def get_simple_description():
        """
        返回简单的功能描述
        """
        return "测试1"

    @staticmethod
    def get_detail_description():
        """
        返回详细的功能描述
        """
        return "这是测试1！"

    def get_reply(self):
        """
        返回最终的回复内容
        """
        self._reply_string = "这是一个测试1"
        return self._reply_string
