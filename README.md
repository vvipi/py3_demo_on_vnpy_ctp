# py3_demo_on_vnpy_ctp
####　更新：

- 20190603 更新穿透式监管ctpapi

####　特点：

- 基于vnpy的ctp接口的简化版本，实现查询功能的基础上增加了ctaEngine。适用于认为vnpy功能太多无法驾驭，只需要ctp和策略功能的新人（像我这样）。

- python3版本，无数据库，无talib，适合开发不依赖历史数据的日内策略。策略载入历史数据需要自行实现。

- 因为是自用的系统，很多处理是个性化和不完善的，请自行修改。

####　运行环境：

- 64位版本windows7或windows10，python3.7（Anaconda3-2019.03-Windows-x86_64测试可用）

- 项目中的ctpapi是从vnpy开源项目搬运过来的，选择上述运行环境可以不需要自行编译ctpapi。

- linux环境需要自行编译ctpapi，推荐方法如下（测评版linux编译方法作者尚未尝试，以后再更新）：
http://www.wepin.online/blog/0015423531636106a227723e4d74f21b6febcdef77a493f000

####　使用方法：

- 修改user.json中的模拟账号。

- 修改basesetting中的工作目录WORKING_DIR为你的工作目录。

- 启动demoMain.py。




![](https://github.com/vvipi/py3_demo_on_vnpy_ctp/raw/master/screenshots/screenshot20180308.PNG)

