#  csgo查询工具

![Static Badge](https://img.shields.io/badge/v3.10.*-blue?style=flat&logo=python&logoColor=white&labelColor=gray)


## install

```bash
pip install -r requirements.txt
```

## usage

```bash
python win_main.py
```

## 使用说明

- 导入账号格式为`account:password`，一行一个账号，不需要邮箱和邮箱密码。
- maFile放置位置为`./maFiles/{steam_id}.maFile`或者`./maFiles/{account}.maFile`。都可识别。


## feature

|   功能    |              说明               |
|:-------:|:-----------------------------:|
|  检查掉落   |        检查最近掉落的物品、掉落日期         |
| 检查个人信息  | 检查个人信息（等级、目前经验值、本周挂箱状态）、VAC状态 |
|  日志输出   |       显示稀有掉落、以及本周未升级账号        |
|  导出功能   |    右键菜单导出功能(稀有掉落、未升级、VAC)     |
|  数据库存储  |     使用sqlite3存储数据，减少请求次数      |
|  机场胜场   |          显示机场地图的胜场数据          |
| 国家地区/余额 |         显示国家地区以及对应余额          |
|  每周箱子   |        每周普通箱子的数据统计         |

## todo
~~- [ ] 查询API化~~
- [ ] 根据地图检查CSGO胜场的功能
- [ ] 红信检查

## changelog
- 修改登录要求格式 不需要邮箱和邮箱密码
- 增加了检查个人信息、VAC状态的功能。
- 增加sqlite3数据库存储数据，不用每次都请求。
- 增加日志输出，会显示稀有掉落以及本周未掉落箱子的账号
- 减少登录次数，防止api限制。
- 右键菜单新增导出功能
- 优化了信息显示
- 调整db结构以及资源路径
- mac版本编译成功&windows版本编辑成功
- 修复了一些bug
- 增加了机场胜场的功能
- 增加了国家、余额
- fix vac检测不正确问题
- fix 读取缓存时的问题
- add 每周普通箱子的数据统计