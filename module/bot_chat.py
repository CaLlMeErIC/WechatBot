"""
使用openapi接口进行聊天的模块
"""
import os
from openai import OpenAI


class FunctionModule:
    """
    ChatGPTModule 类，实现与 OpenAI ChatGPT 模型的聊天互动。
    """

    _instance = None
    # 命令标识，用于标注什么样的命令开头会调用这个功能模块
    # 比如用户发送 "@机器人 聊天" 或 "@机器人 闲聊" 会触发这个模块
    _command_sign = ["聊天"]
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
            print("初始化 ChatGPTModule 实例")
            # 在这里初始化 OpenAI API 设置
            self.api_key = 'sk-8AZopg1uvf41Rthisisnottruekkey55EjUfhimGyb8HLjc2'  # 请替换为您的实际 API 密钥
            self.api_base = 'https://api.openai-proxy.org/v1'  # API 基础 URL，包含 /v1 后缀
            self.model = 'gpt-3.5-turbo'  # 使用的模型名称
            self.max_windows = 5  # 每个用户的上下文消息最多保留 5 条
            self.max_users = 100  # 最多保存 100 个用户的会话
            self.user_contexts = {}  # 用于保存用户的上下文
            self.client = OpenAI(
                # openai系列的sdk，包括langchain，都需要这个/v1的后缀
                base_url=self.api_base,
                api_key=self.api_key,
            )

    def get_command_sign(self):
        """
        返回当前模块的命令标识
        """
        return self._command_sign

    def process_messages(self, sender_nickname, content, directly=False):
        """
        根据发消息人的昵称和消息内容，与 ChatGPT 进行对话。

        Args:
            sender_nickname (str): 发送者的昵称。
            content (str): 消息内容。
            directly : 判断是否是直接发送消息聊天还是通过命令调用聊天

        Returns:
            str: 回复消息。
        """
        # 去掉命令标识，获取实际用户输入
        user_message = content
        if not directly:
            # 如果是通过命令调用聊天的话
            for sign in self._command_sign:
                if content.startswith(sign):
                    user_message = content[len(sign):].strip()
                    break

        # 如果用户没有输入内容，则提示用户输入
        if not user_message:
            self._reply_string = "请在命令后添加您想说的话，例如：'聊天 你好！'"
            return self.get_reply()

        # 管理用户上下文
        # 检查用户是否在上下文字典中
        if sender_nickname not in self.user_contexts:
            # 如果用户数量超过最大值，则删除最早的用户
            if len(self.user_contexts) >= self.max_users:
                first_user = next(iter(self.user_contexts))
                del self.user_contexts[first_user]
            # 初始化该用户的上下文列表
            self.user_contexts[sender_nickname] = []

        # 获取该用户的上下文
        user_context = self.user_contexts[sender_nickname]

        # 添加新消息到上下文
        user_context.append({'role': 'user', 'content': user_message})
        # 只保留最近的 max_windows * 2 条消息（因为包括 AI 的回复）
        if len(user_context) > self.max_windows * 2:
            user_context = user_context[-self.max_windows * 2:]

        # 更新上下文
        self.user_contexts[sender_nickname] = user_context

        # 调用 OpenAI ChatCompletion API 进行对话
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=user_context
            )
            # 提取 AI 回复的内容
            ai_reply = response.choices[0].message.content

            # 将 AI 的回复也加入上下文
            user_context.append({'role': 'assistant', 'content': ai_reply})
            # 同样只保留最近的 max_windows * 2 条消息
            if len(user_context) > self.max_windows * 2:
                user_context = user_context[-self.max_windows * 2:]
            # 更新上下文
            self.user_contexts[sender_nickname] = user_context

            self._reply_string = ai_reply
        except Exception as e:
            # 处理异常
            self._reply_string = f"抱歉，{sender_nickname}，发生错误：{str(e)}"
        return self.get_reply()

    @staticmethod
    def get_simple_description():
        """
        返回简单的功能描述
        """
        return "与 ChatGPT 进行聊天互动"

    @staticmethod
    def get_detail_description():
        """
        返回详细的功能描述
        """
        return ("【聊天功能说明】\n"
                "您可以通过发送“聊天”或“闲聊”作为开头，再加上您的消息，与 ChatGPT 进行对话。\n"
                "例如：“聊天 今天的天气怎么样？”\n"
                "ChatGPT 将会回复您的问题。")

    def get_reply(self):
        """
        返回最终的回复内容
        """
        return self._reply_string

    def close(self):
        """
        如果需要，关闭与 OpenAI 的连接（在这个例子中不需要）。
        """
        pass


if __name__ == "__main__":
    chat_module = FunctionModule()
    # 模拟多个用户的对话
    users = ["Alice", "Bob", "Charlie", "David", "Eve"]
    messages = [
        "聊天 你好，今天天气怎么样？",
        "闲聊 给我讲个笑话吧！",
        "聊天 你知道OpenAI吗？",
        "闲聊 讲个故事吧。",
        "聊天 谈谈人工智能的发展。"
    ]
    for sender, message in zip(users, messages):
        reply = chat_module.process_messages(sender, message)
        print(f"{sender}: {message}")
        print(f"ChatGPT: {reply}")

    # 测试超过用户上限的情况
    for i in range(101):
        sender = f"User_{i}"
        message = "聊天 测试用户上限。"
        reply = chat_module.process_messages(sender, message)
        print(f"{sender}: {message}")
        print(f"ChatGPT: {reply}")
    print(f"当前用户数量：{len(chat_module.user_contexts)}")  # 应该不超过 100
