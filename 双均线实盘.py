#encoding:gbk
import pandas as pd
import numpy as np
import datetime

"""
示例说明：双均线实盘策略，通过计算快慢双均线，在金叉时买入，死叉时做卖出
"""

class a():
	pass
A = a() #创建空的类的实例 用来保存委托状态 
#ContextInfo对象在盘中每次handlebar调用前都会被深拷贝, 如果调用handlebar的分笔不是k线最后分笔 ContextInfo会被回退到深拷贝的内容 所以ContextInfo不能用来记录快速交易的信号

def init(C):
	A.stock= C.stockcode + '.' + C.market #品种为模型交易界面选择品种
	A.acct= account #账号为模型交易界面选择账号
	A.acct_type= accountType #账号类型为模型交易界面选择账号
	A.amount = 10000 #单笔买入金额 触发买入信号后买入指定金额
	A.line1=17   #快线周期
	A.line2=27   #慢线周期
	A.waiting_list = [] #未查到委托列表 存在未查到委托情况暂停后续报单 防止超单
	A.buy_code = 23 if A.acct_type == 'STOCK' else 33 #买卖代码 区分股票 与 两融账号
	A.sell_code = 24 if A.acct_type == 'STOCK' else 34
	#设置股票池 订阅品种行情
	C.set_universe([A.stock])
	print(f'双均线实盘示例{A.stock} {A.acct} {A.acct_type} 单笔买入金额{A.amount}')

def handlebar(C):
	#跳过历史k线
	if not C.is_last_bar():
		return
	now = datetime.datetime.now()
	now_time = now.strftime('%H%M%S')
	#跳过非交易时间
	if now_time < '093000' or now_time > "150000":
		return
	account = get_trade_detail_data(A.acct, A.acct_type, 'account')
	if len(account)==0:
		print(f'账号{A.acct} 未登录 请检查')
		return
	account = account[0]
	available_cash = int(account.m_dAvailable)
	#如果有未查到委托 查询委托
	if A.waiting_list:
		found_list = []
		orders = get_trade_detail_data(A.acct, A.acct_type, 'order')
		for order in orders:
			if order.m_strRemark in A.waiting_list:
				found_list.append(order.m_strRemark)
		A.waiting_list = [i for i in A.waiting_list if i not in found_list]
	if A.waiting_list:
		print(f"当前有未查到委托 {A.waiting_list} 暂停后续报单")
		return
	holdings = get_trade_detail_data(A.acct, A.acct_type, 'position')
	holdings = {i.m_strInstrumentID + '.' + i.m_strExchangeID : i.m_nCanUseVolume for i in holdings}
	#获取行情数据
	data = C.get_history_data(max(A.line1, A.line2)+1, '1d', 'close',dividend_type='front_ratio')
	close_list = data[A.stock]
	if len(close_list) < max(A.line1, A.line2)+1:
		print('行情长度不足(新上市或最近有停牌) 跳过运行')
		return
	pre_line1 = np.mean(close_list[-A.line1-1: -1])
	pre_line2 = np.mean(close_list[-A.line2-1: -1])
	current_line1 = np.mean(close_list[-A.line1:])
	current_line2 = np.mean(close_list[-A.line2:])
	#如果快线穿过慢线,则买入委托 当前无持仓 买入
	vol = int(A.amount / close_list[-1] / 100) * 100 #买入数量 向下取整到100的整数倍
	if A.amount < available_cash and vol >= 100 and A.stock not in holdings and pre_line1 < pre_line2 and current_line1 > current_line2:
		#下单开仓 ，参数说明可搜索PY交易函数 passorder
		msg = f"双均线实盘 {A.stock} 上穿均线 买入 {vol}股"
		passorder(A.buy_code, 1101, A.acct, A.stock, 14, -1, vol, '双均线实盘', 1 , msg, C)
		print(msg)
		A.waiting_list.append(msg)
	#如果快线下穿慢线,则卖出委托
	if A.stock in holdings and holdings[A.stock] > 0 and pre_line1 > pre_line2 and current_line1 < current_line2:
		msg = f"双均线实盘 {A.stock} 下穿均线 卖出 {holdings[A.stock]}股"
		passorder(A.sell_code, 1101, A.acct, A.stock, 14, -1, holdings[A.stock], '双均线实盘', 1 , msg, C)
		print(msg)
		A.waiting_list.append(msg)
