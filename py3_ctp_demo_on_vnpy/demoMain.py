# encoding: UTF-8
'''
主程序
导入CTP API、事件引擎、策略引擎、风控引擎、GUI
'''
# 系统模块
from datetime import datetime, time, timedelta
import functools
# 自己开发的模块
from modules.ctpApi import *
from modules.eventEngine import *
from modules.eventType import  *
from modules.ctaEngine import CtaEngine
from modules.rmEngine import *
from modules.uiWidgets import *
from modules.objects import *
from modules.functions import load_json, save_json
from modules.baseSetting import WORKING_DIR, USER_FILE, globalSetting



def stand_alone(func):
    '''
    装饰器
    如果已经有实例在跑则退出
    '''
    @functools.wraps(func)
    def f(*args,**kwargs):
        import socket
        try:
            # 全局属性，否则变量会在方法退出后被销毁
            global soket_bind
            soket_bind = socket.socket()
            host = socket.gethostname()
            soket_bind.bind((host, 9527))
        except:
            print('已经运行一个实例，不能重复打开')
            return
        return func(*args,**kwargs)
    return f

@stand_alone
class MainEngine:
    """主引擎，负责对API的调度"""

    FINISHED_STATUS = [STATUS_ALLTRADED, STATUS_REJECTED, STATUS_CANCELLED]

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.ee = EventEngine()                                     # 创建事件驱动引擎
        self.re = RmEngine(self.ee)                                 # 创建风控引擎
        self.md = CtpMdApi(self.ee)                                 # 创建行情API接口
        self.td = CtpTdApi(self.re, self.ee)                        # 创建交易API接口
        self.ce = CtaEngine(self, self.ee)                          # 创建CTA引擎
        self.ee.start()                                             # 启动事件驱动引擎
        self.list_instrument = []                                   # 保存合约资料
        self.ee.register(EVENT_INSTRUMENT, self.insertInstrument)
        self.list_marketdata = []                                   # 保存行情截面资料
        self.ee.register(EVENT_MARKETDATA, self.insertMarketData)
        self.contractDict = {}                                      # 合约信息字典
        self.loadContracts()
        self.ee.register(EVENT_CONTRACT, self.updateContract)

        self.userID = ''          # 账号
        self.password = ''        # 密码
        self.brokerID = ''        # 经纪商代码
        self.MdIp = ''         # 行情服务器地址
        self.TdIp = ''         # 交易服务器地址
        self.authCode = ''        # 授权码
        self.appID = ''           # 软件代号
        self.userProductInfo = '' # 产品信息

        # vn格式的委托数据
        self.orderDict = {}
        self.workingOrderDict = {}
        # 持仓细节相关
        self.detailDict = {}                                # vtSymbol:PositionDetail
        self.tdPenaltyList = globalSetting['tdPenalty']     # 平今手续费惩罚的产品代码列表
        # 载入设置
        self.loadSetting()
        # 循环查询持仓和账户相关
        self.countGet = 0  # 查询延时计数
        self.lastGet = 'Position'  # 上次查询的性质，先查询账户
        # 注册持仓和账户、委托事件
        self.ee.register(EVENT_VNORDER, self.processOrderEvent)
        self.ee.register(EVENT_VNTRADE, self.processTradeEvent)
        self.ee.register(EVENT_VNPOSITION, self.processPositionEvent)

        # 策略已启动
        self.ctaActive = False
       
        # 主窗体
        self.mw = MainWindow(mainEngine=self,eventEngine=self.ee)
        self.mw.showMaximized()
        
    #----------------------------------------------------------------------
    def login(self):
        """登陆"""
        self.md.connect(self.userID, self.password, self.brokerID, self.MdIp)
        self.td.connect(self.userID, self.password, self.brokerID, self.TdIp, self.appID, self.authCode, self.userProductInfo)
    # ----------------------------------------------------------------------
    def loadSetting(self):
        """载入设置"""
        # 载入用户信息
        d = load_json(USER_FILE)
        self.userID = d['userID']          # 账号
        self.password = d['password']        # 密码
        self.brokerID = d['brokerID']        # 经纪商代码
        self.MdIp = d['MdIp']         # 行情服务器地址
        self.TdIp = d['TdIp']         # 交易服务器地址
        self.authCode = d['authCode']      # 授权码
        self.appID = d['appID']            # 软件代号
        self.userProductInfo = d['userProductInfo']  # 产品信息

    # ----------------------------------------------------------------------
    def insertInstrument(self, event):
        """插入合约对象"""
        data = event.dict_['data']
        last = event.dict_['last']
        self.list_instrument.append(data)

        # 创建合约信息实例
        contract = CtaContractData() 

        
        contract.vtSymbol = contract.symbol = data['InstrumentID']
        contract.name = data['InstrumentName']
        contract.exchange = data['ExchangeID']

        # 合约数值
        contract.size = data['VolumeMultiple']
        contract.priceTick = data['PriceTick']
        contract.strikePrice = data['StrikePrice']
        contract.underlyingSymbol = data['UnderlyingInstrID']

        # 期权类型
        if data['OptionsType'] == '1':
            contract.optionType = OPTION_CALL
        elif data['OptionsType'] == '2':
            contract.optionType = OPTION_PUT

        # 推送合约信息
        self.onContract(contract)

        if last: # 最后一条数据
            # 将查询完成的合约信息保存到本地文件
            event = Event(type_=EVENT_LOG)
            log = '合约信息查询完成'
            event.dict_['log'] = log
            self.ee.put(event)
            # 保存合约信息到本地
            self.saveContracts()
            # 字典格式的合约数据也保存一份
            instrumentFile = WORKING_DIR + 'temp/InstrumentID.json'
            save_json(self.list_instrument, instrumentFile)
            # 推送日志
            event = Event(type_=EVENT_LOG)
            log = '合约信息已经保存到本地'
            event.dict_['log'] = log
            self.ee.put(event)
    # ----------------------------------------------------------------------
    def insertMarketData(self, event):
        """插入合约截面数据"""
        data = event.dict_['data']
        last = event.dict_['last']
        self.list_marketdata.append(data)
        if last:
            # 更新交易日
            self.md.TradingDay = data['TradingDay']
            # 将查询完成的合约截面数据保存到本地文件
            event = Event(type_=EVENT_LOG)
            log = '合约截面数据查询完成'
            event.dict_['log'] = log
            self.ee.put(event)
            # 字典格式的合约截面数据也保存一份
            makertdataFile = WORKING_DIR + 'temp/Marketdata.json'
            save_json(self.list_marketdata, makertdataFile)
            # 推送日志
            event = Event(type_=EVENT_LOG)
            log = '合约截面数据已经保存到本地'
            event.dict_['log'] = log
            self.ee.put(event)
            if not self.ctaActive:
                self.runStrategy()
                self.ctaActive = True
    # ----------------------------------------------------------------------
    def runStrategy(self):
        """启动策略"""
        # 定时器事件，循环查询
        self.ee.register(EVENT_TIMER, self.getAccountPosition)

        # 发送信号到策略界面，自动载入、初始化、启动全部策略
        event = Event(EVENT_CTA_ROBOT)
        self.ee.put(event)

    #----------------------------------------------------------------------
    def onContract(self, contract):
        """合约基础信息推送"""
        event = Event(type_=EVENT_CONTRACT)
        event.dict_['data'] = contract
        self.ee.put(event)    
    #----------------------------------------------------------------------
    def updateContract(self, event):
        """更新合约数据"""
        contract = event.dict_['data']
        self.contractDict[contract.vtSymbol] = contract
    #----------------------------------------------------------------------
    def getContract(self, vtSymbol):
        """查询合约对象"""
        try:
            return self.contractDict[vtSymbol]
        except KeyError:
            return None
    #----------------------------------------------------------------------
    def saveContracts(self):
        """保存所有合约对象到硬盘"""
        contractFilePath = WORKING_DIR + 'temp/contracts'
        data = {key: value.__dict__ for key, value in self.contractDict.items()}
        save_json(data, contractFilePath)
        
    #----------------------------------------------------------------------
    def loadContracts(self):
        """从硬盘读取合约对象"""

        contractFilePath = WORKING_DIR + 'temp/contracts'
        contractDict = load_json(contractFilePath)
        
        for k, v in contractDict.items():
            # 创建合约信息实例
            contract = CtaContractData() 
            contract.vtSymbol = contract.symbol = k
            contract.name = v.get('name')
            contract.exchange = v.get('exchange')
            contract.size = v.get('size')
            contract.priceTick = v.get('priceTick')
            contract.strikePrice = v.get('strikePrice')
            contract.underlyingSymbol = v.get('underlyingSymbol')
            contract.optionType = v.get('optionType')
            self.contractDict[k] = contract

    #----------------------------------------------------------------------
    def getOrder(self, vtOrderID):
        """查询委托"""
        try:
            return self.orderDict[vtOrderID]
        except KeyError:
            return None
    #----------------------------------------------------------------------
    def processOrderEvent(self, event):
        """处理委托事件"""
        order = event.dict_['data']        
        self.orderDict[order.vtOrderID] = order
        
        # 如果订单的状态是全部成交或者撤销，则需要从workingOrderDict中移除
        if order.status in self.FINISHED_STATUS:
            if order.vtOrderID in self.workingOrderDict:
                del self.workingOrderDict[order.vtOrderID]
        # 否则则更新字典中的数据        
        else:
            self.workingOrderDict[order.vtOrderID] = order
            
        # 更新到持仓细节中
        detail = self.getPositionDetail(order.vtSymbol)
        detail.updateOrder(order)            
    #----------------------------------------------------------------------
    def processTradeEvent(self, event):
        """处理成交事件"""
        trade = event.dict_['data']
    
        # 更新到持仓细节中
        detail = self.getPositionDetail(trade.vtSymbol)
        detail.updateTrade(trade)        
    #----------------------------------------------------------------------
    def processPositionEvent(self, event):
        """处理持仓事件"""
        pos = event.dict_['data']
        last = event.dict_['last']
    
        # 更新到持仓细节中
        detail = self.getPositionDetail(pos.vtSymbol)
        detail.updatePosition(pos)                

    #----------------------------------------------------------------------
    def getPositionDetail(self, vtSymbol):
        """查询持仓细节"""
        if vtSymbol in self.detailDict:
            detail = self.detailDict[vtSymbol]
        else:
            contract = self.getContract(vtSymbol)
            detail = PositionDetail(vtSymbol, contract)
            self.detailDict[vtSymbol] = detail
            
            # 设置持仓细节的委托转换模式
            contract = self.getContract(vtSymbol)
            
            if contract:
                detail.exchange = contract.exchange
                
                # 上期所合约
                if contract.exchange == EXCHANGE_SHFE:
                    detail.mode = detail.MODE_SHFE
                
                # 检查是否有平今惩罚
                for productID in self.tdPenaltyList:
                    if str(productID) in contract.symbol:
                        detail.mode = detail.MODE_TDPENALTY
                
        return detail
    #----------------------------------------------------------------------
    def convertOrderReq(self, req):
        """根据规则转换委托请求"""
        detail = self.detailDict.get(req.vtSymbol, None)
        if not detail:
            return [req]
        else:
            return detail.convertOrderReq(req)
    # ----------------------------------------------------------------------
    def getAccountPosition(self, event):
        """循环查询账户和持仓"""
        self.countGet += 1
        # 每n秒发一次查询
        if self.countGet > 5:
            self.countGet = 0  # 清空计数

            if self.lastGet == 'Account':
                self.qryPosition()
                self.lastGet = 'Position'
            else:
                self.qryAccount()
                self.lastGet = 'Account'
    # ----------------------------------------------------------------------
    def qryAccount(self):
        """查询账户"""
        self.td.qryAccount()
    # ----------------------------------------------------------------------
    def qryPosition(self):
        """查询持仓"""
        self.td.qryPosition()
    # ----------------------------------------------------------------------
    def sendOrder(self, req):
        '''发单'''
        return self.td.sendOrder(req)            
    # ----------------------------------------------------------------------
    def cancelOrder(self, req):
        '''撤单'''
        self.td.cancelOrder(req)        
    # ----------------------------------------------------------------------
    def subscribe(self, req):
        '''订阅行情'''
        self.md.subscribe(req.symbol)
    # ----------------------------------------------------------------------
    def exit(self):
        """退出程序前调用，保证正常退出"""        
        # 停止事件引擎
        self.ee.stop()      
    # ----------------------------------------------------------------------

########################################################################
class PositionDetail(object):
    """本地维护的持仓信息"""
    WORKING_STATUS = [STATUS_UNKNOWN, STATUS_NOTTRADED, STATUS_PARTTRADED]
    
    MODE_NORMAL = 'normal'          # 普通模式
    MODE_SHFE = 'shfe'              # 上期所今昨分别平仓
    MODE_TDPENALTY = 'tdpenalty'    # 平今惩罚

    #----------------------------------------------------------------------
    def __init__(self, vtSymbol, contract=None):
        """Constructor"""
        self.vtSymbol = vtSymbol
        self.symbol = EMPTY_STRING
        self.exchange = EMPTY_STRING
        self.name = EMPTY_UNICODE    
        self.size = 1
        
        if contract:
            self.symbol = contract.symbol
            self.exchange = contract.exchange
            self.name = contract.name
            self.size = contract.size
        
        self.longPos = EMPTY_INT
        self.longYd = EMPTY_INT
        self.longTd = EMPTY_INT
        self.longPosFrozen = EMPTY_INT
        self.longYdFrozen = EMPTY_INT
        self.longTdFrozen = EMPTY_INT
        self.longPnl = EMPTY_FLOAT
        self.longPrice = EMPTY_FLOAT
        
        self.shortPos = EMPTY_INT
        self.shortYd = EMPTY_INT
        self.shortTd = EMPTY_INT
        self.shortPosFrozen = EMPTY_INT
        self.shortYdFrozen = EMPTY_INT
        self.shortTdFrozen = EMPTY_INT
        self.shortPnl = EMPTY_FLOAT
        self.shortPrice = EMPTY_FLOAT
        
        self.lastPrice = EMPTY_FLOAT
        
        self.mode = self.MODE_NORMAL
        self.exchange = EMPTY_STRING
        
        self.workingOrderDict = {}
        
    #----------------------------------------------------------------------
    def updateTrade(self, trade):
        """成交更新"""
        # 多头
        if trade.direction is DIRECTION_LONG:
            # 开仓
            if trade.offset is OFFSET_OPEN:
                self.longTd += trade.volume
            # 平今
            elif trade.offset is OFFSET_CLOSETODAY:
                self.shortTd -= trade.volume
            # 平昨
            elif trade.offset is OFFSET_CLOSEYESTERDAY:
                self.shortYd -= trade.volume
            # 平仓
            elif trade.offset is OFFSET_CLOSE:
                # 上期所等同于平昨
                if self.exchange is EXCHANGE_SHFE:
                    self.shortYd -= trade.volume
                # 非上期所，优先平今(原注释)
                # 应该是优先平昨，否则可能导致平今惩罚模式计算错误（存疑）
                else:
                    # self.shortTd -= trade.volume
                    
                    # if self.shortTd < 0:
                    #     self.shortYd += self.shortTd
                    #     self.shortTd = 0
                    self.shortYd -= trade.volume
                    
                    if self.shortYd < 0:
                        self.shortTd += self.shortYd
                        self.shortYd = 0    
        # 空头
        elif trade.direction is DIRECTION_SHORT:
            # 开仓
            if trade.offset is OFFSET_OPEN:
                self.shortTd += trade.volume
            # 平今
            elif trade.offset is OFFSET_CLOSETODAY:
                self.longTd -= trade.volume
            # 平昨
            elif trade.offset is OFFSET_CLOSEYESTERDAY:
                self.longYd -= trade.volume
            # 平仓
            elif trade.offset is OFFSET_CLOSE:
                # 上期所等同于平昨
                if self.exchange is EXCHANGE_SHFE:
                    self.longYd -= trade.volume
                # 非上期所，优先平今(原注释)
                # 应该是优先平昨，否则可能导致平今惩罚模式计算错误（存疑）
                else:
                    # self.longTd -= trade.volume
                    
                    # if self.longTd < 0:
                    #     self.longYd += self.longTd
                    #     self.longTd = 0
                    self.longYd -= trade.volume
                    
                    if self.longYd < 0:
                        self.longTd += self.longYd
                        self.longYd = 0
                    
        # 汇总
        self.calculatePrice(trade)
        self.calculatePosition()
        self.calculatePnl()
    
    #----------------------------------------------------------------------
    def updateOrder(self, order):
        """委托更新"""
        # 将活动委托缓存下来
        if order.status in self.WORKING_STATUS:
            self.workingOrderDict[order.vtOrderID] = order
            
        # 移除缓存中已经完成的委托
        else:
            if order.vtOrderID in self.workingOrderDict:
                del self.workingOrderDict[order.vtOrderID]
                
        # 计算冻结
        self.calculateFrozen()
    
    #----------------------------------------------------------------------
    def updatePosition(self, pos):
        """持仓更新"""
        if pos.direction is DIRECTION_LONG:
            self.longPos = pos.position
            self.longYd = pos.ydPosition
            self.longTd = self.longPos - self.longYd
            self.longPnl = pos.positionProfit
            self.longPrice = pos.price
        elif pos.direction is DIRECTION_SHORT:
            self.shortPos = pos.position
            self.shortYd = pos.ydPosition
            self.shortTd = self.shortPos - self.shortYd
            self.shortPnl = pos.positionProfit
            self.shortPrice = pos.price
            
        # self.output()
    
    #----------------------------------------------------------------------
    def updateOrderReq(self, req, vtOrderID):
        """发单更新"""
        vtSymbol = req.vtSymbol        
            
        # 基于请求生成委托对象
        order = VtOrderData()
        order.vtSymbol = vtSymbol
        order.symbol = req.symbol
        order.exchange = req.exchange
        order.offset = req.offset
        order.direction = req.direction
        order.totalVolume = req.volume
        order.status = STATUS_UNKNOWN
        
        # 缓存到字典中
        self.workingOrderDict[vtOrderID] = order
        
        # 计算冻结量
        self.calculateFrozen()
        
    #----------------------------------------------------------------------
    def updateTick(self, tick):
        """行情更新"""
        self.lastPrice = tick.lastPrice
        self.calculatePnl()
        
    #----------------------------------------------------------------------
    def calculatePnl(self):
        """计算持仓盈亏"""
        self.longPnl = self.longPos * (self.lastPrice - self.longPrice) * self.size
        self.shortPnl = self.shortPos * (self.shortPrice - self.lastPrice) * self.size
        
    #----------------------------------------------------------------------
    def calculatePrice(self, trade):
        """计算持仓均价（基于成交数据）"""
        # 只有开仓会影响持仓均价
        if trade.offset == OFFSET_OPEN:
            if trade.direction == DIRECTION_LONG:
                cost = self.longPrice * self.longPos
                cost += trade.volume * trade.price
                newPos = self.longPos + trade.volume
                if newPos:
                    self.longPrice = cost / newPos
                else:
                    self.longPrice = 0
            else:
                cost = self.shortPrice * self.shortPos
                cost += trade.volume * trade.price
                newPos = self.shortPos + trade.volume
                if newPos:
                    self.shortPrice = cost / newPos
                else:
                    self.shortPrice = 0
    
    #----------------------------------------------------------------------
    def calculatePosition(self):
        """计算持仓情况"""
        self.longPos = self.longTd + self.longYd
        self.shortPos = self.shortTd + self.shortYd      
        
    #----------------------------------------------------------------------
    def calculateFrozen(self):
        """计算冻结情况"""
        # 清空冻结数据
        self.longPosFrozen = EMPTY_INT
        self.longYdFrozen = EMPTY_INT
        self.longTdFrozen = EMPTY_INT
        self.shortPosFrozen = EMPTY_INT
        self.shortYdFrozen = EMPTY_INT
        self.shortTdFrozen = EMPTY_INT     
        
        # 遍历统计
        for order in self.workingOrderDict.values():
            # 计算剩余冻结量
            frozenVolume = order.totalVolume - order.tradedVolume
            
            # 多头委托
            if order.direction is DIRECTION_LONG:
                # 平今
                if order.offset is OFFSET_CLOSETODAY:
                    self.shortTdFrozen += frozenVolume
                # 平昨
                elif order.offset is OFFSET_CLOSEYESTERDAY:
                    self.shortYdFrozen += frozenVolume
                # 平仓
                elif order.offset is OFFSET_CLOSE:
                    self.shortTdFrozen += frozenVolume
                    
                    if self.shortTdFrozen > self.shortTd:
                        self.shortYdFrozen += (self.shortTdFrozen - self.shortTd)
                        self.shortTdFrozen = self.shortTd
            # 空头委托
            elif order.direction is DIRECTION_SHORT:
                # 平今
                if order.offset is OFFSET_CLOSETODAY:
                    self.longTdFrozen += frozenVolume
                # 平昨
                elif order.offset is OFFSET_CLOSEYESTERDAY:
                    self.longYdFrozen += frozenVolume
                # 平仓
                elif order.offset is OFFSET_CLOSE:
                    self.longTdFrozen += frozenVolume
                    
                    if self.longTdFrozen > self.longTd:
                        self.longYdFrozen += (self.longTdFrozen - self.longTd)
                        self.longTdFrozen = self.longTd
                        
            # 汇总今昨冻结
            self.longPosFrozen = self.longYdFrozen + self.longTdFrozen
            self.shortPosFrozen = self.shortYdFrozen + self.shortTdFrozen
            
    #----------------------------------------------------------------------
    def output(self):
        """"""
        print(self.vtSymbol, '-'*30)
        print('long, total:%s, td:%s, yd:%s' %(self.longPos, self.longTd, self.longYd))
        print('long frozen, total:%s, td:%s, yd:%s' %(self.longPosFrozen, self.longTdFrozen, self.longYdFrozen))
        print('short, total:%s, td:%s, yd:%s' %(self.shortPos, self.shortTd, self.shortYd))
        print('short frozen, total:%s, td:%s, yd:%s' %(self.shortPosFrozen, self.shortTdFrozen, self.shortYdFrozen))      
    
    #----------------------------------------------------------------------
    def convertOrderReq(self, req):
        """转换委托请求"""
        # 普通模式无需转换
        if self.mode is self.MODE_NORMAL:
            return [req]
        
        # 上期所模式拆分今昨，优先平今
        elif self.mode is self.MODE_SHFE:
            # 开仓无需转换
            if req.offset is OFFSET_OPEN:
                return [req]
            
            # 多头
            if req.direction is DIRECTION_LONG:
                posAvailable = self.shortPos - self.shortPosFrozen
                tdAvailable = self.shortTd- self.shortTdFrozen
                ydAvailable = self.shortYd - self.shortYdFrozen            
            # 空头
            else:
                posAvailable = self.longPos - self.longPosFrozen
                tdAvailable = self.longTd - self.longTdFrozen
                ydAvailable = self.longYd - self.longYdFrozen
                
            # 平仓量超过总可用，拒绝，返回空列表
            if req.volume > posAvailable:
                return []
            # 平仓量小于今可用，全部平今
            elif req.volume <= tdAvailable:
                req.offset = OFFSET_CLOSETODAY
                return [req]
            # 平仓量大于今可用，平今再平昨
            else:
                l = []
                
                if tdAvailable > 0:
                    reqTd = copy(req)
                    reqTd.offset = OFFSET_CLOSETODAY
                    reqTd.volume = tdAvailable
                    l.append(reqTd)
                    
                reqYd = copy(req)
                reqYd.offset = OFFSET_CLOSEYESTERDAY
                reqYd.volume = req.volume - tdAvailable
                l.append(reqYd)
                
                return l
            
        # 平今惩罚模式，没有今仓则平昨，否则锁仓
        elif self.mode is self.MODE_TDPENALTY:
            # 多头
            if req.direction is DIRECTION_LONG:
                td = self.shortTd
                ydAvailable = self.shortYd - self.shortYdFrozen
            # 空头
            else:
                td = self.longTd
                ydAvailable = self.longYd - self.longYdFrozen
                
            # 这里针对开仓和平仓委托均使用一套逻辑
            
            # 如果有今仓，则只能开仓（或锁仓）
            if td:
                req.offset = OFFSET_OPEN
                return [req]
            # 如果平仓量小于昨可用，全部平昨
            elif req.volume <= ydAvailable:
                if self.exchange is EXCHANGE_SHFE:
                    req.offset = OFFSET_CLOSEYESTERDAY
                else:
                    req.offset = OFFSET_CLOSE
                return [req]
            # 平仓量大于昨可用，平仓再反向开仓
            else:
                l = []
                
                if ydAvailable > 0:
                    reqClose = copy(req)
                    if self.exchange is EXCHANGE_SHFE:
                        req.offset = OFFSET_CLOSEYESTERDAY
                    else:
                        req.offset = OFFSET_CLOSE
                    reqClose.volume = ydAvailable
                    
                    l.append(reqClose)
                    
                reqOpen = copy(req)
                reqOpen.offset = OFFSET_OPEN
                reqOpen.volume = req.volume - ydAvailable
                l.append(reqOpen)
                
                return l
        
        # 其他情况则直接返回空
        return []


# 直接运行脚本可以进行测试
if __name__ == '__main__':
    # 显示自定义图标
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")
    import sys
    app = QApplication(sys.argv)
    try:
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())   # 黑色主题
        app.setFont(QFont("Microsoft YaHei", 11))               # 微软雅黑字体
    except:
        pass
    
    main = MainEngine()
    main.login()
    app.exec_()   
