#encoding:gbk

import time
lock = 0


def init(ContextInfo):
	# 填写股票的资金账号
	ContextInfo.accountid = str(account)
	ContextInfo.stock = ContextInfo.stockcode+'.'+ContextInfo.market
	ContextInfo.sh = '204001.SH'
	ContextInfo.sz = '131810.SZ'
	ContextInfo.time = end_time
	ContextInfo.min_price = min_price
	print('price_type',price_type)
	back_price_type_dict = {0:'SALE5',1:'SALE4',2:'SALE3',3:'SALE2',4:'SALE1',5:'LATEST',6:'BUY1',
	7:'BUY2',8:'BUY3',9:'BUY4',10:'BUY5',12:'MARKET',13:'HANG',14:'COMPETE'}
	ContextInfo.price_type = back_price_type_dict[price_type]
	"""
	style下单选价类型：LATEST最新,FIX指定,HANG挂单,COMPETE对手,MARKET涨跌停价,SALE5,SALE4,SALE3,SALE2,SALE1卖5-1,BUY1,BUY2,BUY3,BUY4,BUY5买1-5
	"""
	'''
	下单选价类型：
	LATEST 最新, HANG 挂单, COMPETE 对手,MARKET 市价, 
	SALE5, SALE4, SALE3, SALE2, SALE1,   卖5-1
	BUY1, BUY2, BUY3, BUY4, BUY5         买5-1
	'''

	ContextInfo.num = 1000

def handlebar(ContextInfo):
	global lock
	if not ContextInfo.period == 'tick':
		print ('警告！当前运行周期有误，运行周期请选择分笔线！后续操作已停止！')
		return
	if not ContextInfo.is_last_bar():
		return
	pc_time = time.strftime("%H%M%S")
	if pc_time > "153000":
		print("逆回购交易时间已过")
		lock = 1
		return
	avaliable = get_avaliable(ContextInfo.accountid,'STOCK')
	price = ContextInfo.get_full_tick([ContextInfo.sh, ContextInfo.sz])
	if ContextInfo.sh in price:
		sh_price = price[ContextInfo.sh]['lastPrice']
	else:
		sh_price = 0
	if ContextInfo.sz in price:
		sz_price = price[ContextInfo.sz]['lastPrice']
	else:
		sz_price = 0
	if sh_price == sz_price == 0:
		print('未取到价格，跳过，等待能取到价格')
		return
	else:
		if sh_price > sz_price:
			sell_code = ContextInfo.sh
			sell_price = sh_price
		else:
			sell_code = ContextInfo.sz
			sell_price = sz_price
	now = int(timetag_to_datetime(ContextInfo.get_bar_timetag(ContextInfo.barpos),"%H%M%S"))
	now = int(pc_time)
	if ContextInfo.is_last_bar()==True and lock == 0 and now > int(ContextInfo.time):
		lots = int((avaliable*(1-0.0001))//1000*10)
		if sell_price > ContextInfo.min_price :
			passorder(24, 1101,
				ContextInfo.accountid, 
				sell_code,
				price_type,
				sell_price,
				lots,  # * 100即为面额
				2,
				ContextInfo
				)
			print("可用资金:%.2f万元, 卖出逆回购 %d 元"%(avaliable*0.0001, avaliable//1000))
			lock = 1
	elif now <= ContextInfo.time:
		print("逆回购未到开始时间")

	print (int(timetag_to_datetime(ContextInfo.get_bar_timetag(ContextInfo.barpos),"%H%M%S")))


# 取可用资金
def get_avaliable(accountid,datatype):
	result=0
	resultlist=get_trade_detail_data(accountid,datatype,"ACCOUNT")
	for obj in resultlist:
		 result=obj.m_dAvailable
	return result