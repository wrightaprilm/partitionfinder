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
(FinishedEvent, EVT_FINISHED_EVENT) = newevent.NewEvent()

from partfinder import config, analysis_method, reporter

EMPTY_STATE, LOADED_STATE, RUNNING_STATE, FINISHED_STATE = range(4)

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

class MainFrame(wx.Frame):
    def __init__(self, title = "Partition Finder"):
        wx.Frame.__init__(self, None , -1, title)

        layout = self.BuildLayout()

        self.CreateMenu()
        self.CreateStatusBar()

        self.SetAutoLayout(True)
        self.SetSizerAndFit(layout)

        self.cfg = config.Configuration()
        self.SetState(EMPTY_STATE)

        self.Bind(EVT_LOG_EVENT, self.OnLog)
        self.Bind(EVT_FINISHED_EVENT, self.OnFinished)

    def SetState(self, st):
        self.state = st
        if st == EMPTY_STATE:
            self.load_button.Enable(True)
            self.go_button.Enable(False)
        elif st == LOADED_STATE:
            self.go_button.Enable(True)
            self.base_path.SetLabel(self.cfg.config_path)
            # Load up some shit
        elif st == RUNNING_STATE:
            self.load_button.Enable(False)
            self.go_button.Enable(False)

        elif st == FINISHED_STATE:
            self.load_button.Enable(False)
            self.go_button.Enable(False)

    def BuildLayout(self):

        loader = wx.BoxSizer(wx.HORIZONTAL)
        self.base_path = wx.StaticText(self, -1, "<Nothing Selected>")
        self.base_path.SetForegroundColour((255,0,0))
        self.load_button = wx.Button(self, -1, "...", (50,10))
        self.Bind(wx.EVT_BUTTON, self.OnLoadConfig, self.load_button)
        loader.Add(wx.StaticText(self, -1, "Configuration File:"), 0, flag=wx.EXPAND)
        loader.Add(self.base_path, 1, flag=wx.EXPAND)
        loader.Add(self.load_button, 0, flag=wx.EXPAND)

        logging = wx.BoxSizer(wx.VERTICAL)
        # logging.Add(inner, 1, flag=wx.ALL|wx.EXPAND, border=4)
        self.html_log = LogHtmlListBox(self, size=(600, 100))
        self.html_log.SetMinSize((600, 200))
        # logging.Add(wx.StaticText(self, -1, "Logging"), 0, flag=wx.EXPAND|wx.ALL)
        logging.Add(self.html_log, 1, flag=wx.EXPAND|wx.ALL, border=4)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.go_button = wx.Button(self, -1, "Begin", (60,10))
        self.Bind(wx.EVT_BUTTON, self.OnGo, self.go_button)
        buttons.Add(self.go_button, 0, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=4)

        # Stick it all in a border
        border = wx.BoxSizer(wx.VERTICAL)
        border.Add(loader, 0, flag=wx.ALL|wx.EXPAND, border=6)
        border.Add(logging, 1, flag=wx.ALL|wx.EXPAND, border=6)
        border.Add(buttons, 0, flag=wx.ALL|wx.EXPAND, border=6)

        return border

    def ShowConfig(self):
        self.base_folder.SetText(self.cfg.base_folder)

    def OnLog(self, evt):
        # Send the log message to the List Control
        self.html_log.Update(evt.record)

    def OnFinished(self, evt):
        self.SetState(FINISHED_STATE)

    def OnGo(self, evt):
        self.thread = PFThread(self, self.cfg)
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
            self.cfg.load_base_path(path)
            self.SetState(LOADED_STATE)

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
    def __init__(self, win, cfg):
        self.win = win
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
        self.win.PostEvent(FinishedEvent())

        
app = App(False)
app.MainLoop()
