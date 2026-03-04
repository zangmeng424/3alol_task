import json
import random
import time
import requests
from bs4 import BeautifulSoup
from loguru import logger


class _3alol:
    def __init__(self):
        self.sess=requests.session()
        self.sess.headers.update(
        {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'referer': 'https://3a.lol',
            'discourse-present': 'true',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        })
        self.csrf = ""
        self.sess.get("https://3a.lol")

    def get_csrf(self):
        response = self.sess.get('https://3a.lol/session/csrf').json()
        self.csrf = response.get('csrf')
        logger.debug(f"csrf:{self.csrf[:12]}...")

    def get_hp(self):
        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'referer': 'https://3a.lol/signup',
            'x-csrf-token': 'undefined',
            **self.sess.headers
        }

        response = self.sess.get('https://3a.lol/session/hp.json', headers=headers)
        if response.status_code == 200:
            logger.debug(response.json())
            return response.json()

        return None

    def login(self,username,password):
        """
        登录（更新session）
        :param username:
        :param password:
        :return:
        """
        self.get_csrf()
        headers = {
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://3a.lol',
            'referer': 'https://3a.lol/login',
            'x-csrf-token': self.csrf,
            **self.sess.headers
        }

        data = {
            'login': username,
            'password': password,
            'second_factor_method': '1',
            'timezone': 'Etc/GMT-8',
        }
        response = self.sess.post('https://3a.lol/session', headers=headers, data=data).json()

        if login_error := response.get("error"):
            logger.error(login_error)
            return False
        else:
            return True

    def post_actions(self,topic_id):
        """
        点赞
        :param topic_id: 帖子id
        :return: 状态码（200成功,429点赞达到上限）
        """
        headers = {
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'discourse-logged-in': 'true',
            'origin': 'https://3a.lol',
            'referer': f'https://3a.lol/t/topic/{topic_id}',
            'x-csrf-token': self.csrf,
            **self.sess.headers
        }
        data = {
            'id': topic_id,
            'post_action_type_id': '2',
            'flag_topic': 'false',
        }
        try:
            response = self.sess.post('https://3a.lol/post_actions',headers=headers,  data=data)
            return response.status_code
        except:
            logger.error("点赞失败")
            return None

    def register(self,email_address,username,password):
        """
        发送注册申请
        :param email_address:邮箱地址
        :param username:用户名
        :param password:密码
        :return:
        """
        self.get_csrf()
        logger.debug(self.sess.cookies)
        logger.info(f"注册信息：email:{email_address},username:{username},password:{password}")

        hp_json = {}
        for _ in range(3):
            if hp_json := self.get_hp():
                break

        if not hp_json:
            return False

        self.get_csrf()

        headers = {
            **self.sess.headers,
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://3a.lol',
            'referer': 'https://3a.lol/signup',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0',
            'x-csrf-token':  self.csrf,
            'x-requested-with': 'XMLHttpRequest'
        }

        data = {
            'email': email_address,
            'password': password,
            'username': username,
            'password_confirmation': hp_json.get("value"),
            'challenge': hp_json.get("challenge")[::-1],
            'timezone': 'Etc/GMT-8',
        }

        try:
            response = self.sess.post('https://3a.lol/u',  headers=headers, data=data)
            logger.debug(response.text)
            if response.status_code == 200 and response.json().get("success") == True:
                    return True
            else:
                return False
        except:
            return False

    def send_activation_email(self,username):
        """
        发送验证邮件(疑似存在问题，未达到预期响应)
        :param username:用户名
        :return:
        """
        self.get_csrf()
        headers = {
            **self.sess.headers,
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'discourse-present': 'true',
            'origin': 'https://3a.lol',
            'referer': 'https://3a.lol/u/account-created',
            'x-csrf-token': self.csrf,
        }
        data = {
            'username': username,
        }
        response = self.sess.post('https://3a.lol/u/action/send_activation_email', headers=headers, data=data)
        logger.debug(response.text)
        if response.status_code == 200:
            return True
        return False

    def register_verification(self,verification_address:str):
        """
        验证注册信息
        :param verification_address:邮箱验证地址
        :return:
        """
        verification_address = verification_address.replace("http://","https://")
        headers = {
            **self.sess.headers,
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'referer': verification_address,
            'x-csrf-token': 'undefined',
        }
        response = self.sess.get('https://3a.lol/session/hp', headers=headers)
        hp_json = {}
        if response.status_code == 200:
            hp_json = response.json()

        if hp_json:
            self.get_csrf()
            headers = {
                'accept': '*/*',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://3a.lol',
                'referer': verification_address,
                'x-csrf-token': self.csrf,
            }

            data = {
                'password_confirmation': hp_json.get("value"),
                'challenge': hp_json.get("challenge")[::-1],
            }

            response = self.sess.put(
                f'{verification_address}.json',
                headers=headers,
                data=data,
            )
            if response.status_code == 200:
                return True
        else:
            return False

    def post(self,title:str,raw:str,tags:str,draft_key:str = None,featured_link:str = "", category:str = "4") -> bool | dict[str]:
        """
        发布一个帖子
        :param title: 话题标题
        :param raw: 内容
        :param tags: 标签（英文逗号分隔）
        :param draft_key: 值为空发布话题，反之向某话题下回复（topic_XXX,向XXX发送一条帖子留言，new_topic_时间戳，发布一条新话题，携带标题），
        :param featured_link:
        :param category: 类别（日常交流，单机游戏）
        :return: 新帖子信息
        """
        self.get_csrf()
        #构建虚拟打字时间
        typing_duration_msecs = int(int(len(raw)) * 1.1 * 1000 + random.randint(1000,10000))
        # 构建虚拟内部等待时间
        composer_open_duration_msecs = int(typing_duration_msecs * random.randint(8,19) + random.randint(1,1000))

        headers = {
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'discourse-logged-in': 'true',
            'origin': 'https://3a.lol',
            'referer': 'https://3a.lol',
            'x-csrf-token': self.csrf,
        }

        data = {
            'raw': raw,
            'unlist_topic': 'false',
            'category': category,
            'is_warning': 'false',
            'archetype': 'regular',
            'typing_duration_msecs': typing_duration_msecs,#打字时间
            'composer_open_duration_msecs': composer_open_duration_msecs,#编辑总时长
            'composer_version': '2',
            'shared_draft': 'false',
            'draft_key': f'new_topic_{int(time.time() * 1000)}',
            'locale': '',
            'create_as_post_voting': '',
            'nested_post': 'true',
        }

        #更新标签
        data.update({'tags[]':tags}) if tags else None

        #判断发帖目标
        if draft_key:
            data['draft_key'] = f"topic_{draft_key}"
            data.update({'featured_link':featured_link})
        else:
            data.update({'title':title})

        response = self.sess.post('https://3a.lol/posts',  headers=headers, data=data)
        if response.status_code == 200:
            if posts_content := response.json().get("post"):
                logger.info(f"帖子发布成功")
                return json.loads(posts_content)

        return False

    def get_posts(self,topic_id:str | int):
        """
        获取话题下的帖子内容
        :param topic_id: 话题id
        :return:
        """
        #["post_stream"]["posts"]下为回复帖子，
        #["title"]话题标题
        headers = {
            **self.sess.headers,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'upgrade-insecure-requests': '1',
        }

        response = self.sess.get(f'https://3a.lol/t/topic/{topic_id}', headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 使用CSS选择器
            div = soup.find('div', id='data-preloaded')
            if div:
                value = div.get('data-preloaded')
                info=json.loads(value)[f"topic_{topic_id}"]
                logger.debug(info)
                return json.loads(info)

        return False

    def get_summary(self,username:str = ""):
        """
        获取用户个人数据（["user_summary"]中包含个人数据）
        username为空则获取当前类中已登录用户的信息
        :param username: 用户名
        :return:
        """
        if not username:
            headers = {
                **self.sess.headers,
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'upgrade-insecure-requests': '1',
            }
            response = self.sess.get(f'https://3a.lol',headers = headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # 使用CSS选择器
                div = soup.find('div', id='data-preloaded')
                if div:
                    value = div.get('data-preloaded')
                    username = json.loads(value).get("currentUser").get("username")
                    if not username:
                        return False

        self.get_csrf()

        headers = {
            **self.sess.headers,
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'discourse-logged-in': 'true',
            'discourse-track-view': 'true',
            'referer': f'https://3a.lol/u/{username}/activity',
            'x-csrf-token': self.csrf,
        }

        response = self.sess.get(f'https://3a.lol/u/{username}/summary.json',  headers=headers)
        if response.status_code == 200:
            return response.json()

        return False

    def read_topics_timings(self,topic_id:str,topic_time:str="60000",timings:list[int]=[1]):
        """
        帖子阅读接口
        :param topic_id: 话题id
        :param topic_time:阅读话题的总时间（每次不得超过60000）
        :param topic_time:指定话题阅读的帖子
        :return:
        """

        self.get_csrf()
        headers = {
            **self.sess.headers,
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'discourse-logged-in': 'true',
            'discourse-present': 'true',
            'discourse-track-view': 'true',
            'discourse-track-view-topic-id': topic_id,
            'referer': 'https://3a.lol',
            'x-csrf-token': self.csrf,
        }

        params = {
            'track_visit': 'true',
            'forceLoad': 'true',
        }

        self.sess.get(f'https://3a.lol/t/{topic_id}/1.json', params=params, headers=headers)


        headers = {
            **self.sess.headers,
            'discourse-background': 'true',
            'discourse-logged-in': 'true',
            'x-csrf-token': self.csrf,
            'x-silence-logger': 'true',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }

        data = {
            'topic_time': topic_time,
            'topic_id': topic_id,
        }
        for timing in timings:
            data.update({f'timings[{timing}]':topic_time})

        response = self.sess.post('https://3a.lol/topics/timings',headers=headers, data=data)
        if response.status_code == 200:
            return True
        else:
            return False

    def get_latest(self):
        """
        获取最新话题列表
        """
        headers = {
            **self.sess.headers,
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'referer': 'https://3a.lol/latest',
            'x-csrf-token': self.csrf,
        }

        response = self.sess.get('https://3a.lol/latest.json',  headers=headers)
        if response.status_code == 200:
            return response.json().get("topic_list").get("topics")
        else:
            return False




def read_userinfo():
    file_path = "userinfo.txt"
    """从文件读取账号密码，每行格式为: 账号|密码"""
    accounts = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "|" in line:
                    parts = line.split("|", 1)
                    if len(parts) == 2:
                        accounts.append({"username": parts[0].strip(), "password": parts[1].strip()})
                    else:
                        logger.warning(f"格式错误: {line}")
                elif line:
                    logger.warning(f"格式错误，应为 账号|密码: {line}")
    except FileNotFoundError:
        logger.error(f"未找到 {file_path} 文件")
    except Exception as e:
        logger.error(f"读取 {file_path} 文件失败: {str(e)}")
    return accounts


