#!/usr/bin/env python
import thread, time
import gtk.glade
import gst
import os
from player.mouse_utils import is_double_click
from player.time_utils import convert_ns
from player.playlist import PlayList
from player.song import Song

class FoobNIX:
        def __init__(self):                    
                self.gladefile = "foobnix.glade"  
                self.mainWindow = gtk.glade.XML(self.gladefile, "mainWindow")
                    
                dic = {
               "on_mainWindow_destroy" : gtk.main_quit,
               "on_button1_clicked":self.onPlayButton,
               "on_button2_clicked":self.onPauseButton,
               "on_button3_clicked":self.onStopButton,
               "on_hscale2_change_value": self.onVolumeChange,
               "on_hscale1_change_value": self.onSeekChange,
               "on_treeview1_button_press_event":self.onSlectRow
               }
                self.mainWindow.signal_autoconnect(dic)
              

                self.wineFile = self.mainWindow.get_widget("filechooserbutton1")                
                self.wineText = self.mainWindow.get_widget("entry1")
                self.time_label = self.mainWindow.get_widget("label7")                
                
                self.wineVolume = self.mainWindow.get_widget("hscale2")
                self.wineSeek = self.mainWindow.get_widget("hscale1")
                
                self.musicTree = self.mainWindow.get_widget("treeview1")
                self.playListWidget = self.mainWindow.get_widget("treeview2")
                
                
                self.wineText.set_text("/home/ivan/Music/CD1")
                
                self.player = gst.Pipeline("player")
                source = gst.element_factory_make("filesrc", "file-source")
                decoder = gst.element_factory_make("mad", "mp3-decoder")
                conv = gst.element_factory_make("audioconvert", "converter")
                sink = gst.element_factory_make("alsasink", "alsa-output")
                
                
                volume = gst.element_factory_make("volume", "volume")
                
                self.time_format = gst.Format(gst.FORMAT_TIME)
        
                self.player.add(source, decoder, conv, volume, sink)
                gst.element_link_many(source, decoder, volume, conv, sink)
                
                self.time_format = gst.Format(gst.FORMAT_TIME)
                
                self.play_thread_id = None
                self.player.set_state(gst.STATE_NULL)                
                self.time_label.set_text("00:00 / 00:00")
                
                bus = self.player.get_bus()
                bus.add_signal_watch()
                bus.connect("message", self.on_message)
                
                #################
                #ALL Music Directory
                #################
                
                column = gtk.TreeViewColumn("Title", gtk.CellRendererText(), text=0)
                column.set_resizable(True)
                self.musicTree.append_column(column)
                                
                self.musicTreeModel = gtk.TreeStore(str, str)                
                
                path = "/home/ivan/Music/nightwish"
                level = None;
                self.go_recursive(path, level)
                
                self.musicTree.set_model(self.musicTreeModel)
                #################
                #Playlists music directory
                ################
                self.playList = PlayList(self.playListWidget)
                                                 
        
        print "some"    
        
        def go_recursive(self, path, level):
            
            dir = os.path.abspath(path)    
            print "absolute", dir
            list = os.listdir(dir)
                    
            for file in list:
                
                full_path = path + "/" + file        
                sub = self.musicTreeModel.append(level, [file, full_path])              
                
                if os.path.isdir(full_path):            
                    print "dir", file                    
                    self.go_recursive(full_path, sub) 
                else:
                    print "file", file                  
        
        
        def onFileSelect(self, widget):
            print "set file"
            file_name = self.wineFile.get_filename()
            print file_name
            self.wineText.set_text(file_name)
        
        def onPlayButton(self, widget):
            print "Play" 
            file_name = self.wineFile.get_filename()
            if not file_name:
                file_name = self.wineText.get_text()
                print "set file name", file_name                                                    
            #self.player.set_property("uri", "file://" + file_name)
            self.player.get_by_name("file-source").set_property("location", file_name)
            self.player.set_state(gst.STATE_PLAYING)
            self.play_thread_id = thread.start_new_thread(self.play_thread, ())
            

                        
        def onPauseButton(self, widget):
            print "Pause"
            self.player.set_state(gst.STATE_PAUSED)
        def onStopButton(self, widget):
            print "Stop"
            self.player.set_state(gst.STATE_NULL)
            self.time_label.set_text("00:00 / 00:00")
            
        def onVolumeChange(self, widget, obj3, ojb4):
            val = ojb4 / 100            
            print val    
            self.player.get_by_name("volume").set_property('volume', val)
        
        def onSlectRow(self, widget, event):        
                 
            #left double click
     
            if is_double_click(event):
                selection = self.musicTree.get_selection()
                model, selected = selection.get_selected()
                if selected:
                    song_name = model.get_value(selected, 0)
                    song_path = model.get_value(selected, 1)
                    print song_path
                    self.wineText.set_text(song_path)
                    song = Song(song_name, song_path)
                    self.playList.add_song(song)                
 
            
        def onSeekChange(self, widget, obj3, obj4):            
            time.sleep(0.2)          
                        
                        
            pos_current = self.player.query_position(self.time_format, None)[0]
            pos_max = self.player.query_duration(self.time_format, None)[0]            
            
            print "Current", pos_current, pos_max
            seek_ns = pos_max * obj4 / 100;
            print "Set position", seek_ns
                        
            self.player.seek_simple(self.time_format, gst.SEEK_FLAG_FLUSH, seek_ns)
            #self.play_thread_id = thread.start_new_thread(self.play_thread, ())
        
        def play_thread(self):
            print "Thread Start"
            play_thread_id = self.play_thread_id
            gtk.gdk.threads_enter() #@UndefinedVariable
            self.time_label.set_text("00:00 / 00:00")
            gtk.gdk.threads_leave() #@UndefinedVariable
    
            while play_thread_id == self.play_thread_id:
                try:
                    time.sleep(0.2)
                    dur_int = self.player.query_duration(self.time_format, None)[0]
                    dur_str = convert_ns(dur_int)
                    gtk.gdk.threads_enter() #@UndefinedVariable
                    self.time_label.set_text("00:00 / " + dur_str)
                    gtk.gdk.threads_leave() #@UndefinedVariable
                    break
                except:
                    pass
                    
            time.sleep(0.2)
            while play_thread_id == self.play_thread_id:
                pos_int = self.player.query_position(self.time_format, None)[0]
                pos_str = convert_ns(pos_int)
                if play_thread_id == self.play_thread_id:
                    gtk.gdk.threads_enter() #@UndefinedVariable
                    self.time_label.set_text(pos_str + " / " + dur_str)
                    
                    self.wineSeek.set_value(100 * pos_int / dur_int)
                    
                    gtk.gdk.threads_leave() #@UndefinedVariable
                time.sleep(1)

        
        def on_message(self, bus, message):
            t = message.type
            if t == gst.MESSAGE_EOS:
                self.play_thread_id = None
                self.player.set_state(gst.STATE_NULL)
                self.button.set_label("Start")
                self.time_label.set_text("00:00 / 00:00")
            elif t == gst.MESSAGE_ERROR:
                err, debug = message.parse_error()
                print "Error: %s" % err, debug
                self.play_thread_id = None
                self.player.set_state(gst.STATE_NULL)
                self.button.set_label("Start")
                self.time_label.set_text("00:00 / 00:00")                                              
                
if __name__ == "__main__":
    
    player = FoobNIX()
    gtk.gdk.threads_init() #@UndefinedVariable
    gtk.main()
