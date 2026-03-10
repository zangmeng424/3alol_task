"""
3a.lol 每日任务
"""
import random
import sys
import time
from loguru import logger
from _3alol_api import read_userinfo, _3alol, read_cookie, save_cookie


# 回复模板
REPLY_TEMPLATES = [
    "感谢分享，已收藏！",
    "楼主牛逼，这就去试试",
    "666，正好想玩这个",
    "有空玩玩",
    "好帖帮顶！",
    "感谢大佬分享",
    "已入手，感谢推荐",
    "看着不错，试试",
    "这游戏我也在玩，确实不错",
    "感谢分享，正好缺这个",
]


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
        posts = data.get("post_stream", {}).get("posts", [])
        tags = data.get("tags", [])
        posts_count = len(posts)
        # 判断：帖子数 > 5
        if posts_count <= 5:
            logger.warning("回复贴过少")
            return False

        if True in [post["yours"] for post in posts]:
            logger.warning("本话题已回复过")
            return False

        # 判断：是否为游戏分享
        text = title + " " + " ".join(tags)
        is_game = any(k in text for k in ["游戏分享", "单机游戏"]) and (
                any(k in text for k in ["游戏", "steam", "Steam", "单机"]) or
                ("【" in title and "】" in title) or
                any(k in text.lower() for k in ["game", "dlc", "mod"])
        )

        if not is_game:
            logger.warning("非游戏分享贴")
            return False

        # 生成回复（避免与前 5 条回复重复）
        existing = [p.get("raw", "") for p in posts[1:6]]
        reply = random.choice(REPLY_TEMPLATES)

        # 简单去重
        for _ in range(3):
            if not any(reply in e or e in reply for e in existing):
                break
            reply = random.choice(REPLY_TEMPLATES)

        logger.info(f"生成回复：{reply}")

        lol.get_categories()

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
                #获取最新话题
                topics_list = lol.get_latest()
                for topic in topics_list[:10]:
                    topic_id = topic["id"]
                    data = lol.get_posts(topic_id)
                    if data:
                        # 提取关键信息
                        title = data.get("title", "")
                        posts = data.get("post_stream", {}).get("posts", [])
                        tags = data.get("tags", [])
                        posts_count = len(posts)

                        logger.info(f"标题：{title[:20]}... | 帖子数：{posts_count} | 标签：{tags}")

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
                    if random.random() <= 0.4:
                        if reply_topic(lol, topic_id):
                            logger.success("贴子发布成功")
                        else:
                            logger.error("贴子发布失败")


                # 跳过重试
                break

            except Exception as e:
                logger.error(f"任务失败{e}")



if __name__ == "__main__":

    logger.remove()  # 移除所有默认handler
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:MM-DD HH:mm:ss} | {level:<8} | - {message}"
    )
    main()
