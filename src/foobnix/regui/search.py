import gtk
from foobnix.helpers.toggled import OneActiveToggledButton
from foobnix.regui.model.signal import FControl
from foobnix.util import LOG
from foobnix.util.text_utils import capitilize_query
from foobnix.util.key_utils import is_key

class SearchControls(FControl, gtk.Frame):
    def __init__(self, controls):        
        gtk.Frame.__init__(self)
        FControl.__init__(self, controls)
        self.controls = controls
        
        label = gtk.Label()
        label.set_markup("<b>%s:</b>" % _("Search music online"))
        self.set_label_widget(label)
        self.set_border_width(0)
        
        """default search function"""
        self.search_function = self.controls.search_top_tracks
        self.buttons = []
                
        vbox = gtk.VBox(False, 0)
        vbox.pack_start(self.search_line(), False, False, 0)
                
        vbox.pack_start(controls.search_progress, False, False, 0)
           
        self.add(vbox)
        
        self.show_all()
        """search on enter"""
        for button in self.buttons:
            button.connect("key-press-event", self.on_search_key_press)
        
        """only one button active"""    
        OneActiveToggledButton(self.buttons)
        
    
    def set_search_function(self, search_function):
        LOG.info("Set search fucntion", search_function)
        self.search_function = search_function    
        
    
    def on_search(self, *w):
        if self.get_query():
            if self.get_query().startswith("http://vk"):
                self.controls.search_vk_page_tracks(self.get_query())                
            else:
                self.search_function(self.get_query())
    
    def get_query(self):
        query = self.entry.get_text()
        return capitilize_query(query)
        
    def search_line(self):
        self.entry = gtk.Entry()
        self.entry.connect("key-press-event", self.on_search_key_press)
        self.entry.set_text("")
               
        combobox = self.combobox_creator()
        
        hbox = gtk.HBox(False, 0)
        hbox.pack_start(combobox, False, False, 0)        
        hbox.pack_start(self.entry, True, True, 0)
        hbox.show_all()
        
        return hbox 
    
    def set_search_text(self, text):
        self.entry.set_text(text)
    
    def on_search_key_press(self, w, e):        
        if is_key(e, 'Return'):
            self.on_search();
            self.entry.grab_focus()
    
    def combobox_creator(self):
        list_func = []
        liststore = gtk.ListStore(str)
        
        liststore.append([_("All")])
        list_func.append(self.controls.search_all_tracks)
        
        liststore.append([_("Tracks")])
        list_func.append(self.controls.search_top_tracks)
        
        liststore.append([_("_Albums")])
        list_func.append(self.controls.search_top_albums)
        
        liststore.append([_("Similar")])
        list_func.append(self.controls.search_top_similar)
        
        liststore.append([_("Genre")])
        list_func.append(self.controls.search_top_tags)
        
        liststore.append([_("Video")])
        list_func.append(self.controls.search_all_videos)
               
        combobox = gtk.ComboBox(liststore)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)
        combobox.set_active(0)
        self.set_search_function(list_func[0])
        
        def on_changed(combobox):
            n = combobox.get_active()
            self.set_search_function(list_func[n])
            self.entry.grab_focus()
        
        combobox.connect("changed", on_changed)     
        return combobox
        
    def show_menu(self, w, event, menu):
        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)  
        
        