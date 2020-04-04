# coding=utf-8

import wx
import time


class StopwatchMainFrame(wx.Frame):
    """
    主框架
    """
    def __init__(self, *args, **kw):
        super(StopwatchMainFrame, self).__init__(*args, **kw)

        # 初始化变量
        self.timeDifference = 0     # 时间差
        self.timeTemp = 0   # 计时缓存
        self.startTime = 0  # 启动时间
        self.min = 0    # 分
        self.sec = 0    # 秒
        self.ms = 0     # 毫秒

        # 初始化标志符
        self.startTag = 1   # 1 => 停止状态  |  0 => 开始状态

        # 初始化主面板
        mainPanel = wx.Panel(self)

        # 初始化计时器
        self.timer = wx.Timer(self)

        # 主面板开启双缓冲  （解决StaticText控件刷新频率过高导致的闪烁）
        mainPanel.SetDoubleBuffered(True)

        # 时间显示面板样式设定
        timeStr = "{:02d}:{:02d}.{:02d}".format(self.min, self.sec, self.ms)
        self.timeText = wx.StaticText(mainPanel, label=timeStr)

        self.timeText.SetSize((388, 75))
        self.timeText.SetForegroundColour('#000000')
        self.timeText.SetPosition((166, 65))

        fontTemp = self.timeText.GetFont()
        fontTemp.PointSize += 63
        fontTemp.SetWeight(wx.FONTWEIGHT_LIGHT)
        self.timeText.SetFont(fontTemp)

        # 计次/复位按钮样式设定
        self.timesCountButton = wx.Button(mainPanel, label='复位', style=wx.BORDER_NONE)
        self.timesCountButton.SetPosition((30, 183))
        self.timesCountButton.SetSize(73, 73)
        self.timesCountButton.SetBackgroundColour('#333333')
        self.timesCountButton.SetForegroundColour('#ffffff')

        # 开始/停止按钮样式设定
        self.startButton = wx.Button(mainPanel, label='启动', style=wx.BORDER_NONE)
        self.startButton.SetPosition((597, 183))
        self.startButton.SetSize(73, 73)
        self.startButton.SetBackgroundColour('#0a2a12')
        self.startButton.SetForegroundColour('#30d158')

        # 事件绑定
        self.Bind(wx.EVT_BUTTON, self.Onstart, self.startButton)
        self.Bind(wx.EVT_BUTTON, self.OnTimesCount, self.timesCountButton)
        self.Bind(wx.EVT_TIMER, self.updateTime, self.timer)

    def Onstart(self, event):
        """
        开始、停止按钮事件
        """
        if self.startTag:       # 停止状态时点击 => 开始计时
            # 样式变更
            self.startButton.SetLabel('停止')
            self.timesCountButton.SetLabel('计次')
            self.startButton.SetBackgroundColour('#330e0c')
            self.startButton.SetForegroundColour('#ff453a')

            # 标志符变更
            self.startTag = 0

            # 计时事件响应
            self.startTime = int(time.time() * 100)     # 获取开始时间
            self.timer.Start(10)    # 开始计时器循环，循环间隔为10ms

        else:                   # 开始状态时点击 => 停止计时
            # 样式变更
            self.startButton.SetLabel('启动')
            self.timesCountButton.SetLabel('复位')
            self.startButton.SetBackgroundColour('#0a2a12')
            self.startButton.SetForegroundColour('#30d158')

            # 标志符变更
            self.startTag = 1

            # 计时事件响应
            self.timer.Stop()       # 关闭计时器循环
            self.timeTemp = self.timeDifference     # 存储已记录时间数据

            # print self.timeTemp   # 显示缓存数据（调试用

    def OnTimesCount(self, event):
        """
        计次、复位按钮事件
        """
        if self.startTag:       # 停止状态时点击 => 复位功能
            # 初始化时间数据
            self.min = 0
            self.sec = 0
            self.ms = 0
            # 清空缓存区
            self.timeTemp = 0
            # 初始化时间显示
            self.timeText.SetLabel("{:02d}:{:02d}.{:02d}".format(self.min, self.sec, self.ms))

        else:                   # 开始状态时点击 => 计次功能（暂未实现
            pass

    def updateTime(self, event):
        """
        计时更新
        """
        # 获取本次循环时时间戳
        localtime = int(time.time() * 100)

        # 计算时间差 ： 当前时间 - 开始时间 + 缓存区时间（第一次开始时缓存区为0）
        self.timeDifference = localtime - self.startTime + self.timeTemp

        # 分、秒、毫秒换算
        self.min = self.timeDifference / 6000
        self.sec = (self.timeDifference - (self.min * 6000)) / 100
        self.ms = self.timeDifference % 100

        # 更新显示
        self.timeText.SetLabel("{:02d}:{:02d}.{:02d}".format(self.min, self.sec, self.ms))


if __name__ == '__main__':
    swApp = wx.App()
    swFrame = StopwatchMainFrame(None, title='Sw', size=(720, 455))
    swFrame.Show()
    swApp.MainLoop()
