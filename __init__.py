"""
Author: cg8-5712
Date: 2025-04-20
Version: 1.0.0
License: GPL-3.0
LastEditTime: 2025-04-20 19:30:00
Title: Airport Information Query Plugin
Description: This plugin allows users to query airport information using ICAO codes.
            Results can be displayed as text or image format.
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
    name="Airport Information Query",
    description="Query airport information",
    usage="""
    Commands:
        @bot airport [ICAO code]: Display as image
        @bot airport [ICAO code] --raw: Display as text
    """,
)

AirportCommand = on_command("airport", rule=to_me(), priority=5, block=True)


@AirportCommand.handle()
async def handle_airport(event: GroupMessageEvent, args=CommandArg()):
    """
    Handle airport information query command.
    Get airport information based on the specified ICAO code.
    Results can be displayed as text or image format.
    """
    args = args.extract_plain_text().strip().split()
    if not args:
        await MessageUtils.build_message([
            At(flag="user", target=str(event.user_id)),
            Text("Please provide an ICAO code")
        ]).send(reply_to=True)
        return

    icao_code = args[0].upper()
    show_raw = len(args) > 1 and args[1] == "--raw"

    # Get airport information
    airport_data = await AirportInfo.get_airport_info(icao_code)
    if isinstance(airport_data, str):  # Error message
        await MessageUtils.build_message([
            At(flag="user", target=str(event.user_id)),
            Text(airport_data)
        ]).send(reply_to=True)
        return

    if show_raw:
        text_output = airport_data.format_text_output()
        await MessageUtils.build_message([
            At(flag="user", target=str(event.user_id)),
            Text(text_output)
        ]).send(reply_to=True)
    else:
        template_data = airport_data.prepare_template_data()
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