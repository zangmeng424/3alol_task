"""
3a.lol 每日任务
"""
import random
import sys
import time

from loguru import logger
from _3alol_api import read_userinfo,_3alol



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
            logger.info(f"{account["username"]} 开始登陆")
            if lol.login(account["username"], account["password"]):
                logger.success(f"{account["username"]} 登陆成功")
            else:
                logger.error(f"{account["username"]} 登陆失败")
                continue

            #获取最新话题
            topics_list = lol.get_latest()
            for topic in topics_list[:10]:
                topic_id = topic["id"]
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
                        lol.post_actions(post["id"])
                        logger.success(f"{post["id"]} 点赞完成")
                else:
                    logger.warning("目标话题获取帖子失败，点赞取消")


if __name__ == "__main__":

    logger.remove()  # 移除所有默认handler
    logger.add(sys.stderr, level="INFO")  # 只显示INFO及以上级别

    main()
