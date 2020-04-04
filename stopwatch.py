# coding=utf-8

# 引入相关包
import wx
import time
import sqlite3
import re
import string


class DBOperation:
    """
    数据库交互类
    """
    def __init__(self, databaseName):
        try:
            # 开启链接
            self.conn = sqlite3.connect(databaseName)
            # 建立cursor
            self.cursor = self.conn.cursor()
            print '数据库连接成功'
        except:
            print '数据库连接失败'

    def createTable(self, recTime):
        """
        建立记录表
        :param recTime:     记录表对应时间
        :return: 表名 | 失败返回0
        """
        # 拼接sql
        sql = 'create table sw_' + str(recTime)\
              + ' (number int primary key, single varchar(20), accumulated varchar(20))'

        # print sql     # 调试用
        try:
            self.cursor.execute(sql)
            return 'sw_' + str(recTime)
        except:
            return 0

    def insertData(self, tableName, swData):
        """
        向记录表插入数据
        :param tableName:   记录表名
        :param swData:      数据字典
        :return:    成功返回表名 | 失败返回0
        """
        # sql拼接
        sql = "insert into " + tableName + " values"

        for data in swData.values():
            print data
            dataStr = "(" + str(data[0]) + ",\"" + str(data[1]) + "\",\"" + str(data[2]) + "\"),"
            sql += dataStr
        sql = sql[0:-1]

        # print sql   # 调试用
        # 执行
        try:
            self.cursor.execute(sql)
            self.conn.commit()
            return tableName
        except:
            print '保存失败'
            return 0

    def showTable(self):
        """
        显示所有表的时间格式
        :return:    成功返回时间列表 | 失败返回0
        """
        # 初始化存储列表
        timeList = []

        # sql拼接
        sql = 'select name from sqlite_master where type=\'table\' order by name;'

        try:
            # 执行、存储查询结果
            self.cursor.execute(sql)
            tableList = self.cursor.fetchall()

            # print tableList     # 调试用
            # 处理表名
            for tbTime in tableList:
                tbTime = tbTime[0]
                timeList.append(tbTime[3:7] + '.' + tbTime[7:9] + '.' + tbTime[9:11] + ' ' + \
                                tbTime[11:13] + ':' + tbTime[13:15] + '.' + tbTime[15:17])
            # 返回列表
            return timeList
        except:
            return 0

    def showData(self, tableName):
        """
        查询记录表数据
        :param tableName:   目标表名
        :return:    成功返回数据列表 | 失败返回0
        """
        # sql拼接
        sql = 'select * from ' + tableName
        try:
            self.cursor.execute(sql)
            data = self.cursor.fetchall()
            # print data      # 调试用
            return data
        except:
            return 0


class SwButton(wx.Button):
    """
    按钮类
    """
    def __init__(self, *args, **kw):
        super(SwButton, self).__init__(*args, **kw)

    def styleInit(self, pos=None, size=None, label=None, bgcolor=None, fgcolor=None):
        """
        按钮样式设置
        :param pos:     位置
        :param size:    大小
        :param label:   标签
        :param bgcolor:     背景色
        :param fgcolor:     前景色
        :return:
        """
        if pos:
            self.SetPosition(pos)
        if size:
            self.SetSize(size[0], size[1])
        if label:
            self.SetLabel(label)
        if bgcolor:
            self.SetBackgroundColour(bgcolor)
        if fgcolor:
            self.SetForegroundColour(fgcolor)


class StopwatchMainFrame(wx.Frame):
    """
    主框架
    """
    def __init__(self, *args, **kw):
        super(StopwatchMainFrame, self).__init__(*args, **kw)

        # 数据库名称
        self.dbName = 'Stopwatch.db'

        # 初始化标志符
        self.startTag = 1   # 1 => 停止状态  |  0 => 开始状态
        self.selectTag = 1  # 1 => 列表未展开  |  0 => 列表已展开
        self.loadingTag = 1 # 1 => 记录未读取  |  0 => 记录读取中

        # 初始化变量
        self.timeDifference = 0  # 时间差
        self.timeTemp = 0  # 计时缓存
        self.startTime = 0  # 启动时间
        self.timeRecord = 0  # 时间计次数据
        self.recordNum = 0  # 时间计次次数
        self.timeAdd = 0    # 分次时间总时长

        self.min = 0  # 分
        self.sec = 0  # 秒
        self.ms = 0  # 毫秒

        self.dbStartTime = 0    # 数据库时间记录
        self.dataDict = {}      # 数据字典初始化

        self._frameInit()   # 主框架预设

        # 初始化主面板
        self.mainPanel = wx.Panel(self)
        self._panelInit()   # 主面板预设

        # 初始化计时器
        self.timer = wx.Timer(self)

        # 初始化时间显示面板
        timeStr = "{:02d}:{:02d}.{:02d}".format(self.min, self.sec, self.ms)
        self.timeText = wx.StaticText(self.mainPanel, label=timeStr)
        self._timeTextInit()    # 时间显示面板预设

        # 计次显示面板样式设定
        self.timeList = wx.TextCtrl(self.mainPanel, -1, style=wx.TE_READONLY | wx.TE_MULTILINE | wx.NO_BORDER | wx.TE_CENTER)
        self._timeListInit()    # 计次显示面板预设

        # 读取选择面板
        self.selectList = wx.ListBox(self.mainPanel)
        self._selectListInit()      # 读取选择面板预设

        # 计次/复位按钮预设
        self.timesCountButton = SwButton(self.mainPanel, style=wx.BORDER_NONE)
        self.timesCountButton.styleInit((30, 183), (73, 73), '复位', '#333333', '#ffffff')

        # 开始/停止按钮预设
        self.startButton = SwButton(self.mainPanel, style=wx.BORDER_NONE)
        self.startButton.styleInit((597, 183), (73, 73), '启动', '#0a2a12', '#30d158')

        # 保存按钮预设
        self.saveButton = SwButton(self.mainPanel, style=wx.BORDER_NONE)
        self.saveButton.styleInit((597, 260), (73, 36), '保存', '#333333', '#ffffff')

        # 读取按钮预设
        self.loadButton = SwButton(self.mainPanel, style=wx.BORDER_NONE)
        self.loadButton.styleInit((30, 260), (73, 36), '加载', '#333333', '#ffffff')

        # 事件绑定
        self._bindInit()

    def _dataInit(self):
        # 初始化变量
        self.timeDifference = 0     # 时间差
        self.timeTemp = 0   # 计时缓存
        self.startTime = 0  # 启动时间
        self.timeRecord = 0     # 时间计次数据
        self.recordNum = 0      # 时间计次次数
        self.timeAdd = 0    # 分次时间总时长

        self.min = 0    # 分
        self.sec = 0    # 秒
        self.ms = 0     # 毫秒

        self.dataDict.clear()   # 字典重置
        self.dbStartTime = 0    # 数据库时间记

    def _frameInit(self):
        # 初始化框架样式
        self.SetMaxSize((720, 455))
        self.SetMinSize((720, 455))
        self.SetBackgroundColour('#000000')

    def _panelInit(self):
        # 主面板开启双缓冲  （解决StaticText控件刷新频率过高导致的闪烁）
        self.mainPanel.SetDoubleBuffered(True)

    def _timeTextInit(self):
        # 初始化时间显示面板样式
        self.timeText.SetSize((388, 75))
        self.timeText.SetForegroundColour('#ffffff')
        self.timeText.SetPosition((160, 65))

        fontTemp = self.timeText.GetFont()
        fontTemp.PointSize += 63
        fontTemp.SetWeight(wx.FONTWEIGHT_LIGHT)
        self.timeText.SetFont(fontTemp)

    def _timeListInit(self):
        # 初始化计次显示面板样式
        self.timeList.SetPosition((152, 190))
        self.timeList.SetSize(400, 200)
        self.timeList.SetBackgroundColour("#000000")
        self.timeList.SetForegroundColour("#ffffff")
        self.timeList.SetScrollbar(wx.VERTICAL, 0, 50, 50)

        fontTemp = self.timeList.GetFont()
        fontTemp.PointSize += 5
        fontTemp.SetWeight(wx.FONTWEIGHT_LIGHT)
        self.timeList.SetFont(fontTemp)

    def _selectListInit(self):
        # 初始化记录选择面板样式
        self.selectList.SetPosition((152, 190))
        self.selectList.SetSize(0, 0)
        self.timeList.SetBackgroundColour("#000000")
        self.timeList.SetForegroundColour("#ffffff")

    def _bindInit(self):
        # 按钮事件绑定
        self.Bind(wx.EVT_BUTTON, self.OnStart, self.startButton)
        self.Bind(wx.EVT_BUTTON, self.OnTimesCount, self.timesCountButton)
        self.Bind(wx.EVT_BUTTON, self.OnSave, self.saveButton)
        self.Bind(wx.EVT_BUTTON, self.OnLoad, self.loadButton)
        # 定时器事件绑定
        self.Bind(wx.EVT_TIMER, self.updateTime, self.timer)
        # 记录列表交互事件绑定
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.updateRecord, self.selectList)

    def _displayInit(self):
        # 初始化计次面板
        self.timeList.Clear()
        # 初始化时间显示
        self.timeText.SetLabel("{:02d}:{:02d}.{:02d}".format(self.min, self.sec, self.ms))

    def _timeOperation(self, timeStamp, strOut=False):
        """
        时间戳操作
        :param timeStamp:   目标时间戳
        :param strOut:      是否输出格式化字符串（默认False）
        :return:    格式化字符串 | 无
        """
        if strOut:
            minTemp = timeStamp / 6000
            secTemp = (timeStamp - (self.min * 6000)) / 100
            msTemp = timeStamp % 100

            return "{:02d}:{:02d}.{:02d}".format(minTemp, secTemp, msTemp)
        else:
            # 分、秒、毫秒换算
            self.min = timeStamp / 6000
            self.sec = (timeStamp - (self.min * 6000)) / 100
            self.ms = timeStamp % 100

    def OnStart(self, event):
        """
        开始、停止按钮事件
        """
        if self.startTag:       # 停止状态时点击 => 开始计时
            # 样式变更
            self.startButton.styleInit(label='停止', bgcolor='#330e0c', fgcolor='#ff453a')
            self.timesCountButton.styleInit(label='计次')

            # 标志符变更
            self.startTag = 0

            # 开始计时
            self.TimingStart()
        else:                   # 开始状态时点击 => 停止计时
            # 样式变更
            self.startButton.styleInit(label='启动', bgcolor='#0a2a12', fgcolor='#30d158')
            self.timesCountButton.styleInit(label='复位')

            # 标志符变更
            self.startTag = 1

            # 暂停计时
            self.TimingPause()

    def OnTimesCount(self, event):
        """
        计次、复位按钮事件
        """
        if self.startTag:       # 停止状态时点击 => 复位功能
            # 数据初始化
            self._dataInit()
            # 显示初始化
            self._displayInit()

        else:                   # 开始状态时点击 => 计次功能
            # 计次计数
            self.recordNum += 1

            # 分次时间计算
            self.timeRecord = self.timeDifference - self.timeAdd
            self.timeAdd += self.timeRecord

            # 写入字典
            self.dataDict[self.recordNum - 1] = {0: self.recordNum,
                                                 1: self._timeOperation(self.timeRecord, strOut=True),
                                                 2: self._timeOperation(self.timeDifference, strOut=True)}

            # 显示计次
            self.AddTimeDisplay(self.recordNum, self._timeOperation(self.timeRecord, strOut=True),
                                self._timeOperation(self.timeDifference, strOut=True))

    def OnSave(self, event):
        """
        保存按钮事件
        """
        # 当计时开始时间存在且计时停止时
        if self.dbStartTime != 0 and self.startTag:
            # 实例化数据库操作类
            dbConn = DBOperation(self.dbName)
            # 开始时间时间戳格式化
            timeArray = time.localtime(self.dbStartTime)
            tbName = time.strftime("%Y%m%d%H%M%S", timeArray)
            # 创建记录表
            tbName = dbConn.createTable(tbName)
            # 插入数据
            dbConn.insertData(tbName, self.dataDict)
            # 添加交互信息
            self.timeList.AppendText(time.strftime("%Y-%m-%d %H:%M:%S", timeArray) + '数据 保存成功')
            # 关闭链接
            dbConn.conn.close()

    def OnLoad(self, event):
        """
        读取按钮事件
        """
        # 选择面板已关闭且计时终止时
        if self.selectTag and self.startTag:
            # 清空选择列表
            self.selectList.Clear()
            # 开启数据库链接
            dbConn = DBOperation(self.dbName)
            # 加载记录表列表
            List = dbConn.showTable()
            for value in List:
                self.selectList.Append(value)
            # 关闭链接
            dbConn.conn.close()

            # 面板展开
            self.selectList.SetSize(400, 200)
            self.timeList.SetSize(0, 0)

            # 标志符切换
            self.selectTag = 0
            self.loadingTag = 0
        else:
            # 面板关闭
            self.selectList.SetSize(0, 0)
            self.timeList.SetSize(400, 200)

            # 标志符切换
            self.selectTag = 1

    def updateTime(self, event):
        """
        计时更新
        """
        # 获取本次循环时时间戳
        localtime = int(time.time() * 100)

        # print localtime     # 调试用

        # 计算时间差 ： 当前时间 - 开始时间 + 缓存区时间（第一次开始时缓存区为0）
        self.timeDifference = localtime - self.startTime + self.timeTemp

        self._timeOperation(self.timeDifference)

        # 更新显示
        self.timeText.SetLabel("{:02d}:{:02d}.{:02d}".format(self.min, self.sec, self.ms))

    def updateRecord(self, event):
        """
        双击列表项读取记录
        :param event:
        :return:
        """
        # 获取选项数据并格式化
        tbName = re.sub(r"[,:.*'!\n-]", "", event.GetString())
        tbName = 'sw_' + string.replace(tbName, ' ', '')

        # print tbName    # 调试用

        # 链接数据库
        dbConn = DBOperation(self.dbName)
        # 加载查询数据
        recList = dbConn.showData(tbName)
        # 清空显示区
        self.timeList.Clear()
        # 遍历加载显示
        for data in recList:
            self.AddTimeDisplay(data[0], data[1], data[2])

        # 切换显示面板
        self.selectList.SetSize(0, 0)
        self.timeList.SetSize(400, 200)
        self.selectTag = 1

    def TimingStart(self):
        # 是否已有计时任务或是否正在读取记录
        if not self.timeTemp or not self.loadingTag:
            # 数据、显示初始化
            self._dataInit()
            self._displayInit()

        self.startTime = int(time.time() * 100)  # 获取开始时间
        self.dbStartTime = int(time.time())  # 数据库记录开始时间
        self.timer.Start(10)  # 开始计时器循环，循环间隔为10ms

    def TimingPause(self):
        # 计时事件响应
        self.timer.Stop()  # 关闭计时器循环
        self.timeTemp = self.timeDifference  # 存储已记录时间数据

        # print self.timeTemp   # 显示缓存数据（调试用

    def AddTimeDisplay(self, number, single, accumulated):
        """
        计次面板显示
        :param number:  次数
        :param single:  单次记录
        :param accumulated:     累计记录
        :return:
        """
        self.timeList.AppendText('计次' + str(number) +
                                 '   分段：' + str(single) +
                                 '  累计：' + str(accumulated) + "\n")


class StopwatchApp(wx.App):
    """
    应用程序类
    """
    def __init__(self):
        super(StopwatchApp, self).__init__()


if __name__ == '__main__':
    # 实例化应用程序
    swApp = StopwatchApp()
    # 实例化主窗口
    swFrame = StopwatchMainFrame(None, title='Sw', size=(720, 455))
    # 显示主窗口
    swFrame.Show()
    # 进入主循环
    swApp.MainLoop()