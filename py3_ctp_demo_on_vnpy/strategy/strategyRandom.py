# encoding: UTF-8

'''
模仿vnpy的CTA策略模板开发的策略,无数据库，数据来源csv或json。
'''
import numpy as np
from datetime import datetime, time
from random import randint
from modules.objects import *




########################################################################
class StrategyRandom(object):
    """随机策略"""
    
    # 策略类的名称和作者
    className = 'StrategyRandom'      # 随便下单
    author = 'vvipi'

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        self.ctaEngine = ctaEngine
        
        # 直接从json读tick数据,本策略初始化时不需要读取历史数据，这里忽略
        self.TickJsonName = ''
        
        # 策略的基本参数
        self.name = EMPTY_UNICODE           # 策略实例名称
        self.vtSymbol = EMPTY_STRING        # 交易的合约vt系统代码
        self.volume = 1                     # 默认开仓手数    
        self.priceTick = 0                  # 最小变动单位
        self.size = 500                     # 缓存tick的数量

 
        # 策略的基本变量，由引擎管理
        self.inited = False                 # 是否进行了初始化
        self.trading = False                # 是否启动交易，由引擎管理
        self.pos = 0                        # 持仓情况
        self.status = 0                     # 策略状态（0 空闲， 1 等待确认， 2 持仓中
        self.direction = ''                 # 持仓方向
        self.loaded = False                 # 已缓存足够的tick
        self.tickCount = EMPTY_INT          # tick计数
        self.openPrice = EMPTY_FLOAT
        self.stopPrice = EMPTY_FLOAT
        self.exitPrice = EMPTY_FLOAT

        # 其他参数
        self.arrayTick = np.zeros(self.size)

        # 参数列表，保存了参数的名称
        self.paramList = [
            'name',
            'className',
            'author',
            'vtSymbol',
            'volume',
            'priceTick',
            'size',
        ]
        
        # 变量列表，保存了变量的名称
        self.varList = [
            'inited',
            'trading',
            'pos',
            'direction',
            'status',
            'direction',
            'loaded',
            'openPrice',
            'stopPrice',
            'exitPrice',
            'tickCount',
        ]

        # 同步列表，保存了需要保存到本地文件的变量名称
        self.syncList = [
            'pos',
        ]
        # 设置策略的参数
        if setting:
            d = self.__dict__
            for key in self.paramList:
                if key in setting:
                    d[key] = setting[key]
    
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略"""
        # raise NotImplementedError
        self.writeCtaLog('%s策略初始化' %self.name)
        
        # # 载入历史数据，并采用回放计算的方式初始化策略数值
        # initData = self.loadBar(self.initDays)
        # for bar in initData:
        #     self.onBar(bar)

        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略"""
        self.writeCtaLog('%s策略启动' %self.name)
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略"""
        self.writeCtaLog('%s策略停止' %self.name)
        self.putEvent()

    def initArray(self, tick):
        '''初始化tick缓存'''
        self.tickCount += 1
        if not self.loaded and self.tickCount >= self.size:
            self.loaded = True
            self.tickCount = 0
        self.newTick(tick)

    def newTick(self, tick):
        '''更新缓存的tick'''
        self.arrayTick[0:self.size-1] = self.arrayTick[1:self.size]
        self.arrayTick[-1] = tick.lastPrice
        # 计算指标
        self.rangeMax = np.percentile(self.arrayTick, 99.5)
        self.rangeMin = np.percentile(self.arrayTick, 0.5)

    def onTick(self, tick):
        """ 处理tick数据，产生交易信号"""

        # 先初始化
        if not self.loaded:
            self.initArray(tick)
            return
        else:
            self.newTick(tick)

        # 根据策略阶段选择方法
        func = self.case0 if self.status == 0 else self.case1
        func(tick)
        
    def case0(self, tick):
        """空仓阶段"""

        r = self.rangeMax / self.rangeMin

        if r > 1.01:
            n = randint(0, 9) % 2
            self.direction = DIRECTION_LONG if n else DIRECTION_SHORT # 随机多空
            
            if self.direction is DIRECTION_LONG:
                price = tick.bidPrice1 - self.priceTick * 3
                self.buy(price, self.volume)
                self.openPrice = tick.askPrice1
                self.stopPrice = tick.askPrice1 * 0.998
                self.exitPrice = tick.askPrice1 * 1.006
            elif self.direction is DIRECTION_SHORT:
                price = tick.bidPrice1 - self.priceTick * 3
                self.short(price, self.volume)
                self.openPrice = tick.bidPrice1
                self.stopPrice = tick.bidPrice1 * 1.002
                self.exitPrice = tick.bidPrice1 * 0.994
            self.status = 1
            self.putEvent()

    def case1(self, tick):
        """持仓阶段"""
        l = tick.lastPrice
        
        if self.direction is DIRECTION_LONG: # 多头退出
            if l > self.exitPrice or l < self.stopPrice:
                self.closePos(tick)
                self.putEvent()
                
        if self.direction is DIRECTION_SHORT: # 空头退出
            if l < self.exitPrice or l > self.stopPrice:
                self.closePos(tick)
                self.putEvent()
    #----------------------------------------------------------------------
    def closePos(self, tick):
        """平仓"""
        if self.pos > 0:
            price = tick.bidPrice1 - self.priceTick * 3
            self.sell(price, self.pos)

        if self.pos < 0:
            price = tick.bidPrice1 + self.priceTick * 3
            self.cover(price, self.pos)

        self.status = 0
        self.putEvent()

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送"""

        pass

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送"""

        self.putEvent()
    
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（本策略没有用到Bar）"""
        pass

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """收到停止单推送（本策略没有用到停止单）"""
        pass
    
    #----------------------------------------------------------------------
    def buy(self, price, volume, stop=False):
        """买开"""
        return self.sendOrder(CTAORDER_BUY, price, volume, stop)
    
    #----------------------------------------------------------------------
    def sell(self, price, volume, stop=False):
        """卖平"""
        return self.sendOrder(CTAORDER_SELL, price, volume, stop)       

    #----------------------------------------------------------------------
    # def sellToday(self, price, volume, stop=False):
    #     """卖平今"""
    #     return self.sendOrder(CTAORDER_SELLTODAY, price, volume, stop)      

    #----------------------------------------------------------------------
    def short(self, price, volume, stop=False):
        """卖开"""
        return self.sendOrder(CTAORDER_SHORT, price, volume, stop)
 
    #----------------------------------------------------------------------
    def cover(self, price, volume, stop=False):
        """买平"""
        return self.sendOrder(CTAORDER_COVER, price, volume, stop)
 
    #----------------------------------------------------------------------
    # def coverToday(self, price, volume, stop=False):
    #     """买平今"""
    #     return self.sendOrder(CTAORDER_COVERTODAY, price, volume, stop)
        
    #----------------------------------------------------------------------
    def sendOrder(self, orderType, price, volume, stop=False):
        """发送委托"""
        if self.trading:
            # 如果stop为True，则意味着发本地停止单
            if stop:
                vtOrderIDList = self.ctaEngine.sendStopOrder(self.vtSymbol, orderType, price, volume, self)
            else:
                vtOrderIDList = self.ctaEngine.sendOrder(self.vtSymbol, orderType, price, volume, self) 
            return vtOrderIDList
        else:
            # 交易停止时发单返回空字符串
            return []
        
    #----------------------------------------------------------------------
    def cancelOrder(self, vtOrderID):
        """撤单"""
        # 如果发单号为空字符串，则不进行后续操作
        if not vtOrderID:
            return
        
        if STOPORDERPREFIX in vtOrderID:
            self.ctaEngine.cancelStopOrder(vtOrderID)
        else:
            self.ctaEngine.cancelOrder(vtOrderID)
            
    #----------------------------------------------------------------------
    def cancelAll(self):
        """全部撤单"""
        self.ctaEngine.cancelAll(self.name)
    
    #----------------------------------------------------------------------
    # def insertTick(self, tick):
    #     """向数据库中插入tick数据"""
    #     self.ctaEngine.insertData(self.tickDbName, self.vtSymbol, tick)
    
    #----------------------------------------------------------------------
    # def insertBar(self, bar):
    #     """向数据库中插入bar数据"""
    #     self.ctaEngine.insertData(self.barDbName, self.vtSymbol, bar)
        
    #----------------------------------------------------------------------
    def loadTick(self, days):
        """读取tick数据"""
        return self.ctaEngine.loadTick(self.TickJsonName, self.vtSymbol, days)
    
    #----------------------------------------------------------------------
    # def loadBar(self, days):
    #     """读取bar数据"""
    #     return self.ctaEngine.loadBar(self.TickJsonName, self.vtSymbol, days)
    
    #----------------------------------------------------------------------
    def writeCtaLog(self, content):
        """记录CTA日志"""
        content = self.name + ':' + content
        self.ctaEngine.writeCtaLog(content)
        
    #----------------------------------------------------------------------
    def putEvent(self):
        """发出策略状态变化事件"""
        self.ctaEngine.putStrategyEvent(self.name)
        
    #----------------------------------------------------------------------
    def getEngineType(self):
        """查询当前运行的环境"""
        return self.ctaEngine.engineType

