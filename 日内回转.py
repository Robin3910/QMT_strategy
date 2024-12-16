# coding:gbk
'''
回测模型示例（非实盘交易策略）

本策略首先买入当前股票10000股
随后根据60s的数据来计算MACD(12,26,9)线,并在MACD>0，MACD_pre<0的时候买入100股,MACD<0,MACD_pre>0的时候卖出100股
但每日操作的股票数不超过原有仓位,并于收盘前把仓位调整至开盘前的仓位
本策略需在个股分钟线下运行
'''
import numpy as np
import pandas as pd
import talib


def init(ContextInfo):
	MarketPosition = {}
	ContextInfo.MarketPosition = MarketPosition  # 初始化持仓
	ContextInfo.set_universe([ContextInfo.stockcode + '.' + ContextInfo.market])
	ContextInfo.first = 0
	ContextInfo.Lots = 100  # 设定交易手数
	ContextInfo.day = [0, 0]
	ContextInfo.ending = 0
	ContextInfo.total = 10000
	ContextInfo.accountID = 'testS'


def handlebar(ContextInfo):
	d = ContextInfo.barpos
	if d < 35:
		return
	startdate = timetag_to_datetime(ContextInfo.get_bar_timetag(d - 35), '%Y%m%d%H%M%S')
	enddate = timetag_to_datetime(ContextInfo.get_bar_timetag(d), '%Y%m%d%H%M%S')
	##print startdate,enddate
	date = timetag_to_datetime(ContextInfo.get_bar_timetag(d), '%Y-%m-%d %H:%M:%S')
	print('日期', date)
	flage = False
	singleemited = False

	df = ContextInfo.get_market_data(['close'], stock_code=ContextInfo.get_universe(), start_time=startdate,
									end_time=enddate, period=ContextInfo.period)
	# print df
	if df.empty:
		return
	# print df
	if ContextInfo.first == 0:
		order_shares(ContextInfo.get_universe()[0], ContextInfo.total, 'fix', df.iloc[-1, 0], ContextInfo,
						ContextInfo.accountID)
		flage = True
		singleemited = True
		ContextInfo.first = 1
		ContextInfo.day[-1] = date[8:10]
		ContextInfo.turnaround = [0, 0]
		ContextInfo.MarketPosition[ContextInfo.get_universe()[0]] = ContextInfo.total
		return

	ContextInfo.day[0] = date

	# 14:55:00之后不再交易
	if int(date[-8:-6] + date[-5:-3]) > 1455:
		return
	avaliable = get_avaliable(ContextInfo.accountID, 'STOCK')

	holding = get_holdings(ContextInfo.accountID, 'STOCK')
	if ContextInfo.get_universe()[0] not in list(holding.keys()):
		holding[ContextInfo.get_universe()[0]] = 0

	# 计算MACD线
	if ContextInfo.total >= 0:
		recent_date = np.array(df.iloc[-35:, 0])

		macd = talib.MACD(recent_date)[0][-1]
		macd_pre = talib.MACD(recent_date)[0][-2]

		# 根据MACD>0则开仓,小于0则平仓

		if date[-8:-3] != '14:55':
			if macd > 0 and macd_pre < 0:
				# 根据MACD>0则开仓,小于0则平仓
				if avaliable > df.iloc[-1, 0] * ContextInfo.Lots * 100:
					order_shares(ContextInfo.get_universe()[0], ContextInfo.Lots, 'fix', df.iloc[-1, 0], ContextInfo,
									ContextInfo.accountID)
					flage = True
					singleemited = True
					ContextInfo.MarketPosition[ContextInfo.get_universe()[0]] += ContextInfo.Lots
					print (ContextInfo.get_universe()[0], 'open position at market price', ContextInfo.Lots, '股')

			elif macd < 0 and macd_pre > 0 and holding[ContextInfo.get_universe()[0]] >= ContextInfo.Lots:
				order_shares(ContextInfo.get_universe()[0], -ContextInfo.Lots, 'fix', df.iloc[-1, 0], ContextInfo,
								ContextInfo.accountID)
				flage = False
				singleemited = True
				print(ContextInfo.get_universe()[0], 'close position at market price', ContextInfo.Lots, '股')
				ContextInfo.MarketPosition[ContextInfo.get_universe()[0]] -= ContextInfo.Lots
			# 临近收盘时若仓位数不等于昨仓则回转所有仓位

		else:
			if ContextInfo.MarketPosition[ContextInfo.get_universe()[0]] > ContextInfo.total:
				order_shares(ContextInfo.get_universe()[0],
								-(ContextInfo.MarketPosition[ContextInfo.get_universe()[0]] - ContextInfo.total), 'fix',
								df.iloc[-1, 0], ContextInfo, ContextInfo.accountID)
				flage = False
				singleemited = True
				# print ContextInfo.get_universe()[0], '回转操作市价单平多仓', ContextInfo.MarketPosition[ContextInfo.get_universe()[0]] - ContextInfo.total, '股'
				ContextInfo.MarketPosition[ContextInfo.get_universe()[0]] = ContextInfo.total

			if ContextInfo.MarketPosition[ContextInfo.get_universe()[0]] < ContextInfo.total:
				order_shares(ContextInfo.get_universe()[0],
								(ContextInfo.total - ContextInfo.MarketPosition[ContextInfo.get_universe()[0]]), 'fix',
								df.iloc[-1, 0], ContextInfo, ContextInfo.accountID)
				flage = True
				singleemited = True
				# print ContextInfo.get_universe()[0], '回转操作市价单开多仓', ContextInfo.total - ContextInfo.MarketPosition[ContextInfo.get_universe()[0]] , '股'
				ContextInfo.MarketPosition[ContextInfo.get_universe()[0]] = ContextInfo.total

		# 更新过去的日期数据
		'''ContextInfo.day[-1] = ContextInfo.day[0]
		if singleemited:
			if flage:
				ContextInfo.paint('do_buy',1,-1,0,"yellow",'noaxis')
				ContextInfo.paint('do_sell',0,-1,0,"red",'noaxis')
			else:
				ContextInfo.paint('do_buy',0,-1,0,"yellow",'noaxis')
				ContextInfo.paint('do_sell',1,-1,0,"red",'noaxis')'''


# ContextInfo.paint('holding',ContextInfo.MarketPosition[ContextInfo.get_universe()[0]],-1,0)

def get_avaliable(accountid, datatype):
	result = 0
	resultlist = get_trade_detail_data(accountid, datatype, "ACCOUNT")
	for obj in resultlist:
		result = obj.m_dAvailable
	return result


def get_holdings(accountid, datatype):
	holdinglist = {}
	resultlist = get_trade_detail_data(accountid, datatype, "POSITION")
	for obj in resultlist:
		holdinglist[obj.m_strInstrumentID + "." + obj.m_strExchangeID] = obj.m_nCanUseVolume
	return holdinglist









