# encoding: UTF-8
"""
窗口部件
"""
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from py_ctp.eventEngine import  *
from py_ctp.eventType import  *
from py_ctp.constant import *
from datetime import datetime, date
import json
import logging

class MainWindow(QMainWindow):
    """主窗口"""
    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        super(MainWindow, self).__init__()
        
        self.me = mainEngine
        self.ee = eventEngine
        
        self.widgetDict = {}    # 用来保存子窗口的字典
        
        self.initUi()
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle("CTP demo——基于vnpy的ctp接口")
        widgetLogM, dockLogM = self.createDock(LogMonitor, '日志', Qt.TopDockWidgetArea, 1, True)
        widgetAccountM, dockAccountM = self.createDock(AccountMonitor, '账户资金', Qt.TopDockWidgetArea)
        widgetPositionM, dockPositionM = self.createDock(PositionMonitor, '持仓', Qt.TopDockWidgetArea, 2)
        widgetTradeM, dockTradeM = self.createDock(TradeMonitor, '成交', Qt.TopDockWidgetArea)
        widgetOrderM, dockOrderM = self.createDock(OrderMonitor, '委托', Qt.TopDockWidgetArea)
        widgetNonetradeM, dockNonetradeM = self.createDock(NonetradeMonitor, '撤单', Qt.TopDockWidgetArea, 2)    
        self.tabifyDockWidget(dockAccountM, dockPositionM)
        self.tabifyDockWidget(dockAccountM, dockTradeM)
        self.tabifyDockWidget(dockAccountM, dockOrderM)
        self.tabifyDockWidget(dockAccountM, dockNonetradeM)
        self.tabifyDockWidget(dockAccountM, dockLogM)     
        
        dockLogM.raise_()
        dockAccountM.setMinimumWidth(720)
        dockLogM.setMinimumWidth(260)
       
        aboutAction = QAction(u'关于', self)
        aboutAction.triggered.connect(self.openAbout)    
        
       
        menubar = self.menuBar()
        helpMenu = menubar.addMenu(u'帮助')
        helpMenu.addAction(aboutAction)
            
    def createDock(self, widgetClass, widgetName, widgetArea, engines=1, float=False):
        """创建停靠组件"""
        if engines ==1:
            widget = widgetClass( self.ee)
        elif engines ==2:
            widget = widgetClass( self.ee, self.me)
        dock = QDockWidget(widgetName)
        dock.setWidget(widget)
        dock.setObjectName(widgetName)
        if float == True:
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
        path = 'log/eventLog%s'%date.today()
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
        
        logging.info(t + ',' + log)

########################################################################
class AccountMonitor(QTableWidget):
    """用于显示账户"""
    signal = pyqtSignal(type(Event()))#这里的TYPE也可以是DICT，需要在注册事件中进行数据格式转换
    #----------------------------------------------------------------------
    def __init__(self, eventEngine, parent=None):
        """Constructor"""
        super(AccountMonitor, self).__init__(parent)
        self.dictLabels = ["动态权益","总保证金","冻结保证金", "手续费","平仓盈亏", "持仓盈亏","可用资金","可取资金"]
        self.__eventEngine = eventEngine
        #self.__mainEngine = mainEngine
        self.list_account = []#保存账户数据的LIST
        self.count = 0  # 账户数据第一次保存记号
        self.dict = {}	    # 用来保存账户对应的单元格
        self.setWindowTitle('账户')
        self.setColumnCount(len(self.dictLabels))#设置列
        self.insertRow(0)#因为只有1行数据，直接初始化
        col=0#表格列计数器
        for i in self.dictLabels:#初始化表格为空格
            self.dict[i] = QTableWidgetItem('')
            self.dict[i].setTextAlignment(0x0004 | 0x0080)  # 居中
            self.setItem(0,col,self.dict[i] )
            col +=1
        self.setHorizontalHeaderLabels(self.dictLabels)
        self.verticalHeader().setVisible(False)                 # 关闭左边的垂直表头
        self.setEditTriggers(QTableWidget.NoEditTriggers) # 设为不可编辑状态
        self.signal.connect(self.updateAccount)
        self.__eventEngine.register(EVENT_ACCOUNT, self.signal.emit)

    def updateAccount(self, event):
        var =self.TradingAccountField(event.dict_['data'])#这里的dict'keys要包含self.dictLabels，否则会出错。
        self.count += 1#也可以每执行一次保存一次，收盘后可以看到账户的曲线。
        if self.count ==1:#记录一次账户数据，只记录登陆后的第一个数据。
            self.list_account.append(var)#这个代码可有可无，看个人的使用而言。
        for i in self.dictLabels:#刷新表格
            value = var[i]#i就是DICT的key
            try:
                value = str(round(value, 2))#保留2位小数
            except:
                value = str(value)
            self.dict[i].setText(value)#刷新单元格数据
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
        
########################################################################
class PositionMonitor(QTableWidget):
    """用于显示持仓"""
    signal = pyqtSignal(type(Event()))
    #----------------------------------------------------------------------
    def __init__(self, eventEngine, mainEngine, parent=None):
        """Constructor"""
        super(PositionMonitor, self).__init__(parent)
        self.dictLabels = ["合约代码", "合约名称","持仓方向", "总持仓量", "昨持仓量", "今持仓量","今冻结","昨冻结",
                           "合约开仓价值", "合约持仓价值", "开仓均价", "持仓盈亏","开仓盈亏","风险度"]
        self.__eventEngine = eventEngine
        self.__mainEngine = mainEngine
        self.dict ={}
        self.setWindowTitle('持仓')
        self.setColumnCount(len(self.dictLabels))
        self.setHorizontalHeaderLabels(self.dictLabels)
        self.verticalHeader().setVisible(False)                 # 关闭左边的垂直表头
        self.setEditTriggers(QTableWidget.NoEditTriggers) # 设为不可编辑状态
        self.signal.connect(self.updateposition)
        self.__eventEngine.register(EVENT_POSITION, self.signal.emit)
        self.insertRow(0)#插入合计的表格
        col = 0
        self.dict['合计'] = {}
        for i in self.dictLabels:
            self.dict['合计'][i] = QTableWidgetItem('')
            self.dict['合计'][i].setTextAlignment(0x0004 | 0x0080)  # 居中
            self.setItem(0, col, self.dict['合计'][i])
            col += 1
        self.dict['合计']["合约代码"].setText('合计')
        
        
    def updateposition(self,event):
        var = event.dict_['data']
        last = event.dict_['last']
        PreBalance = float(self.__mainEngine.dict_account["静态权益"])
        directionmap = {'多持':DIRECTION_LONG, '空持':DIRECTION_SHORT}
        ExchangeID =var['ExchangeID']
        
        # if var["InstrumentID"] == 'j1801':
            # print('date', var["PositionDate"], 'pos', var["Position"], 'taday', var["TodayPosition"], 'yestoday', var["YdPosition"], 'longfrozen', var["LongFrozen"], 'shortfrozen', var["ShortFrozen"])
        
        if var["Position"] != 0:#有持仓
            index = var["InstrumentID"] + '.' + var["PosiDirection"]
            if index not in self.dict.keys():#计算持仓数据
                self.dict[index] = {}
                self.dict[index]["合约代码"] = QTableWidgetItem(str(var["InstrumentID"]))
                self.dict[index]["合约名称"] = QTableWidgetItem(str(var['InstrumentName']))
                self.dict[index]["合约持仓价值"] = QTableWidgetItem(str(var["PositionCost"]))
                self.dict[index]["昨结算价"] = QTableWidgetItem(str(var["PreSettlementPrice"]))
                self.dict[index]["乘数"] = var["VolumeMultiple"]
                self.dict[index]["持仓盈亏"] = QTableWidgetItem(str(round(var["PositionProfit"],2)))
                self.dict[index]["合约开仓价值"] = QTableWidgetItem(str(var["OpenCost"]))
                self.dict[index]["开仓均价"] =QTableWidgetItem(str(round( var["OpenCost"]/ self.dict[index]["乘数"],2)))
                self.dict[index]["总持仓量"] =  QTableWidgetItem(str(var["Position"]))
                self.dict[index]["今持仓量"] = QTableWidgetItem('0')
                self.dict[index]["昨持仓量"] = QTableWidgetItem('0') 
                self.dict[index]["风险度"] = QTableWidgetItem(str(round(var["OpenCost"] / PreBalance * 100, 2)))

                if var["PosiDirection"] == DIRECTION_LONG:
                    self.dict[index]["持仓方向"] =QTableWidgetItem(str('多持'))
                    self.dict[index]["持仓方向"].setBackground(QColor(255, 0, 0))
                    po = var["PositionProfit"] + var["PositionCost"] - var["OpenCost"]
                    self.dict[index]["开仓盈亏"]  =QTableWidgetItem(str(po))
                else:
                    self.dict[index]["持仓方向"] =QTableWidgetItem(str('空持'))
                    self.dict[index]["持仓方向"].setBackground(QColor(34, 139, 34))
                    po = round(var["PositionProfit"] + var["OpenCost"] - var["PositionCost"], 2)
                    self.dict[index]["开仓盈亏"]  =QTableWidgetItem(str(po))
                if var["PositionProfit"] > 0 :
                    self.dict[index]["持仓盈亏"].setBackground(QColor(255, 0, 0))
                else:
                    self.dict[index]["持仓盈亏"].setBackground(QColor(34, 139, 34))
                if po >0 :
                    self.dict[index]["开仓盈亏"].setBackground(QColor(255, 0, 0))
                else:
                    self.dict[index]["开仓盈亏"].setBackground(QColor(34, 139, 34))
                if ExchangeID == EXCHANGE_SHFE:
                    if var["PositionDate"] == "2":   #1今仓，2昨仓
                        self.dict[index]["昨持仓量"].setText(str(var["Position"]))
                        self.dict[index]["昨冻结"] = QTableWidgetItem(str( var["LongFrozen"] + var["ShortFrozen"]))
                        self.dict[index]["今冻结"] = QTableWidgetItem('')
                    if var["PositionDate"] == "1":  #1今仓，2昨仓
                        self.dict[index]["今持仓量"].setText(str(var["Position"]))
                        self.dict[index]["今冻结"] = QTableWidgetItem(str( var["LongFrozen"] + var["ShortFrozen"]))
                        self.dict[index]["昨冻结"] = QTableWidgetItem('')
                    pt = int(self.dict[index]["今持仓量"].text()) + int(self.dict[index]["昨持仓量"].text())
                    self.dict[index]["总持仓量"].setText(str(pt))
                else:
                #非上期所的品种都算昨持
                    self.dict[index]["昨持仓量"].setText(str(var["Position"]))
                    self.dict[index]["昨冻结"] = QTableWidgetItem(str( var["LongFrozen"] + var["ShortFrozen"]))
                    self.dict[index]["今冻结"] = QTableWidgetItem('')
                
                self.insertRow(0)#插入表格第一行
                col = 0#列计数
                for label in self.dictLabels:
                    self.dict[index][label].setTextAlignment(0x0004 | 0x0080)  # 居中
                    self.setItem(0, col, self.dict[index][label])
                    col += 1

            else:#更新可能会变的数据
                self.dict[index]["持仓盈亏"].setText(str(round(var["PositionProfit"],2)))
                if var["PosiDirection"] == DIRECTION_LONG:
                    po = round(var["PositionProfit"] + var["PositionCost"] - var["OpenCost"], 2)
                    self.dict[index]["开仓盈亏"].setText(str(po))
                else:
                    po = round(var["PositionProfit"] + var["OpenCost"] - var["PositionCost"], 2)
                    self.dict[index]["开仓盈亏"].setText(str(po))
                    
                self.dict[index]["总持仓量"] .setText(str(var["Position"]))
                if ExchangeID == EXCHANGE_SHFE:
                    if var["PositionDate"] == "2":   #1今仓，2昨仓
                        self.dict[index]["昨持仓量"].setText(str(var["Position"]))
                        self.dict[index]["昨冻结"].setText(str( var["LongFrozen"] + var["ShortFrozen"]))
                    if var["PositionDate"] == "1":  #1今仓，2昨仓
                        self.dict[index]["今持仓量"].setText(str(var["Position"]))
                        self.dict[index]["今冻结"].setText(str( var["LongFrozen"] + var["ShortFrozen"]))
                    pt = int(self.dict[index]["今持仓量"].text()) + int(self.dict[index]["昨持仓量"].text())
                    self.dict[index]["总持仓量"].setText(str(pt))
                else:
                    self.dict[index]["昨持仓量"].setText(str(var["Position"]))
                    self.dict[index]["昨冻结"].setText(str( var["LongFrozen"] + var["ShortFrozen"]))

                if var["PositionProfit"] > 0:
                    self.dict[index]["持仓盈亏"].setBackground(QColor(255, 0, 0))
                else:
                    self.dict[index]["持仓盈亏"].setBackground(QColor(34, 139, 34))
                if po > 0:
                    self.dict[index]["开仓盈亏"].setBackground(QColor(255, 0, 0))
                else:
                    self.dict[index]["开仓盈亏"].setBackground(QColor(34, 139, 34))
        else :#没有持仓，有2个情况：1，已经全部平仓，2，有开仓挂单
            index = var["InstrumentID"] + '.' + var["PosiDirection"]
            if index in self.dict.keys():#只处理全部平仓的表格
                del self.dict[index]
                r = self.rowCount()
                for i in range(r ):
                    row = r - 1 - i
                    if self.item(row, 0).text() == var["InstrumentID"] and directionmap[self.item(row, 2).text()] == var["PosiDirection"]:
                        self.removeRow(row)#删除表格
                        
        if last == True :#处理合计表格
            row = self.rowCount()
            p = {}
            p["总持仓量"] = 0
            p["昨持仓量"] = 0
            p["今持仓量"] = 0
            p["合约持仓价值"] = float(0)
            p["合约开仓价值"] = float(0)
            p["持仓盈亏"] = float(0)
            p["开仓盈亏"] = float(0)
            p["风险度"] = float(0)

            for i in range(row - 1):
                p["总持仓量"] += int(self.item(i, 3).text())
                p["昨持仓量"] += int(self.item(i, 4).text())
                p["今持仓量"] += int(self.item(i, 5).text())
                p["合约持仓价值"] += float(self.item(i, 8).text())
                p["合约开仓价值"] += float(self.item(i, 9).text())
                p["持仓盈亏"] += float(self.item(i, 11).text())
                p["开仓盈亏"] += float(self.item(i, 12).text())
                p["风险度"] = round(float(self.item(i, 13).text()) + p["风险度"], 2)
            self.dict['合计']['总持仓量'].setText(str(p["总持仓量"]))
            self.dict['合计']['昨持仓量'].setText(str( p["昨持仓量"]))
            self.dict['合计']['今持仓量'].setText(str(p["今持仓量"]))
            self.dict['合计']['合约持仓价值'].setText(str(p["合约持仓价值"]))
            self.dict['合计']['合约开仓价值'].setText(str(p["合约开仓价值"]))
            self.dict['合计']['持仓盈亏'].setText(str(round(p["持仓盈亏"],2) ))
            self.dict['合计']['开仓盈亏'].setText(str(round(p["开仓盈亏"],2)))
            self.dict['合计']['风险度'].setText(str(p["风险度"]))

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
        #print(data)
        self.insertRow(0)
        for i in range(4,self.c):
            value = str(data[self.dictLabels[i]])
            item = QTableWidgetItem(value)
            self.setItem(0, i, item)
        self.setItem(0, 1, QTableWidgetItem(data["合约代码"]))
        self.setItem(0, 0, QTableWidgetItem(var["InstrumentName"]))
        if data["开平标志"] == OFFSET_OPEN:
            if data['买卖方向'] == DIRECTION_LONG:
                value ='多开'
            else:
                value ='空开'
        else:
            if data['买卖方向'] == DIRECTION_LONG:
                value = '空平'
            else:
                value = '多平'
        self.setItem(0, 2, QTableWidgetItem(value))
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
        
        req.symbol = self.item( self.currentRow(),2).text()              # 代码
        req.exchange = self.item( self.currentRow(),1).text()            # 交易所
        req.orderID = self.item( self.currentRow(),11).text()            # 报单引用
        req.frontID = self.item( self.currentRow(),12).text()             # 前置机号
        req.sessionID = self.item( self.currentRow(),13).text()           # 会话号
        req.OrderSysID = self.item( self.currentRow(),10).text()        #报单编号

        #print('symbol:%s,exchange:%s,orderID:%s,frontID:%s,sessionID:%s'%(req.symbol, req.exchange, req.orderID, req.frontID, req.sessionID))
        
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
        self.setWindowTitle(u'关于本demo')

        text = u"""
            Developed by vvipi.

            感谢VNPY！
            
            感谢PYCTP！

            感谢何先生的封装教程！
            
            本demo是为个人定制的自动交易终端的基础部分
            
            十二月，是期货投机最危险的月份，同样危险的月份还有：
            二月、十月、七月、三月、六月、一月、八月、十一月、五月、九月、四月。
            
            加油！
            
            2017.12
            
            """

        label = QLabel()
        label.setText(text)
        label.setMinimumWidth(500)

        vbox = QVBoxLayout()
        vbox.addWidget(label)

        self.setLayout(vbox)    