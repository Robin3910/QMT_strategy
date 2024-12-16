#coding:gbk

#导入常用库
import pandas as pd
import numpy as np
import talib
#示例说明：本策略，通过计算快慢双均线，在金叉时买入，死叉时做卖出 点击回测运行 主图选择要交易的股票品种

def init(C):
	#init handlebar函数的入参是ContextInfo对象 可以缩写为C
	#设置测试标的为主图品种
	C.stock= C.stockcode + '.' +C.market
	#line1和line2分别为两条均线期数
	C.line1=10   #快线参数
	C.line2=20   #慢线参数
	#accountid为测试的ID 回测模式资金账号可以填任意字符串
	C.accountid = "testS"  

def handlebar(C):
	#当前k线日期
	bar_date = timetag_to_datetime(C.get_bar_timetag(C.barpos), '%Y%m%d%H%M%S')
	#回测不需要订阅最新行情使用本地数据速度更快 指定subscribe参数为否. 如果回测多个品种 需要先下载对应周期历史数据 
	local_data = C.get_market_data_ex(['close'], [C.stock], end_time = bar_date, period = C.period, count = max(C.line1, C.line2), subscribe = False)
	close_list = list(local_data[C.stock].iloc[:, 0])
	#将获取的历史数据转换为DataFrame格式方便计算
	#如果目前未持仓，同时快线穿过慢线，则买入8成仓位
	if len(close_list) <1:
		print(bar_date, '行情不足 跳过')
	line1_mean = round(np.mean(close_list[-C.line1:]), 2)
	line2_mean = round(np.mean(close_list[-C.line2:]), 2)
	print(f"{bar_date} 短均线{line1_mean} 长均线{line2_mean}")
	account = get_trade_detail_data('test', 'stock', 'account')
	account = account[0]
	available_cash = int(account.m_dAvailable)
	holdings = get_trade_detail_data('test', 'stock', 'position')
	holdings = {i.m_strInstrumentID + '.' + i.m_strExchangeID : i.m_nVolume for i in holdings}
	holding_vol = holdings[C.stock] if C.stock in holdings else 0
	if holding_vol == 0 and line1_mean > line2_mean:
		vol = int(available_cash / close_list[-1] / 100) * 100
		#下单开仓
		passorder(23, 1101, C.accountid, C.stock, 5, -1, vol, C)
		print(f"{bar_date} 开仓")
		C.draw_text(1, 1, '开')
	#如果目前持仓中，同时快线下穿慢线，则全部平仓
	elif holding_vol > 0 and line1_mean < line2_mean:
		#状态变更为未持仓
		C.holding=False
		#下单平仓
		passorder(24, 1101, C.accountid, C.stock, 5, -1, holding_vol, C)
		print(f"{bar_date} 平仓")
		C.draw_text(1, 1, '平')
