from nonebot import on_startup, on_command, CommandSession, on_notice, NoticeSession, on_request, RequestSession
from nonebot.permission import SUPERUSER, GROUP_ADMIN
from nonebot.log import logger
from apscheduler.triggers.date import DateTrigger
from ftptsgame import FTPtsGame
from ftptsgame.database import DATABASE_42
from .core import fetch, is_online, is_enabled
from .global_value import *
from .info import get_user_info, format_user_info
import os
import sys
import json
import hashlib
import nonebot
import traceback

async def update_group_members(bot, group_id):
    group_members_list = await bot.get_group_member_list(group_id=group_id)
    for member in group_members_list:
        group_member_info = await bot.get_group_member_info(group_id=group_id, user_id=member['user_id'])
        user_id = str(group_member_info['user_id'])
        if user_id not in CURRENT_GROUP_MEMBERS[group_id]:
            CURRENT_GROUP_MEMBERS[group_id][user_id] = {}
        CURRENT_GROUP_MEMBERS[group_id][user_id]['id'] = group_member_info['title']
        CURRENT_GROUP_MEMBERS[group_id][user_id]['nickname'] = group_member_info['nickname']
        CURRENT_GROUP_MEMBERS[group_id][user_id]['card'] = group_member_info['card']
        if '42score' not in CURRENT_GROUP_MEMBERS[group_id][user_id]:
            CURRENT_GROUP_MEMBERS[group_id][user_id]['42score'] = 0
        if 'restricted' not in CURRENT_GROUP_MEMBERS[group_id][user_id]:
            CURRENT_GROUP_MEMBERS[group_id][user_id]['restricted'] = False

@on_command('enable', aliases=('启动', '启动机器人'), permission=SUPERUSER | GROUP_ADMIN, only_to_me=False)
async def enable(session: CommandSession):
    if not is_online():
        session.finish('请登录关联账号')

    if is_enabled(session.event):
        session.finish()

    group_id = session.event['group_id']
    group_hash = hashlib.sha3_256(PRIMARY_PASSWORD + str(group_id).encode()).hexdigest()
    database_path = os.path.join(LOCAL_DATABASE_PATH, '%s.dat') % (group_hash)

    if os.path.isfile(database_path): # preserving state when the bot is shut
        with open(database_path, 'rb') as f:
            database = json.loads(PRIMARY_DECRYPT(f.read()))
    else: # default database
        database = {
            'group_message': '', 
            'combo_counter': 0, 
            'group_members': {},
            'conflict_counter': 0,
            '42_probability_list': { str(k): 2000 for k in DATABASE_42.keys() },
            'word_blacklist': [],
            'game_frequency': 1,
        }
        with open(database_path, 'wb') as f:
            f.write(PRIMARY_ENCRYPT(json.dumps(database)))

    if group_id not in CURRENT_ENABLED: 
        CURRENT_GROUP_MESSAGE[group_id] = database['group_message'] if 'group_message' in database else ''
        CURRENT_GROUP_MESSAGE_INCREMENT[group_id] = database['group_message_increment'] if 'group_message_increment' in database else ''
        CURRENT_COMBO_COUNTER[group_id] = database['combo_counter'] if 'combo_counter' in database else 0
        CURRENT_42_APP[group_id] = FTPtsGame()
        CURRENT_42_PROB_LIST[group_id] = database['42_probability_list'] if '42_probability_list' in database else { str(k): 2000 for k in DATABASE_42.keys() }
        CURRENT_GROUP_MEMBERS[group_id] = database['group_members'] if 'group_members' in database else {}
        CURRENT_ID_COLDING_LIST[group_id] = []
        CURRENT_CONFLICT_COUNTER[group_id] = database['conflict_counter'] if 'conflict_counter' in database else 0
        CURRENT_WORD_BLACKLIST[group_id] = database['word_blacklist'] if 'word_blacklist' in database else []
        GAME_FREQUENCY[group_id] = database['game_frequency'] if 'game_frequency' in database else 1

    CURRENT_ENABLED[group_id] = True

    await update_group_members(session.bot, group_id)
    await session.send('小鱼已启动，内核版本 v0.9.0 ~')

@on_command('disable', aliases=('关闭', '关闭机器人'), permission=SUPERUSER | GROUP_ADMIN, only_to_me=False)
async def disable(session: CommandSession):
    if not is_enabled(session.event):
        session.finish()

    group_id = session.event['group_id']
    CURRENT_ENABLED[group_id] = False
    await session.send('小鱼已关闭')

@on_command('block', aliases=('屏蔽'), permission=SUPERUSER | GROUP_ADMIN, only_to_me=False)
async def block(session: CommandSession):
    if not is_enabled(session.event):
        session.finish('小鱼睡着了zzz~')
        
    group_id = session.event['group_id']
    word = session.get('word')
    if word not in CURRENT_WORD_BLACKLIST[group_id]:
        CURRENT_WORD_BLACKLIST[group_id].append(word)
        await session.send('词语[%s]已被加入屏蔽列表' % (word))
    else:
        await session.send('词语[%s]已在屏蔽列表中' % (word))

@block.args_parser
async def _(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if session.is_first_run:
        if stripped_arg:
            session.state['word'] = stripped_arg
        else:
            session.finish()

@on_command('unblock', aliases=('解除屏蔽'), permission=SUPERUSER | GROUP_ADMIN, only_to_me=False)
async def unblock(session: CommandSession):
    if not is_enabled(session.event):
        session.finish('小鱼睡着了zzz~')
        
    group_id = session.event['group_id']
    word = session.get('word')
    if word in CURRENT_WORD_BLACKLIST[group_id]:
        CURRENT_WORD_BLACKLIST[group_id].remove(word)
        await session.send('词语[%s]已被移除屏蔽列表' % (word))
    else:
        await session.send('词语[%s]不在屏蔽列表中' % (word))

@unblock.args_parser
async def _(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if session.is_first_run:
        if stripped_arg:
            session.state['word'] = stripped_arg
        else:
            session.finish()

@on_request('group')
async def _(session: RequestSession):
    comment = session.event['comment']
    player_id = comment[comment.find('答案') + 3:].strip()
    await session.send('有小伙伴(Id: %s)申请加群了~' % (player_id))
    name = ' ' * 20 + str(player_id)
    user_info = await get_user_info(name)
    user_info_message = format_user_info(user_info)
    await session.send(user_info_message)

@on_notice('group_increase')
async def _(session: NoticeSession):
    group_id = session.event['group_id']
    await session.send('欢迎大佬，希望大佬天天破pb~')
    await update_group_members(session.bot, group_id)  # update if new member join the group

@on_notice('group_decrease')
async def _(session: NoticeSession):
    leave_id = str(session.event['user_id'])
    group_id = session.event['group_id']
    player_id = CURRENT_GROUP_MEMBERS[group_id][leave_id]['id']
    await session.send('有群员(Id: %s)跑路了[CQ:face,id=111]' % (player_id if player_id else '未知'))

@nonebot.scheduler.scheduled_job('cron', hour='11,23', minute=0, second=0, misfire_grace_time=30)
async def _():
    bot = nonebot.get_bot()
    try:
        for group_id in CURRENT_ENABLED.keys():
            logger.info('Updating group members database ...')
            await update_group_members(bot, group_id)
    except Exception as e:
        logger.error(traceback.format_exc())
