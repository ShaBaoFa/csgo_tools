#  csgo查询工具

![Static Badge](https://img.shields.io/badge/v3.10.*-blue?style=flat&logo=python&logoColor=white&labelColor=gray)

## background
>在
>[**steam-check-recently-dropped**](https://github.com/Cra2yQi/steam-check-recently-dropped)
>的基础上进行了修改，增加了检查个人信息、VAC状态的功能。

## install

```bash
    pip install -r requirements.txt
```

## usage

```bash
    python win_main.py
```

## feature

| 功能 |              说明               |
| :---: |:-----------------------------:|
| 检查掉落 |        检查最近掉落的物品、掉落日期         |
| 检查个人信息 | 检查个人信息（等级、目前经验值、本周挂箱状态）、VAC状态 |

## todo
- [ ] 查询API化
- [ ] 根据地图检查CSGO胜场的功能
- [ ] 红信检查

## changelog
- 修改登录要求格式 不需要邮箱和邮箱密码
- 增加了检查个人信息、VAC状态的功能。
- 增加sqlite3数据库存储数据，不用每次都请求。
- 增加日志输出，会显示稀有掉落以及本周未掉落箱子的账号