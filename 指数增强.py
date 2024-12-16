#coding:gbk
'''
回测模型示例（非实盘交易策略）

本策略以0.8为初始权重跟踪指数标的沪深300中权重大于0.35%的成份股.
个股所占的百分比为(0.8*成份股权重)*100%.然后根据个股是否:
1.连续上涨5天 2.连续下跌5天
来判定个股是否为强势股/弱势股,并对其把权重由0.8调至1.0或0.6'''
#在指数（例如HS300）日线下运行
import numpy as np

def init(ContextInfo):
	#设置股票池
	stock300 =ContextInfo.get_stock_list_in_sector('沪深300')
	ContextInfo.stock300_weight = {}
	stock300_symbol = []
	stock300_weightlist = [] 
	ContextInfo.index_code = ContextInfo.stockcode+"."+ContextInfo.market
	for key in stock300:
		# 保留权重大于0.35%的成份股
		
		if (ContextInfo.get_weight_in_index(ContextInfo.index_code, key) / 100) > 0.0035:
			stock300_symbol.append(key)
			ContextInfo.stock300_weight[key] = ContextInfo.get_weight_in_index(ContextInfo.index_code, key) / 100
			stock300_weightlist.append(ContextInfo.get_weight_in_index(ContextInfo.index_code, key) / 100)
	print('选择的成分股权重总和为: ', np.sum(stock300_weightlist)) 
	ContextInfo.set_universe(stock300_symbol)
	
	#print ContextInfo.stock300_weight
	# 资产配置的初始权重,配比为0.6-0.8-1.0
	ContextInfo.ratio = 0.8

	#账号
	ContextInfo.accountid = "testS"

def handlebar(ContextInfo):
	buy_sum = 0
	sell_sum = 0
	index  = ContextInfo.barpos
	realtimetag = ContextInfo.get_bar_timetag(index)
	print(timetag_to_datetime(realtimetag, '%Y%m%d %H:%M:%S'))
	dict_close=ContextInfo.get_history_data(7,'1d','close',3)
	#持仓市值
	holdvalue = 0
	#持仓
	holdings=get_holdings(ContextInfo.accountid,"STOCK")
	#剩余资金
	surpluscapital=get_avaliablecost(ContextInfo.accountid,"STOCK")
	for stock in ContextInfo.stock300_weight:
		if  stock  in holdings:
			if len(dict_close[stock]) == 7:
				holdvalue += dict_close[stock][-2] * holdings[stock]
	
	for stock in ContextInfo.stock300_weight:
		# 若没有仓位则按照初始权重开仓
		if  stock not in holdings and stock in list(dict_close.keys()):
			if len(dict_close[stock]) == 7:
				pre_close = dict_close[stock][-1]
				buy_num = int(ContextInfo.stock300_weight[stock] * ( holdvalue + surpluscapital ) *ContextInfo.ratio / pre_close /100)
				order_shares(stock,buy_num*100,'fix',pre_close,ContextInfo,ContextInfo.accountid)
				buy_sum += 1
				#print "买入",stock,buy_num
		elif stock in list(dict_close.keys()):
			if len(dict_close[stock]) == 7:
				diff = np.array(dict_close[stock][1:6]) - np.array(dict_close[stock][:-2])
				pre_close = dict_close[stock][-1]
				buytarget_num = int(ContextInfo.stock300_weight[stock] * ( holdvalue + surpluscapital ) * (ContextInfo.ratio + 0.2)/ pre_close /100)
				selltarget_num = int(ContextInfo.stock300_weight[stock] * ( holdvalue + surpluscapital ) *(ContextInfo.ratio - 0.2)/ pre_close /100)
				# 获取过去5天的价格数据,若连续上涨则为强势股,调仓到（权重+0.2）的仓位
				if all(diff>0) and holdings[stock] < buytarget_num:
					buy_num = buytarget_num - holdings[stock]
					order_shares(stock,buy_num*100,'fix',pre_close,ContextInfo,ContextInfo.accountid)
					buy_sum += 1
					#print "买入",stock,buy_num
				# 获取过去5天的价格数据,若连续下跌则为弱势股,调仓到（权重-0.2）的仓位
				elif all(diff<0) and holdings[stock] > selltarget_num:
					sell_num = holdings[stock] - selltarget_num
					order_shares(stock,(-1.0)*sell_num*100,'fix',pre_close,ContextInfo,ContextInfo.accountid)
					sell_sum += 1
					#print "卖出",stock,sell_num
	if not ContextInfo.do_back_test:
		ContextInfo.paint('buy_num', buy_sum, -1, 0)
		ContextInfo.paint('sell_num', sell_sum, -1, 0)
					
def get_holdings(accountid,datatype):
	holdinglist={}
	resultlist=get_trade_detail_data(accountid,datatype,"POSITION")
	for obj in resultlist:
		holdinglist[obj.m_strInstrumentID+"."+obj.m_strExchangeID]=obj.m_nVolume/100
	return holdinglist

def get_avaliablecost(accountid,datatype):
	result=0
	resultlist=get_trade_detail_data(accountid,datatype,"ACCOUNT")
	for obj in resultlist:
		 result=obj.m_dAvailable
	return result

