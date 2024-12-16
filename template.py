#coding:gbk
#! /usr/bin/python 

def init(ContextInfo):
	#init初始设定函数,无设定则直接pass
	pass

def handlebar(ContextInfo):
	#handlebar 逐跟K线调用运行函数
        
	#当前K线的对应的下标从0开始
	index = ContextInfo.barpos
	
	#当前K线对应的时间：毫秒
	realtime = ContextInfo.get_bar_timetag(index)

	#当前周期
	period = ContextInfo.period
	
	#当前主图复权方式
	dividend_type = ContextInfo.dividend_type
	
	#取当前K线图对应的合约当前K线的当前主图复权方式下的收盘价
	close = ContextInfo.get_market_data(['close'],period=period,dividend_type=dividend_type)
	
	#在图上画出close的曲线图
	ContextInfo.paint('close',close,-1,0)

