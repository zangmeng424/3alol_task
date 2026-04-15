# 回复模板
START = [
    "感谢分享",
    "多谢楼主",
    "不错啊",
    "看起来可以",
    "有点意思",
    "这个可以",
    "正好需要这个",
    "来得太及时了",
]
CONTENT = [
    "这个游戏之前听说过",
    "刚好最近在找这个类型的",
    "一直想玩这个来着",
    "看画面感觉挺不错",
    "玩法看起来还行",
    "第一次看到这个",
    "这类型我挺喜欢的",
]
ACTION = [
    "这就去下载试试",
    "先收藏了",
    "有空玩一下",
    "等会就去看看",
    "回头体验一下",
    "先留着备用",
]
EXTRA = [
    "",
    "",
    "",
    "谢谢大佬",
    "辛苦了",
    "666",
    "支持一下",
]

# 等级晋升条件
LEVEL_REQUIREMENTS = {
    0: {
        "metrics": [
            {"key": "topics_entered", "target": 5, "source": "summary", "label": "已读主题数"},
            {"key": "posts_read_count", "target": 30, "source": "summary", "label": "已读帖子数"},
            {"key": "time_read", "target": 600, "source": "summary", "label": "阅读时长(秒)"},
        ],
    },
    1: {
        "metrics": [
            {"key": "days_visited", "target": 15, "source": "summary", "label": "访问天数"},
            {"key": "topics_entered", "target": 20, "source": "summary", "label": "已读主题数"},
            {"key": "posts_read_count", "target": 100, "source": "summary", "label": "已读帖子数"},
            {"key": "time_read", "target": 3600, "source": "summary", "label": "阅读时长(秒)"},
            {"key": "replied_topics", "target": 3, "source": "activity", "label": "回复话题数"},
            {"key": "likes_given", "target": 1, "source": "summary", "label": "已点赞数"},
            {"key": "likes_received", "target": 1, "source": "summary", "label": "获赞数"},
        ],
    },
    2: {
        "metrics": [
            {"key": "days_visited", "target": 50, "source": "directory", "label": "访问天数(最近100天)"},
            {"key": "likes_given", "target": 30, "source": "directory", "label": "已点赞数(最近100天)"},
            {"key": "likes_received", "target": 20, "source": "directory", "label": "获赞数(最近100天)"},
            {"key": "topics_entered", "target": 20000, "source": "summary", "label": "累计已读主题(25%)"},
            {"key": "posts_read_count", "target": 500, "source": "summary", "label": "累计已读帖子(25%)"},
        ],
    },
    3: {
        "metrics": [
            {"key": "days_visited", "target": 50, "source": "directory", "label": "访问天数(最近100天)"},
            {"key": "likes_given", "target": 30, "source": "directory", "label": "已点赞数(最近100天)"},
            {"key": "likes_received", "target": 20, "source": "directory", "label": "获赞数(最近100天)"},
            {"key": "topics_entered", "target": 20000, "source": "summary", "label": "累计已读主题(25%)"},
            {"key": "posts_read_count", "target": 500, "source": "summary", "label": "累计已读帖子(25%)"},
        ],
    },
    4: {
        "metrics": [],
    },
}
