"""
Generate random integers.

Invoke this command by: [begin] [end] [count] [extras]
Available extra commands:
r: allow repetitions
a: ascending order (prior to d)
d: descending order

The command requires to be invoked in groups.
"""

import random
from nonebot import on_command
from nonebot.adapters.cqhttp import Bot, Event
from littlefish._policy.rule import check
from littlefish._exclaim import exclaim_msg


def get_randi(begin: int, end: int, count: int, extras: list) -> list:
    """Get random integers from a fixed range."""
    begin, end = min(begin, end), max(begin, end)  # ensure a valid list
    number_range = range(begin, end + 1)
    count = 1 + (count - 1) * (0 < count <= 10)  # shrink range

    if 'r' in extras:  # repetition feature
        result = [random.sample(number_range, 1)[0] for _ in range(0, count)]
    else:
        result = random.sample(number_range, min(count, len(number_range)))

    if 'a' in extras:  # ascending order
        result.sort()
    elif 'd' in extras:  # descending order
        result.sort(reverse=True)

    return result


randi = on_command(cmd='randi ', aliases={'随机数 '}, rule=check('randi'))


@randi.handle()
async def _(bot: Bot, event: Event, state: dict):
    """Handle the randi command."""
    args = str(event.message).split()
    try:
        begin = int(args[0])
        end = int(args[1])
        count = int(args[2])
        extras = args[3:]
        result = get_randi(begin, end, count, extras)
        message = '随机结果: %s' % ' '.join(map(str, result))
        await randi.send(message=message)
    except Exception:
        await randi.send(message=exclaim_msg('', '3', False, 1))
