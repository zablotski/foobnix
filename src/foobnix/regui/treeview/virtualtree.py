'''
Created on Sep 29, 2010

@author: ivan
'''
from foobnix.regui.state import LoadSave
from foobnix.regui.treeview import TreeViewControl
from foobnix.util.mouse_utils import is_double_left_click, is_rigth_click
import gtk
from foobnix.helpers.menu import Popup
from foobnix.helpers.dialog_entry import one_line_dialog
from foobnix.regui.model import FModel
class VirtualTreeControl(TreeViewControl, LoadSave):
    def __init__(self, controls):
        TreeViewControl.__init__(self, controls)
        
        """column config"""
        column = gtk.TreeViewColumn("Virtual Lybrary", gtk.CellRendererText(), text=self.text[0], font=self.font[0])
        column.set_resizable(True)
        self.append_column(column)
        
    def on_button_press(self, w, e):
        if is_double_left_click(e):
            bean = self.get_selected_bean()
            self.controls.append_to_notebook(bean.text, [bean])
            print "double left"
        if is_rigth_click(e):            
                menu = Popup()
                menu.add_item(_("Add playlist"), gtk.STOCK_ADD, self.create_playlist, None)
                menu.add_item(_("Rename playlist"), gtk.STOCK_EDIT, self.rename_playlist, None)
                menu.add_item(_("Delete playlist"), gtk.STOCK_DELETE, self.delete_playlist, None)
                menu.show(e)
    
    def create_playlist(self):
        text = one_line_dialog("Create new playlist")
        bean = FModel(text).add_font("bold")
        self.append(bean)
              
    
    def delete_playlist(self):
        self.delete_selected()
    
    def rename_playlist(self):
        bean = self.get_selected_bean()
        text = one_line_dialog("Rename playlist", bean.text)
        if not text:
            return
        selection = self.get_selection()
        fm, paths = selection.get_selected_rows()
        path = paths[0]
        path = self.filter_model.convert_path_to_child_path(path)        
        iter = self.model.get_iter(path)
        
        self.model.set_value(iter, self.text[0], text)
        
    
    def on_load(self):
        self.scroll.hide()
        pass
    
    def on_save(self):
        pass