"""
领豆子功能模块
"""

from utils.bean_actions import BeanManager  # 假设 BeanManager 类保存在 bean_manager.py 文件中
import datetime


class FunctionModule:
    """
    CollectBeansModule 类，实现领取豆子的功能，继承自 FunctionModule。
    """

    _instance = None
    # 命令标识，用于标注什么样的命令开头会调用这个功能模块
    # 比如用户发送 "@机器人 领豆子" 或 "@机器人 我要领豆子" 会触发这个模块
    _command_sign = ["领豆子", "我要领豆子"]
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
            print("初始化 CollectBeansModule 实例")
            self.bean_manager = BeanManager()

    def get_command_sign(self):
        """
        返回当前模块的命令标识
        """
        return self._command_sign

    def process_messages(self, sender_nickname, content):
        """
        根据发消息人的昵称和消息内容，处理领取豆子的请求。

        Args:
            sender_nickname (str): 发送者的昵称。
            content (str): 消息内容。

        Returns:
            str: 回复消息。
        """
        # 调用 BeanManager 的 collect_beans 方法处理领取逻辑
        success = self.bean_manager.collect_beans(sender_nickname)
        if success:
            # 领取成功，获取当前豆子数量
            total_beans = self.bean_manager.get_bean_count(sender_nickname)
            self._reply_string = f"🎉 恭喜，{sender_nickname}，您已成功领取 10000 个豆子！\n当前豆子总数：{total_beans}。"
        else:
            # 领取失败，计算下次可领取时间
            next_collect_time = self.get_next_collect_time(sender_nickname)
            next_time_str = next_collect_time.strftime("%Y-%m-%d %H:%M:%S")
            self._reply_string = f"抱歉，{sender_nickname}，您距离上次领取不足一周，无法领取豆子。\n下次可领取时间：{next_time_str}。"
        return self.get_reply()

    def get_next_collect_time(self, username):
        """
        获取用户下次可领取豆子的时间。

        Args:
            username (str): 用户名。

        Returns:
            datetime: 下次可领取时间。
        """
        cursor = self.bean_manager.conn.cursor()
        cursor.execute('SELECT last_collect_time FROM user_beans WHERE username = ?', (username,))
        result = cursor.fetchone()
        if result:
            last_collect_time_str = result[0]
            last_collect_time = datetime.datetime.fromisoformat(last_collect_time_str)
            next_collect_time = last_collect_time + datetime.timedelta(weeks=1)
            return next_collect_time
        else:
            # 如果用户不存在，立即可领取
            return datetime.datetime.now()

    @staticmethod
    def get_simple_description():
        """
        返回简单的功能描述
        """
        return "可以每周领取一次豆子"

    @staticmethod
    def get_detail_description():
        """
        返回详细的功能描述
        """
        return ("【领取豆子功能说明】\n"
                "您可以通过发送“领豆子”或“我要领豆子”来领取豆子。\n"
                "每位用户每周只能领取一次，每次可获得 10000 个豆子。\n"
                "豆子可以用于参与平台的各种活动，快来领取吧！")

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

