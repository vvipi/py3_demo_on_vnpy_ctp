# encoding: UTF-8

# 默认空值
EMPTY_STRING = ''
EMPTY_UNICODE = u''
EMPTY_INT = 0
EMPTY_FLOAT = 0.0

# 方向常量
DIRECTION_NONE = u'无方向'
DIRECTION_LONG = u'买入'
DIRECTION_SHORT = u'卖出'
DIRECTION_UNKNOWN = u'未知'
DIRECTION_NET = u'净'
DIRECTION_SELL = u'卖出'              # IB接口
DIRECTION_COVEREDSHORT = u'备兑空'    # 证券期权

# 开平常量
OFFSET_NONE = u'无开平'
OFFSET_OPEN = u'开仓'
OFFSET_CLOSE = u'平仓'
OFFSET_CLOSETODAY = u'平今'
OFFSET_CLOSEYESTERDAY = u'平昨'
OFFSET_UNKNOWN = u'未知'

# 状态常量
STATUS_NOTTRADED = u'未成交'
STATUS_PARTTRADED = u'部分成交'
STATUS_ALLTRADED = u'全部成交'
STATUS_CANCELLED = u'已撤销'
STATUS_REJECTED = u'拒单'
STATUS_UNKNOWN = u'未知'

# 合约类型常量
PRODUCT_EQUITY = u'股票'
PRODUCT_FUTURES = u'期货'
PRODUCT_OPTION = u'期权'
PRODUCT_INDEX = u'指数'
PRODUCT_COMBINATION = u'组合'
PRODUCT_FOREX = u'外汇'
PRODUCT_UNKNOWN = u'未知'
PRODUCT_SPOT = u'现货'
PRODUCT_DEFER = u'延期'
PRODUCT_NONE = ''

# 价格类型常量
PRICETYPE_LIMITPRICE = u'限价'
PRICETYPE_MARKETPRICE = u'市价'
PRICETYPE_FAK = u'FAK'
PRICETYPE_FOK = u'FOK'

# 期权类型
OPTION_CALL = u'看涨期权'
OPTION_PUT = u'看跌期权'

# 交易所类型
EXCHANGE_SSE = 'SSE'       # 上交所
EXCHANGE_SZSE = 'SZSE'     # 深交所
EXCHANGE_CFFEX = 'CFFEX'   # 中金所
EXCHANGE_SHFE = 'SHFE'     # 上期所
EXCHANGE_CZCE = 'CZCE'     # 郑商所
EXCHANGE_DCE = 'DCE'       # 大商所
EXCHANGE_SGE = 'SGE'       # 上金所
EXCHANGE_INE = 'INE'       # 国际能源交易中心
EXCHANGE_UNKNOWN = 'UNKNOWN'# 未知交易所
EXCHANGE_NONE = ''          # 空交易所


# 货币类型
CURRENCY_USD = 'USD'            # 美元
CURRENCY_CNY = 'CNY'            # 人民币
CURRENCY_HKD = 'HKD'            # 港币
CURRENCY_UNKNOWN = 'UNKNOWN'    # 未知货币
CURRENCY_NONE = ''              # 空货币

# 接口类型
GATEWAYTYPE_FUTURES = 'futures'                 # 期货、期权、贵金属
GATEWAYTYPE_DATA = 'data'                       # 数据（非交易）

# CTA相关常量定义
# CTA引擎中涉及到的交易方向类型
CTAORDER_BUY = u'买开'
CTAORDER_SELL = u'卖平'
CTAORDER_SHORT = u'卖开'
CTAORDER_COVER = u'买平'

# 本地停止单状态
STOPORDER_WAITING = u'等待中'
STOPORDER_CANCELLED = u'已撤销'
STOPORDER_TRIGGERED = u'已触发'

# 本地停止单前缀
STOPORDERPREFIX = 'CtaStopOrder.'
# 引擎类型，用于区分当前策略的运行环境
ENGINETYPE_BACKTESTING = 'backtesting'  # 回测
ENGINETYPE_TRADING = 'trading'          # 实盘

# CTA模块事件
EVENT_CTA_LOG = 'eCtaLog'               # CTA相关的日志事件
EVENT_CTA_STRATEGY = 'eCtaStrategy.'    # CTA策略状态变化事件

# CTA text
INIT = u'初始化'
START = u'启动'
STOP = u'停止'

CTA_ENGINE_STARTED = u'CTA引擎启动成功'

CTA_STRATEGY = u'CTA策略'
LOAD_STRATEGY = u'加载策略'
INIT_ALL = u'全部初始化'
START_ALL = u'全部启动'
STOP_ALL = u'全部停止'
SAVE_POSITION_DATA = u'保存持仓'

STRATEGY_LOADED = u'策略加载成功'

SAVE_POSITION_QUESTION = u'是否要保存策略持仓数据到数据库？'
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
        self.orderSysID = EMPTY_STRING          #  本地报单编号
        self.price = EMPTY_FLOAT                # 价格
        self.volume = EMPTY_INT                 # 数量
    
        self.priceType = EMPTY_STRING           # 价格类型
        self.direction = EMPTY_STRING           # 买卖
        self.offset = EMPTY_STRING              # 开平
       
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
        self.gatewayName = EMPTY_STRING         # Gateway名称      
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
class CtaTradeData(object):
    """成交数据类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.gatewayName = EMPTY_STRING         # Gateway名称      
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
class CtaContractData(object):
    """合约详细信息类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.gatewayName = EMPTY_STRING         # Gateway名称      
        self.symbol = EMPTY_STRING              # 代码
        self.exchange = EMPTY_STRING            # 交易所代码
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码
        self.name = EMPTY_UNICODE               # 合约中文名
        
        self.productClass = EMPTY_UNICODE       # 合约类型
        self.size = EMPTY_INT                   # 合约大小
        self.priceTick = EMPTY_FLOAT            # 合约最小价格TICK
        
        # 期权相关
        self.strikePrice = EMPTY_FLOAT          # 期权行权价
        self.underlyingSymbol = EMPTY_STRING    # 标的物合约代码
        self.optionType = EMPTY_UNICODE         # 期权类型
########################################################################

class CtaSubscribeReq(object):
    """订阅行情时传入的对象类"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.symbol = EMPTY_STRING              # 代码
        self.exchange = EMPTY_STRING            # 交易所
        
        # 以下为IB相关
        self.productClass = EMPTY_UNICODE       # 合约类型
        self.currency = EMPTY_STRING            # 合约货币
        self.expiry = EMPTY_STRING              # 到期日
        self.strikePrice = EMPTY_FLOAT          # 行权价
        self.optionType = EMPTY_UNICODE         # 期权类型

########################################################################
class StopOrder(object):
    """本地停止单"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.vtSymbol = EMPTY_STRING
        self.orderType = EMPTY_UNICODE
        self.direction = EMPTY_UNICODE
        self.offset = EMPTY_UNICODE
        self.price = EMPTY_FLOAT
        self.volume = EMPTY_INT
        
        self.strategy = None             # 下停止单的策略对象
        self.stopOrderID = EMPTY_STRING  # 停止单的本地编号 
        self.status = EMPTY_STRING       # 停止单状态
