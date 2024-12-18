# 创建交易对象
# 创建xt_trader对象需要两个参数：
# path：路径，就是安装QMT软件的文件下下的/userdata_mini文件夹。
# session_id : 回话id，当创建多个xt_trader对象时，需要不同，这里我们用6位随机数字生成。

import random
from xtquant.xttrader import XtQuantTrader

path = r'D:\qmt\userdata_mini'
session_id = int(random.randint(100000, 999999))
xt_trader = XtQuantTrader(path, session_id)


# 链接QMT
# 执行xt_trader.connect()，需要保证已登录QMT极简模式并保持客户端运行状态，即可连接成功。非极简模式进入客户端，是连接不成功了，亲测。

xt_trader.start()

connect_result = xt_trader.connect()

print(connect_result)

if connect_result == 0:
    print('连接成功')


# 这一步是用来订阅资金账户的，注意需要替换成你正在登录的资金账户号，订阅成功subscribe_result会是0，不成功是-1
from xtquant.xttype import StockAccount

acc = StockAccount('自己的账户')
subscribe_result = xt_trader.subscribe(acc)
print(subscribe_result)

# 下单，xtconstant.STOCK_BUY表单下单类型是买入，xtconstant.FIX_PRICE代表报价类型是限价，执行成功后，在miniQMT终端里，就直接可以看到委托记录，这就可以确认，我们的委托成功了
from xtquant import xtconstant

stock_code = '000429.SZ'

order_id = xt_trader.order_stock(acc, stock_code, xtconstant.STOCK_BUY, 300, xtconstant.FIX_PRICE, 7.5)
print(order_id)