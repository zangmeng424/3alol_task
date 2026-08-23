import json
import os
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
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/511.36',
            'x-requested-with': 'XMLHttpRequest',
        })
        self.csrf = ""
        self.sess.get("https://3a.lol")

    def get_csrf(self):
        for _ in range(3):
            try:
                response = self.sess.get('https://3a.lol/session/csrf').json()
                self.csrf = response.get('csrf')
                logger.debug(f"csrf:{self.csrf[:12]}...")
                break
            except:
                logger.debug(f"csrf获取失败")
                time.sleep(1)

    def get_hp(self) -> dict | None:
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

    def login(self,username:str,password:str) -> tuple[bool, str]:
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
            logger.debug(login_error)
            return False,login_error
        else:
            return True,";".join([f"{k}={v}" for k, v in self.sess.cookies.get_dict().items()])

    def login_with_cookie(self,cookie_string:str) -> bool:
        """
        注入cookie进行登录
        为防止出现 您无法从该 IP 地址以 XXX 身份登录。
        :param cookie_string: cookie字符串
        :return: 是否登陆成功
        """
        result = {}
        # 按分号分割不同的cookie
        cookies = cookie_string.split(';')

        for cookie in cookies:
            cookie = cookie.strip()  # 去除首尾空格
            if not cookie:
                continue

            # 按等号分割键值
            if '=' in cookie:
                key, value = cookie.split('=', 1)  # 只分割第一个等号
                result[key.strip()] = value.strip()

        self.sess.cookies.update(result)

        if self.get_summary():
            return True
        else:
            return False

    def post_like(self,topic_id:str) -> int | None:
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
            logger.debug("点赞失败")
            return None

    def register(self,email_address:str,username:str,password:str) -> bool:
        """
        发送注册申请
        :param email_address:邮箱地址
        :param username:用户名
        :param password:密码
        :return:
        """
        self.get_csrf()
        logger.debug(f"注册信息：email:{email_address},username:{username},password:{password}")

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

    def send_activation_email(self,username:str) -> bool:
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

    def register_verification(self,verification_address:str) -> bool:
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

        return False

    def post(self,title:str,raw:str,tags:str,draft_key:str = None,featured_link:str = "", category:str = "4") -> bool | dict:
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
            data.update({'topic_id':draft_key})
        else:
            data.update({'title':title})

        response = self.sess.post('https://3a.lol/posts',  headers=headers, data=data)
        if response.status_code == 200:
            if posts_content := response.json().get("post"):
                return posts_content

        return False

    def get_categories(self) -> list[dict]:
        """
        获取分区列表
        :return:
        """
        self.get_csrf()

        headers = {
            **self.sess.headers,
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'discourse-logged-in': 'true',
            'discourse-track-view': 'true',
            'referer': 'https://3a.lol/',
            'x-csrf-token': self.csrf,
        }

        response = self.sess.get('https://3a.lol/categories_and_latest',  headers=headers).json()

        return response.get("category_list").get("categories",[])

    def get_posts(self,topic_id:str | int) -> bool | dict:
        """
        获取话题下的帖子内容
        :param topic_id: 话题id
        :return:
        """
        #["post_stream"]["posts"]下为回复帖子，
        #["title"]话题标题
        #["category_id"]所属分区id
        headers = {
            **self.sess.headers,
            'accept': 'application/json, text/javascript, */*; q=0.01'
        }

        response = self.sess.get(f'https://3a.lol/t/{topic_id}.json?track_visit=true&forceLoad=true', headers=headers)
        if response.status_code == 200:
            return response.json()

        return False

    def get_summary(self,username:str = "") -> bool | dict:
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
                div = soup.find('script', id='data-preloaded')
                if div:
                    value = div.text
                    try:
                        username = json.loads(json.loads(value).get("currentUser", {})).get("username")
                        if not username:
                            return False
                    except:
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

    def get_user_detail(self,username:str = "") -> bool | dict:
        """
        获取用户详细信息（包含信任级别）
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
                    try:
                        username = json.loads(json.loads(value).get("currentUser", {})).get("username")
                        if not username:
                            return False
                    except:
                        return False

        self.get_csrf()

        headers = {
            **self.sess.headers,
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'discourse-logged-in': 'true',
            'discourse-track-view': 'true',
            'referer': f'https://3a.lol/u/{username}',
            'x-csrf-token': self.csrf,
        }

        response = self.sess.get(f'https://3a.lol/u/{username}.json',  headers=headers)
        if response.status_code == 200:
            return response.json()

        return False

    def get_directory_data(self,username:str = "") -> bool | dict:
        """
        获取用户目录数据（季度统计）
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
                    try:
                        username = json.loads(json.loads(value).get("currentUser", {})).get("username")
                        if not username:
                            return False
                    except:
                        return False

        self.get_csrf()

        headers = {
            **self.sess.headers,
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'discourse-logged-in': 'true',
            'discourse-track-view': 'true',
            'referer': f'https://3a.lol/u/{username}',
            'x-csrf-token': self.csrf,
        }

        response = self.sess.get(f'https://3a.lol/directory_items?period=quarterly&order=days_visited&name={username}',  headers=headers)
        if response.status_code == 200:
            return response.json()

        return False

    def get_user_actions(self,username:str = "",filter:str = 5) -> bool | dict:
        """
        获取用户互动数据
        username为空则获取当前类中已登录用户的信息
        :param username: 用户名
        :param filter: `1`:点赞行为  `5`:回复行为
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
                    try:
                        username = json.loads(json.loads(value).get("currentUser", {})).get("username")
                        if not username:
                            return False
                    except:
                        return False

        self.get_csrf()

        headers = {
            **self.sess.headers,
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'discourse-logged-in': 'true',
            'discourse-track-view': 'true',
            'referer': f'https://3a.lol/u/{username}',
            'x-csrf-token': self.csrf,
        }

        response = self.sess.get(f'https://3a.lol/user_actions.json?offset=0&username={username}&filter={filter}', headers=headers)
        if response.status_code == 200:
            return response.json()

        return False

    def get_user_level_info(self, username: str = "") -> dict:
        """
        获取用户等级信息（综合摘要、详细信息和目录数据）
        :param username: 用户名
        :return: 包含所有等级信息的字典
        """
        summary_data = self.get_summary(username)
        detail_data = self.get_user_detail(username)
        directory_data = self.get_directory_data(username)

        if not summary_data or not detail_data:
            return {}

        user_summary = summary_data.get("user_summary", {})
        user = detail_data.get("user", {})
        directory_items = directory_data.get("directory_items", []) if directory_data else []

        # 获取当前用户在目录中的数据
        directory_item = None
        if directory_items:
            for item in directory_items:
                if item.get("user", {}).get("username") == username:
                    directory_item = item
                    break
            if not directory_item and directory_items:
                directory_item = directory_items[0]

        return {
            "user": user,
            "summary": user_summary,
            "directory": directory_item,
            "trust_level": user.get("trust_level", 0)
        }

    def read_topics_timings(self,topic_id:str,topic_time:str="60000",timings:list[int]=[1]) -> bool:
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

    def get_latest(self) -> dict | bool:
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

    def query(self,term:str):
        """
        搜索
        :param term: 搜索内容
        :return: 结果
        """
        self.get_csrf()
        headers = {
            **self.sess.headers,
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'discourse-logged-in': 'true',
            'referer': 'https://3a.lol/',
            'x-csrf-token': self.csrf,
        }

        params = {
            'term': term,
        }

        response = self.sess.get('https://3a.lol/search/query', params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return False



def read_userinfo() -> list[dict]:
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
                        logger.debug(f"格式错误: {line}")
                elif line:
                    logger.debug(f"格式错误，应为 账号|密码: {line}")
    except FileNotFoundError:
        logger.debug(f"未找到 {file_path} 文件")
    except Exception as e:
        logger.debug(f"读取 {file_path} 文件失败: {str(e)}")
    return accounts



def read_cookie(username:str) -> str|bool:
    """
    读取JSON文件并添加新的键值对
    """
    file_path="cookie.json"

    if not os.path.exists(file_path):
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump({}, f)
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data.get(username,False)

    except Exception as e:
        logger.debug(f"{username} cookie读取失败")
        return False

def save_cookie(username:str,cookie:str) -> bool:
    """
    读取JSON文件并添加新的键值对
    """
    file_path="cookie.json"

    if not os.path.exists(file_path):
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump({}, f)

    try:
        # 读取现有数据
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 更新数据
        data.update({username:cookie})

        # 写回文件（保持缩进）
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.debug(f"{username} cookie更新成功")
        return True

    except Exception as e:
        logger.debug(f"{username} cookie更新失败")
        return False
