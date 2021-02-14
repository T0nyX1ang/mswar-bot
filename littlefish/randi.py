"""
Generate random integers.

Invoke this command by: [begin] [end] [count] [extras]
Available extra commands:
r: allow repetitions
a: ascending order (prior to d)
d: descending order

The command requires to be invoked in groups.
"""

from nonebot import on_command
from nonebot.adapters.cqhttp import Bot, Event
from littlefish._policy import check
from littlefish._exclaim import exclaim_msg
import random

randi = on_command(cmd='randi', aliases={'随机数'}, rule=check('randi'))


def get_randi(begin: int, end: int, count: int, extras: list) -> list:
    """Get random integers from a fixed range."""
    begin, end = min(begin, end), max(begin, end)  # ensure a valid list
    number_range = range(begin, end + 1)
    count = 1 + (count - 1) * (0 < count <= 10)   # shrink range

    if 'r' in extras:  # repetition feature
        result = [random.sample(number_range, 1)[0] for _ in range(0, count)]
    else:
        result = random.sample(number_range, min(count, len(number_range)))

    if 'a' in extras:  # ascending order
        result.sort()
    elif 'd' in extras:  # descending order
        result.sort(reverse=True)

    return result


@randi.handle()
async def randi(bot: Bot, event: Event, state: dict):
    """Generate random integers."""
    args = str(event.message).split()
    try:
        begin = int(args[0])
        end = int(args[1])
        count = int(args[2])
        extras = args[3:]
        result = get_randi(begin, end, count, extras)
        message = '随机结果: %s' % ' '.join(map(str, result))
        await bot.send(event=event, message=message)
    except Exception:
        await bot.send(event=event, message=exclaim_msg('', '3', False, 1))
