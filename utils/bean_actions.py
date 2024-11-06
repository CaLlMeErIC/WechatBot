"""
用于处理豆子的类
"""
import os
import sqlite3
import datetime

# 全局定义数据库路径
DB_DIRECTORY = './data/'
DB_PATH = os.path.join(DB_DIRECTORY, 'beans.db')


class BeanManager:
    """
    处理豆子相关功能的类，采用单例模式。
    """
    _instance = None  # 用于存储单例实例
    conn = None  # 用于存储数据库连接

    def __new__(cls):
        if cls._instance is None:
            # 如果实例不存在，创建一个新的实例
            cls._instance = super(BeanManager, cls).__new__(cls)
            # 创建并保存数据库连接
            cls._instance.conn = sqlite3.connect(DB_PATH,check_same_thread=False)
            # 在第一次创建实例后，初始化数据库
            cls._instance.init_db()
            print("初始化 BeanManager 单例实例")
        return cls._instance

    def init_db(self):
        """
        初始化数据库，创建用户豆子表（如果尚未创建）。
        """
        # 如果目录不存在，创建目录
        if not os.path.exists(DB_DIRECTORY):
            os.makedirs(DB_DIRECTORY)

        # 使用实例的连接
        cursor = self.conn.cursor()

        # 创建表（如果不存在）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_beans (
                username TEXT PRIMARY KEY,
                last_collect_time TEXT,
                total_beans INTEGER
            )
        ''')
        self.conn.commit()

    def collect_beans(self, username):
        """
        处理用户领取豆子的请求。

        如果用户上次领取豆子的时间距离现在超过一周，则允许领取并增加豆子数量；
        否则，提示领取失败。

        Args:
            username (str): 用户名。

        Returns:
            bool: 如果成功领取豆子，返回 True；否则返回 False。
        """
        cursor = self.conn.cursor()

        # 确保表已创建（如果未调用 init_db，这一步保证表存在）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_beans (
                username TEXT PRIMARY KEY,
                last_collect_time TEXT,
                total_beans INTEGER
            )
        ''')

        # 查询用户数据
        cursor.execute('SELECT last_collect_time, total_beans FROM user_beans WHERE username = ?', (username,))
        result = cursor.fetchone()

        if result:
            # 如果用户存在，获取上次领取时间和豆子总数
            last_collect_time_str, total_beans = result
            last_collect_time = datetime.datetime.fromisoformat(last_collect_time_str)
        else:
            # 如果用户不存在，初始化数据
            last_collect_time = datetime.datetime(2000, 1, 1)  # 初始化为很早的时间
            total_beans = 0

        now = datetime.datetime.now()
        delta = now - last_collect_time

        if delta >= datetime.timedelta(weeks=1):
            # 如果距离上次领取时间超过一周，给予领取
            total_beans += 10000
            last_collect_time_str = now.isoformat()

            # 更新或插入用户数据
            cursor.execute('''
                INSERT INTO user_beans (username, last_collect_time, total_beans)
                VALUES (?, ?, ?)
                ON CONFLICT(username)
                DO UPDATE SET last_collect_time=excluded.last_collect_time, total_beans=excluded.total_beans
            ''', (username, last_collect_time_str, total_beans))
            self.conn.commit()
            return True  # 返回成功
        return False  # 返回失败，未到领取时间

    def add_beans(self, username, amount):
        """
        给指定用户增加豆子数量。

        Args:
            username (str): 用户名。
            amount (int): 要增加的豆子数量。

        Returns:
            None
        """
        cursor = self.conn.cursor()

        # 确保表已创建
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_beans (
                username TEXT PRIMARY KEY,
                last_collect_time TEXT,
                total_beans INTEGER
            )
        ''')

        # 查询用户的豆子数量
        cursor.execute('SELECT total_beans FROM user_beans WHERE username = ?', (username,))
        result = cursor.fetchone()

        if result:
            # 如果用户存在，更新豆子数量
            total_beans = result[0] + amount
            cursor.execute('''
                UPDATE user_beans
                SET total_beans = ?
                WHERE username = ?
            ''', (total_beans, username))
        else:
            # 如果用户不存在，插入新用户
            total_beans = amount
            last_collect_time_str = datetime.datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO user_beans (username, last_collect_time, total_beans)
                VALUES (?, ?, ?)
            ''', (username, last_collect_time_str, total_beans))

        self.conn.commit()

    def get_bean_count(self, username):
        """
        获取指定用户的豆子数量。

        Args:
            username (str): 用户名。

        Returns:
            int: 用户的豆子总数。如果用户不存在，返回 0。
        """
        cursor = self.conn.cursor()

        # 确保表已创建
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_beans (
                username TEXT PRIMARY KEY,
                last_collect_time TEXT,
                total_beans INTEGER
            )
        ''')

        # 查询用户的豆子数量
        cursor.execute('SELECT total_beans FROM user_beans WHERE username = ?', (username,))
        result = cursor.fetchone()

        if result:
            total_beans = result[0]
        else:
            total_beans = 0

        return total_beans

    def get_top_users(self, n=10):
        """
        获取豆子数量最多的前 n 个用户。

        Args:
            n (int): 要获取的用户数量，默认是 10。

        Returns:
            list of tuple: 包含用户名和豆子数量的列表，格式为 [(username, total_beans), ...]
        """
        cursor = self.conn.cursor()

        # 确保表已创建
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_beans (
                username TEXT PRIMARY KEY,
                last_collect_time TEXT,
                total_beans INTEGER
            )
        ''')

        # 查询豆子数量前 n 的用户
        cursor.execute('''
            SELECT username, total_beans FROM user_beans
            ORDER BY total_beans DESC
            LIMIT ?
        ''', (n,))
        result = cursor.fetchall()

        return result

    def get_next_collect_time(self, username):
        """
        获取用户下次可领取豆子的时间。

        Args:
            username (str): 用户名。

        Returns:
            datetime: 下次可领取时间。如果用户不存在，返回当前时间。
        """
        cursor = self.conn.cursor()

        # 查询用户的最后领取时间
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

    def close_connection(self):
        """
        关闭数据库连接。
        """
        if self.conn:
            self.conn.close()
            self.conn = None


if __name__ == '__main__':
    # 获取 BeanManager 实例（单例）
    bean_manager = BeanManager()

    # 测试代码
    test_usernames = ['user1', 'user2', 'user3', 'user4', 'user5',
                      'user6', 'user7', 'user8', 'user9', 'user10',
                      'user11', 'user12']

    # 模拟用户领取豆子
    for username in test_usernames:
        bean_manager.collect_beans(username)

    # 给指定用户增加豆子
    bean_manager.add_beans('user1', 5000)
    print("已给 user1 增加 5000 个豆子。")

    # 查询用户的豆子数量
    for username in test_usernames:
        beans = bean_manager.get_bean_count(username)
        print(f"{username} 当前的豆子总数是：{beans}")

    # 获取豆子数量最多的前 10 名用户
    top_users = bean_manager.get_top_users(10)
    print("\n豆子数量最多的前 10 名用户：")
    for rank, (username, total_beans) in enumerate(top_users, start=1):
        print(f"第 {rank} 名：{username}，豆子数量：{total_beans}")

    # 关闭数据库连接
    bean_manager.close_connection()
