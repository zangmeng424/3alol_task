"""
3a.lol 每日任务
"""
import random
import sys
import time
from loguru import logger
from wcwidth import wcswidth
from _3alol_api import read_userinfo, _3alol, read_cookie, save_cookie
from source_data import *


class UserLevelTask:
    """用户等级信息获取和显示任务"""

    def __init__(self, lol: _3alol, account: dict):
        self.lol = lol
        self.account = account
        self.username = account["username"]
        self.level_info = {}
        self.completed_tasks = {}

    def get_user_level_info(self) -> bool:
        """获取用户等级信息"""
        try:
            self.level_info = self.lol.get_user_level_info(self.username)
            if not self.level_info:
                logger.error(f"获取用户 {self.username} 等级信息失败")
                return False

            logger.success(f"获取用户 {self.username} 等级信息成功")
            return True
        except Exception as e:
            logger.error(f"获取用户 {self.username} 等级信息时发生错误: {e}")
            return False

    def calculate_task_progress(self):
        """计算任务进度"""
        if not self.level_info:
            return

        user = self.level_info.get("user", {})
        trust_level = user.get("trust_level", 0)
        summary = self.level_info.get("summary", {})
        directory = self.level_info.get("directory", {})

         # 获取当前等级的晋升条件
        requirements = LEVEL_REQUIREMENTS.get(trust_level, {})
        metrics = requirements.get("metrics", [])

        # 计算每个指标的进度
        self.completed_tasks = {}
        for metric in metrics:
            key = metric["key"]
            target = metric["target"]
            source = metric["source"]

            current = 0
            # 获取当前值
            if source == "summary":
                current = summary.get(key, 0)
            elif source == "directory":
                current = directory.get(key, 0) if directory else 0
            elif source == "activity":
                # 只有一处需要这个数据，需要再调用
                if actions_data := self.lol.get_user_actions(self.username):
                    current = len(actions_data.get("user_actions"))
                else:
                    current = 0

            # 计算进度
            progress = f"{current}/{target}"
            self.completed_tasks[metric["label"]] = progress

    def display_user_info(self):
        """显示用户信息"""
        if not self.level_info:
            logger.warning("没有用户信息可显示")
            return

        user = self.level_info.get("user", {})
        trust_level = user.get("trust_level", 0)
        username = user.get("username", self.username)

        # 第一行：用户名和等级
        user_level_line = f"{username} {' ' * 10} TL{trust_level} -> TL{trust_level if trust_level >= 3 else trust_level + 1}"
        logger.info("=" * 30)
        logger.info(user_level_line)
        logger.info("-" * 30)

        # 显示任务进度表格
        if self.completed_tasks:
            # 获取所有任务的标签和进度
            tasks = list(self.completed_tasks.items())

            def align_text(text, width):
                display_width = wcswidth(text)  # 实际显示宽度
                padding = width - display_width
                if padding > 0:
                    return text + " " * padding
                return text

            label_width = 18  # 显示宽度

            for label, progress in tasks:
                logger.info(f"{align_text(label, label_width)} | {progress}")
            logger.info("=" * 30)
        else:
            logger.info("暂无任务进度信息")
            logger.info("=" * 30)


def login(lol: _3alol,account: dict) -> bool:
    if cookie := read_cookie(account["username"]):
        logger.info(f"{account['username']} 使用cookie登录")
        if lol.login_with_cookie(cookie):
            logger.success(f"{account['username']} 登陆成功")
            return True
        else:
            logger.error(f"{account['username']} cookie登录失败")

    logger.info(f"{account['username']} 正常登录")
    status, error = lol.login(account["username"], account["password"])
    if status:
        logger.success(f"{account['username']} 登陆成功")
        save_cookie(account["username"], error)
        return True
    else:
        logger.error(f"{account['username']} 登陆失败")
        # 疑似IP被拉黑后会有连坐机制，强制结束任务保后续账号
        if "密码不正确" in error or "IP" in error:
            logger.error(f"登录响应异常，疑似IP被拉黑，已强制结束")
            exit(1)
        return False

def gen_reply():
    s = random.choice(START)
    c = random.choice(CONTENT)
    a = random.choice(ACTION)
    e = random.choice(EXTRA)

    # 随机去掉某一段（模拟真人简写）
    parts = [s, c, a]

    # 随机删2段（增强随机性）
    for _ in range(2):
        if random.random() < 0.5:
            parts.pop(random.randint(0, len(parts)-1))

    reply = random.choice(["，"," "]).join(parts)

    if e:
        reply += "，" + e

    # 随机句尾符号
    reply +="" if random.random() < 0.7 else random.choice(["！", "～", "。"])

    return reply

def reply_topic(lol: _3alol,topic_id: str) -> bool:
    """
    自动回复话题帖子
    """
    try:
        logger.info("开始话题发帖留言")
        data = lol.get_posts(topic_id)
        if not data:
            return False

        # 提取关键信息
        title = data.get("title", "")
        category_id = data.get("category_id", None)
        posts = data.get("post_stream", {}).get("posts", [])
        posts_count = len(posts)
        # 判断：帖子数 > 5
        if posts_count <= 5:
            logger.warning("回复贴过少")
            return False

        if True in [post["yours"] for post in posts]:
            logger.warning("本话题已回复过")
            return False

        # 判断：是否为游戏分享
        is_game = ("【" in title and "】" in title) and (category_id == 5)# 检测标题格式中括号 属于游戏分享区（id为5）

        if not is_game:
            logger.warning("非游戏分享贴")
            return False

        # 生成回复
        reply = gen_reply()

        logger.info(f"生成回复：{reply}")

        result = lol.post(
            title="",
            raw=reply,
            tags="",
            draft_key=topic_id,  # 设置为话题 ID 表示回复
            category=data.get("category_id", "5"),
        )

        if result:
            return True
        else:
            return False

    except Exception as e:
        return False


def main():
    accounts = read_userinfo()
    if not accounts:
        logger.error("未找到任何账号信息，请检查 userinfo.txt 文件")
        exit(1)

    logger.info(f"共读取到 {len(accounts)} 个账号")
    for i, account in enumerate(accounts, 1):
        for try_number in range(3):#重试次数
            logger.info(f"========== 正在处理第 {i}/{len(accounts)} 个账号 重试 {try_number + 1}/3 ==========")
            lol = _3alol()

            #登录
            if not login(lol, account):
                continue

            try:
                # 获取用户等级信息
                user_level_task = UserLevelTask(lol, account)
                if user_level_task.get_user_level_info():
                    user_level_task.calculate_task_progress()
                    user_level_task.display_user_info()

                #获取最新话题
                topics_list = lol.get_latest()
                for topic in topics_list[:10]:
                    topic_id = topic["id"]
                    data = lol.get_posts(topic_id)
                    categories_list = lol.get_categories()

                    if data:
                        # 提取关键信息
                        title = data.get("title", "")
                        category_id = data.get("category_id", None)
                        posts = data.get("post_stream", {}).get("posts", [])
                        tags = [tag.get("name") for tag in data.get("tags", [])]
                        posts_count = len(posts)
                        if category_name_list := [categories["name"] for categories in categories_list if categories["id"] == category_id]:
                            category = category_name_list[0]

                        logger.info(f"标题：{title[:20]}... | 分区：{category} | 帖子数：{posts_count} | 标签：{tags}")

                    logger.info(f"{topic_id} 开始阅读")

                    # 遍历10次，每次选择一个话题中的三个帖子刷时间
                    for post_start in range(30)[::3]:
                        lol.read_topics_timings(topic_id = str(topic_id),topic_time = str(random.randint(50000,60000)),timings = [timing for timing in range(1,topic["posts_count"]+1)][min(topic["posts_count"]-1,post_start):post_start+3])
                        time.sleep(0.2)
                    logger.success(f"{topic_id} 阅读完成")

                    #点赞
                    posts = lol.get_posts(topic_id)
                    if posts:
                        posts_list = posts["post_stream"]["posts"]
                        selected_posts = random.sample(posts_list, random.randint(1,min(3,len(posts_list))))
                        for post in selected_posts:
                            lol.post_like(post["id"])
                            logger.success(f"{post['id']} 点赞完成")
                    else:
                        logger.warning("目标话题获取帖子失败，点赞取消")

                    #回复
                    if random.random() <= 0.6:
                        if reply_topic(lol, topic_id):
                            logger.success("贴子发布成功")
                        else:
                            logger.error("贴子发布失败")


                # 跳过重试
                break

            except Exception as e:
                logger.exception(f"任务失败{e}")



if __name__ == "__main__":

    logger.remove()  # 移除所有默认handler
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:MM-DD HH:mm:ss} | {level:<8} | - {message}"
    )
    main()
