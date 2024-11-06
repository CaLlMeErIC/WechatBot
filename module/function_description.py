"""
功能介绍模块，用于输出所有功能的介绍。
"""

import threading
import json
import os


class FunctionModule:
    """
    FunctionModule 类，实现线程安全的单例模式。
    """

    _instance_lock = threading.Lock()
    _instance = None
    # 命令标识，用于标注什么样的命令开头会调用这个功能模块
    # 如@机器人 功能介绍 或者 @机器人 help 就会触发这个模块
    _command_sign = ["介绍", "功能", "help", "功能说明", "说明", "所有功能"]
    _reply_string = None
    # 如果未被激活就不会使用
    is_active = True
    descriptions = {}

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
            print("初始化 功能介绍模块 实例")
            self.load_descriptions()

    def load_descriptions(self):
        """
        从 description.json 文件中加载功能描述。
        """
        description_file = os.path.join('.', 'data', 'description.json')
        try:
            with open(description_file, 'r', encoding='utf-8') as f:
                self.descriptions = json.load(f)
        except Exception as e:
            print(f"加载描述文件时出错: {e}")


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
        return "输出所有功能的介绍"

    @staticmethod
    def get_detail_description():
        """
        返回详细的功能描述
        """
        return "输出所有功能的介绍"

    def get_reply(self):
        """
        返回最终的回复内容
        """
        if not self.descriptions:
            self._reply_string = "抱歉，未能加载功能描述。"
        else:
            reply_lines = []
            for function_name, description in self.descriptions.items():
                reply_lines.append(f"{function_name}：{description}")
            self._reply_string = "\n".join(reply_lines)
        return self._reply_string
