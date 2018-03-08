# encoding: UTF-8

"""
从vnpy搬运过来的各种对象，部分有略改
"""

from py_ctp.constant import *

class CtaTickData(object):
    """Tick数据"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.vtSymbol = ''            # vt系统代码
        self.symbol = ''              # 合约代码
        self.exchange = ''            # 交易所代码

        # 成交数据
        self.lastPrice = 0.0            # 最新成交价
        self.volume = 0                 # 最新成交量
        self.openInterest = 0           # 持仓量

        self.upperLimit = 0.0           # 涨停价
        self.lowerLimit = 0.0           # 跌停价

        # tick的时间
        self.date = ''            # 日期
        self.time = ''            # 时间
        self.datetime = None                # python的datetime时间对象
        
        # 五档行情
        self.bidPrice1 = 0.0
        self.bidPrice2 = 0.0
        self.bidPrice3 = 0.0
        self.bidPrice4 = 0.0
        self.bidPrice5 = 0.0
        
        self.askPrice1 = 0.0
        self.askPrice2 = 0.0
        self.askPrice3 = 0.0
        self.askPrice4 = 0.0
        self.askPrice5 = 0.0        
        
        self.bidVolume1 = 0
        self.bidVolume2 = 0
        self.bidVolume3 = 0
        self.bidVolume4 = 0
        self.bidVolume5 = 0
        
        self.askVolume1 = 0
        self.askVolume2 = 0
        self.askVolume3 = 0
        self.askVolume4 = 0
        self.askVolume5 = 0    

########################################################################
class CtaOrderReq(object):
    """发单时传入的对象类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.symbol = EMPTY_STRING              # 代码
        self.exchange = EMPTY_STRING            # 交易所
        self.price = EMPTY_FLOAT                # 价格
        self.volume = EMPTY_INT                 # 数量
    
        self.priceType = EMPTY_STRING           # 价格类型
        self.direction = EMPTY_STRING           # 买卖
        self.offset = EMPTY_STRING              # 开平
        
        # 以下为IB相关
        # self.productClass = EMPTY_UNICODE       # 合约类型
        # self.currency = EMPTY_STRING            # 合约货币
        # self.expiry = EMPTY_STRING              # 到期日
        # self.strikePrice = EMPTY_FLOAT          # 行权价
        # self.optionType = EMPTY_UNICODE         # 期权类型        
        

########################################################################
class CtaCancelOrderReq(object):
    """撤单时传入的对象类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.symbol = EMPTY_STRING              # 代码
        self.exchange = EMPTY_STRING            # 交易所
        
        # 以下字段主要和CTP、LTS类接口相关
        self.orderID = EMPTY_STRING             # 报单号
        self.frontID = EMPTY_STRING             # 前置机号
        self.sessionID = EMPTY_STRING           # 会话号
        self.OrderSysID = EMPTY_STRING
########################################################################
class CtaOrderData(object):
    """订单数据类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(CtaOrderData, self).__init__()
        
        # 代码编号相关
        self.symbol = EMPTY_STRING              # 合约代码
        self.exchange = EMPTY_STRING            # 交易所代码
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码
        
        self.orderID = EMPTY_STRING             # 订单编号
        self.vtOrderID = EMPTY_STRING           # 订单在vt系统中的唯一编号，通常是 Gateway名.订单编号
        
        # 报单相关
        self.direction = EMPTY_UNICODE          # 报单方向
        self.offset = EMPTY_UNICODE             # 报单开平仓
        self.price = EMPTY_FLOAT                # 报单价格
        self.totalVolume = EMPTY_INT            # 报单总数量
        self.tradedVolume = EMPTY_INT           # 报单成交数量
        self.status = EMPTY_UNICODE             # 报单状态
        
        self.orderTime = EMPTY_STRING           # 发单时间
        self.cancelTime = EMPTY_STRING          # 撤单时间
        
        # CTP/LTS相关
        self.frontID = EMPTY_INT                # 前置机编号
        self.sessionID = EMPTY_INT              # 连接编号


class CtaTradeData(object):
    """成交数据类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(VtTradeData, self).__init__()
        
        # 代码编号相关
        self.symbol = EMPTY_STRING              # 合约代码
        self.exchange = EMPTY_STRING            # 交易所代码
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码
        
        self.tradeID = EMPTY_STRING             # 成交编号
        self.vtTradeID = EMPTY_STRING           # 成交在vt系统中的唯一编号，通常是 Gateway名.成交编号
        
        self.orderID = EMPTY_STRING             # 订单编号
        self.vtOrderID = EMPTY_STRING           # 订单在vt系统中的唯一编号，通常是 Gateway名.订单编号
        
        # 成交相关
        self.direction = EMPTY_UNICODE          # 成交方向
        self.offset = EMPTY_UNICODE             # 成交开平仓
        self.price = EMPTY_FLOAT                # 成交价格
        self.volume = EMPTY_INT                 # 成交数量
        self.tradeTime = EMPTY_STRING           # 成交时间
   



########################################################################
class CtaPositionData(object):
    """持仓数据类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.gatewayName = EMPTY_STRING         # Gateway名称      
        # 代码编号相关
        self.symbol = EMPTY_STRING              # 合约代码
        self.exchange = EMPTY_STRING            # 交易所代码
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码，合约代码.交易所代码  
        
        # 持仓相关
        self.direction = EMPTY_STRING           # 持仓方向
        self.position = EMPTY_INT               # 持仓量
        self.frozen = EMPTY_INT                 # 冻结数量
        self.price = EMPTY_FLOAT                # 持仓均价
        self.vtPositionName = EMPTY_STRING      # 持仓在vt系统中的唯一代码，通常是vtSymbol.方向
        self.ydPosition = EMPTY_INT             # 昨持仓
        self.positionProfit = EMPTY_FLOAT       # 持仓盈亏（盯）

        # 自行添加
        self.openPrice = EMPTY_FLOAT            # 开仓均价
        self.openProfit = EMPTY_FLOAT           # 开仓盈亏（浮）
        self.name = EMPTY_STRING                # 合约名称
########################################################################
class CtaAccountData(object):
    """账户数据类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(CtaAccountData, self).__init__()
        
        # 账号代码相关
        self.accountID = EMPTY_STRING           # 账户代码
        self.vtAccountID = EMPTY_STRING         # 账户在vt中的唯一代码，通常是 Gateway名.账户代码
        
        # 数值相关
        self.preBalance = EMPTY_FLOAT           # 昨日账户结算净值
        self.balance = EMPTY_FLOAT              # 账户净值
        self.available = EMPTY_FLOAT            # 可用资金
        self.commission = EMPTY_FLOAT           # 今日手续费
        self.margin = EMPTY_FLOAT               # 保证金占用
        self.closeProfit = EMPTY_FLOAT          # 平仓盈亏
        self.positionProfit = EMPTY_FLOAT       # 持仓盈亏
        

