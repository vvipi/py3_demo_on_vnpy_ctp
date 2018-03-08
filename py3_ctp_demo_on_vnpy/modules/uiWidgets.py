# encoding: UTF-8
"""
窗口部件
"""
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from datetime import datetime, date
import json
import logging
import pyqtgraph as pg

from modules.eventEngine import  *
from modules.eventType import  *
from modules.objects import *


class MainWindow(QMainWindow):
    """主窗口"""
    # signal = pyqtSignal(type(Event()))
    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        super(MainWindow, self).__init__()

        self.widgetDict = {}    # 用来保存子窗口的字典
        self.me = mainEngine
        self.ee = eventEngine
        
        self.initUi()
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle("CTP DEMO——基于vnpy的ctp接口")
        self.setWindowIcon(QIcon('resource/fs.ico'))

        widgetStrategyM, dockStrategyM = self.createDock(CtaEngineManager, '策略', Qt.TopDockWidgetArea, engine=self.me.ce)
        widgetLogM, dockLogM = self.createDock(LogMonitor, '日志', Qt.BottomDockWidgetArea, engine=None, floatable=True)
        widgetAccountM, dockAccountM = self.createDock(AccountMonitor, '账户资金', Qt.BottomDockWidgetArea)
        widgetPositionM, dockPositionM = self.createDock(PositionMonitor, '持仓', Qt.BottomDockWidgetArea)
        widgetTradeM, dockTradeM = self.createDock(TradeMonitor, '成交', Qt.BottomDockWidgetArea)
        widgetOrderM, dockOrderM = self.createDock(OrderMonitor, '委托', Qt.BottomDockWidgetArea)
        widgetNonetradeM, dockNonetradeM = self.createDock(NonetradeMonitor, '撤单', Qt.BottomDockWidgetArea, engine=self.me)
        
        self.tabifyDockWidget(dockAccountM, dockPositionM)
        self.tabifyDockWidget(dockAccountM, dockTradeM)
        self.tabifyDockWidget(dockAccountM, dockOrderM)
        self.tabifyDockWidget(dockAccountM, dockNonetradeM)
        self.tabifyDockWidget(dockAccountM, dockLogM)     
        
        # dockPlotM.raise_()
        dockLogM.raise_()
        dockAccountM.setMinimumWidth(720)
        dockLogM.setMinimumWidth(260)
        
        aboutAction = QAction(u'关于', self)
        aboutAction.triggered.connect(self.openAbout)    
        
        rmAction = QAction(u'风险管理', self)
        rmAction.triggered.connect(self.openRM)   
        
        menubar = self.menuBar()
        sysMenu = menubar.addMenu(u'系统')
        sysMenu.addAction(rmAction)
        helpMenu = menubar.addMenu(u'帮助')
        helpMenu.addAction(aboutAction)
            
    def createDock(self, widgetClass, widgetName, widgetArea, engine=None, floatable=False):
        """创建停靠组件"""
        widget = widgetClass(self.ee, engine) if engine else widgetClass(self.ee) 

        dock = QDockWidget(widgetName)
        dock.setWidget(widget)
        dock.setObjectName(widgetName)
        if floatable:
            dock.setFeatures(dock.DockWidgetFloatable|dock.DockWidgetMovable|dock.DockWidgetClosable)
        else:
            dock.setFeatures(dock.DockWidgetMovable)
        self.addDockWidget(widgetArea, dock)
        return widget, dock
            
    def openAbout(self):
        """打开关于"""
        try:
            self.widgetDict['aboutW'].show()
        except KeyError:
            self.widgetDict['aboutW'] = AboutWidget(self)
            self.widgetDict['aboutW'].show()
                        
    def openRM(self):
        """打开风控模块"""
        try:
            self.widgetDict['rmW'].show()
        except KeyError:
            self.widgetDict['rmW'] = RmEngineManager(self.me.re, self.ee)
            self.widgetDict['rmW'].show()

    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(self, '退出',
                                           '确认退出?', QMessageBox.Yes | 
                                           QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes: 
            for widget in self.widgetDict.values():
                widget.close()
            
            self.me.exit()
            event.accept()
        else:
            event.ignore()
            
########################################################################
class LogMonitor(QTableWidget):
    """用于显示日志"""
    signal = pyqtSignal(type(Event()))
    #----------------------------------------------------------------------
    def __init__(self,eventEngine, parent=None):
        """Constructor"""
        super(LogMonitor, self).__init__(parent)
        self.__eventEngine = eventEngine
        self.setWindowTitle('日志')
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['时间', '日志'])
        self.verticalHeader().setVisible(False)                 # 关闭左边的垂直表头
        self.setEditTriggers(QTableWidget.NoEditTriggers) # 设为不可编辑状态
        self.setColumnWidth(0, 80)
        self.setColumnWidth(1, 800)
        # Qt图形组件的GUI更新必须使用Signal/Slot机制，否则有可能导致程序崩溃
        # 因此这里先将图形更新函数作为Slot，和信号连接起来
        # 然后将信号的触发函数注册到事件驱动引擎中
        self.signal.connect(self.updateLog)
        self.__eventEngine.register(EVENT_LOG, self.signal.emit)
        #保存日志到文件
        path = 'log/EventLog/eventLog{date}'.format(date=date.today())
        logging.basicConfig(filename=path, level=logging.INFO)
    #----------------------------------------------------------------------
    def updateLog(self, event):
        """更新日志"""
        # 获取当前时间和日志内容
        t = datetime.now()
        t = t.strftime('%H:%M:%S')
        log = event.dict_['log']
        # 在表格最上方插入一行
        self.insertRow(0)
        # 创建单元格
        cellTime = QTableWidgetItem(t)
        cellLog = QTableWidgetItem(log)

        # 将单元格插入表格
        self.setItem(0, 0, cellTime)
        self.setItem(0, 1, cellLog)
        
        logging.info(','.join([t, log]))

########################################################################
class AccountMonitor(QTableWidget):
    """用于显示账户"""
    signal = pyqtSignal(type(Event()))# 这里的TYPE也可以是DICT，需要在注册事件中进行数据格式转换
    #----------------------------------------------------------------------
    def __init__(self, eventEngine, parent=None):
        """Constructor"""
        super(AccountMonitor, self).__init__(parent)
        self.dictLabels = ["动态权益", "总保证金", "冻结保证金", "手续费", "平仓盈亏", "持仓盈亏", "可用资金", "可取资金"]
        self.__eventEngine = eventEngine
        #self.__mainEngine = mainEngine
        self.list_account = []  # 保存账户数据的LIST
        self.count = 0      # 账户数据第一次保存记号
        self.dict = {}	    # 用来保存账户对应的单元格
        self.setWindowTitle('账户')
        self.setColumnCount(len(self.dictLabels))   # 设置列
        self.insertRow(0)   # 因为只有1行数据，直接初始化
        col = 0     # 表格列计数器
        for i in self.dictLabels:   # 初始化表格为空格
            self.dict[i] = QTableWidgetItem('')
            self.dict[i].setTextAlignment(0x0004 | 0x0080)  # 居中
            self.setItem(0, col, self.dict[i])
            col += 1
        self.setHorizontalHeaderLabels(self.dictLabels)
        self.verticalHeader().setVisible(False)                 # 关闭左边的垂直表头
        self.setEditTriggers(QTableWidget.NoEditTriggers)   # 设为不可编辑状态
        self.signal.connect(self.updateAccount)
        self.__eventEngine.register(EVENT_ACCOUNT, self.signal.emit)

    def updateAccount(self, event):
        var = self.TradingAccountField(event.dict_['data']) # 这里的dict'keys要包含self.dictLabels，否则会出错。
        self.count += 1     # 也可以每执行一次保存一次，收盘后可以看到账户的曲线。
        if self.count == 1: # 记录一次账户数据，只记录登陆后的第一个数据。
            self.list_account.append(var)   # 这个代码可有可无，看个人的使用而言。
        for i in self.dictLabels:   # 刷新表格
            value = var[i]  # i就是DICT的key
            try:
                value = str(round(value, 2))    # 保留2位小数
            except:
                value = str(value)
            self.dict[i].setText(value) # 刷新单元格数据
    #----------------------------------------------------------------------
    def TradingAccountField(self, var):
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
        tmp["时间"] = datetime.now()
        return tmp
        
########################################################################
class PositionMonitor(QTableWidget):
    """用于显示持仓"""
    signal = pyqtSignal(type(Event()))
    #----------------------------------------------------------------------
    def __init__(self, eventEngine, parent=None):
        """Constructor"""
        super(PositionMonitor, self).__init__(parent)
        self.dictLabels = [
            "合约代码", "合约名称", "持仓方向", "总持仓量", "昨持仓量", "今持仓量", "总冻结",
            "持仓均价", "开仓均价", "持仓盈亏", "开仓盈亏"]
        self.__eventEngine = eventEngine
        self.dict = {}
        self.setWindowTitle('持仓')
        self.setColumnCount(len(self.dictLabels))
        self.setHorizontalHeaderLabels(self.dictLabels)
        self.verticalHeader().setVisible(False)                 # 关闭左边的垂直表头
        self.setEditTriggers(QTableWidget.NoEditTriggers) # 设为不可编辑状态
        self.signal.connect(self.updateposition)
        self.__eventEngine.register(EVENT_VNPOSITION, self.signal.emit)
        self.insertRow(0) # 插入合计的表格
        col = 0
        self.dict['合计'] = {}
        for i in self.dictLabels:
            self.dict['合计'][i] = QTableWidgetItem('')
            self.dict['合计'][i].setTextAlignment(0x0004 | 0x0080)  # 居中
            self.setItem(0, col, self.dict['合计'][i])
            col += 1
        self.dict['合计']["合约代码"].setText('合计')
        
    def updateposition(self, event):
        pos = event.dict_['data']
        last = event.dict_['last']
        dm = {
            DIRECTION_LONG: "多持",
            DIRECTION_SHORT: "空持",
        }

        posName = '.'.join([pos.symbol + pos.direction])
        if pos.position != 0: # 有持仓
            if posName not in self.dict.keys(): # 插入新持仓
                self.dict[posName] = {}
                self.dict[posName]["合约代码"] = QTableWidgetItem(str(pos.symbol))
                self.dict[posName]["合约名称"] = QTableWidgetItem(str(pos.name))
                self.dict[posName]["持仓方向"] = QTableWidgetItem(str(dm.get(pos.direction, '未知方向')))
                self.dict[posName]["总持仓量"] =  QTableWidgetItem(str(pos.position))
                self.dict[posName]["昨持仓量"] = QTableWidgetItem(str(pos.ydPosition))
                self.dict[posName]["今持仓量"] = QTableWidgetItem(str(pos.position - pos.ydPosition))
                self.dict[posName]["总冻结"] = QTableWidgetItem(str(pos.frozen))
                self.dict[posName]["持仓均价"] = QTableWidgetItem(str(round(pos.price, 2)))
                self.dict[posName]["开仓均价"] = QTableWidgetItem(str(round(pos.openPrice, 2)))
                self.dict[posName]["持仓盈亏"] = QTableWidgetItem(str(round(pos.positionProfit, 2)))
                self.dict[posName]["开仓盈亏"] = QTableWidgetItem(str(round(pos.openProfit, 2)))
                self.insertRow(0) # 插入表格第一行
                col = 0 # 列计数
                for label in self.dictLabels:
                    self.dict[posName][label].setTextAlignment(0x0004 | 0x0080)  # 居中
                    self.setItem(0, col, self.dict[posName][label])
                    col += 1
            else: # 更新可能会变的数值
                self.dict[posName]["总持仓量"].setText(str(pos.position))
                self.dict[posName]["昨持仓量"].setText(str(pos.ydPosition))
                self.dict[posName]["今持仓量"].setText(str(pos.position - pos.ydPosition))
                self.dict[posName]["总冻结"].setText(str(pos.frozen))
                self.dict[posName]["持仓均价"].setText(str(round(pos.price, 2)))
                self.dict[posName]["开仓均价"].setText(str(round(pos.openPrice, 2)))
                self.dict[posName]["持仓盈亏"].setText(str(round(pos.positionProfit, 2)))
                self.dict[posName]["开仓盈亏"].setText(str(round(pos.openProfit, 2)))
            # 设置颜色
            if pos.direction == DIRECTION_LONG:
                self.dict[posName]["持仓方向"].setBackground(QColor(255, 0, 0))
            else:
                self.dict[posName]["持仓方向"].setBackground(QColor(34, 139, 34))
            if pos.positionProfit > 0:
                self.dict[posName]["持仓盈亏"].setBackground(QColor(255, 0, 0))
            else:
                self.dict[posName]["持仓盈亏"].setBackground(QColor(34, 139, 34))
            if pos.openProfit > 0 :
                self.dict[posName]["开仓盈亏"].setBackground(QColor(255, 0, 0))
            else:
                self.dict[posName]["开仓盈亏"].setBackground(QColor(34, 139, 34))

        else: # 无持仓
            if posName in self.dict.keys(): 
                del self.dict[posName]
                r = self.rowCount()
                for i in range(r):
                    row = r - 1 - i
                    if (self.item(row, 0).text() == str(pos.symbol)) and (self.item(row, 2).text() == dm[pos.direction]):
                        self.removeRow(row) # 删除表格

        if last: # 处理合计表格
            row = self.rowCount()
            p = {}
            p["总持仓量"] = 0
            p["昨持仓量"] = 0
            p["今持仓量"] = 0
            p["总冻结"] = 0
            p["持仓盈亏"] = float(0)
            p["开仓盈亏"] = float(0)

            for i in range(row - 1):
                p["总持仓量"] += int(self.item(i, 3).text())
                p["昨持仓量"] += int(self.item(i, 4).text())
                p["今持仓量"] += int(self.item(i, 5).text())
                p["总冻结"] += int(self.item(i, 6).text())
                p["持仓盈亏"] += float(self.item(i, 9).text())
                p["开仓盈亏"] += float(self.item(i, 10).text())
            self.dict['合计']['总持仓量'].setText(str(p["总持仓量"]))
            self.dict['合计']['昨持仓量'].setText(str(p["昨持仓量"]))
            self.dict['合计']['今持仓量'].setText(str(p["今持仓量"]))
            self.dict['合计']['总冻结'].setText(str(p["总冻结"]))
            self.dict['合计']['持仓盈亏'].setText(str(round(p["持仓盈亏"],2)))
            self.dict['合计']['开仓盈亏'].setText(str(round(p["开仓盈亏"],2)))

########################################################################
class TradeMonitor(QTableWidget):
    """用于显示成交记录"""
    signal = pyqtSignal(type(Event()))
    #----------------------------------------------------------------------
    def __init__(self, eventEngine, parent=None):
        """Constructor"""
        super(TradeMonitor, self).__init__(parent)
        self.dictLabels = ["合约名称","合约代码",  "买卖标志","成交时间", "价格", "数量", "成交编号", "报单引用",
                           "报单编号","本地报单编号"]
        self.__eventEngine = eventEngine
        self.setWindowTitle('成交')
        self.c = len(self.dictLabels)
        self.setColumnCount(self.c)
        self.setHorizontalHeaderLabels(self.dictLabels)
        self.verticalHeader().setVisible(False)                 # 关闭左边的垂直表头
        self.setEditTriggers(QTableWidget.NoEditTriggers) # 设为不可编辑状态
        self.signal.connect(self.updateTrade)
        self.__eventEngine.register(EVENT_TRADE, self.signal.emit)
        

    #----------------------------------------------------------------------
    def updateTrade(self, event):
        """"""
        var = event.dict_['data']
        data = self.TradeField(event.dict_['data'])

        self.insertRow(0)
        for i in range(4, self.c):
            value = str(data[self.dictLabels[i]])
            item = QTableWidgetItem(value)
            self.setItem(0, i, item)
        self.setItem(0, 1, QTableWidgetItem(data["合约代码"]))
        self.setItem(0, 0, QTableWidgetItem(var["InstrumentName"]))

        if data["开平标志"] == OFFSET_OPEN:
            kp = '多开' if data['买卖方向'] == DIRECTION_LONG else '空开'
        else:
            kp = '空平' if data['买卖方向'] == DIRECTION_LONG else '多平'

        self.setItem(0, 2, QTableWidgetItem(kp))
        
        t = data['成交日期']
        value = t[:4] +'-'+t[4:6] +'-'+t[6:8] +' ' + data["成交时间"]
        self.setItem(0, 3, QTableWidgetItem(value))
        self.setColumnWidth(3, 150)

    def TradeField(self, var):
        tmp = {}
        tmp["合约代码"] = var["InstrumentID"]
        tmp["报单引用"] = var["OrderRef"]
        tmp["交易所代码"] = var["ExchangeID"]
        tmp["成交编号"] = var["TradeID"]
        tmp["买卖方向"] = var["Direction"]
        tmp["报单编号"] = var["OrderSysID"]
        tmp["合约在交易所的代码"] = var["ExchangeInstID"]
        tmp["开平标志"] = var["OffsetFlag"]
        tmp["价格"] = var["Price"]
        tmp["数量"] = var["Volume"]
        tmp["成交日期"] = var["TradeDate"]
        tmp["成交时间"] = var["TradeTime"]
        tmp["本地报单编号"] = var["OrderLocalID"]
        tmp["交易日"] = var["TradingDay"]
        return tmp

########################################################################
class OrderMonitor(QTableWidget):
    """用于显示所有报单"""
    signal = pyqtSignal(type(Event()))
    #----------------------------------------------------------------------
    def __init__(self, eventEngine, parent=None):
        """Constructor"""
        super(OrderMonitor, self).__init__(parent)
        self.__eventEngine = eventEngine
        self.dictLabels = ["报单日期","合约代码","状态信息", "买卖开平标志", "价格", "数量","今成交数量",
                           "剩余数量", "前置编号", "会话编号", "报单引用","本地报单编号","报单编号",]
        self.dict = {}	    # 用来保存报单号对应的单元格对象

        self.setWindowTitle('报单')
        self.setColumnCount(len(self.dictLabels))
        self.setHorizontalHeaderLabels(self.dictLabels)
        self.verticalHeader().setVisible(False)                 # 关闭左边的垂直表头
        self.setEditTriggers(QTableWidget.NoEditTriggers) # 设为不可编辑状态
        self.signal.connect(self.updateOrder)
        self.__eventEngine.register(EVENT_ORDER, self.signal.emit)
    #----------------------------------------------------------------------
    def updateOrder(self, event):
        """"""
        var = event.dict_['data']
        index = str(var["OrderLocalID"])+'.'+var["InstrumentID"]
        if index not in self.dict.keys():
            self.insertRow(0)
            self.dict[index] = {}
            self.dict[index]["合约代码"] = QTableWidgetItem (str(var["InstrumentID"]))
            self.dict[index]["报单引用"] = QTableWidgetItem(str(var["OrderRef"]))
            self.dict[index]["价格"] = QTableWidgetItem(str(var["LimitPrice"]))
            self.dict[index]["数量"] = QTableWidgetItem(str(var["VolumeTotalOriginal"]))
            self.dict[index]["本地报单编号"] = QTableWidgetItem(str(var["OrderLocalID"]))
            self.dict[index]["今成交数量"] = QTableWidgetItem(str(var["VolumeTraded"]))
            self.dict[index]["剩余数量"] = QTableWidgetItem(str(var["VolumeTotal"]))
            self.dict[index]["报单编号"] = QTableWidgetItem(str(var["OrderSysID"]))
            self.dict[index]["前置编号"] = QTableWidgetItem(str(var["FrontID"]))
            self.dict[index]["会话编号"] = QTableWidgetItem(str(var["SessionID"]))
            self.dict[index]["状态信息"] = QTableWidgetItem(str(var["OrderStatus"]))
            t =str(var["InsertDate"]) + ' '+str(var["InsertTime"])
            self.dict[index]["报单日期"] = QTableWidgetItem(str(t))
            if var["CombOffsetFlag"] == OFFSET_OPEN:
                if var["Direction"] == DIRECTION_LONG:
                    self.dict[index]["买卖开平标志"] = QTableWidgetItem('多开')
                    kp = '多开'  #方便log
                else:
                    self.dict[index]["买卖开平标志"] = QTableWidgetItem('空开')
                    kp = '空开'  #方便log
            else:
                if var["Direction"] == DIRECTION_SHORT:
                    self.dict[index]["买卖开平标志"] = QTableWidgetItem('多平')
                    kp = '多平'  #方便log
                else:
                    self.dict[index]["买卖开平标志"] = QTableWidgetItem('空平')
                    kp = '空平'  #方便log
            col =0
            for i in self.dictLabels :
                self.setItem(0,col,self.dict[index][i])
                col +=1
            self.setColumnWidth(0,150)
            self.setColumnWidth(2, 120)
            
            """
            log首次报单，由于每次更新状态都有order事件，后面的不更新
            """        
            log = u'委托回报：%s,方向：%s,价格：%d,数量：%d,已成交：%d,未成交：%d,状态:%s' %(var["InstrumentID"], kp, var["LimitPrice"], var["VolumeTotalOriginal"], var["VolumeTraded"], var["VolumeTotal"],  var["StatusMsg"])
            event = Event(type_=EVENT_LOG)
            event.dict_['log'] = log
            self.__eventEngine.put(event)
            
        else:#更新可能变化的数据
            self.dict[index]["本地报单编号"] .setText(str(var["OrderLocalID"]))
            self.dict[index]["今成交数量"] .setText(str(var["VolumeTraded"]))
            self.dict[index]["剩余数量"] .setText(str(var["VolumeTotal"]))
            self.dict[index]["报单编号"] .setText(str(var["OrderSysID"]))
            self.dict[index]["前置编号"] .setText(str(var["FrontID"]))
            self.dict[index]["会话编号"] .setText(str(var["SessionID"]))
            self.dict[index]["状态信息"] .setText(str(var["OrderStatus"]))
            


########################################################################
class NonetradeMonitor(QTableWidget):
    """用于未成交报单"""
    signal = pyqtSignal(type(Event()))
    #----------------------------------------------------------------------
    def __init__(self, eventEngine,mainEngine,  parent=None):
        """Constructor"""
        super(NonetradeMonitor, self).__init__(parent)
        self.__eventEngine = eventEngine
        self.__mainEngine = mainEngine
        self.dictLabels = ["报单日期", "交易所代码", "合约代码",   "买卖开平标志", "价格", "数量", "今成交数量", "剩余数量", "状态信息", "本地报单编号", "报单编号", "报单引用", "前置编号", "会话编号"]
        self.L=len(self.dictLabels )
        #self.orderref= {}	    # 用来保存报单号
        self.dict = {}	    # 用来保存报单数据

        self.setWindowTitle('未成交')
        self.setColumnCount(len(self.dictLabels))
        self.setHorizontalHeaderLabels(self.dictLabels)
        self.verticalHeader().setVisible(False)                 # 关闭左边的垂直表头
        self.setEditTriggers(QTableWidget.NoEditTriggers) # 设为不可编辑状态
        self.signal.connect(self.updateOrder)
        self.__eventEngine.register(EVENT_ORDER, self.signal.emit)
        self.itemDoubleClicked.connect(self.cancelOrder)
        
    def cancelOrder(self):
        """撤单"""
        req = CtaCancelOrderReq()
        
        req.symbol = self.item(self.currentRow(),2).text()              # 代码
        req.exchange = self.item(self.currentRow(),1).text()            # 交易所
        req.orderID = self.item(self.currentRow(),11).text()            # 报单引用
        req.frontID = self.item(self.currentRow(),12).text()             # 前置机号
        req.sessionID = self.item(self.currentRow(),13).text()           # 会话号
        req.OrderSysID = self.item(self.currentRow(),10).text()        #报单编号

        
        self.__mainEngine.cancelOrder(req)
    #----------------------------------------------------------------------
    def updateOrder(self, event):
        """更新可撤单"""
        var = event.dict_['data']
        index = str(var["OrderSysID"])+'.'+var["InstrumentID"]
        
        if index not in self.dict.keys() and var["StatusMsg"] == '未成交':
            self.insertRow(0)
            self.dict[index] = {}
            self.dict[index]["合约代码"] = QTableWidgetItem (str(var["InstrumentID"]))
            self.dict[index]["报单引用"] = QTableWidgetItem(str(var["OrderRef"]))
            self.dict[index]["价格"] = QTableWidgetItem(str(var["LimitPrice"]))
            self.dict[index]["数量"] = QTableWidgetItem(str(var["VolumeTotalOriginal"]))
            self.dict[index]["本地报单编号"] = QTableWidgetItem(str(var["OrderLocalID"]))
            self.dict[index]["今成交数量"] = QTableWidgetItem(str(var["VolumeTraded"]))
            self.dict[index]["剩余数量"] = QTableWidgetItem(str(var["VolumeTotal"]))
            self.dict[index]["报单编号"] = QTableWidgetItem(str(var["OrderSysID"]))
            self.dict[index]["前置编号"] = QTableWidgetItem(str(var["FrontID"]))
            self.dict[index]["会话编号"] = QTableWidgetItem(str(var["SessionID"]))
            self.dict[index]["状态信息"] = QTableWidgetItem(str(var["StatusMsg"]))
            self.dict[index]["交易所代码"] = QTableWidgetItem(str(var["ExchangeID"]))
            t =str(var["InsertDate"]) + ' '+str(var["InsertTime"])
            self.dict[index]["报单日期"] = QTableWidgetItem(str(t))
            if var["CombOffsetFlag"] == OFFSET_OPEN:
                if var["Direction"] == DIRECTION_LONG:
                    self.dict[index]["买卖开平标志"] = QTableWidgetItem('多开')
                else:
                    self.dict[index]["买卖开平标志"] = QTableWidgetItem('空开')
            else:
                if var["Direction"] == DIRECTION_SHORT:
                    self.dict[index]["买卖开平标志"] = QTableWidgetItem('多平')
                else:
                    self.dict[index]["买卖开平标志"] = QTableWidgetItem('空平')
            col =0
            for i in self.dictLabels :
                self.setItem(0,col,self.dict[index][i])
                col +=1
            self.setColumnWidth(0,120)
            self.setColumnWidth(2, 120)
            

            
        if index  in self.dict.keys():#撤单
            self.dict[index]["状态信息"].setText(str(var["StatusMsg"]))
            if var["StatusMsg"] == '全部成交':
                r =self.rowCount()
                for i in range(r):
                    j=r-1-i
                    if self.item(j,9).text() != '未成交':
                        self.removeRow(j)


########################################################################
class RmSpinBox(QSpinBox):
    """调整参数用的数值框"""

    #----------------------------------------------------------------------
    def __init__(self, value):
        """Constructor"""
        super(RmSpinBox, self).__init__()

        self.setMinimum(0)
        self.setMaximum(1000000)
        
        self.setValue(value)
    
########################################################################
class RmLine(QFrame):
    """水平分割线"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(RmLine, self).__init__()
        self.setFrameShape(self.HLine)
        self.setFrameShadow(self.Sunken)
    
########################################################################
class RmEngineManager(QWidget):
    """风控引擎的管理组件"""

    #----------------------------------------------------------------------
    def __init__(self, rmEngine, eventEngine, parent=None):
        """Constructor"""
        super(RmEngineManager, self).__init__(parent)
        
        self.rmEngine = rmEngine
        self.eventEngine = eventEngine
        
        self.initUi()
        self.updateEngineStatus()

    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(u'风险管理')
        
        # 设置界面
        self.buttonSwitchEngineStatus = QPushButton(u'风控模块运行中')
        
        self.spinOrderFlowLimit = RmSpinBox(self.rmEngine.orderFlowLimit)
        self.spinOrderFlowClear = RmSpinBox(self.rmEngine.orderFlowClear)
        self.spinOrderSizeLimit = RmSpinBox(self.rmEngine.orderSizeLimit)
        self.spinTradeLimit = RmSpinBox(self.rmEngine.tradeLimit)
        #self.spinWorkingOrderLimit = RmSpinBox(self.rmEngine.workingOrderLimit)
        
        buttonClearOrderFlowCount = QPushButton(u'清空流控计数')
        buttonClearTradeCount = QPushButton(u'清空总成交计数')
        buttonSaveSetting = QPushButton(u'保存设置')
        
        Label = QLabel
        grid = QGridLayout()
        grid.addWidget(Label(u'工作状态'), 0, 0)
        grid.addWidget(self.buttonSwitchEngineStatus, 0, 1)
        grid.addWidget(RmLine(), 1, 0, 1, 2)
        grid.addWidget(Label(u'流控上限'), 2, 0)
        grid.addWidget(self.spinOrderFlowLimit, 2, 1)
        grid.addWidget(Label(u'流控清空（秒）'), 3, 0)
        grid.addWidget(self.spinOrderFlowClear, 3, 1)
        grid.addWidget(RmLine(), 4, 0, 1, 2)
        grid.addWidget(Label(u'单笔委托上限'), 5, 0)
        grid.addWidget(self.spinOrderSizeLimit, 5, 1)
        grid.addWidget(RmLine(), 6, 0, 1, 2)
        grid.addWidget(Label(u'总成交上限'), 7, 0)
        grid.addWidget(self.spinTradeLimit, 7, 1)
        grid.addWidget(RmLine(), 8, 0, 1, 2)
        #grid.addWidget(Label(u'活动订单上限'), 9, 0)
        #grid.addWidget(self.spinWorkingOrderLimit, 9, 1)
        
        hbox = QHBoxLayout()
        hbox.addWidget(buttonClearOrderFlowCount)
        hbox.addWidget(buttonClearTradeCount)
        hbox.addStretch()
        hbox.addWidget(buttonSaveSetting)
        
        vbox = QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        
        # 连接组件信号
        self.spinOrderFlowLimit.valueChanged.connect(self.rmEngine.setOrderFlowLimit)
        self.spinOrderFlowClear.valueChanged.connect(self.rmEngine.setOrderFlowClear)
        self.spinOrderSizeLimit.valueChanged.connect(self.rmEngine.setOrderSizeLimit)
        self.spinTradeLimit.valueChanged.connect(self.rmEngine.setTradeLimit)
        #self.spinWorkingOrderLimit.valueChanged.connect(self.rmEngine.setWorkingOrderLimit)
        
        self.buttonSwitchEngineStatus.clicked.connect(self.switchEngineSatus)
        buttonClearOrderFlowCount.clicked.connect(self.rmEngine.clearOrderFlowCount)
        buttonClearTradeCount.clicked.connect(self.rmEngine.clearTradeCount)
        buttonSaveSetting.clicked.connect(self.rmEngine.saveSetting)
        
        # 设为固定大小
        self.setFixedSize(self.sizeHint())
        
    #----------------------------------------------------------------------
    def switchEngineSatus(self):
        """控制风控引擎开关"""
        self.rmEngine.switchEngineStatus()
        self.updateEngineStatus()
        
    #----------------------------------------------------------------------
    def updateEngineStatus(self):
        """更新引擎状态"""
        if self.rmEngine.active:
            self.buttonSwitchEngineStatus.setText(u'风控模块运行中')
        else:
            self.buttonSwitchEngineStatus.setText(u'风控模块未启动')

########################################################################
class CtaValueMonitor(QTableWidget):
    """参数监控"""

    #----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(CtaValueMonitor, self).__init__(parent)
        
        self.keyCellDict = {}
        self.data = None
        self.inited = False
        
        self.initUi()
        
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setRowCount(1)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(self.NoEditTriggers)
        
        self.setMaximumHeight(self.sizeHint().height())
        
    #----------------------------------------------------------------------
    def updateData(self, data):
        """更新数据"""
        if not self.inited:
            self.setColumnCount(len(data))
            self.setHorizontalHeaderLabels(data.keys())
            
            col = 0
            for k, v in data.items():
                # cell = QTableWidgetItem(unicode(v))
                cell = QTableWidgetItem(str(v))
                self.keyCellDict[k] = cell
                self.setItem(0, col, cell)
                col += 1
            
            self.inited = True
        else:
            for k, v in data.items():
                cell = self.keyCellDict[k]
                # cell.setText(unicode(v))
                cell.setText(str(v))

########################################################################
class CtaStrategyManager(QGroupBox):
    """策略管理组件"""
    signal = pyqtSignal(type(Event()))

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, eventEngine, name, parent=None):
        """Constructor"""
        super(CtaStrategyManager, self).__init__(parent)
        
        self.ctaEngine = ctaEngine
        self.eventEngine = eventEngine
        self.name = name
        
        self.initUi()
        self.updateMonitor()
        self.registerEvent()
        
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setTitle(self.name)
        
        self.paramMonitor = CtaValueMonitor(self)
        self.varMonitor = CtaValueMonitor(self)
        
        height = 65
        self.paramMonitor.setFixedHeight(height)
        self.varMonitor.setFixedHeight(height)
        
        buttonInit = QPushButton(INIT)
        buttonStart = QPushButton(START)
        buttonStop = QPushButton(STOP)
        buttonInit.clicked.connect(self.init)
        buttonStart.clicked.connect(self.start)
        buttonStop.clicked.connect(self.stop)
        
        hbox1 = QHBoxLayout()     
        hbox1.addWidget(buttonInit)
        hbox1.addWidget(buttonStart)
        hbox1.addWidget(buttonStop)
        hbox1.addStretch()
        
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.paramMonitor)
        
        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.varMonitor)
        
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)

        self.setLayout(vbox)
        
    #----------------------------------------------------------------------
    def updateMonitor(self, event=None):
        """显示策略最新状态"""
        paramDict = self.ctaEngine.getStrategyParam(self.name)
        if paramDict:
            self.paramMonitor.updateData(paramDict)
            
        varDict = self.ctaEngine.getStrategyVar(self.name)
        if varDict:
            self.varMonitor.updateData(varDict)        
            
    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.signal.connect(self.updateMonitor)
        self.eventEngine.register(EVENT_CTA_STRATEGY+self.name, self.signal.emit)
    
    #----------------------------------------------------------------------
    def init(self):
        """初始化策略"""
        self.ctaEngine.initStrategy(self.name)
    
    #----------------------------------------------------------------------
    def start(self):
        """启动策略"""
        self.ctaEngine.startStrategy(self.name)
        
    #----------------------------------------------------------------------
    def stop(self):
        """停止策略"""
        self.ctaEngine.stopStrategy(self.name)


########################################################################
class CtaEngineManager(QWidget):
    """CTA引擎管理组件"""
    signal = pyqtSignal(type(Event()))

    #----------------------------------------------------------------------
    def __init__(self, eventEngine, ctaEngine, parent=None):
        """Constructor"""
        super(CtaEngineManager, self).__init__(parent)
        
        self.ctaEngine = ctaEngine
        self.eventEngine = eventEngine
        
        self.strategyLoaded = False
        
        self.initUi()
        self.registerEvent()
        
        # 记录日志
        self.ctaEngine.writeCtaLog(CTA_ENGINE_STARTED)        
        
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(CTA_STRATEGY)
        
        # 按钮
        loadButton = QPushButton(LOAD_STRATEGY)
        initAllButton = QPushButton(INIT_ALL)
        startAllButton = QPushButton(START_ALL)
        stopAllButton = QPushButton(STOP_ALL)
        
        loadButton.clicked.connect(self.load)
        initAllButton.clicked.connect(self.initAll)
        startAllButton.clicked.connect(self.startAll)
        stopAllButton.clicked.connect(self.stopAll)
        
        # 滚动区域，放置所有的CtaStrategyManager
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        
        # CTA组件的日志监控
        # self.ctaLogMonitor = QTextEdit()
        # self.ctaLogMonitor.setReadOnly(True)
        # self.ctaLogMonitor.setMaximumHeight(200)
        
        # 设置布局
        hbox2 = QHBoxLayout()
        hbox2.addWidget(loadButton)
        hbox2.addWidget(initAllButton)
        hbox2.addWidget(startAllButton)
        hbox2.addWidget(stopAllButton)
        hbox2.addStretch()
        
        vbox = QVBoxLayout()
        vbox.addLayout(hbox2)
        vbox.addWidget(self.scrollArea)
        # vbox.addWidget(self.ctaLogMonitor)
        self.setLayout(vbox)
        
    #----------------------------------------------------------------------
    def initStrategyManager(self):
        """初始化策略管理组件界面"""        
        w = QWidget()
        vbox = QVBoxLayout()
        
        for name in self.ctaEngine.strategyDict.keys():
            strategyManager = CtaStrategyManager(self.ctaEngine, self.eventEngine, name)
            vbox.addWidget(strategyManager)
        
        vbox.addStretch()
        
        w.setLayout(vbox)
        self.scrollArea.setWidget(w)   
        
    #----------------------------------------------------------------------
    def initAll(self):
        """全部初始化"""
        self.ctaEngine.initAll()    
            
    #----------------------------------------------------------------------
    def startAll(self):
        """全部启动"""
        self.ctaEngine.startAll()
            
    #----------------------------------------------------------------------
    def stopAll(self):
        """全部停止"""
        self.ctaEngine.stopAll()
            
    #----------------------------------------------------------------------
    def load(self):
        """加载策略"""
        if not self.strategyLoaded:
            self.ctaEngine.loadSetting()
            self.initStrategyManager()
            self.strategyLoaded = True
            self.ctaEngine.writeCtaLog(STRATEGY_LOADED)
        
    #----------------------------------------------------------------------
    # def updateCtaLog(self, event):
    #     """更新CTA相关日志"""
    #     log = event.dict_['data']
    #     content = '\t'.join([log.logTime, log.logContent])
    #     self.ctaLogMonitor.append(content)
    def robot(self):
        '''自动载入、初始化、启动'''
        self.load()
        self.initAll()
        self.startAll()
    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        # self.signal.connect(self.updateCtaLog)
        # self.eventEngine.register(EVENT_CTA_LOG, self.signal.emit)
        self.signal.connect(self.robot)
        self.eventEngine.register(EVENT_CTA_ROBOT, self.signal.emit)

#######################################################################            
class AboutWidget(QDialog):
    """显示关于信息"""

    #----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(AboutWidget, self).__init__(parent)

        self.initUi()

    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setWindowTitle(u'关于刀削面')

        text = u"""
            Developed by vvipi.

            感谢VNPY！
            
            感谢PYCTP！

            感谢何先生的封装教程！
            
            本交易助手是为刀削面定制的自动交易终端
            交易策略采用土鳖交易法则
            
            八月，是期货投机最危险的月份，同样危险的月份还有：
            二月、十月、七月、三月、六月、一月、十二月、十一月、五月、九月、四月。
            
            刀削面加油！
            
            2017.8
            
            """

        label = QLabel()
        label.setText(text)
        label.setMinimumWidth(500)

        vbox = QVBoxLayout()
        vbox.addWidget(label)

        self.setLayout(vbox)    