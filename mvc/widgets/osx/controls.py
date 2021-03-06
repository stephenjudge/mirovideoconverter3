import os

from AppKit import *

from .base import Widget

class OptionMenu(Widget):

    def __init__(self, options):
        self.view = NSPopUpButton.alloc().init()
        titles, options = zip(*options)
        self.options = options
        self.view.addItemsWithTitles_(titles)
        super(OptionMenu, self).__init__()

    def calc_size_request(self):
        size = self.view.cell().cellSize()
        return size.width, size.height

    def get_selected(self):
        index = self.view.indexOfSelectedItem()
        return self.options[index]


class MVCButton(NSButton):
    def initWithParent_(self, parent):
        self.parent = parent
        return super(MVCButton, self).init()

    def sendAction_to_(self, action, to):
        self.parent.on_clicked()


class Button(Widget):
    def __init__(self, title):
        self.view = MVCButton.alloc().initWithParent_(self)
        self.view.setButtonType_(NSMomentaryPushInButton)
        self.view.setBezelStyle_(NSRoundedBezelStyle)
        self.view.setTitle_(title)
        super(Button, self).__init__()

    def calc_size_request(self):
        size = self.view.cell().cellSize()
        return max(size.width + 10, 112), size.height

    def on_clicked(self):
        self.emit('clicked')


class FileChooserButton(Button):

    def __init__(self, title):
        super(FileChooserButton, self).__init__(title)
        self.filename = None

    def on_clicked(self):
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseFiles_(YES)
        panel.setCanChooseDirectories_(NO)
        response = panel.runModalForDirectory_file_(os.getcwd(), "")
        if response == NSFileHandlingPanelOKButton:
            self.filename = panel.filename()
        else:
            self.filename = ""

    def get_filename(self):
        return self.filename
