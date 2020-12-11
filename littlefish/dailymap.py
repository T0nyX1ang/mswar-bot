"""
Fetch the information of the daily map.

The information includes:
Map: lines, columns, mines, bv, openings, islands.
User: best_time (math.inf) as default.

The command is automatically invoked at 00:03:00 +- 30s everyday.
The command requires to be invoked in groups.
"""

import nonebot
import math
import traceback
from nonebot import on_command
from nonebot.log import logger
from nonebot.permission import GROUP
from nonebot.adapters.cqhttp import Bot, Event
from littlefish._analyzer import get_board, get_board_result
from littlefish._netcore import fetch
from littlefish._policy import check, boardcast


def format_daily_map(daily_map: dict) -> str:
    """Formatter for information."""
    line = [
        '每日一图:',
        '%d 行, %d 列, %d 雷' %
        (daily_map['row'], daily_map['column'], daily_map['mines']),
        '%d bv, %d op, %d is' %
        (daily_map['bv'], daily_map['op'], daily_map['is']),
        '最佳时间: %.3f' % (daily_map['best_time']), '大佬们冲鸭!'
    ]
    result_message = ''
    for each_line in line:
        result_message = result_message + each_line + '\n'
    return result_message.strip()


async def get_daily_map() -> str:
    """Get daily map information from the remote server."""
    daily_map_result = await fetch(
        page='/MineSweepingWar/minesweeper/daily/map/today')
    daily_map_board = get_board(
        daily_map_result['data']['map']['map'].split('-')[0:-1])
    daily_map = get_board_result(daily_map_board)
    daily_map['id'] = daily_map_result['data']['mapId']

    query = 'mapId=%d&page=0&count=1' % (daily_map['id'])
    daily_map_highest_result = await fetch(
        page='/MineSweepingWar/rank/daily/list', query=query)
    if daily_map_highest_result['data']:
        daily_map[
            'best_time'] = daily_map_highest_result['data'][0]['time'] / 1000
    else:
        daily_map['best_time'] = math.inf
    return daily_map


dailymap = on_command(cmd='dailymap', aliases={'每日一图'},
                      permission=GROUP, rule=check('dailymap'))


@dailymap.handle()
async def dailymap(bot: Bot, event: Event, state: dict):
    """Handle the dailymap command."""
    daily_map_info = await get_daily_map()
    await bot.send(event=event, message=format_daily_map(daily_map_info))


@nonebot.scheduler.scheduled_job('cron',
                                 hour=0, minute=3, second=0,
                                 misfire_grace_time=30)
@boardcast('dailymap')
async def _(allowed: list):
    """Scheduled dailymap boardcast at 00:03:00."""
    daily_map = await get_daily_map()
    message = format_daily_map(daily_map)
    for bot_id, group_id in allowed:
        try:
            bot = nonebot.get_bots()[bot_id]
            await bot.send_group_msg(group_id=int(group_id),
                                     message=message)
        except Exception:
            logger.error(traceback.format_exc())
