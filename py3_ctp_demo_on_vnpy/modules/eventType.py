# encoding: UTF-8

'''
本文件仅用于存放对于事件类型常量的定义。
由于python中不存在真正的常量概念，因此选择使用全大写的变量名来代替常量。
这里设计的命名规则以EVENT_前缀开头。
常量的内容通常选择一个能够代表真实意义的字符串（便于理解）。
建议将所有的常量定义放在该文件中，便于检查是否存在重复的现象。
'''


EVENT_TIMER = 'eTimer'                  # 计时器事件，每隔1秒发送一次
EVENT_LOG = 'eLog'                        # 日志事件
EVENT_MARKETDATA_CONTRACT = 'eMarketdataContract'   # TICK行情事件
EVENT_INSTRUMENT = 'eInstrument'        # 合约事件
EVENT_MARKETDATA = 'eMarketData'        # 常规行情事件
EVENT_CONTRACT = 'eContract'            # 合约信息
EVENT_ACCOUNT = 'eAccount'              # 账户事件
EVENT_POSITION = 'ePosition'            # 常规持仓事件
EVENT_VNPOSITION = 'eVnPosition'        # vn格式的持仓事件
EVENT_ORDER = 'eOrder'                  # 常规报单事件
EVENT_VNORDER = 'eVnOrder'              # vn格式的报单事件
EVENT_TRADE ='eTrade'                   # 常规成交事件
EVENT_VNTRADE = 'eVnTrade'              # vn格式的成交事件
EVENT_PRODUCT = 'eProduct'              # 主力合约事件
EVENT_TICK = 'eTick'                    # tick行情事件
EVENT_TURTLE = 'eTurtle'            # 土鳖策略事件
EVENT_GRAPH = 'eGraph'              # 绘图事件
EVENT_PLOT = 'ePlot'                # 新版绘图事件
EVENT_GRAPHSHOW = 'eGraphshow'      # 显示图形监控界面事件
EVENT_ALARM = 'eAlarm'              # 警报事件
EVENT_ALARMSEND = 'eAlarmSend'      # 警报已发送事件
EVENT_ALIVE = 'eAlive'              # 存活确认事件 
EVENT_STATUS = 'eStatus'            # 观察者的状态事件
EVENT_CTA_ROBOT = 'eCtaRobot'       # 策略自动启动事件
    

# 直接运行脚本可以进行测试
if __name__ == '__main__':
    #----------------------------------------------------------------------
    def test():
        """检查是否存在内容重复的常量定义"""
        check_dict = {}
        
        global_dict = globals()    
        
        for key, value in global_dict.items():
            if '__' not in key:                       # 不检查python内置对象
                if value in check_dict:
                    check_dict[value].append(key)
                else:
                    check_dict[value] = [key]
                
        for key, value in check_dict.items():
            if len(value)>1:
                print(u'存在重复的常量定义:' + str(key) )
                for name in value:
                    print(name)
                print('')
            
        print(u'测试完毕')
    test()