import random
# 请确保 BeanManager 类的代码已经正确导入或者定义
from utils.bean_actions import BeanManager  # 导入你的 BeanManager 类


class FunctionModule:
    """
    FunctionModule 类，实现线程安全的单例模式。
    """

    _instance = None
    # 命令标识，用于标注什么样的命令开头会调用这个功能模块
    # 如@机器人 21点 或者@机器人 blackjack就会触发这个模块
    _command_sign = ["21点", "blackjack", "要牌", "停牌"]
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
            # 用户游戏状态存储，key为用户昵称，value为玩家状态
            self.user_states = {}
            # 初始化一副牌
            self.deck = self.create_deck()
            self.help_commands_set = set()
            for command in self._command_sign:
                # 构建帮助命令的各种可能格式
                help_variants = [
                    f"{command} 介绍",
                    f"{command} 帮助",
                    f"{command} 说明",
                    f"{command} help",
                    f"{command} 功能"
                ]
                # 将所有变体转换为小写并添加到集合中，确保大小写不敏感
                for variant in help_variants:
                    self.help_commands_set.add(variant.lower())
            # 初始化 BeanManager 实例
            self.bean_manager = BeanManager()

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
        return "21点游戏"

    @staticmethod
    def get_detail_description():
        """
        返回详细的功能描述
        """
        description_string = """一个简单的21点（Blackjack）游戏。你可以发送'开始21点'来开始游戏，'要牌'来获取一张新牌，'停牌'来结束当前回合。
玩家与庄家比较牌面点数，最接近21点而不爆牌（超过21点）的玩家获胜。庄家在16点或以下必须继续要牌，17点或以上则停牌。
A：两种方式，可以作为11点（软手），亦作为1点（硬手）。2-10：牌面点数即其数值。J、Q、K：每张牌的点数为10点。"""
        return description_string.strip()

    def process_messages(self, sender_nickname, content):
        """
        根据发消息人的昵称和发消息的内容，制作回复
        """
        # 初始化玩家状态，如果不存在
        if sender_nickname not in self.user_states:
            self.user_states[sender_nickname] = {
                'player_hand': [],
                'dealer_hand': [],
                'in_game': False,
                'deck': [],
                'bet_amount': None  # 押注金额，None 表示未押注
            }

        user_state = self.user_states[sender_nickname]
        reply_string = ""
        content_lower = content.strip().lower()

        if content_lower in self.help_commands_set:
            return self.get_detail_description()

        # 解析用户输入，检查是否包含押注金额
        if any(content_lower.startswith(cmd) for cmd in ['21点', 'blackjack']):
            # 解析押注金额
            parts = content.strip().split()
            bet_amount = None
            if len(parts) >= 2:
                # 尝试解析押注金额
                bet_input = parts[1]
                try:
                    # 支持多种押注指令，如'押1000'，'赌1000'，或直接'1000'
                    if bet_input.startswith(('押', '赌')):
                        bet_amount = int(bet_input[1:])
                    else:
                        bet_amount = int(bet_input)
                except ValueError:
                    reply_string = "请输入有效的押注金额，例如：'21点 押1000'，或直接发送'21点'开始游戏。"
                    return reply_string

            if user_state['in_game']:
                reply_string = "你已经在游戏中了！"
            else:
                if bet_amount is not None:
                    # 用户选择押注，检查豆子余额
                    total_beans = self.bean_manager.get_bean_count(sender_nickname)
                    if total_beans < bet_amount:
                        reply_string = f"你的豆子不足！当前豆子：{total_beans}，需要押注：{bet_amount}"
                        return reply_string
                    elif bet_amount <= 0:
                        reply_string = "押注金额必须大于0！"
                        return reply_string
                    # 扣除押注金额
                    self.bean_manager.add_beans(sender_nickname, -bet_amount)
                    user_state['bet_amount'] = bet_amount
                else:
                    # 用户未选择押注，设置押注金额为 None
                    user_state['bet_amount'] = None

                # 重新创建并洗牌
                user_state['deck'] = self.create_deck()
                random.shuffle(user_state['deck'])
                user_state['player_hand'] = []
                user_state['dealer_hand'] = []
                user_state['in_game'] = True
                # 玩家发两张初始牌
                user_state['player_hand'].append(self.draw_card(user_state['deck']))
                user_state['player_hand'].append(self.draw_card(user_state['deck']))
                # 庄家发两张牌，一张明牌，一张暗牌
                user_state['dealer_hand'].append(self.draw_card(user_state['deck']))
                user_state['dealer_hand'].append(self.draw_card(user_state['deck']))
                player_total = self.calculate_total(user_state['player_hand'])
                dealer_visible_card = user_state['dealer_hand'][0]

                if bet_amount is not None:
                    potential_win = bet_amount * 2 * 0.95  # 计算可能的赢取金额，扣除5%抽水
                    reply_string = (
                        f"游戏开始！你押注了 {bet_amount} 豆子，可赢取 {int(potential_win)} 豆子（扣除5%抽水）。\n"
                    )
                else:
                    reply_string = "游戏开始！\n"

                reply_string += (
                    f"你的手牌是：{self.format_hand(user_state['player_hand'])}，总点数：{player_total}。\n"
                    f"庄家明牌：{dealer_visible_card}。\n"
                    "你可以选择'要牌'或者'停牌'。"
                )

        elif content_lower == '要牌':
            if not user_state['in_game']:
                reply_string = "你还没有开始游戏，请发送'21点'或'21点 押注金额'来开始游戏。"
            else:
                user_state['player_hand'].append(self.draw_card(user_state['deck']))
                player_total = self.calculate_total(user_state['player_hand'])
                if player_total > 21:
                    reply_string = (
                        f"你抽到了 {self.format_hand([user_state['player_hand'][-1]])}，你的手牌是：{self.format_hand(user_state['player_hand'])}，总点数 {player_total}。\n"
                        "爆掉了！你输了！\n"
                    )
                    if user_state['bet_amount'] is not None:
                        reply_string += f"你失去了 {user_state['bet_amount']} 豆子。\n"
                    reply_string += "游戏结束。"
                    user_state['in_game'] = False
                    user_state['bet_amount'] = None
                elif player_total == 21:
                    reply_string = (
                        f"你抽到了 {self.format_hand([user_state['player_hand'][-1]])}，你的手牌是：{self.format_hand(user_state['player_hand'])}，总点数 {player_total}。\n"
                        "恭喜你，Blackjack！你赢了！\n"
                    )
                    if user_state['bet_amount'] is not None:
                        winnings = int(user_state['bet_amount'] * 2 * 0.95)
                        self.bean_manager.add_beans(sender_nickname, winnings)
                        reply_string += f"你赢得了 {winnings} 豆子（扣除5%抽水）。\n"
                    reply_string += "游戏结束。"
                    user_state['in_game'] = False
                    user_state['bet_amount'] = None
                else:
                    reply_string = (
                        f"你抽到了 {self.format_hand([user_state['player_hand'][-1]])}，你的手牌是：{self.format_hand(user_state['player_hand'])}，总点数 {player_total}。\n"
                        "你可以继续选择'要牌'或者'停牌'。"
                    )

        elif content_lower == '停牌':
            if not user_state['in_game']:
                reply_string = "你还没有开始游戏，请发送'21点'或'21点 押注金额'来开始游戏。"
            else:
                player_total = self.calculate_total(user_state['player_hand'])
                # 庄家揭开暗牌并进行操作
                dealer_hand = user_state['dealer_hand']
                dealer_total = self.calculate_total(dealer_hand)
                while dealer_total < 17:
                    dealer_card = self.draw_card(user_state['deck'])
                    dealer_hand.append(dealer_card)
                    dealer_total = self.calculate_total(dealer_hand)

                reply_string = (
                    f"你的手牌是：{self.format_hand(user_state['player_hand'])}，总点数 {player_total}。\n"
                    f"庄家的手牌是：{self.format_hand(dealer_hand)}，总点数 {dealer_total}。\n"
                )
                if dealer_total > 21 or player_total > dealer_total:
                    reply_string += "恭喜你，你赢了！\n"
                    if user_state['bet_amount'] is not None:
                        winnings = int(user_state['bet_amount'] * 2 * 0.95)
                        self.bean_manager.add_beans(sender_nickname, winnings)
                        reply_string += f"你赢得了 {winnings} 豆子（扣除5%抽水）。\n"
                elif player_total < dealer_total:
                    reply_string += "很遗憾，你输了！\n"
                    if user_state['bet_amount'] is not None:
                        reply_string += f"你失去了 {user_state['bet_amount']} 豆子。\n"
                else:
                    reply_string += "平局！\n"
                    if user_state['bet_amount'] is not None:
                        # 返还押注金额
                        self.bean_manager.add_beans(sender_nickname, user_state['bet_amount'])
                        reply_string += f"你的押注 {user_state['bet_amount']} 豆子已返还。\n"
                reply_string += "游戏结束。"
                user_state['in_game'] = False
                user_state['bet_amount'] = None
            # 清空手牌，不清空牌库
            user_state['player_hand'] = []
            user_state['dealer_hand'] = []

        else:
            reply_string = "无法识别的指令。你可以发送'21点'或'21点 押注金额'来开始游戏，'要牌'来获取一张新牌，'停牌'来结束当前回合。"

        return reply_string

    @staticmethod
    def create_deck():
        """
        创建一副52张的扑克牌
        """
        suits = ['♠️', '♥️', '♣️', '♦️']
        ranks = ['A'] + [str(n) for n in range(2, 11)] + ['J', 'Q', 'K']
        deck = []
        for suit in suits:
            for rank in ranks:
                deck.append(f"{suit}{rank}")
        return deck

    def draw_card(self, deck):
        """
        从牌堆中抽一张牌
        """
        if len(deck) == 0:
            # 如果牌堆没牌了，重新创建并洗牌
            deck.extend(self.create_deck())
            random.shuffle(deck)
        return deck.pop()

    @staticmethod
    def calculate_total(hand):
        """
        计算手牌的总点数，处理A的情况（A可以是1也可以是11）
        """
        total = 0
        aces = 0
        for card in hand:
            rank = card[2:] if card[1] in ['️'] else card[1:]  # 处理可能的特殊字符
            if rank in ['J', 'Q', 'K']:
                total += 10
            elif rank == 'A':
                aces += 1
                total += 11
            else:
                total += int(rank)
        # 如果总点数超过21，且有A，把A当1处理
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    @staticmethod
    def format_hand(hand):
        """
        格式化手牌输出
        """
        return '、'.join(hand)

    @staticmethod
    def get_card_value(card):
        """
        获取单张牌的点数, 用于显示庄家的明牌点数
        """
        rank = card[2:] if card[1] in ['️'] else card[1:]
        if rank in ['J', 'Q', 'K']:
            return 10
        elif rank == 'A':
            return 11
        else:
            return int(rank)
