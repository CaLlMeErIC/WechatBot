"""
玩百家乐的功能模块，增加了押豆子的功能
"""
import random
# 请确保 BeanManager 类的代码已经正确导入或者定义
from utils.bean_actions import BeanManager  # 导入你的 BeanManager 类


class FunctionModule:
    """
    FunctionModule 类，实现线程安全的单例模式。
    """

    _instance = None
    # 命令标识，用于标注什么样的命令开头会调用这个功能模块
    # 如@机器人 百家乐 或者@机器人 baccarat就会触发这个模块
    _command_sign = ["百家乐", "baccarat", "下注", "停止"]
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
            # 帮助命令集合
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
        return "百家乐游戏模块"

    @staticmethod
    def get_detail_description():
        """
        返回详细的功能描述
        """
        description_string = """
        一个简单的百家乐（Baccarat）游戏。你可以发送'百家乐'来开始游戏。
        游戏开始后，你可以选择下注，玩家的目标是预测哪一方的手牌点数总和最接近9点。
        A（Ace）：计为1点。
        2-9：按牌面数字计算点数。
        10、J、Q、K：计为0点
        将两张或三张牌的点数相加，得出的总点数个位数即为该手的点数。例如，牌点总和为15点，则实际点数为5点。
        系统将按照百家乐的规则进行发牌和算点，并告知你结果。
        如果庄家或闲家在前两张牌的总点数为8或9点，称为“自然胜利”，游戏立即结束，该方获胜。否则需要补牌。
        闲家补牌规则：如果闲家的点数为0-5点，必须补第三张牌。如果闲家的点数为6或7点，则不补牌（停牌）
        庄家是否补牌取决于庄家的点数和闲家是否补牌及其第三张牌的点数。具体规则如下：
        庄家当前点数/闲家第三张牌点数/庄家动作:\n
        0-2/不论/必须补牌\n
        3/不为8/必须补牌\n
        4/2-7/必须补牌\n
        5/4-7/必须补牌\n
        6/6或7/必须补牌\n
        7/不补牌/停牌\n
        8-9/不论/停牌
        """
        return description_string.strip()

    def process_messages(self, sender_nickname, content):
        """
        根据发消息人的昵称和发消息的内容，制作回复
        """
        # 初始化玩家状态，如果不存在
        if sender_nickname not in self.user_states:
            self.user_states[sender_nickname] = {
                'player_hand': [],
                'banker_hand': [],
                'in_game': False,
                'bet': None,
                'bet_amount': None,
                'deck': []
            }

        user_state = self.user_states[sender_nickname]
        reply_string = ""
        content_lower = content.strip().lower()

        if content_lower in self.help_commands_set:
            return self.get_detail_description()

        # 解析用户输入，检查是否包含押注金额
        if any(content_lower.startswith(cmd) for cmd in ['百家乐', 'baccarat']):
            if user_state['in_game']:
                reply_string = "你已经在游戏中了！请先完成当前游戏。"
            else:
                # 重新创建并洗牌
                user_state['deck'] = self.create_deck()
                random.shuffle(user_state['deck'])
                user_state['player_hand'] = []
                user_state['banker_hand'] = []
                user_state['bet'] = None
                user_state['bet_amount'] = None
                user_state['in_game'] = True
                reply_string = (
                    "欢迎来到百家乐游戏！\n"
                    "请下注，你可以选择：'闲'、'庄'、'和'。\n"
                    "例如，输入'下注 闲 押1000'"
                )

        elif content.strip().startswith('下注'):
            if not user_state['in_game']:
                reply_string = "你还没有开始游戏，请发送'百家乐'来开始游戏。"
            else:
                # 解析下注选项和押注金额
                parts = content.strip().split()
                if len(parts) >= 3:
                    bet_option = parts[1]
                    if bet_option not in ['闲', '庄', '和']:
                        reply_string = "无效的下注选项。请下注'闲'、'庄'或'和'。"
                        return reply_string
                    # 解析押注金额
                    bet_input = parts[2]
                    try:
                        if bet_input.startswith(('押', '赌')):
                            bet_amount = int(bet_input[1:])
                        else:
                            bet_amount = int(bet_input)
                    except ValueError:
                        reply_string = "请输入有效的押注金额，例如：'下注 闲 押1000'。"
                        return reply_string
                    if bet_amount <= 0:
                        reply_string = "押注金额必须大于0！"
                        return reply_string
                    # 检查豆子余额
                    total_beans = self.bean_manager.get_bean_count(sender_nickname)
                    if total_beans < bet_amount:
                        reply_string = f"你的豆子不足！当前豆子：{total_beans}，需要押注：{bet_amount}"
                        return reply_string
                    # 扣除押注金额
                    self.bean_manager.add_beans(sender_nickname, -bet_amount)
                    user_state['bet_amount'] = bet_amount
                    user_state['bet'] = bet_option
                    # 发牌
                    user_state['player_hand'].append(self.draw_card(user_state['deck']))
                    user_state['player_hand'].append(self.draw_card(user_state['deck']))
                    user_state['banker_hand'].append(self.draw_card(user_state['deck']))
                    user_state['banker_hand'].append(self.draw_card(user_state['deck']))
                    # 计算初始点数
                    player_total = self.calculate_hand_value(user_state['player_hand'])
                    banker_total = self.calculate_hand_value(user_state['banker_hand'])

                    reply_string = (
                        f"你下注的是：'{bet_option}' {bet_amount} 豆子。\n"
                        f"已扣除你的押注金额 {bet_amount} 豆子。\n"
                        f"闲家的手牌是：{self.format_hand(user_state['player_hand'])}，点数为 {player_total}。\n"
                        f"庄家的手牌是：{self.format_hand(user_state['banker_hand'])}，点数为 {banker_total}。\n"
                    )

                    # 检查是否有自然胜利
                    if player_total >= 8 or banker_total >= 8:
                        # 自然胜利
                        result = self.determine_winner(sender_nickname, player_total, banker_total)
                        reply_string += f"{result}\n游戏结束。"
                        user_state['in_game'] = False
                        user_state['bet_amount'] = None
                    else:
                        # 玩家是否需要第三张牌
                        if player_total <= 5:
                            user_state['player_hand'].append(self.draw_card(user_state['deck']))
                            reply_string += f"闲家抽了第三张牌：{user_state['player_hand'][-1]}。\n"
                            player_total = self.calculate_hand_value(user_state['player_hand'])

                        # 根据庄家规则决定是否抽牌
                        banker_draw = self.banker_should_draw(user_state['banker_hand'],
                                                              user_state['player_hand'][-1] if len(
                                                                  user_state['player_hand']) == 3 else None)
                        if banker_draw:
                            user_state['banker_hand'].append(self.draw_card(user_state['deck']))
                            reply_string += f"庄家抽了第三张牌：{user_state['banker_hand'][-1]}。\n"
                            banker_total = self.calculate_hand_value(user_state['banker_hand'])

                        # 最终点数
                        reply_string += (
                            f"闲家的最终手牌是：{self.format_hand(user_state['player_hand'])}，点数为 {player_total}。\n"
                            f"庄家的最终手牌是：{self.format_hand(user_state['banker_hand'])}，点数为 {banker_total}。\n"
                        )
                        # 判断胜负
                        result = self.determine_winner(sender_nickname, player_total, banker_total)
                        reply_string += f"{result}\n游戏结束。"
                        user_state['in_game'] = False
                        user_state['bet_amount'] = None
                else:
                    # 参数不足
                    reply_string = "请输入下注选项和押注金额，例如：'下注 闲 押1000'。"

        elif content.strip() == '停止':
            if user_state['in_game']:
                if user_state['bet_amount'] is not None:
                    # 返还押注金额
                    self.bean_manager.add_beans(sender_nickname, user_state['bet_amount'])
                    reply_string = f"游戏已停止，返还你的押注金额 {user_state['bet_amount']} 豆子。谢谢参与！"
                    user_state['bet_amount'] = None
                else:
                    reply_string = "游戏已停止，谢谢参与！"
                user_state['in_game'] = False
            else:
                reply_string = "你当前没有正在进行的游戏。"

        else:
            reply_string = "无法识别的指令。你可以发送'百家乐'来开始游戏，或发送'下注 闲/庄/和 押注金额'来下注。"

        return reply_string

    @staticmethod
    def create_deck():
        """
        创建一副52张的扑克牌，包含花色和点数
        """
        suits = ['♠', '♥', '♣', '♦']
        ranks = [str(n) for n in range(1, 10)] + ['10', 'J', 'Q', 'K']
        deck = []
        for _ in range(6):  # 使用6副牌
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
    def calculate_card_value(card):
        """
        计算单张牌的点数（百家乐规则）
        """
        # 考虑花色占一个字符，提取牌面的数字或字母
        rank = card[1:]
        if rank in ['10', 'J', 'Q', 'K']:
            return 0
        else:
            return int(rank)

    def calculate_hand_value(self, hand):
        """
        计算手牌的点数总和（百家乐规则）
        """
        total = sum(self.calculate_card_value(card) for card in hand)
        return total % 10

    @staticmethod
    def format_hand(hand):
        """
        格式化手牌输出
        """
        return '、'.join(hand)

    def determine_winner(self, sender_nickname, player_total, banker_total):
        """
        判断胜负，并调整豆子
        """
        bet_option = self.user_states[sender_nickname]['bet']
        bet_amount = self.user_states[sender_nickname]['bet_amount']
        if player_total > banker_total:
            winner = '闲'
        elif player_total < banker_total:
            winner = '庄'
        else:
            winner = '和'

        result_message = f"结果是：{winner}赢！"

        if winner == '和':
            if bet_option == '和':
                winnings = bet_amount * 9  # 1:8 赔率，赢得8倍，加上本金共9倍
                self.bean_manager.add_beans(sender_nickname, int(winnings))
                result_message += f"恭喜你，你赢了！你赢得了 {int(winnings - bet_amount)} 豆子。"
            else:
                # 返还押注金额
                self.bean_manager.add_beans(sender_nickname, bet_amount)
                result_message += f"你下注的是'{bet_option}'，与结果不同，押注金额 {bet_amount} 豆子已返还。"
        else:
            if bet_option == winner:
                # 玩家胜利
                if winner == '闲':
                    winnings = bet_amount * 2  # 1:1 赔率
                elif winner == '庄':
                    winnings = bet_amount * 1.95  # 1:0.95 赔率，扣除5%佣金
                self.bean_manager.add_beans(sender_nickname, int(winnings))
                result_message += f"恭喜你，你赢了！你赢得了 {int(winnings - bet_amount)} 豆子。"
            else:
                # 玩家失败
                result_message += f"很遗憾，你输了！失去了 {bet_amount} 豆子。"

        return result_message

    def banker_should_draw(self, banker_hand, player_third_card):
        """
        根据庄家的规则决定是否应该抽第三张牌
        """
        banker_total = self.calculate_hand_value(banker_hand)
        if len(banker_hand) == 2:
            if banker_total <= 2:
                return True
            elif banker_total == 3:
                return player_third_card is None or self.calculate_card_value(player_third_card) != 8
            elif banker_total == 4:
                return player_third_card is not None and 2 <= self.calculate_card_value(player_third_card) <= 7
            elif banker_total == 5:
                return player_third_card is not None and 4 <= self.calculate_card_value(player_third_card) <= 7
            elif banker_total == 6:
                return player_third_card is not None and self.calculate_card_value(player_third_card) in [6, 7]
            else:
                return False
        else:
            return False
