# encoding: UTF-8
"""
CTP的底层接口来自VNPY,大佬bigtan帮助编译的python3版本
"""
from modules.vnctpmd import MdApi
from modules.vnctptd import TdApi
from modules.eventEngine import *
from modules.eventType import *
from modules.ctpDataType import *
from modules.objects import *

from time import sleep
from datetime import datetime, time
import random
import os
from copy import copy

# 以下为一些VT类型和CTP类型的映射字典
# 价格类型映射
priceTypeMap = {}
priceTypeMap[PRICETYPE_LIMITPRICE] = defineDict["THOST_FTDC_OPT_LimitPrice"]
priceTypeMap[PRICETYPE_MARKETPRICE] = defineDict["THOST_FTDC_OPT_AnyPrice"]
priceTypeMapReverse = {v: k for k, v in priceTypeMap.items()} 

# 方向类型映射
directionMap = {}
directionMap[DIRECTION_LONG] = defineDict['THOST_FTDC_D_Buy']
directionMap[DIRECTION_SHORT] = defineDict['THOST_FTDC_D_Sell']
directionMapReverse = {v: k for k, v in directionMap.items()}

# 开平类型映射
offsetMap = {}
offsetMap[OFFSET_OPEN] = defineDict['THOST_FTDC_OF_Open']
offsetMap[OFFSET_CLOSE] = defineDict['THOST_FTDC_OF_Close']
offsetMap[OFFSET_CLOSETODAY] = defineDict['THOST_FTDC_OF_CloseToday']
offsetMap[OFFSET_CLOSEYESTERDAY] = defineDict['THOST_FTDC_OF_CloseYesterday']
offsetMapReverse = {v:k for k,v in offsetMap.items()}

# 交易所类型映射
exchangeMap = {}
exchangeMap[EXCHANGE_CFFEX] = 'CFFEX'
exchangeMap[EXCHANGE_SHFE] = 'SHFE'
exchangeMap[EXCHANGE_CZCE] = 'CZCE'
exchangeMap[EXCHANGE_DCE] = 'DCE'
exchangeMap[EXCHANGE_SSE] = 'SSE'
exchangeMap[EXCHANGE_UNKNOWN] = ''
exchangeMapReverse = {v:k for k,v in exchangeMap.items()}

# 持仓类型映射
posiDirectionMap = {}
posiDirectionMap[DIRECTION_NET] = defineDict["THOST_FTDC_PD_Net"]
posiDirectionMap[DIRECTION_LONG] = defineDict["THOST_FTDC_PD_Long"]
posiDirectionMap[DIRECTION_SHORT] = defineDict["THOST_FTDC_PD_Short"]
posiDirectionMapReverse = {v:k for k,v in posiDirectionMap.items()}

# 产品类型映射
productClassMap = {}
productClassMap[PRODUCT_FUTURES] = defineDict["THOST_FTDC_PC_Futures"]
productClassMap[PRODUCT_OPTION] = defineDict["THOST_FTDC_PC_Options"]
productClassMap[PRODUCT_COMBINATION] = defineDict["THOST_FTDC_PC_Combination"]
productClassMapReverse = {v:k for k,v in productClassMap.items()}

# 委托状态映射
statusMap = {}
statusMap[STATUS_ALLTRADED] = defineDict["THOST_FTDC_OST_AllTraded"]
statusMap[STATUS_PARTTRADED] = defineDict["THOST_FTDC_OST_PartTradedQueueing"]
statusMap[STATUS_NOTTRADED] = defineDict["THOST_FTDC_OST_NoTradeQueueing"]
statusMap[STATUS_CANCELLED] = defineDict["THOST_FTDC_OST_Canceled"]
statusMapReverse = {v:k for k,v in statusMap.items()}

class CtpMdApi(MdApi):
    """
    Demo中的行情API封装
    封装后所有数据自动推送到事件驱动引擎中，由其负责推送到各个监听该事件的回调函数上

    对用户暴露的主动函数包括:
    连接connect
    登陆 login
    订阅合约 subscribe
    """
    def __init__(self, eventEngine):
        """
        API对象的初始化函数
        """
        super(CtpMdApi, self).__init__()

        self.__eventEngine = eventEngine
        
        self.reqID = 0              # 操作请求编号
        
        self.connectionStatus = False       # 连接状态
        self.loginStatus = False            # 登录状态
        
        self.subscribedSymbols = set()      # 已订阅合约代码       
        self.TradingDay = ''
        
        self.userID = ''          # 账号
        self.password = ''        # 密码
        self.brokerID = ''        # 经纪商代码
        self.address = ''         # 服务器地址
        
    def put_log_event(self, log):  # log事件注册
        event = Event(type_=EVENT_LOG)
        event.dict_['log'] = log
        self.__eventEngine.put(event)
        
    def put_alarm_event(self, alarm):  # log事件注册
        event = Event(type_=EVENT_ALARM)
        event.dict_['data'] = alarm
        self.__eventEngine.put(event)
        
    def onFrontConnected(self):
        """服务器连接"""
        self.connectionStatus = True
        
        log = u'行情服务器连接成功'
        self.put_log_event(log)

        self.login()
    #----------------------------------------------------------------------  
    def onFrontDisconnected(self, n):
        """服务器断开"""
        self.connectionStatus = False
        self.loginStatus = False

        log = u'行情服务器连接断开'
        self.put_log_event(log)
        
        now = datetime.now().time()
        if time(8, 48) < now < time(15, 30) or time(20, 48) < now <= time(23, 59) or time(0, 0) < now < time(2, 31):
            alarm = '行情服务器断开连接'
            self.put_alarm_event(alarm)
    #----------------------------------------------------------------------  
    def login(self):
        """登录"""
        # 如果填入了用户名密码等，则登录
        if self.userID and self.password and self.brokerID:
            req = {}
            req['UserID'] = self.userID
            req['Password'] = self.password
            req['BrokerID'] = self.brokerID
            self.reqID += 1
            self.reqUserLogin(req, self.reqID)    
    
    #----------------------------------------------------------------------
    def close(self):
        """关闭"""
        self.exit()
        
    def connect(self, userID, password, brokerID, address):
        """初始化连接"""
        self.userID = userID                # 账号
        self.password = password            # 密码
        self.brokerID = brokerID            # 经纪商代码
        self.address = address              # 服务器地址
        
        # 如果尚未建立服务器连接，则进行连接
        if not self.connectionStatus:
            # 创建C++环境中的API对象，这里传入的参数是需要用来保存.con文件的文件夹路径
            path = os.getcwd() + '/temp/'
            if not os.path.exists(path):
                os.makedirs(path)
            self.createFtdcMdApi(path)
            
            # 注册服务器地址
            self.registerFront(self.address)
            
            # 初始化连接，成功会调用onFrontConnected
            self.init()
            
        # 若已经连接但尚未登录，则进行登录
        else:
            if not self.loginStatus:
                self.login()
                
    def onRtnDepthMarketData(self, data):
        """行情推送"""
        if not data['Volume']:
            return
        
        # 创建对象
        tick = CtaTickData()
        
        tick.symbol = data['InstrumentID']
        tick.exchange = data['ExchangeID']   #exchangeMapReverse.get(data['ExchangeID'], u'未知')
        tick.vtSymbol = tick.symbol #'.'.join([tick.symbol, EXCHANGE_UNKNOWN]) # 只用到ctp一个接口，这里没有必要区分
        
        tick.lastPrice = data['LastPrice']
        tick.volume = data['Volume']
        tick.openInterest = data['OpenInterest']
        

        tick.time = '.'.join([data['UpdateTime'], str(int(data['UpdateMillisec']/100))])
        # 不带毫秒的时间，方便转换datetime
        tick.time2 = data['UpdateTime'] 
        # 把交易日也保存下来，转换datetime用  
        tick.tradedate = self.TradingDay
        # print('tick.tradedate:%s'%tick.tradedate)
        
        # 这里由于交易所夜盘时段的交易日数据有误，所以选择本地获取
        tick.date = datetime.now().strftime('%Y%m%d')   
        
        tick.openPrice = data['OpenPrice']
        tick.highPrice = data['HighestPrice']
        tick.lowPrice = data['LowestPrice']
        tick.preClosePrice = data['PreClosePrice']
        
        tick.upperLimit = data['UpperLimitPrice']
        tick.lowerLimit = data['LowerLimitPrice']
        
        # CTP只有一档行情
        # 无报价时用涨跌停板价替换
        if data['BidPrice1'] > tick.upperLimit:
            tick.bidPrice1 = tick.lowerLimit
        else:
            tick.bidPrice1 = data['BidPrice1']
        if data['AskPrice1'] > tick.upperLimit:
            tick.askPrice1 = tick.upperLimit
        else:
            tick.askPrice1 = data['AskPrice1']
            
        tick.bidVolume1 = data['BidVolume1']
        tick.askVolume1 = data['AskVolume1']
        
        event1 = Event(type_=(EVENT_TICK + data['InstrumentID']))
        event1.dict_['data'] = tick
        self.__eventEngine.put(event1)

        event2 = Event(type_=(EVENT_TICK))
        event2.dict_['data'] = tick
        self.__eventEngine.put(event2)
        
    def subscribe(self, symbol):
        """订阅合约"""
        # 这里的设计是，如果尚未登录就调用了订阅方法
        # 则先保存订阅请求，登录完成后会自动订阅
        if self.loginStatus:
            self.subscribeMarketData(str(symbol))
        self.subscribedSymbols.add(symbol)   
        
    #----------------------------------------------------------------------
    def unsubscribe(self, symbol):
        """退订合约"""
        self.unSubscribeMarketData(str(symbol))
        
    #----------------------------------------------------------------------   
    def onRspError(self, error, n, last):
        """错误回报"""
        log = error['ErrorMsg']
        self.put_log_event(log)
        
    #----------------------------------------------------------------------
    def onRspUserLogin(self, data, error, n, last):
        """登陆回报"""
        # 如果登录成功，推送日志信息
        if error['ErrorID'] == 0:
            self.loginStatus = True
            
            log = u'行情服务器登录完成'
            self.put_log_event(log)
            
            # 重新订阅之前订阅的合约
            for symbol in self.subscribedSymbols:
                self.subscribe(symbol)
                
        # 否则，推送错误信息
        else:
            log = error['ErrorMsg']
            self.put_log_event(log)

    #---------------------------------------------------------------------- 
    def onRspUserLogout(self, data, error, n, last):
        """登出回报"""
        # 如果登出成功，推送日志信息
        if error['ErrorID'] == 0:
            self.loginStatus = False
            self.gateway.mdConnected = False
            
            log = u'行情服务器登出完成'
            self.put_log_event(log)
                
        # 否则，推送错误信息
        else:
            log = error['ErrorMsg'].decode('gbk')
            self.put_log_event(log)
        
    #----------------------------------------------------------------------  
    def onRspSubMarketData(self, data, error, n, last):
        """订阅合约回报"""
        # 通常不在乎订阅错误，选择忽略
        pass
        
    #----------------------------------------------------------------------  
    def onRspUnSubMarketData(self, data, error, n, last):
        """退订合约回报"""
        # 同上
        pass  
        
########################################################################
class CtpTdApi(TdApi):
    """CTP交易API实现"""
    
    #----------------------------------------------------------------------
    def __init__(self, riskengine, eventEngine):
        """API对象的初始化函数"""
        super(CtpTdApi, self).__init__()
        
        self.__eventEngine = eventEngine
        self.__riskengine = riskengine  # 风控引擎

        self.reqID = 0              # 操作请求编号
        self.orderRef = random.randrange(start=1000,stop=9000,step=random.randint(10,100)  )           # 订单编号

        
        self.connectionStatus = False       # 连接状态
        self.loginStatus = False            # 登录状态
        
        self.userID = ''          # 账号
        self.password = ''        # 密码
        self.brokerID = ''        # 经纪商代码
        self.address = ''         # 服务器地址
        
        self.frontID = 0            # 前置机编号
        self.sessionID = 0          # 会话编号

        self.posDict = {}                   # 持仓缓存
        # self.posBufferDict = {}             # 缓存持仓数据的字典
        self.symbolExchangeDict = {}        # 保存合约代码和交易所的映射关系
        self.symbolSizeDict = {}            # 保存合约代码和合约大小的映射关系
        self.symbolNameDict = {}        # 保存合约代码和合约名称的映射关系
        
    #----------------------------------------------------------------------
    def put_log_event(self, log):  # 投放log事件
        event = Event(type_=EVENT_LOG)
        event.dict_['log'] = log
        self.__eventEngine.put(event)
    #----------------------------------------------------------------------
    def onFrontConnected(self):
        """服务器连接"""
        self.connectionStatus = True
    
        log = u'交易服务器连接成功'
        self.put_log_event(log)
    
        self.login()

    #----------------------------------------------------------------------
    def onFrontDisconnected(self, n):
        """服务器断开"""
        self.connectionStatus = False
        self.loginStatus = False
    
        log = u'交易服务器连接断开'
        self.put_log_event(log)
        
    #----------------------------------------------------------------------
    def onRspUserLogin(self, data, error, n, last):
        """登陆回报"""
        # 如果登录成功，推送日志信息
        if error['ErrorID'] == 0:
            self.frontID = str(data['FrontID'])
            self.sessionID = str(data['SessionID'])
            self.loginStatus = True
            
            log = data['UserID'] + u'交易服务器登录完成'
            self.put_log_event(log)
            
            # 确认结算信息
            req = {}
            req['BrokerID'] = self.brokerID
            req['InvestorID'] = self.userID
            self.reqID += 1
            self.reqSettlementInfoConfirm(req, self.reqID)              
                
        # 否则，推送错误信息
        else:
            log = error['ErrorMsg']
            self.put_log_event(log)

    #----------------------------------------------------------------------
    def onRspUserLogout(self, data, error, n, last):
        """登出回报"""
        # 如果登出成功，推送日志信息
        if error['ErrorID'] == 0:
            self.loginStatus = False
            
            log = u'交易服务器登出完成'
            self.put_log_event(log)
                
        # 否则，推送错误信息
        else:
            log = error['ErrorMsg']
            self.put_log_event(log)
    #----------------------------------------------------------------------
    def connect(self, userID, password, brokerID, address):
        """初始化连接"""
        self.userID = userID                # 账号
        self.password = password            # 密码
        self.brokerID = brokerID            # 经纪商代码
        self.address = address              # 服务器地址
        
        # 如果尚未建立服务器连接，则进行连接
        if not self.connectionStatus:
            # 创建C++环境中的API对象，这里传入的参数是需要用来保存.con文件的文件夹路径
            path = os.getcwd() + '/temp/'
            if not os.path.exists(path):
                os.makedirs(path)
            self.createFtdcTraderApi(path)
            
            # 注册服务器地址
            self.registerFront(self.address)
            
            # 初始化连接，成功会调用onFrontConnected
            self.init()
            
        # 若已经连接但尚未登录，则进行登录
        else:
            if not self.loginStatus:
                self.login()    
    
    #----------------------------------------------------------------------
    def login(self):
        """连接服务器"""
        # 如果填入了用户名密码等，则登录
        if self.userID and self.password and self.brokerID:
            req = {}
            req['UserID'] = self.userID
            req['Password'] = self.password
            req['BrokerID'] = self.brokerID
            self.reqID += 1
            self.reqUserLogin(req, self.reqID)   
        
    #----------------------------------------------------------------------
    def qryAccount(self):
        """查询账户"""
        self.reqID += 1
        self.reqQryTradingAccount({}, self.reqID)
        
    #----------------------------------------------------------------------
    def qryPosition(self):
        """查询持仓"""
        self.reqID += 1
        req = {}
        req['BrokerID'] = self.brokerID
        req['InvestorID'] = self.userID
        self.reqQryInvestorPosition(req, self.reqID)
        
    def qryInstrument(self):
        """查询合约"""
        self.reqID += 1
        req = {}
        self.reqQryInstrument(req, self.reqID)

    def qryMarketData(self):
        """查询合约截面数据"""
        self.reqID += 1
        req = {}
        self.reqQryDepthMarketData(req, self.reqID)  # 查询合约截面数据        
    #----------------------------------------------------------------------
    def sendOrder(self, orderReq):
        """发单"""
        self.reqID += 1
        self.orderRef += 1
        
        #风控检查
        if not self.__riskengine.checkRisk(orderReq):
            return
            
        # # 不发单实盘测试
        # log = '接收到委托指令，未发出'
        # self.put_log_event(log)
        # return    
            
        req = {}
        
        req['InstrumentID'] = orderReq.symbol # 合约代码
        req['LimitPrice'] = orderReq.price # 价格
        req['VolumeTotalOriginal'] = orderReq.volume # 数量
        
        # 下面如果由于传入的类型本接口不支持，则会返回空字符串
        req['OrderPriceType'] = priceTypeMap.get(orderReq.priceType, '') # 价格类型
        req['Direction'] = directionMap.get(orderReq.direction, '') # 方向
        req['CombOffsetFlag'] = offsetMap.get(orderReq.offset, '') # 组合标志
            
        req['OrderRef'] = str(self.orderRef) # 报单引用
        req['InvestorID'] = self.userID # 投资者代码
        req['UserID'] = self.userID # 账号
        req['BrokerID'] = self.brokerID # 经纪商代码
        
        req['CombHedgeFlag'] = defineDict['THOST_FTDC_HF_Speculation']       # 投机单
        req['ContingentCondition'] = defineDict['THOST_FTDC_CC_Immediately'] # 立即发单
        req['ForceCloseReason'] = defineDict['THOST_FTDC_FCC_NotForceClose'] # 非强平
        req['IsAutoSuspend'] = 0                                             # 非自动挂起
        req['TimeCondition'] = defineDict['THOST_FTDC_TC_GFD']               # 今日有效
        req['VolumeCondition'] = defineDict['THOST_FTDC_VC_AV']              # 任意成交量
        req['MinVolume'] = 1                                                 # 最小成交量为1
        
        # 判断FAK和FOK
        if orderReq.priceType == PRICETYPE_FAK:
            req['OrderPriceType'] = defineDict["THOST_FTDC_OPT_LimitPrice"]
            req['TimeCondition'] = defineDict['THOST_FTDC_TC_IOC']
            req['VolumeCondition'] = defineDict['THOST_FTDC_VC_AV']
        if orderReq.priceType == PRICETYPE_FOK:
            req['OrderPriceType'] = defineDict["THOST_FTDC_OPT_LimitPrice"]
            req['TimeCondition'] = defineDict['THOST_FTDC_TC_IOC']
            req['VolumeCondition'] = defineDict['THOST_FTDC_VC_CV']        
        
        self.reqOrderInsert(req, self.reqID)
        
        # 返回订单号（字符串），便于某些算法进行动态管理
        return '.'.join(["CTP", str(self.orderRef)])
    #----------------------------------------------------------------------
    def buy(self, symbol, price, vol):  # 多开
        orderReq = CtaOrderReq()
        orderReq.symbol = symbol              # 代码
        orderReq.price = price                # 价格
        orderReq.volume = vol                 # 数量
    
        orderReq.priceType = PRICETYPE_LIMITPRICE           # 价格类型
        orderReq.direction = DIRECTION_LONG           # 买卖
        orderReq.offset = OFFSET_OPEN              # 开平
        
        return self.sendOrder(orderReq)

    def sell(self, symbol, price, vol):  # 多平
        orderReq = CtaOrderReq()
        orderReq.symbol = symbol              # 代码
        orderReq.price = price                # 价格
        orderReq.volume = vol                 # 数量
    
        orderReq.priceType = PRICETYPE_LIMITPRICE           # 价格类型
        orderReq.direction = DIRECTION_SHORT           # 买卖
        orderReq.offset = OFFSET_CLOSE              # 开平

        return self.sendOrder(orderReq)
        
    def selltoday(self, symbol, price, vol):  # 多头平今
        orderReq = CtaOrderReq()
        orderReq.symbol = symbol              # 代码
        orderReq.price = price                # 价格
        orderReq.volume = vol                 # 数量
    
        orderReq.priceType = PRICETYPE_LIMITPRICE           # 价格类型
        orderReq.direction = DIRECTION_SHORT           # 买卖
        orderReq.offset = OFFSET_CLOSETODAY              # 开平

        return self.sendOrder(orderReq)

    def short(self, symbol, price, vol):  # 空开
        orderReq = CtaOrderReq()
        orderReq.symbol = symbol              # 代码
        orderReq.price = price                # 价格
        orderReq.volume = vol                 # 数量
    
        orderReq.priceType = PRICETYPE_LIMITPRICE           # 价格类型
        orderReq.direction = DIRECTION_SHORT           # 买卖
        orderReq.offset = OFFSET_OPEN              # 开平
        
        return self.sendOrder(orderReq)

    def cover(self, symbol, price, vol):  # 空平
        orderReq = CtaOrderReq()
        orderReq.symbol = symbol              # 代码
        orderReq.price = price                # 价格
        orderReq.volume = vol                 # 数量
    
        orderReq.priceType = PRICETYPE_LIMITPRICE       # 价格类型
        orderReq.direction = DIRECTION_LONG             # 买卖
        orderReq.offset = OFFSET_CLOSE                  # 开平

        return self.sendOrder(orderReq)

    def covertoday(self, symbol, price, vol):  # 空头平今
        orderReq = CtaOrderReq()
        orderReq.symbol = symbol              # 代码
        orderReq.price = price                # 价格
        orderReq.volume = vol                 # 数量
    
        orderReq.priceType = PRICETYPE_LIMITPRICE       # 价格类型
        orderReq.direction = DIRECTION_LONG             # 买卖
        orderReq.offset = OFFSET_CLOSETODAY             # 开平

        return self.sendOrder(orderReq)
    #----------------------------------------------------------------------
    def cancelOrder(self, cancelOrderReq):
        """撤单"""
        self.reqID += 1

        req = {}
        
        # req['InstrumentID'] = cancelOrderReq.symbol
        # req['OrderRef'] = cancelOrderReq.orderID
        # req['FrontID'] = cancelOrderReq.frontID
        # req['SessionID'] = cancelOrderReq.sessionID
        # 撤单有两种字段组合，其中一种没试成功
        req['ExchangeID'] = cancelOrderReq.exchange
        req['OrderSysID'] = cancelOrderReq.orderSysID
        
        req['ActionFlag'] = defineDict['THOST_FTDC_AF_Delete']
        req['BrokerID'] = self.brokerID
        req['InvestorID'] = self.userID
        
        self.reqOrderAction(req, self.reqID)
        
    #----------------------------------------------------------------------
    def close(self):
        """关闭"""
        self.exit()

    #----------------------------------------------------------------------
    def onRspSettlementInfoConfirm(self, data, error, n, last):
        """确认结算信息回报"""
        log = u'结算信息确认完成'
        self.put_log_event(log)
    
        # 查询合约代码
        self.reqID += 1
        self.reqQryInstrument({}, self.reqID)
        
    #----------------------------------------------------------------------
    def onRspQryInstrument(self, data, error, n, last):
        """
        合约查询回报
        由于该回报的推送速度极快，因此不适合全部存入队列中处理，
        选择先储存在一个本地字典中，全部收集完毕后再推送到队列中
        （由于耗时过长目前使用其他进程读取）
        """
        if error['ErrorID'] == 0:
            self.symbolExchangeDict[data['InstrumentID']] = data['ExchangeID'] # 合约代码和交易所的映射关系
            self.symbolSizeDict[data['InstrumentID']] = data['VolumeMultiple'] # 合约代码和合约乘数映射关系
            self.symbolNameDict[data['InstrumentID']] = data['InstrumentName'] # 合约代码和合约名称映射关系

            event = Event(type_=EVENT_INSTRUMENT)
            event.dict_['data'] = data
            event.dict_['last'] = last
            self.__eventEngine.put(event)
            
            if last:
                sleep(1)
                self.reqID += 1
                self.reqQryDepthMarketData({}, self.reqID)  # 查询合约截面数据
                
        else:
            log = '合约投资者回报，错误代码：' + str(error['ErrorID']) + ',   错误信息：' + str(error['ErrorMsg'])
            self.put_log_event(log)

    #----------------------------------------------------------------------
    def onRspQryInvestorPosition(self, data, error, n, last):
        """持仓查询回报"""
        if not data['InstrumentID']:
            return
        if error['ErrorID'] == 0:
            # 读取交易所id|合约名称|方向|合约乘数
            ExchangeID = data['ExchangeID'] = self.symbolExchangeDict.get(data['InstrumentID'], EXCHANGE_UNKNOWN)
            data['InstrumentName'] = self.symbolNameDict.get(data['InstrumentID'], PRODUCT_UNKNOWN)
            data['PosiDirection'] = posiDirectionMapReverse.get(data['PosiDirection'], '')
            # 读取不到的先按1计算，持仓中的开仓均价虽然会显示错误的数字，但程序不会崩溃
            data['VolumeMultiple'] = self.symbolSizeDict.get(data['InstrumentID'], 1)
            # 组合持仓的合约乘数为0，会导致除数为零的错误，暂且修改为1
            if data['VolumeMultiple'] == 0:
                data['VolumeMultiple'] = 1
            
            event = Event(type_=EVENT_POSITION)
            event.dict_['data'] = data
            event.dict_['last'] = last
            self.__eventEngine.put(event)

            # 获取持仓缓存对象
            posName = '.'.join([data['InstrumentID'], data['PosiDirection']])

            if posName in self.posDict:
                pos = self.posDict[posName]
            else:
                pos = CtaPositionData()
                self.posDict[posName] = pos
                
                pos.gatewayName = 'CTP'
                pos.symbol = data['InstrumentID']
                pos.vtSymbol = pos.symbol
                pos.direction = data['PosiDirection']
                pos.vtPositionName = '.'.join([pos.vtSymbol, pos.direction]) 
                pos.name = self.symbolNameDict.get(data['InstrumentID'], PRODUCT_UNKNOWN)
            
            # 针对上期所持仓的今昨分条返回（有昨仓、无今仓），读取昨仓数据.其他交易所只有一条，直接读取
            if (data['YdPosition'] and not data['TodayPosition']) and ExchangeID == EXCHANGE_SHFE:
                pos.ydPosition = data['Position']
            # YdPosition字段存在一个问题，今天平昨仓不会减少这个字段的数量，改为从TodayPosition计算
            if ExchangeID != EXCHANGE_SHFE:
                pos.ydPosition = data['Position'] - data['TodayPosition']
                
            # 计算成本
            size = self.symbolSizeDict[pos.symbol]
            cost = pos.price * pos.position * size
            openCost = pos.openPrice * pos.position * size
            
            # 汇总总仓
            pos.position += data['Position']
            pos.positionProfit += data['PositionProfit']
            # 计算开仓盈亏（浮）
            sign = 1 if pos.direction == DIRECTION_LONG else -1
            op = data["PositionProfit"] + (data["PositionCost"] - data["OpenCost"]) * sign
            pos.openProfit += op
            
            # 计算持仓均价和开仓均价
            if pos.position and size:    
                pos.price = (cost + data['PositionCost']) / (pos.position * size)
                pos.openPrice = (openCost + data["OpenCost"]) / (pos.position * size)
            
            # 读取冻结
            if pos.direction == DIRECTION_LONG: 
                pos.frozen += data['LongFrozen']
            else:
                pos.frozen += data['ShortFrozen']
            
            # 查询回报结束
            if last:
                # 遍历推送
                i = 0
                for pos in self.posDict.values():
                    # vnpy格式持仓事件
                    i += 1
                    lastPos = True if i >= len(self.posDict) else False

                    event2 = Event(type_=EVENT_VNPOSITION)
                    event2.dict_['data'] = pos
                    event2.dict_['last'] = lastPos
                    self.__eventEngine.put(event2)
                
                # 清空缓存
                self.posDict.clear()

        else:
            log = ('持仓查询回报，错误代码：'  + str(error['ErrorID']) + ',   错误信息：' +str(error['ErrorMsg']))
            self.put_log_event(log)

    #----------------------------------------------------------------------
    def onRspQryDepthMarketData(self, data, error, n, last): 
        # 常规行情事件,查询合约截面数据的回报
        event = Event(type_=EVENT_MARKETDATA)
        event.dict_['data'] = data
        event.dict_['last'] = last
        self.__eventEngine.put(event)
   
    #----------------------------------------------------------------------
    def onRspQryTradingAccount(self, data, error, n, last):
        """资金账户查询回报"""
        if error['ErrorID'] == 0:
            event = Event(type_=EVENT_ACCOUNT)
            event.dict_['data'] = data
            self.__eventEngine.put(event)
        else:
            log = ('账户查询回报，错误代码：' +str(error['ErrorID']) + ',   错误信息：' +str(error['ErrorMsg']))
            self.put_log_event(log)

    #----------------------------------------------------------------------
    def onRspOrderInsert(self, data, error, n, last):
        """发单错误（柜台）"""
        log = error['ErrorMsg']
        self.put_log_event(log)
        
    #----------------------------------------------------------------------
    def onRspOrderAction(self, data, error, n, last):
        """撤单错误（柜台）"""
        log = error['ErrorMsg']
        self.put_log_event(log)
        
    #----------------------------------------------------------------------
    def onRspError(self, error, n, last):
        """错误回报"""
        log = error['ErrorMsg']
        self.put_log_event(log)
        
    #----------------------------------------------------------------------
    def onRtnOrder(self, data):
        """报单回报"""
        # 更新最大报单编号
        newref = data['OrderRef']
        self.orderRef = max(self.orderRef, int(newref))
        
        # 合约名称
        data['InstrumentName'] = self.symbolNameDict.get(data['InstrumentID'], PRODUCT_UNKNOWN)
        # 方向
        data['Direction'] = directionMapReverse.get(data['Direction'], DIRECTION_UNKNOWN)
        # 开平
        data['CombOffsetFlag'] = offsetMapReverse.get(data['CombOffsetFlag'], OFFSET_UNKNOWN)
        # 状态
        data['OrderStatus'] = statusMapReverse.get(data['OrderStatus'], STATUS_UNKNOWN)
        
        # 常规报单事件
        event1 = Event(type_=EVENT_ORDER)
        event1.dict_['data'] = data
        self.__eventEngine.put(event1)
        # # 特定合约报单事件
        # event2 = Event(type_=EVENT_ORDER+data['InstrumentID'])  
        # event2.dict_['data'] = data
        # self.__eventEngine.put(event2)
        # 创建报单数据对象
        order = CtaOrderData()
        order.gatewayName = 'CTP'
        
        # # 保存代码和报单号
        order.symbol = data['InstrumentID']
        order.exchange = exchangeMapReverse[data['ExchangeID']]
        order.vtSymbol = '.'.join([order.symbol, order.exchange])
        
        # 报单号
        order.orderID = data['OrderRef']
        # # CTP的报单号一致性维护需要基于frontID, sessionID, orderID三个字段
        # # 但在本接口设计中，已经考虑了CTP的OrderRef的自增性，避免重复
        # # 唯一可能出现OrderRef重复的情况是多处登录并在非常接近的时间内（几乎同时发单）
        # # 考虑到VtTrader的应用场景，认为以上情况不会构成问题
        order.vtOrderID = '.'.join([order.gatewayName, order.orderID])        
        
        order.direction = data['Direction']
        order.offset = data['CombOffsetFlag']
        order.status = data['OrderStatus']
        # order.direction = directionMapReverse.get(data['Direction'], DIRECTION_UNKNOWN)
        # order.offset = offsetMapReverse.get(data['CombOffsetFlag'], OFFSET_UNKNOWN)
        # order.status = statusMapReverse.get(data['OrderStatus'], STATUS_UNKNOWN)            
            
        # # 价格、报单量等数值
        order.price = data['LimitPrice']
        order.totalVolume = data['VolumeTotalOriginal']
        order.tradedVolume = data['VolumeTraded']
        order.orderTime = data['InsertTime']
        order.cancelTime = data['CancelTime']
        order.frontID = data['FrontID']
        order.sessionID = data['SessionID']
        order.orderSysID = data['OrderSysID']
        # # vnpy格式报单事件
        event2 = Event(type_=EVENT_VNORDER)
        event2.dict_['data'] = order
        self.__eventEngine.put(event2)
        
    #----------------------------------------------------------------------
    def onRtnTrade(self, data):
        """成交回报"""
        # 合约名称
        data['InstrumentName'] = self.symbolNameDict.get(data['InstrumentID'], PRODUCT_UNKNOWN)
        
        # 方向
        data['Direction'] = directionMapReverse.get(data['Direction'], '')
            
        # 开平
        data['OffsetFlag'] = offsetMapReverse.get(data['OffsetFlag'], '')
        
        event1 = Event(type_=EVENT_TRADE)
        event1.dict_['data'] = data
        self.__eventEngine.put(event1)

        # 创建报单数据对象
        trade = CtaTradeData()
        trade.gatewayName = "CTP"
        
        # 保存代码和报单号
        trade.symbol = data['InstrumentID']
        trade.exchange = exchangeMapReverse[data['ExchangeID']]
        trade.vtSymbol = trade.symbol #'.'.join([trade.symbol, trade.exchange])
        
        # 成交号
        trade.tradeID = data['TradeID']
        trade.vtTradeID = '.'.join([trade.gatewayName, trade.tradeID])
        
        # 报单号
        trade.orderID = data['OrderRef']
        trade.vtOrderID = '.'.join([trade.gatewayName, trade.orderID])  
        # 方向
        trade.direction = data['Direction'] # directionMapReverse.get(data['Direction'], '')
            
        # 开平
        trade.offset = data['OffsetFlag'] # offsetMapReverse.get(data['OffsetFlag'], '')
            
        # 价格、报单量等数值
        trade.price = data['Price']
        trade.volume = data['Volume']
        trade.tradeTime = data['TradeTime']
        
        # vn格式成交推送
        event2 = Event(type_=EVENT_VNTRADE)
        event2.dict_['data'] = trade
        self.__eventEngine.put(event2)
    #----------------------------------------------------------------------
    def onErrRtnOrderInsert(self, data, error):
        """发单错误回报（交易所）"""
        log = error['ErrorMsg']
        self.put_log_event(log)
        
    #----------------------------------------------------------------------
    def onErrRtnOrderAction(self, data, error):
        """撤单错误回报（交易所）"""
        log = error['ErrorMsg']
        self.put_log_event(log)
        
    #----------------------------------------------------------------------
    def onHeartBeatWarning(self, n):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspAuthenticate(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspRemoveParkedOrder(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQueryMaxOrderVolume(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspRemoveParkedOrderAction(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspUserPasswordUpdate(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspTradingAccountPasswordUpdate(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspParkedOrderInsert(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspParkedOrderAction(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspExecOrderInsert(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspExecOrderAction(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspForQuoteInsert(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQuoteInsert(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQuoteAction(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspLockInsert(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspCombActionInsert(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryOrder(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryTrade(self, data, error, n, last):
        """"""
        pass
        

    #----------------------------------------------------------------------
    def onRspQryInvestor(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryTradingCode(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryInstrumentMarginRate(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryInstrumentCommissionRate(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryExchange(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryProduct(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQrySettlementInfo(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryTransferBank(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryInvestorPositionDetail(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryNotice(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQrySettlementInfoConfirm(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryInvestorPositionCombineDetail(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryCFMMCTradingAccountKey(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryEWarrantOffset(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryInvestorProductGroupMargin(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryExchangeMarginRate(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryExchangeMarginRateAdjust(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryExchangeRate(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQrySecAgentACIDMap(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryProductExchRate(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryProductGroup(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryOptionInstrTradeCost(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryOptionInstrCommRate(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryExecOrder(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryForQuote(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryQuote(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryLock(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryLockPosition(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryInvestorLevel(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryExecFreeze(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryCombInstrumentGuard(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryCombAction(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryTransferSerial(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryAccountregister(self, data, error, n, last):
        """"""
        pass
        

    #----------------------------------------------------------------------
    def onRtnInstrumentStatus(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnTradingNotice(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnErrorConditionalOrder(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnExecOrder(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onErrRtnExecOrderInsert(self, data, error):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onErrRtnExecOrderAction(self, data, error):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onErrRtnForQuoteInsert(self, data, error):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnQuote(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onErrRtnQuoteInsert(self, data, error):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onErrRtnQuoteAction(self, data, error):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnForQuoteRsp(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnCFMMCTradingAccountToken(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnLock(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onErrRtnLockInsert(self, data, error):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnCombAction(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onErrRtnCombActionInsert(self, data, error):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryContractBank(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryParkedOrder(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryParkedOrderAction(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryTradingNotice(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryBrokerTradingParams(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQryBrokerTradingAlgos(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQueryCFMMCTradingAccountToken(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnFromBankToFutureByBank(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnFromFutureToBankByBank(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnRepealFromBankToFutureByBank(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnRepealFromFutureToBankByBank(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnFromBankToFutureByFuture(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnFromFutureToBankByFuture(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnRepealFromBankToFutureByFutureManual(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnRepealFromFutureToBankByFutureManual(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnQueryBankBalanceByFuture(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onErrRtnBankToFutureByFuture(self, data, error):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onErrRtnFutureToBankByFuture(self, data, error):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onErrRtnRepealBankToFutureByFutureManual(self, data, error):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onErrRtnRepealFutureToBankByFutureManual(self, data, error):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onErrRtnQueryBankBalanceByFuture(self, data, error):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnRepealFromBankToFutureByFuture(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnRepealFromFutureToBankByFuture(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspFromBankToFutureByFuture(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspFromFutureToBankByFuture(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRspQueryBankAccountMoneyByFuture(self, data, error, n, last):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnOpenAccountByBank(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnCancelAccountByBank(self, data):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onRtnChangeAccountByBank(self, data):
        """"""
        pass
        


