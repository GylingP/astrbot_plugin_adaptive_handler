from astrbot.api.star import Context, register, Star
from astrbot.api.event import filter, AstrMessageEvent,MessageEventResult
from astrbot.core.star.filter.permission import PermissionType
from astrbot.core.message.components import Image
from astrbot.api import AstrBotConfig
import random
import httpx
import os
from datetime import datetime

@register("adaptive-handler", "Gyling", "提供更加灵活的消息处理", "0.1.0")
class AdaptiveHandler(Star):

    def __init__(self, context: Context, config: AstrBotConfig): # AstrBotConfig 继承自 Dict，拥有字典的所有方法
        super().__init__(context)
        self.config = config
        self.feed_counts = {}
        self._current_date = datetime.now().strftime("%Y-%m-%d")

    def _cleanup_old_data(self):
        """清理旧日期的数据"""
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._current_date:
            # 日期变化，清理旧数据
            self.feed_counts = {}
            self._current_date = today

    @filter.command("help", alias={'helps','帮助'},priority=10)
    async def help(self, event: AstrMessageEvent):
        msg = self.config.get("help_msg", "欢迎使用本bot！更多内容请咨询管理员")
        msg = msg.replace("\\n", "\n")
        event.set_result(MessageEventResult().message(msg).use_t2i(False))
        event.stop_event()

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def random_reply(self, event: AstrMessageEvent):
        prob = float(self.config.get("reply_probability", 0))
        replies = self.config.get("reply_list", ["你好！", "在的~", "需要帮助吗？"])
        if random.random() < prob:
            msg = random.choice(replies)
            event.set_result(MessageEventResult().message(msg).use_t2i(False))

    @filter.command("蝈曰")
    async def get_cs_image(self, event: AstrMessageEvent, keyword: str):
        config = self.context.get_config()
        url = config.get("api_url", "https://www.gpcat.top/apis/cs")
        params = {}
        params["q"] = keyword
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                # 保存图片到临时文件
                tmp_path = os.path.join(os.path.dirname(__file__), "tmp_cs_img.jpg")
                with open(tmp_path, "wb") as f:
                    f.write(resp.content)
                # 发送图片
                event.set_result(MessageEventResult().file_image(tmp_path))
                # 可选：发送后删除临时文件
                # os.remove(tmp_path)
            else:
                event.set_result(MessageEventResult().message("未获取到图片，或API返回异常。"))
        except Exception as e:
            event.set_result(MessageEventResult().message(f"API请求异常: {e}"))
        event.stop_event()

    @filter.command("随机蝈曰")
    async def random_img(self, event: AstrMessageEvent):
        # 随机蝈曰 -> 随机图片
        config = self.context.get_config()
        url = config.get("api_url", "https://www.gpcat.top/apis/cs")
        rand_num = random.randint(1, 10)
        tmp_path = os.path.join(os.path.dirname(__file__), f"{rand_num}.jpg")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                headers = {
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache"
                }
                resp = await client.get(url, headers=headers)
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                with open(tmp_path, "wb") as f:
                    f.write(resp.content)
                event.set_result(MessageEventResult().file_image(tmp_path))
            else:
                event.set_result(MessageEventResult().message("未获取到图片，或API返回异常。"))
        except Exception as e:
            event.set_result(MessageEventResult().message(f"API请求异常: {e}"))
        event.stop_event()
    
    @filter.command("喂奶",alias={'张嘴'})
    async def feed_cat(self, event: AstrMessageEvent):
        # 清理旧数据
        self._cleanup_old_data()
        
        # 获取群ID，私聊用用户ID
        group_id = event.get_group_id()
        session_id = group_id if group_id else str(event.get_sender_id())
        
        # 获取当前群/私聊今天的喂奶次数
        current_count = self.feed_counts.get(session_id, 0)
        current_count += 1
        self.feed_counts[session_id] = current_count
        
        # 获取配置的最大次数
        max_count = self.config.get("max_feed_count", 3)
        
        if current_count >= max_count:
            # 达到最大次数，回复已喂饱（不重置，等明天自动重置）
            msg = "喵呜~猫咪已喂饱"
        else:
            # 未达到最大次数
            msg = "喜欢~感谢牛奶~"
        
        event.set_result(MessageEventResult().message(msg).use_t2i(False))
        event.stop_event()