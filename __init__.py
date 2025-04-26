"""
Author: cg8-5712
Date: 2025-04-20
Version: 1.0.0
License: GPL-3.0
LastEditTime: 2025-04-20 19:30:00
Title: 机场信息查询插件
Description: 该插件允许用户通过机场的 ICAO 代码查询机场信息。
             结果可以以文本或图片的形式显示。
"""

from nonebot import on_command
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from nonebot_plugin_htmlrender import template_to_pic
from nonebot_plugin_alconna import At, Text

from zhenxun.configs.path_config import TEMPLATE_PATH
from zhenxun.utils.message import MessageUtils
from .airport import AirportInfo

__plugin_meta__ = PluginMetadata(
    name="机场信息查询",
    description="查询机场信息",
    usage="""
    指令:
        @机器人 airport [机场ICAO代码]: 以图片形式显示
        @机器人 airport [机场ICAO代码] --raw: 以文字形式显示
    """,
)

AirportCommand = on_command("airport", rule=to_me(), priority=5, block=True)


@AirportCommand.handle()
async def handle_airport(event: GroupMessageEvent, args=CommandArg()):
    """
    处理机场信息查询命令。
    根据指定的机场 ICAO 代码获取机场信息。
    结果可以以文本或图片的形式显示。
    """
    args = args.extract_plain_text().strip().split()
    if not args:
        await MessageUtils.build_message([
            At(flag="user", target=str(event.user_id)),
            Text("请提供机场 ICAO 代码")
        ]).send(reply_to=True)
        return

    icao_code = args[0].upper()
    show_raw = len(args) > 1 and args[1] == "--raw"

    # 获取机场信息
    airport_data = await AirportInfo.get_airport_info(icao_code)
    if isinstance(airport_data, str):  # 错误信息
        await MessageUtils.build_message([
            At(flag="user", target=str(event.user_id)),
            Text(airport_data)
        ]).send(reply_to=True)
        return

    if show_raw:
        text_output = AirportInfo.format_text_output(airport_data)
        await MessageUtils.build_message([
            At(flag="user", target=str(event.user_id)),
            Text(text_output)
        ]).send(reply_to=True)
    else:
        template_data = AirportInfo.prepare_template_data(airport_data)
        image = await template_to_pic(
            template_path=str(
                (TEMPLATE_PATH / "aviation" / "airport").absolute()
            ),
            template_name="main.html",
            templates=template_data,
            pages={
                "viewport": {"width": 800, "height": 600},
                "base_url": f"file://{TEMPLATE_PATH}"
            },
            wait=2
        )
        await MessageUtils.build_message([
            At(flag="user", target=str(event.user_id)),
            image
        ]).send(reply_to=True)