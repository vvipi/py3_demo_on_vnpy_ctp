# encoding: UTF-8
'''
demo主程序
导入CTP API、事件引擎、GUI
'''
# 系统模块
from datetime import datetime, time, timedelta
import json
import functools
# 自己开发的模块
from py_ctp.ctp_api import  *
from py_ctp.eventEngine import  *
from py_ctp.eventType import  *
from py_ctp.demo_ui_widgets import *
from py_ctp.constant import *


def stand_alone(func):
    '''
    装饰器
    如果已经有实例在跑则退出
    :return:
    '''
    @functools.wraps(func)
    def f(*args,**kwargs):
        import socket
        try:
            # 全局属性，否则变量会在方法退出后被销毁
            global soket_bind
            soket_bind = socket.socket()
            host = socket.gethostname()
            soket_bind.bind((host, 7788))
        except:
            print('已经运行一个实例，不能重复打开')
            return None
        return func(*args,**kwargs)
    return f

@stand_alone
class MainEngine:
    """主引擎，负责对API的调度"""
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.userID = ''          # 账号
        self.password = ''        # 密码
        self.brokerID = '9999'        # 经纪商代码
        self.MdIp = 'tcp://180.168.146.187:10011'         # 行情服务器地址
        self.TdIp = 'tcp://180.168.146.187:10001'         # 交易服务器地址
        
        self.ee = EventEngine()         # 创建事件驱动引擎
        self.md = CtpMdApi(self.ee)    # 创建行情API接口
        self.td = CtpTdApi(self, self.ee)      # 创建交易API接口
        
        self.list_instrument = []#保存合约资料
        self.list_marketdata = []#保存合约资料
        #持仓和账户、委托数据
        self.dict_account = {}
        # 循环查询持仓和账户相关
        self.countGet = 0  # 查询延时计数
        self.lastGet = 'Position'  # 上次查询的性质，先查询账户
        
        self.ee.start()                 # 启动事件驱动引擎
        self.ee.register(EVENT_INSTRUMENT, self.insertInstrument)
        self.ee.register(EVENT_MARKETDATA, self.insertMarketData)
        self.ee.register (EVENT_ACCOUNT, self.account)

        # self.dict_position = {}
        # self.orderDict = {}
        # self.workingOrderDict = {}
        # self.ee.register (EVENT_POSITION, self.position)
        
        self.mw = MainWindow(mainEngine=self,eventEngine=self.ee)
        self.mw.showMaximized()
    #----------------------------------------------------------------------
    def login(self):
        """登陆"""
        self.md.connect(self.userID, self.password, self.brokerID, self.MdIp)
        self.td.connect(self.userID, self.password, self.brokerID, self.TdIp)
    # ----------------------------------------------------------------------
    def insertInstrument(self, event):
        """插入合约对象"""
        data = event.dict_['data']
        last = event.dict_['last']
        self.list_instrument.append(data)
        if last:# 最后一条数据
            # 将查询完成的合约信息保存到本地文件，今日登录可直接使用不再查询
            event = Event(type_=EVENT_LOG)
            log = '合约信息查询完成'
            event.dict_['log'] = log
            self.ee.put(event)
            with open('Market/InstrumentID.json', 'w', encoding="utf-8") as f:
                jsonD = json.dumps(self.list_instrument,indent=4)
                f.write(jsonD)
            self.list_instrument = []
            event = Event(type_=EVENT_LOG)
            log = '合约信息已经保存'
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
            # 将查询完成的合约信息保存到本地文件
            event = Event(type_=EVENT_LOG)
            log = '合约截面数据查询完成'
            event.dict_['log'] = log
            self.ee.put(event)
            with open('Market/Marketdata.json', 'w', encoding="utf-8") as f:
                jsonD = json.dumps(self.list_marketdata, indent=4)
                f.write(jsonD)
            self.list_marketdata = []
            event = Event(type_=EVENT_LOG)
            log = '合约截面数据已经保存'
            event.dict_['log'] = log
            self.ee.put(event)

            # 开始循环查询
            self.ee.register(EVENT_TIMER, self.getAccountPosition)
    # ----------------------------------------------------------------------
    def exit(self):
        """退出程序前调用，保证正常退出"""        
        self.ee.stop()      
    # ----------------------------------------------------------------------
    def account(self,event):#处理账户事件数据
        self.dict_account  = self.TradingAccountField(event.dict_['data'])
     #----------------------------------------------------------------------
    def TradingAccountField(self,var):
        tmp = {}
        tmp["投资者帐号"] = var["AccountID"]
        tmp["静态权益"] = var["PreBalance"]
        tmp["上次存款额"] = var["PreDeposit"]
        tmp["入金金额"] = var["Deposit"]
        tmp["出金金额"] = var["Withdraw"]
        tmp["冻结保证金"] = var["FrozenMargin"]
        tmp["总保证金"] = var["CurrMargin"]
        tmp["手续费"] = var["Commission"]
        tmp["平仓盈亏"] = var["CloseProfit"]
        tmp["持仓盈亏"] = var["PositionProfit"]
        tmp["动态权益"] = var["Balance"]
        tmp["可用资金"] = var["Available"]
        tmp["可取资金"] = var["WithdrawQuota"]
        tmp["交易日"] = var["TradingDay"]
        tmp["时间"] =datetime.now()
        return tmp
    # ----------------------------------------------------------------------
    def position(self, event):#处理持仓事件数据
        pass
    # ----------------------------------------------------------------------
    def getAccountPosition(self, event):
        """循环查询账户和持仓"""
        self.countGet += 1
        # 每n秒发一次查询
        if self.countGet > 5:
            self.countGet = 0  # 清空计数

            if self.lastGet == 'Account':
                self.getPosition()
                self.lastGet = 'Position'
            else:
                self.getAccount()
                self.lastGet = 'Account'
    # ----------------------------------------------------------------------
    def getAccount(self):
        """查询账户"""
        self.td.qryAccount()
    # ----------------------------------------------------------------------
    def getPosition(self):
        """查询持仓"""
        self.td.qryPosition()        
    # ----------------------------------------------------------------------
    def buy(self, symbol, price, vol):  # 买开多开
        self.td.buy(symbol, price, vol)

    def sell(self, symbol, price, vol):  # 多平
        self.td.sell(symbol, price, vol)

    def selltoday(self, symbol, price, vol):  # 多平今
        self.td.selltoday(symbol, price, vol)

    def short(self, symbol, price, vol):  # 空开
        self.td.short(symbol, price, vol)

    def cover(self, symbol, price, vol):  # 空平
        self.td.cover(symbol, price, vol)

    def covertoday(self, symbol, price, vol):  # 空平今
        self.td.covertoday(symbol, price, vol)
    # ----------------------------------------------------------------------
    def cancelOrder(self, req):#撤单
        self.td.cancelOrder(req)        
    # ----------------------------------------------------------------------
# 直接运行脚本可以进行测试
if __name__ == '__main__':
    import sys
    app =QApplication(sys.argv)
    try:
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        app.setFont(QFont("Microsoft YaHei", 11))
    except:
        pass
    
    main = MainEngine()
    main.login()
    app.exec_()   
