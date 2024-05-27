import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

'''
正则最近掉落记录
'''

def regex_seesion_check(text):
    soup = BeautifulSoup(text, 'html.parser')
    # 找到 youraccount_steamid
    youraccount_steamid = soup.find("div", class_="youraccount_steamid")
    if youraccount_steamid:
        return True
    else:
        return False

def regex_recently_dropped(text, num=2):
    inventory_list = []
    soup = BeautifulSoup(text, 'html.parser')

    # 找到所有的交易历史记录
    trade_history_rows = soup.find_all("div", class_="tradehistoryrow")

    # 初始化一个列表来收集符合条件的记录
    matched_records = []

    # 对每一条记录进行处理
    for row in trade_history_rows:
        event_description = row.find("div", class_="tradehistory_event_description").get_text(strip=True)
        if "已提升到新等级并获得物品掉落" in event_description:
            # 如果记录符合条件，加入到列表中
            matched_records.append(row)

    # matched_records 包含了所有符合条件的记录
    # 从这个列表中提取前两条记录
    for row in matched_records[:num]:
        date = row.find("div", class_="tradehistory_date").get_text(strip=True)
        item_name = row.find("span", class_="history_item_name").get_text(strip=True)
        inventory_list.append({
            'date': date,
            'item_name': item_name
        })
    return inventory_list


'''
正则csgo信息
'''


def regex_vac_status(text):
    soup = BeautifulSoup(text, 'html.parser')
    # 找到vac状态
    vac_status = soup.find("div", class_="no_vac_bans_header")
    ban_vac_status = soup.find("div", class_="no_vac_bans_header")
    # 如果存在,则vac为0
    if vac_status:
        vac = 0
        vac_mes = '无封禁'
    elif ban_vac_status:
        vac = 1
        vac_mes = '有封禁'
    else:
        vac = -1
        vac_mes = '未知'
    return vac, vac_mes


def regex_match_making(text, map_name='Vertigo'):
    soup = BeautifulSoup(text, 'html.parser')
    # 正则表达式模式，使用format方法将地图名插入到正则表达式中
    pattern = re.compile(
        r'<tr>\s*<td>竞技模式</td>\s*<td>{}</td>\s*<td>(\d+)</td>\s*<td>(\d+)</td>\s*<td>(\d+)</td>\s*<td>([^<]*)</td>\s*<td>([^<]+)</td>\s*<td>(\d+)</td>\s*</tr>'.format(re.escape(map_name))
    )

    # 使用正则表达式查找匹配的内容
    matches = pattern.findall(str(soup))
    if not matches:
        return None
    # 返回匹配到胜利次数
    print(matches[0])
    return int(matches[0][0])

def regex_csgo_account_info(text):
    account_info = []

    soup = BeautifulSoup(text, 'html.parser')
    info_rows = soup.find_all("div", class_="generic_kv_line")
    rank = None
    exp = None
    for row in info_rows:
        # 获取文本内容
        kv = row.get_text(strip=True)
        # 通过:分割字符串
        key, value = kv.split(": ", 1)
        # 如果 key == CS:GO Profile Rank
        if key == "CS:GO Profile Rank":
            rank = value.strip()
        # 如果 key == Experience points earned towards next rank
        if key == "Experience points earned towards next rank":
            exp = value.strip()
    account_info = {
        'rank': rank,
        'exp': exp
    }
    return account_info


# 定义函数来将字符串转换为 datetime 对象
def parse_datetime(date_str):
    # 使用正则表达式提取年、月、日、上午/下午、小时和分钟信息
    pattern = r"(\d{4}) 年 (\d{1,2}) 月 (\d{1,2}) 日(上午|下午) (\d{1,2}):(\d{1,2})"
    match = re.match(pattern, date_str)

    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        ampm = match.group(4)
        hour = int(match.group(5))
        minute = int(match.group(6))

        # 上午下午转换小时
        if ampm == "下午" and hour != 12:
            hour += 12

    else:
        return None
    # 返回 datetime 对象
    return datetime(int(year), int(month), int(day), int(hour), int(minute))


def is_this_week_drop(date_str):
    # 将日期字符串转换为 datetime 对象
    date = parse_datetime(date_str)
    if date is None:
        return False
    # 获取当前日期和时间
    now = datetime.now()
    # 计算当前日期是本周的第几天（周一为0，周二为1，...，周日为6）
    current_weekday = now.weekday()

    # 计算本周三上午10点的时间
    this_wednesday = now + timedelta((2 - current_weekday) % 7)
    this_wednesday_10am = datetime(this_wednesday.year, this_wednesday.month, this_wednesday.day, 10, 0, 0)

    # 如果现在时间是本周三上午10点之后
    if now > this_wednesday_10am:
        result_time = this_wednesday_10am
    else:
        # 如果现在时间是本周三上午10点之前，则设置为上周三上午10点
        last_wednesday = this_wednesday - timedelta(weeks=1)
        last_wednesday_10am = datetime(last_wednesday.year, last_wednesday.month, last_wednesday.day, 10, 0, 0)
        result_time = last_wednesday_10am
    # 比较日期是否大于本周三上午10点
    if date > result_time:
        return 1
    else:
        return 0
