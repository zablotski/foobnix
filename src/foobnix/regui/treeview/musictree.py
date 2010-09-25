#-*- coding: utf-8 -*-
'''
Created on 25 сент. 2010

@author: ivan
'''
from foobnix.regui.treeview import TreeViewControl
import gtk
class MusicTreeControl(TreeViewControl):
    def __init__(self):
        TreeViewControl.__init__(self)
        self.set_reorderable(False)
        
        """column config"""
        column = gtk.TreeViewColumn("Title", gtk.CellRendererText(), text=self.text, font=self.font)
        column.set_resizable(True)
        self.append_column(column)
    
    def append(self, bean):           
        return super(MusicTreeControl, self).append(level=bean.level, text=bean.text, visible=True, font=bean.font, play_icon=None, time=bean.time)
  
    
    def populate_from_scanner(self, beans):
        self.model.clear()
        hash = {None:None}
        for bean in beans:
            if hash.has_key(bean.level):
                level = hash[bean.level]
            else:
                level = None

            if bean.is_file:
                child_level = self.append(bean.add_font("normal").add_level(level))
            else:
                child_level = self.append(bean.add_font("bold").add_level(level))
                
            hash[bean.path] = child_level
