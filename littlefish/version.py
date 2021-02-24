"""
Print the version of littlefish.

Support version check, version display on first connection.
"""

import os
import httpx
import nonebot
import traceback
from nonebot import on_metaevent
from nonebot.adapters.cqhttp import Bot, Event, LifecycleMetaEvent
from nonebot.log import logger
from littlefish._policy import boardcast

version_directory = os.path.join(os.path.join(os.getcwd(), 'docs'),
                                 'changelog.md')

with open(version_directory, 'r', encoding='utf-8') as f:
    changelog = f.read()

start = changelog.find('##') + 2
stop = changelog.find('\n', start)
version = 'v' + changelog[start:stop].strip()


async def get_server_version():
    """Get the version of littlefish on Github."""
    url = 'https://api.github.com/repos/T0nyX1ang/littlefish/releases'
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url=url)
            data = r.json()[0]  # get the latest version
            server_version = data['tag_name']
            if server_version > version:
                logger.warning('New version [%s] available.' % server_version)
                return
            logger.info('Version check completed, littlefish is up to date.')
    except Exception:
        logger.warning('Version check failed, please check your network.')


version_checker = on_metaevent(priority=1, block=True, temp=True)


@version_checker.handle()
async def version_checker(bot: Bot, event: Event, state: dict):
    """Handle the version checker metaevent."""
    if not isinstance(event, LifecycleMetaEvent):
        return

    @boardcast('version')
    async def get_allowed(allowed: list):
        await get_server_version()
        version_message = '小鱼已启动，内核版本%s~' % version
        for bot_id, group_id in allowed:
            bot = nonebot.get_bots()[bot_id]
            try:
                await bot.send_group_msg(group_id=int(group_id),
                                         message=version_message)
            except Exception:
                logger.error(traceback.format_exc())

    await get_allowed()
