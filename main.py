"""
启动微信机器人并导入不同的功能模块
"""
import traceback
import threading
import queue
import logging
import itchat
from itchat.content import TEXT
from utils.scan_module import get_command_module_dict

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(threadName)s %(message)s')


class WeChatBot:
    """
    微信机器人
    """

    def __init__(self):
        # 功能模块映射，根据消息前缀映射到对应的模块名
        self.module_mapping = get_command_module_dict()

        # 定义消息队列
        self.message_queue = queue.Queue()
        self.num_worker_threads = 5  # 工作线程数

        # 初始化发送者锁字典和锁
        self.sender_locks = {}
        self.sender_locks_lock = threading.Lock()

        self.handle_private_message = None
        self.handle_group_message = None

        # 初始化 itchat
        itchat.auto_login(hotReload=False)

        # 注册消息处理函数
        self.register_handlers()

        # 启动消息处理线程
        self.start_worker_threads()

    def register_handlers(self):
        """
        注册消息处理器
        """

        # 由于装饰器的使用，我们需要将函数定义在这里，并使用 self 作为参数

        @itchat.msg_register(TEXT, isFriendChat=True)
        def handle_private_message(msg):
            # 将消息放入队列，不直接处理
            self.message_queue.put(('private', msg))

        @itchat.msg_register(TEXT, isGroupChat=True)
        def handle_group_message(msg):
            # 将消息放入队列，不直接处理
            if msg['IsAt']:
                self.message_queue.put(('group', msg))

        # 将函数绑定到实例
        self.handle_private_message = handle_private_message
        self.handle_group_message = handle_group_message

    def start_worker_threads(self):
        """
        启动工作线程
        """
        for i in range(self.num_worker_threads):
            thread_pool = threading.Thread(target=self.message_worker, name=f'Worker-{i + 1}')
            thread_pool.daemon = True
            thread_pool.start()

    def message_worker(self):
        """
        通过多线程和队列处理信息，使用锁确保一时间
        同一人只能占用一个线程
        """
        while True:
            try:
                msg_type, msg_data = self.message_queue.get(timeout=1)
                sender_id = msg_data['FromUserName']

                # 获取或创建发送者的锁
                with self.sender_locks_lock:
                    if sender_id not in self.sender_locks:
                        self.sender_locks[sender_id] = threading.Lock()
                    sender_lock = self.sender_locks[sender_id]

                # 使用发送者的锁，确保同一时间只有一个线程处理该发送者的消息
                with sender_lock:
                    if msg_type == 'private':
                        self.handle_private_message_worker(msg_data)
                    elif msg_type == 'group':
                        self.handle_group_message_worker(msg_data)

                self.message_queue.task_done()
            except queue.Empty:
                continue
            except Exception as exception:
                logging.error("消息处理时发生异常：%s", exception)

    def handle_private_message_worker(self, msg):
        """
        处理私聊消息
        """
        sender = msg['User']
        nickname = sender['NickName']
        content = msg['Text']
        logging.info("私聊消息 - 来自 %s：%s", nickname, content)
        reply = self.generate_reply(nickname, content)
        itchat.send(reply, toUserName=sender['UserName'])

    def handle_group_message_worker(self, msg):
        """
        处理群消息
        """
        if msg['IsAt']:
            group_name = msg['User']['NickName']
            sender_nickname = msg['ActualNickName']
            actual_content = msg['Content']
            # 获取自己的昵称
            my_nickname = itchat.search_friends()['NickName']
            # 去除@信息，提取实际内容
            content = actual_content.replace(f'@{my_nickname}', '').strip()
            logging.info("群聊消息 - %s 中 @%s 说：%s", group_name, sender_nickname, content)
            reply_content = self.generate_reply(sender_nickname, content)
            reply = f"@{sender_nickname} {reply_content}"
            itchat.send(reply, toUserName=msg['FromUserName'])

    def generate_reply(self, nickname, content):
        """
        调用不同的功能模块，处理消息生成回复
        """
        try:
            command_sign = content.split(" ")[0]
            if command_sign in self.module_mapping:
                module_instance = self.module_mapping[command_sign]
                reply = module_instance.process_messages(nickname, content)
            else:
                # 如果没有特殊命令，就直接调用聊天模块
                module_instance = self.module_mapping["聊天"]
                reply = module_instance.process_messages(nickname, content, directly=True)
            return reply
        except Exception as exception:
            print(traceback.format_exc())
            logging.error("处理模块时发生异常：%s", exception)
            return '抱歉，出现了一些错误。'

    @staticmethod
    def run():
        """
        开始运行机器人
        """
        while True:
            try:
                itchat.run(blockThread=True)
            except KeyboardInterrupt:
                # 如果用户手动中断，退出循环
                logging.info("微信机器人已停止")
                break
            except Exception as exception:
                logging.error("主循环发生异常：%s", exception)
                if 'request' in str(exception) or 'Logout' in str(exception) or 'login' in str(exception).lower():
                    try:
                        itchat.auto_login(hotReload=True)
                        logging.info("重新登录成功")
                    except Exception as login_exception:
                        logging.error("重新登录失败：%s", login_exception)
                        print("无法重新登录，程序即将退出")
                        break  # 退出循环，不再尝试重新登录
                else:
                    logging.error("无法识别的异常，未能重新登录：%s", exception)
                    print("遇到无法识别的异常，程序即将退出")
                    break  # 退出循环，不再尝试


if __name__ == '__main__':
    bot = WeChatBot()
    bot.run()
