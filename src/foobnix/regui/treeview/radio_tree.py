'''
Created on Sep 29, 2010

@author: ivan
'''
from __future__ import with_statement

import gtk
import gobject
import logging
import os.path
import thread

from foobnix.fc.fc import FC
from foobnix.regui.model import FModel, FTreeModel
from foobnix.helpers.menu import Popup
from foobnix.helpers.dialog_entry import two_line_dialog
from foobnix.fc.fc_cache import FCache, CACHE_RADIO_FILE
from foobnix.regui.service.radio_service import RadioFolder
from foobnix.regui.treeview.common_tree import CommonTreeControl
from foobnix.util.const import FTYPE_RADIO, LEFT_PERSPECTIVE_RADIO
from foobnix.util.mouse_utils import is_double_left_click, is_rigth_click,\
    is_left_click


class RadioTreeControl(CommonTreeControl):
    def __init__(self, controls):
        CommonTreeControl.__init__(self, controls)
        self.set_reorderable(False)
        self.switcher_label = _("My channels")
        """column config"""
        column = gtk.TreeViewColumn(_("Radio Stations"), gtk.CellRendererText(), text=self.text[0], font=self.font[0])
        column.set_resizable(True)
        self.set_headers_visible(True)
        self.append_column(column)
        
        self.configure_send_drag()
        self.configure_recive_drag()
        self.set_type_tree()
        self.lazy_load()
        
    
    def activate_perspective(self):
        FC().left_perspective = LEFT_PERSPECTIVE_RADIO
    
    def on_button_press(self, w, e):
        if is_double_left_click(e):
            selected = self.get_selected_bean()
            beans = self.get_all_child_beans_by_selected()  
            self.controls.notetabs._append_tab(selected.text, [selected] + beans, optimization=True)
            "run radio channel"
            self.controls.play_first_file_in_playlist()
            
        if is_rigth_click(e): 
            menu = Popup()
            #menu.add_item(_("Add Station"), gtk.STOCK_ADD, self.on_add_station, None)
            menu.add_item(_("Delete Station"), gtk.STOCK_DELETE, self.on_delete_station, None)
            menu.add_item(_("Edit Radio"), gtk.STOCK_EDIT, self.on_edit_radio, None)
            menu.add_separator()
            menu.add_item(_("Reload radio folder"), gtk.STOCK_REFRESH, self.update_radio_tree, None)            
            menu.show(e)
          
    def on_edit_radio(self):
        bean = self.get_selected_bean()
        name, url = two_line_dialog(_("Change Radio Station name and path"), _("Url"), bean.text, bean.path)
        if not name or not url:
            return
        if os.path.isfile(CACHE_RADIO_FILE) and os.path.getsize(CACHE_RADIO_FILE)>0:
            with open(CACHE_RADIO_FILE, 'r') as f:
                list = f.readlines()
                for i, line in enumerate(list):
                    if line == "#" + bean.text + '\n' and list[i+1] == bean.path + '\n':
                        list[i] = "#" + name + '\n'
                        list[i+1] = url + '\n'
            with open(CACHE_RADIO_FILE, 'w') as f:
                f.writelines(list)

        bean.add_text(name)
        bean.add_path(url)
        
        rows = self.find_rows_by_element(self.UUID, bean.UUID)
        if rows:
            rows[0][self.text[0]] = name
            rows[0][self.path[0]] = url
                
    def on_add_station(self):
        name, url = two_line_dialog("Add New Radio Station", "Enter Name and URL", "", "http://")
        #with open(CACHE_RADIO_FILE, 'a') as f:
           #f.write('#' + name + '\n' + url + '\n')
        bean = FModel(name, url).add_is_file(True)
        bean.type=FTYPE_RADIO
        self.append(bean)
    
    def on_save(self):
        pass
    
    def on_delete_station(self):
        bean = self.get_selected_bean()
        
        if os.path.isfile(CACHE_RADIO_FILE) and os.path.getsize(CACHE_RADIO_FILE) > 0:
            with open(CACHE_RADIO_FILE, 'r') as f:
                list = f.readlines()
                for i, line in enumerate(list):
                    if line == "#" + bean.text + '\n' and list[i+1] == bean.path + '\n':
                        del list[i+1]
                        del list[i]
                        
            with open(CACHE_RADIO_FILE, 'w') as f:
                f.writelines(list)
        
        self.delete_selected()
        
    def update_radio_tree(self):
        self.controls.in_thread.run_with_progressbar(self._update_radio_tree)
        
    def _update_radio_tree(self):
        logging.info("in update radio")
        self.clear_tree()
        self.radio_folder = RadioFolder()
        files = self.radio_folder.get_radio_FPLs()    
        def task():    
            for fpl in files:
                parent = FModel(fpl.name).add_is_file(False)
                self.append(parent)
                for radio, urls in fpl.urls_dict.iteritems():
                    child = FModel(radio, urls[0]).parent(parent).add_type(FTYPE_RADIO).add_is_file(True)
                    self.append(child)
            
            
        gobject.idle_add(task)            

    def auto_add_user_station(self):
        if os.path.isfile(CACHE_RADIO_FILE) and os.path.getsize(CACHE_RADIO_FILE) > 0:
            with open(CACHE_RADIO_FILE, 'r') as f:
                list = f.readlines()
                parent_level_for_depth = {}
                previous = {"bean": None, "depth": 0, "name": '', "url": ''} 
                for line in list:
                    depth = self.simbol_counter(line, '-')
                    name = line[depth : line.index('#')]
                    url = line[line.index('#') + 1 : -1]
                    bean = FModel(name)
                    if url:
                        bean.add_is_file(True).add_path(url)
                    if previous["depth"] < depth:
                        bean.add_parent(previous["bean"].level)
                    elif previous["depth"] > depth:
                        bean.add_parent(parent_level_for_depth[depth]) 
                    else:
                        if previous["bean"]:
                            bean.add_parent(previous["bean"].parent_level)
                        
                    self.append(bean)
                    parent_level_for_depth[depth] = bean.parent_level
                    previous = {"bean": bean, "depth": depth, "name": name, "url": url}
                        
    def simbol_counter(self, line, simbol):
        counter = 0
        for letter in line:
            if letter == simbol:
                counter += 1
            else:
                break
        return counter
    
    def lazy_load(self):
        def task():
            logging.debug("radio Lazy loading")
            if FCache().cache_radio_tree_beans:
                self.populate_all(FCache().cache_radio_tree_beans)
            else:
                self.update_radio_tree()
            self.is_radio_populated = True
        thread.start_new_thread(task, ())                      
            
    def on_quit(self):
        FCache().cache_radio_tree_beans = self.controls.radio.get_all_beans()
        
                        
class MyRadioTreeControl(RadioTreeControl):
    def __init__(self, controls):
        RadioTreeControl.__init__(self, controls)
        self.switcher_label = _("Common channels")
        
    def lazy_load(self):
        logging.debug("updating My Radio tree")
        self.auto_add_user_station()
       
    def on_button_press(self, w, e):
        if is_double_left_click(e):
            selected = self.get_selected_bean()
            beans = self.get_all_child_beans_by_selected()  
            self.controls.notetabs._append_tab(selected.text, [selected] + beans, optimization=True)
            "run radio channel"
            self.controls.play_first_file_in_playlist()
            
        if is_rigth_click(e): 
            menu = Popup()
            menu.add_item(_("Add Station"), gtk.STOCK_ADD, self.on_add_station, None)
            if self.get_selected_bean():
                menu.add_item(_("Delete Station"), gtk.STOCK_DELETE, self.on_delete_station, None)
                menu.add_item(_("Edit Radio"), gtk.STOCK_EDIT, self.on_edit_radio, None)
            menu.add_separator()
            menu.add_item(_("Reload radio folder"), gtk.STOCK_REFRESH, self.update_radio_tree, None)            
            menu.show(e)
            
    def on_quit(self):
        with open(CACHE_RADIO_FILE, 'w') as f:
                   
            def task(row):
                iter = row.iter
                level = self.model.iter_depth(iter)
                text = self.model.get_value(iter, FTreeModel().text[0])
                path = self.model.get_value(iter, FTreeModel().path[0])
                if not path:
                    path = ""
                f.write(level * '-' + text + '#' + path + '\n') 
                if row.iterchildren():
                    for child_row in row.iterchildren():
                        task(child_row)
        
            for row in self.model:
                task(row)