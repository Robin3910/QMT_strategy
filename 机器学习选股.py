#coding:gbk
#!/usr/bin/python
"""
回测模型示例（非实盘交易策略）

#单股机器学习模型，在主图下直接运行即可
#模型中以过去15个交易日数据生成特征变量以预测5个交易日后的涨跌，
#特征变量我们选取了平均收盘价，平均成交量，平均最高价，平均最低价，总收益，收盘价的标准差
#训练结束后，回测过程中在每个星期一预测本周五的涨跌，以此为据开仓
"""
import pandas as pd
import numpy as np
import time
from datetime import *
from sklearn import svm
import traceback
def init(ContextInfo):
	ContextInfo.stock = ContextInfo.stockcode + '.' + ContextInfo.market
	ContextInfo.set_universe([ContextInfo.stock])
	ContextInfo.holding = 0
	ContextInfo.days = 0
	ContextInfo.money = ContextInfo.capital
	ContextInfo.accountid = "testS"

def handlebar(ContextInfo):
	buy_condition = False
	sell_condition = False
	d = ContextInfo.barpos
	if ContextInfo.days == 0:
		#用20160101到20170101一年间的数据生成训练集
		df = ContextInfo.get_market_data(['open','high','low','close','volume'],stock_code=[ContextInfo.stock],start_time='20160101',end_time='20170101',dividend_type='front')
		df = df.sort_index()
		days = df.index.values
		days_close = df['close'].values
		print('start training SVM')
		x_all = []
		y_all = []
		for i in range(14, len(days) - 5):
			start_day = days[i - 14]
			end_day = days[i]
			data = ContextInfo.get_market_data(['open','high','low','close','volume'],stock_code=[ContextInfo.stock],end_time=end_day,count=15,skip_paused=False,dividend_type='front')
			data = data.sort_index()
			open = data['open'].values
			close = data['close'].values
			max = data['high'].values
			min = data['low'].values
			volume = data['volume'].values
			close_mean = close[-1] / np.mean(close)
			volume_mean = volume[-1] / np.mean(volume)
			max_mean = max[-1] / np.mean(max)
			min_mean = min[-1] / np.mean(min)
			vol = volume[-1]
			return_now = close[-1] / close[0]
			std = np.std(np.array(close), axis = 0)
			#features用于存放因子
			features = [close_mean, volume_mean, max_mean, min_mean, vol, return_now, std]           #计算出的6个因子作为特征
			x_all.append(features)

		for i in range(len(days_close) - 19):
			if days_close[i+19] > days_close[i+14]:
				label = 1
			else:
				label = 0
			y_all.append(label)
		x_train = x_all[:-1]
		y_train = y_all[:-1]

		ContextInfo.clf = svm.SVC(C=1.0, kernel='rbf', degree=3, gamma='auto', coef0=0.0, shrinking=True, probability=False,tol=0.001, cache_size=200, verbose=False, max_iter=-1, decision_function_shape='ovr', random_state=None)
		try:
			ContextInfo.clf.fit(x_train, y_train)
		except:
			e = traceback.format_exc()
			print(('value error, bar:', e))
		print('training finish!')

	timetag = ContextInfo.get_bar_timetag(d)
	timetag_start = ContextInfo.get_bar_timetag(d-15)
	timetag_end = ContextInfo.get_bar_timetag(d-1)           #过去15个交易日的起止时间

	today = timetag_to_datetime(timetag, '%Y%m%d')
	start_date = timetag_to_datetime(timetag_start, '%Y%m%d')
	end_date = timetag_to_datetime(timetag_end, '%Y%m%d')
	weekday = datetime.strptime(today, '%Y%m%d').isoweekday()
	open_today = ContextInfo.get_market_data(['open'],stock_code=[ContextInfo.stock],skip_paused=False,dividend_type='front')
	close_today = ContextInfo.get_market_data(['close'],stock_code=[ContextInfo.stock],skip_paused=False,dividend_type='front')
	#print ContextInfo.holding
	#print weekday
	if ContextInfo.holding == 0 and weekday == 1:            #每个星期一判断是否开仓
		data = ContextInfo.get_market_data(['open','high','low','close','volume'],stock_code=[ContextInfo.stock],end_time=end_date,count=15,skip_paused=False, dividend_type='front')
		data = data.sort_index()
		close = data['close'].values
		max = data['high'].values
		min = data['low'].values
		volume = data['volume'].values
		close_mean = close[-1] / np.mean(close)
		volume_mean = volume[-1] / np.mean(volume)
		max_mean = max[-1] / np.mean(max)
		min_mean = min[-1] / np.mean(min)
		vol = volume[-1]
		return_now = close[-1] / close[0]
		std = np.std(np.array(close), axis = 0)

		features = [close_mean, volume_mean, max_mean, min_mean, vol, return_now, std]
		features = np.array(features).reshape(1, -1)
		try:
			prediction = ContextInfo.clf.predict(features)[0]
			if prediction == 1:
				ContextInfo.holding = int(ContextInfo.money*0.95/(open_today))/100
				order_shares(ContextInfo.stock,ContextInfo.holding*100,'fix',open_today,ContextInfo,ContextInfo.accountid)
				ContextInfo.buyprice = open_today
				buy_condition = True
				print(today)
				print('open long position to 0.95')
		except :
			print(('predict error occur,bar:', d))
	elif ContextInfo.holding > 0 and close_today/ContextInfo.buyprice >= 1.1:        #每个交易日判断止盈止损
		order_shares(ContextInfo.stock,-ContextInfo.holding*100,'fix',close_today,ContextInfo,ContextInfo.accountid)
		ContextInfo.holding = 0
		sell_condition = True
		print(today)
		print('reach profit stop limit, close position')
	elif ContextInfo.holding > 0 and close_today/ContextInfo.buyprice < 0.98 and weekday == 5:
		order_shares(ContextInfo.stock,-ContextInfo.holding*100,'fix',close_today,ContextInfo,ContextInfo.accountid)
		ContextInfo.holding = 0
		sell_condition = True
		print(today)
		print('reach lose stop limit, close position')
	ContextInfo.days += 1

	ContextInfo.paint('do_buy', int(buy_condition), -1, 0)
	ContextInfo.paint('do_sell', int(sell_condition), -1, 0)
























