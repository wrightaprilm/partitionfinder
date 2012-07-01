#
# Many ideas are taken from here:
# http://wiki.wxpython.org/Optimizing%20for%20Mac%20OS%20X
#
# TODO
# * Set a flag for breaking out of the analysis cleanly (make it part of the
# progress monitor?)
# * Sort out the logging later
# * Editing, on another tab
# * Use the dv.PyDataViewIndexListModel Example for the logger

import logging
import thread
import os
log = logging.getLogger("gui")

import wx
from wx.lib import newevent, sized_controls, rcsizer
# We'll create a new event type to post messages across threads
(LogEvent, EVT_LOG_EVENT) = newevent.NewEvent()

from partfinder import config, analysis_method, reporter

class Handler(logging.Handler):
    def __init__(self, win, *args, **kwargs):
        logging.Handler.__init__(self, *args, **kwargs)
        self.win = win

    def emit(self, record):
        evt = LogEvent(record=record)
        wx.PostEvent(self.win, evt)

htmlformatter = logging.Formatter(
    '''
    <font size=3>
        <!-- <font color='red'>%(asctime)s</font> -->
        <!-- <b><font color='blue'>%(levelname)s: %(name)s</font></b> -->
        <!-- # %(filename)s, %(lineno)s: %(message)s -->
        %(message)s
    </font>
    ''')

class LogHtmlListBox(wx.HtmlListBox):
    def __init__(self, parent, **kwargs):
        wx.HtmlListBox.__init__(self, parent, style=wx.SUNKEN_BORDER, **kwargs)
        self.records = []
        self.SetItemCount(0)
    
    def Update(self, evt):
        self.records.append(evt)
        self.SetItemCount(len(self.records))
        self.ScrollToLine(self.GetRowCount())
        self.Refresh()

    def OnGetItem(self, n):
        rec = self.records[n]
        return htmlformatter.format(rec)

    def OnDrawSeparator(self, dc, rect, n):
        # Place some simple separation between each of the items.
        dc.SetBrush(wx.NullBrush)
        dc.SetPen(wx.LIGHT_GREY_PEN)
        dc.DrawLine(rect.left, rect.bottom, rect.right, rect.bottom)

class MainPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        sizer = rcsizer.RowColSizer()

        text = "This sizer lays out it's items by row and column "\
               "that are specified explicitly when the item is \n"\
               "added to the sizer.  Grid cells with nothing in "\
               "them are supported and column- or row-spanning is \n"\
               "handled as well.  Growable rows and columns are "\
               "specified just like the wxFlexGridSizer."

        # sizer.Add(wx.StaticText(self, -1, text), row=0, col=0, colspan=3)

        sizer.Add(wx.TextCtrl(self, -1, "(3,1)"), flag=wx.EXPAND|wx.ALL,
                  row=0, col=0, border=4)
        sizer.Add(wx.TextCtrl(self, -1, "(3,2)"), flag=wx.EXPAND|wx.ALL, row=1,
                  col=0, border=4)
        sizer.Add(wx.TextCtrl(self, -1, "(3,2)"), flag=wx.EXPAND|wx.ALL, row=1,
                  col=1, border=4)
        # sizer.Add(wx.TextCtrl(self, -1, "(3,3)"), row=3, col=3)
        self.html_log = LogHtmlListBox(self, size=(200, 100))
        sizer.Add(self.html_log, flag=wx.EXPAND|wx.ALL, row=2, col=0, colspan=3,
                  border=4)
        sizer.AddGrowableCol(1)
        sizer.AddGrowableRow(2)
        # sizer.AddGrowableCol(1)
        # sizer.AddGrowableCol(2)

        # sizer.AddSpacer(5,5, col=0, row=3, colspan=3)
        # sizer.AddSpacer(5,5, col=0, row=1, colspan=3)
        # sizer.AddSpacer(10,10, pos=(13,1))

        self.SetAutoLayout(True)
        self.SetSizerAndFit(sizer)
        self.Layout()
        # self.SetMinSize(self.GetSize())

class MainFrame(wx.Frame):
    def __init__(self, title = "Partition Finder"):
        wx.Frame.__init__(self, None , -1, title)

        self.pane = MainPanel(self)
        # pane = self.GetContentsPane()
        # pane.SetSizerType("form")
        #
        self.CreateMenu()


    def Old(self):
        
        # row 1
        wx.StaticText(pane, -1, "")
        button = wx.Button(pane, -1, "Choose a configuration file", (50,50))
        button.SetSizerProps(expand=True)
        self.Bind(wx.EVT_BUTTON, self.OnLoadConfig, button)

        # row 2
        wx.StaticText(pane, -1, "Base Folder")
        self.base_folder = wx.TextCtrl(pane, -1, "xx", style=wx.TE_READONLY)
        self.base_folder.SetSizerProps(expand=True)
        
        # row 3
        wx.StaticText(pane, -1, "Go")
        self.go = wx.Button(pane, -1)
        self.Bind(wx.EVT_BUTTON, self.OnGo, self.go)
        
        self.html_log = LogHtmlListBox(pane, size=(600, 200))
        self.html_log.SetSizerProps(expand=True, proportion=1)
        # self.ConfigureListCtrl()
        
        self.CreateMenu()
        # self.CreateStatusBar()
        self.Fit()
        self.SetMinSize(self.GetSize())

        self.Bind(EVT_LOG_EVENT, self.OnLog)

        self.cfg = config.Configuration()
        # subscribe('button.press', self.GetPath)
        self.running = None

    def ShowConfig(self):
        self.base_folder.SetText(self.cfg.base_folder)


    def OnLog(self, evt):
        # Send the log message to the List Control
        self.html_log.Update(evt.record)
    # def __str__(self):
        # return '<LogRecord: %s, %s, %s, %s, "%s">'%(self.name, self.levelno,
            # self.pathname, self.lineno, self.msg)

    def OnGo(self, evt):
        self.thread = PFThread(self.cfg)
        self.thread.Start()

    def OnLoadConfig(self, evt):
        # In this case we include a "New directory" button. 

        dlg = wx.FileDialog(
            self, message="Choose a configuration file",
            defaultDir=os.getcwd(), 
            defaultFile="",
            wildcard="Configuration File (*.cfg)|*.cfg",
            style=wx.OPEN | wx.CHANGE_DIR
            )
        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it. 
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            try:
                self.cfg.load_base_path(path)
                self.ShowConfig()
                self.state = LOADED
            except:
                pass

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()

    def CreateMenu(self):

        MenuBar = wx.MenuBar()
        FileMenu = wx.Menu()
        item = FileMenu.Append(wx.ID_EXIT, text = "&Exit")
        self.Bind(wx.EVT_MENU, self.OnQuit, item)
        item = FileMenu.Append(wx.ID_ANY, text = "&Open")
        self.Bind(wx.EVT_MENU, self.OnOpen, item)
        item = FileMenu.Append(wx.ID_PREFERENCES, text = "&Preferences")
        self.Bind(wx.EVT_MENU, self.OnPrefs, item)
        MenuBar.Append(FileMenu, "&File")
        
        HelpMenu = wx.Menu()
        item = HelpMenu.Append(wx.ID_HELP, "Test &Help",
                                "Help for this simple test")
        self.Bind(wx.EVT_MENU, self.OnHelp, item)
        ## this gets put in the App menu on OS-X
        item = HelpMenu.Append(wx.ID_ABOUT, "&About",
                                "More information About this program")
        self.Bind(wx.EVT_MENU, self.OnAbout, item)
        MenuBar.Append(HelpMenu, "&Help")

        self.SetMenuBar(MenuBar)

    # def OnPressed(self, evt):
        # if self.running is None:
            # self.running = PFThread()
            # self.running.Start()

    def OnQuit(self,Event):
        self.Destroy()
        
    def OnAbout(self, event):
        dlg = wx.MessageDialog(self, "This is a small program to test\n"
                                     "the use of menus on Mac, etc.\n",
                                "About Me", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnHelp(self, event):
        dlg = wx.MessageDialog(self, "This would be help\n"
                                     "If there was any\n",
                                "Test Help", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnOpen(self, event):
        dlg = wx.MessageDialog(self, "This would be an open Dialog\n"
                                     "If there was anything to open\n",
                                "Open File", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnPrefs(self, event):
        dlg = wx.MessageDialog(self, "This would be an preferences Dialog\n"
                                     "If there were any preferences to set.\n",
                                "Preferences", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        
class App(wx.App):
    def __init__(self, *args, **kwargs):
        wx.App.__init__(self, *args, **kwargs)
        # This catches events when the app is asked to activate by some other
        # process
        self.Bind(wx.EVT_ACTIVATE_APP, self.OnActivate)

    def OnInit(self):
        # Make the Frame
        #
        self.frame = MainFrame()
        self.frame.Show()

        # Set up the GUI Logging
        logging.getLogger("").addHandler(Handler(self.frame))
        logging.getLogger("").setLevel(logging.INFO)

        return True

    def BringWindowToFront(self):
        try: # it's possible for this event to come when the frame is closed
            self.GetTopWindow().Raise()
        except:
            pass
        
    def OnActivate(self, event):
        # if this is an activate event, rather than something else, like iconize.
        if event.GetActive():
            self.BringWindowToFront()
        event.Skip()
    
    def OpenFileMessage(self, filename):
        dlg = wx.MessageDialog(None,
                               "This app was just asked to open:\n%s\n"%filename,
                               "File Dropped",
                               wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    # def MacOpenFile(self, filename):
        # """Called for files droped on dock icon, or opened via finders context menu"""
        # print filename
        # print "%s dropped on app"%(filename) #code to load filename goes here.
        # self.OpenFileMessage(filename)
        
    def MacReopenApp(self):
        """Called when the doc icon is clicked, and ???"""
        self.BringWindowToFront()

    def MacNewFile(self):
        pass
    
    def MacPrintFile(self, file_path):
        pass


class PFThread(object):
    def __init__(self, cfg):
        self.cfg = cfg

    def Start(self):
        self.keepGoing = self.running = True
        thread.start_new_thread(self.Run, ())

    def Stop(self):
        self.keepGoing = False

    def IsRunning(self):
        return self.running

    def Run(self):
        # logging.getLogger("").addHandler(gui_logging.gui_handler) # add at base level
        # logging.getLogger("").setLevel(logging.INFO)
        method = analysis_method.choose_method(self.cfg.search)
        rpt = reporter.TextReporter(self.cfg)
        anal = method(self.cfg, rpt, False, False)
        anal.analyse()
 
app = App(False)
app.MainLoop()
