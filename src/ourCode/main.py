import sys
sys.path.append('..')
from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.synth import Synth
from common.gfxutil import topleft_label
from common.clock import Clock, SimpleTempoMap, AudioScheduler, tick_str, kTicksPerQuarter, quantize_tick_up
from common.metro import Metronome
from common.gfxutil import topleft_label, CEllipse, KFAnim, AnimGroup
from common.writer import AudioWriter

import numpy as np

from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Triangle, Line
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate

from barPlayer import StaticBarPlayer, LineComposeBarPlayer
from selectionButton import SelectionButton, BetterButton
from notes import transpose_instrument, transpose_melody, chords_to_changes, combine_changes_and_scale
from nowBar import NowBar

class StyleSelection(FloatLayout):
    def __init__(self, styleCallback):
        super(StyleSelection, self).__init__()
        
        self.label = topleft_label()
        self.label.text = "Select the style of music that you would like to replicate."
        self.add_widget(self.label)

        self.orientation = "vertical"
        self.button_size = (900, 400)

        b1 = BetterButton("", self.button_size, (Window.width/2 - self.button_size[0]/2, Window.height/2), styleCallback, "Chainsmokers")
        b1.background_normal = "../img/chainsmokers.png"
        self.option1 = b1

        b2 = BetterButton("", self.button_size, (Window.width/2 - self.button_size[0]/2, Window.height/2 - self.button_size[1]), styleCallback, "Ed Sheeran")
        b2.background_normal = "../img/sheeran.png"
        self.option2 = b2
        
        self.add_widget(self.option1)
        self.add_widget(self.option2)

    def on_update(self):
        self.option1.on_update()
        self.option2.on_update()
        return

    def on_touch_move(self, touch):
        pass

    def on_key_down(self, keycode, modifiers):
        pass

    def on_layout(self, winsize):
        w = winsize[0]
        h = winsize[1]
        self.option1.pos = (w/2 - self.button_size[0]/2, h/2)
        self.option2.pos = (w/2 - self.button_size[0]/2, h/2 - self.button_size[1])
        self.label.pos=(w * 0.3, h * 0.5)

class KeySelection(FloatLayout):
    def __init__(self, transposeCallback):
        super(KeySelection, self).__init__()
        
        self.label = topleft_label()
        self.label.text = "Select the key that you'd like to use."
        self.add_widget(self.label)

        self.orientation = "vertical"

        self.b1 = Button(text="A", size_hint = (None, None), size = (300, 50), pos = (Window.width/2-150, Window.height/2 + 225))
        self.b1.bind(on_press=transposeCallback)

        self.b2 = Button(text="B", size_hint = (None, None), size = (300, 50), pos = (Window.width/2-150, Window.height/2 + 150))
        self.b2.bind(on_press=transposeCallback)

        self.b3 = Button(text="C", size_hint = (None, None), size = (300, 50), pos = (Window.width/2-150, Window.height/2 + 75))
        self.b3.bind(on_press=transposeCallback)

        self.b4 = Button(text="D", size_hint = (None, None), size = (300, 50), pos = (Window.width/2-150, Window.height/2))
        self.b4.bind(on_press=transposeCallback)

        self.b5 = Button(text="E", size_hint = (None, None), size = (300, 50), pos = (Window.width/2-150, Window.height/2 - 75))
        self.b5.bind(on_press=transposeCallback)

        self.b6 = Button(text="F", size_hint = (None, None), size = (300, 50), pos = (Window.width/2-150, Window.height/2 - 150))
        self.b6.bind(on_press=transposeCallback)

        self.b7 = Button(text="G", size_hint = (None, None), size = (300, 50), pos = (Window.width/2-150, Window.height/2 - 225))
        self.b7.bind(on_press=transposeCallback)
        
        self.add_widget(self.b1)
        self.add_widget(self.b2)
        self.add_widget(self.b3)
        self.add_widget(self.b4)
        self.add_widget(self.b5)
        self.add_widget(self.b6)
        self.add_widget(self.b7)

    def on_update(self):
        pass

    def on_touch_move(self, touch):
        pass

    def on_key_down(self, keycode, modifiers):
        pass

    def on_layout(self, winsize):
        w = winsize[0]
        h = winsize[1]
        self.b1.pos = (w/2-150, h/2 + 225)
        self.b2.pos = (w/2-150, h/2 + 150)
        self.b3.pos = (w/2-150, h/2 + 75)
        self.b4.pos = (w/2-150, h/2)
        self.b5.pos = (w/2-150, h/2 - 75)
        self.b6.pos = (w/2-150, h/2 - 150)
        self.b7.pos = (w/2-150, h/2 - 225)
        self.label.pos=(w * 0.3, h * 0.5)

class ChordSelection(FloatLayout):
    def __init__(self, chordCallback, sched, synth, chord_options):
        super(ChordSelection, self).__init__()
        
        self.orientation = "vertical"

        self.label = topleft_label()
        self.label.text = "Select the chords you would like to use."
        self.add_widget(self.label)

        size = (300, 50)
        channel = 1
        program = (0,0)
        velocity = 60
        self.options = []

        text1 = "Chord 1"
        pos1 = (Window.width/2-150, Window.height/2)
        notes = chord_options[1]["midi"]
        b1 = SelectionButton(text1, size, pos1, chordCallback, sched, synth, channel, program, notes, velocity, 1)
        self.options.append(b1)

        text2 = "Chord 2"
        pos2 = (Window.width/2-150, Window.height/2 - 200)
        notes = chord_options[2]["midi"]
        b2 = SelectionButton(text2, size, pos2, chordCallback, sched, synth, channel, program, notes, velocity, 2)
        self.options.append(b2)

        for option in self.options:
            self.add_widget(option)
    
    def on_update(self):
        pos = Window.mouse_pos
        for option in self.options:
            option.on_update(pos)
    
    def on_touch_down(self, touch):
        for option in self.options:
            option.on_touch_down(touch)

    def on_touch_move(self, touch):
        pass

    def on_key_down(self, keycode, modifiers):
        pass

class PercSelection(FloatLayout):
    def __init__(self, percCallback, sched, synth, perc_options):
        super(PercSelection, self).__init__()
        
        self.orientation = "vertical"

        self.label = topleft_label()
        self.label.text = "Select the percussion you would like to use."
        self.add_widget(self.label)

        self.options = []
        size = (300, 50)
        channel = 2
        program = (128,0)
        velocity = 100

        text1 = "Percussion 1"
        pos1 = (Window.width/2-150, Window.height/2)
        notes = perc_options[1]["midi"]
        b1 = SelectionButton(text1, size, pos1, percCallback, sched, synth, channel, program, notes, velocity, 1)
        self.options.append(b1)

        text2 = "Percussion 2"
        pos2 = (Window.width/2-150, Window.height/2 - 200)
        notes = perc_options[2]["midi"]
        b2 = SelectionButton(text2, size, pos2, percCallback, sched, synth, channel, program, notes, velocity, 2)
        self.options.append(b2)
        
        for option in self.options:
            self.add_widget(option)
    
    def on_update(self):
        pos = Window.mouse_pos
        for option in self.options:
            option.on_update(pos)

    def on_touch_down(self, touch):
        for option in self.options:
            option.on_touch_down(touch)

    def on_touch_move(self, touch):
        pass

    def on_key_down(self, keycode, modifiers):
        pass
        
class MelodySelection(Widget):
    def __init__(self, synth, sched, chords, perc, melody, change_key, change_chord, change_perc, writer):
        super(MelodySelection, self).__init__()
        w = Window.width
        h = Window.height
        padding = 20

        self.melody = melody
        self.currCompIndex = 0
        
        # Audio Generation
        self.synth = synth
        self.sched = sched
        self.writer = writer
        self.is_playing = False

        halfHeight = (h - 4*padding) / 2
        quarterHeight = halfHeight / 3
        paddedWidth = w - 2*padding

        # Now Bar Speed Calculation
        now_bar_padding = 20
        length = paddedWidth - 2*now_bar_padding
        num_beats = 16
        self.speed = length / num_beats * 95*2 / 60

        botBarPlayerPos = (padding,padding)
        botBarPlayerSize = (paddedWidth, quarterHeight)
        #def __init__(self, botLeft, size, sched, synth, channel, program, notes, posPitches, velocity):
        self.botBPlayer = StaticBarPlayer(botBarPlayerPos, botBarPlayerSize, self.sched, self.synth, 2, (128,0), perc['midi'], perc['pitches'], 100)

        midBarPlayerPos = (padding, 2*padding + quarterHeight)
        midBarPlayerSize = (paddedWidth, quarterHeight)
        self.midBPlayer = StaticBarPlayer(midBarPlayerPos, midBarPlayerSize, self.sched, self.synth, 1, (0,0), chords['midi'], chords['pitches'], 60)

        changesAndNotes = chords_to_changes(chords)
        changes = changesAndNotes[0]
        changeNotes = changesAndNotes[1]
        scaleNotes = melody['pitches']
        combinedNotes = combine_changes_and_scale(changeNotes, scaleNotes)
        #def __init__(self, botLeft, size, sched, synth, channel, program, changes, allPitches, velocity):
        compBarPlayerPos = (padding, 3*padding + 2*quarterHeight)
        compBarPlayerSize = (paddedWidth, halfHeight)
        self.compBPlayer = LineComposeBarPlayer(compBarPlayerPos, compBarPlayerSize, self.sched, self.synth, 1, (0,0), changes, combinedNotes, scaleNotes, 110, self.four_bar_done_callback)
        self.compBPlayer2 = LineComposeBarPlayer(compBarPlayerPos, compBarPlayerSize, self.sched, self.synth, 1, (0,0), changes, combinedNotes, scaleNotes, 110, self.four_bar_done_callback)
        self.compBPlayer3 = LineComposeBarPlayer(compBarPlayerPos, compBarPlayerSize, self.sched, self.synth, 1, (0,0), changes, combinedNotes, scaleNotes, 110, self.four_bar_done_callback)
        self.compBPlayer4 = LineComposeBarPlayer(compBarPlayerPos, compBarPlayerSize, self.sched, self.synth, 1, (0,0), changes, combinedNotes, scaleNotes, 110, self.four_bar_done_callback)
        self.currentCompBar = self.compBPlayer
        self.compBars = [self.compBPlayer, self.compBPlayer2, self.compBPlayer3, self.compBPlayer4]

        self.nowBar = NowBar(botBarPlayerPos, (paddedWidth, halfHeight+quarterHeight+quarterHeight+2*padding), now_bar_padding, self.speed)
        self.barPlayers = [self.botBPlayer, self.midBPlayer]
        self.objects = self.barPlayers + [self.nowBar]

        self.canvas.add(self.compBPlayer)
        for obj in self.objects:
            self.canvas.add(obj)

        b_width = Window.width / 12.75
        b_padding = b_width / 4
        dist_between = b_width + b_padding

        b_height = Window.height / 15
        b_y = Window.height - 3*b_padding
        button_size = (b_width, b_height)

        self.b3 = BetterButton("Convert", button_size, (b_padding + 4*dist_between, b_y), self.currentCompBar.do_v_b, False)
        self.b4 = BetterButton("Pitch Snap", button_size, (b_padding + 5*dist_between, b_y), self.currentCompBar.do_n, False)
        self.b5 = BetterButton("Auto Compose", button_size, (b_padding + 6*dist_between, b_y), self.currentCompBar.do_m, False)
        self.b6 = BetterButton("Toggle Draw/Edit", button_size, (b_padding + 7*dist_between, b_y), self.currentCompBar.toggle_select_mode, False)

        b1 = BetterButton("Prev", button_size, (b_padding, b_y), self.prev_bars, False)
        b2 = BetterButton("Next", button_size, (b_padding + dist_between, b_y), self.next_bars, False)
        b7 = BetterButton("Play/Stop", button_size, (b_padding + 2*dist_between, b_y), self.do_q, False)
        b8 = BetterButton("Record/Stop", button_size, (b_padding + 3*dist_between, b_y), self.writer.toggle, False)

        b9 = BetterButton("Change Chord", button_size, (b_padding + 8*dist_between, b_y), change_chord)
        b10 = BetterButton("Change Drums", button_size, (b_padding + 9*dist_between, b_y), change_perc)

        self.controlButtons = [b1, b2, b7, b8]
        self.computeButtons = [self.b3, self.b4, self.b5, self.b6]
        self.buttons = self.controlButtons + self.computeButtons + [b9, b10]
        for button in self.buttons:
            self.add_widget(button)

    def stop(self):
        for obj in self.objects:
                obj.stop()
        self.compBars[self.currCompIndex].stop()

    def next_bars(self):
        self.canvas.remove(self.nowBar)
        if self.currCompIndex < len(self.compBars) -1:
            self.canvas.remove(self.compBars[self.currCompIndex])
            self.currCompIndex += 1
            self.canvas.add(self.compBars[self.currCompIndex])
            self.currentCompBar = self.compBars[self.currCompIndex]

            self.b3.update_callback(self.compBars[self.currCompIndex].do_v_b)
            self.b4.update_callback(self.compBars[self.currCompIndex].do_n)
            self.b5.update_callback(self.compBars[self.currCompIndex].do_m)
            self.b6.update_callback(self.compBars[self.currCompIndex].toggle_select_mode)
        self.canvas.add(self.nowBar)

    def prev_bars(self):
        self.canvas.remove(self.nowBar)
        if self.currCompIndex > 0:
            self.canvas.remove(self.compBars[self.currCompIndex])
            self.currCompIndex -= 1
            self.canvas.add(self.compBars[self.currCompIndex])
            self.currentCompBar = self.compBars[self.currCompIndex]

            self.b3.update_callback(self.currentCompBar.do_v_b)
            self.b4.update_callback(self.currentCompBar.do_n)
            self.b5.update_callback(self.currentCompBar.do_m)
            self.b6.update_callback(self.currentCompBar.toggle_select_mode)
        self.canvas.add(self.nowBar)        

    def four_bar_done_callback(self):
        #print("currIndex: ", self.currCompIndex)
        if self.currCompIndex < len(self.compBars) - 1:
            #print("in the if statement")
            # self.compBars[self.currCompIndex].stop()
            self.botBPlayer.stop()
            self.midBPlayer.stop()
            # self.nowBar.stop()
            self.next_bars()
            # thing = 0
            # #literally here just to slow things down idk
            # for i in range(700000):
            #     thing+=1
            self.nowBar.play()
            self.botBPlayer.play()
            self.midBPlayer.play()
            self.compBars[self.currCompIndex].play()
            
    
    def on_touch_down(self, touch):
        self.compBars[self.currCompIndex].on_touch_down(touch)
        #self.compBPlayer.on_touch_down(touch)
        for button in self.buttons:
            button.on_touch_down(touch)
    
    def on_touch_move(self, touch):
        self.compBars[self.currCompIndex].on_touch_move(touch)
        #self.compBPlayer.on_touch_move(touch)

    def on_touch_up(self, touch):
        self.compBars[self.currCompIndex].on_touch_up(touch)
        #self.compBPlayer.on_touch_up(touch)

    def change_chords(self, chords):
        self.midBPlayer.set_notes(chords['midi'])
        self.midBPlayer.set_pitches(chords['pitches'])
        self.midBPlayer.clear_note_graphics()
        self.midBPlayer.display_note_graphics()

        changesAndNotes = chords_to_changes(chords)
        changes = changesAndNotes[0]
        changeNotes = changesAndNotes[1]
        scaleNotes = self.melody['pitches']
        combinedNotes = combine_changes_and_scale(changeNotes, scaleNotes)

        for compBPlayer in self.compBars:
            compBPlayer.set_changes(changes)
            compBPlayer.set_allPitches(combinedNotes)
            compBPlayer.set_scaleNotes(scaleNotes)
            compBPlayer.clear_note_graphics()
            compBPlayer.clear_real_notes()
            compBPlayer.lines_to_notes()
            compBPlayer.apply_rules()
            compBPlayer.display_note_graphics()


    def change_perc(self, perc):
        self.botBPlayer.set_notes(perc['midi'])
        self.botBPlayer.set_pitches(perc['pitches'])
        self.botBPlayer.clear_note_graphics()
        self.botBPlayer.display_note_graphics()

    def on_layout(self, win_size):
        w = win_size[0]
        h = win_size[1]
        padding = 20
        halfHeight = (h - 4*padding) / 2
        quarterHeight = halfHeight / 2
        paddedWidth = w - 2*padding

        botBarPlayerPos = (padding,padding)
        botBarPlayerSize = (paddedWidth, quarterHeight)
        self.botBPlayer.resize(botBarPlayerSize, botBarPlayerPos)

        midBarPlayerPos = (padding, 2*padding + quarterHeight)
        midBarPlayerSize = (paddedWidth, quarterHeight)
        self.midBPlayer.resize(midBarPlayerSize, midBarPlayerPos)

        compBarPlayerPos = (padding, 3*padding + 2*quarterHeight)
        compBarPlayerSize = (paddedWidth, halfHeight)
        self.compBPlayer.resize(compBarPlayerSize, compBarPlayerPos)

        b_width = Window.width / 15
        b_padding = b_width / 4
        dist_between = b_width + b_padding

        b_height = Window.height / 15
        b_y = Window.height - 3*b_padding
        button_size = (b_width, b_height)

        for i in range(len(self.buttons)):
            b = self.buttons[i]
            b.pos = (b_padding + dist_between*i, b_y)
            b.size = button_size
    
    def do_q(self):
        if not self.is_playing:
            self.is_playing = True
            self.canvas.remove(self.nowBar)
            self.canvas.remove(self.compBars[self.currCompIndex])
            self.currCompIndex = 0
            self.canvas.add(self.compBars[self.currCompIndex])
            self.canvas.add(self.nowBar)             
            self.compBars[self.currCompIndex].play()
            for obj in self.objects:
                obj.play()
        else:
            self.is_playing = False
            self.compBars[self.currCompIndex].toggle()
            for obj in self.objects:
                obj.toggle()

    def on_key_down(self, keycode, modifiers):
        self.compBars[self.currCompIndex].on_key_down(keycode, modifiers)
        #self.compBPlayer.on_key_down(keycode, modifiers)
        if keycode[1] == 'q':
            self.is_playing = True
            self.canvas.remove(self.nowBar)
            self.canvas.remove(self.compBars[self.currCompIndex])
            self.currCompIndex = 0
            self.canvas.add(self.compBars[self.currCompIndex])
            self.canvas.add(self.nowBar)             
            self.compBars[self.currCompIndex].play()
            for obj in self.objects:
                obj.play()
        elif keycode[1] == 'p':
            self.next_bars()
        elif keycode[1] == 'o':
            self.prev_bars()

    def on_update(self):     
        self.nowBar.on_update()
        # for obj in self.nowBars:
        #     obj.on_update()  


key_to_transpose = {
            "A": -3,
            "B": -1,
            "C": 0,
            "D": 2,
            "E": 4,
            "F": 5,
            "G": 7
        }

class MainWidget(BaseWidget):
    def __init__(self):
        super(MainWidget, self).__init__()

        self.writer = AudioWriter('song')
        self.audio = Audio(2, self.writer.add_audio)
        self.synth = Synth('../data/FluidR3_GM.sf2')

        # create TempoMap, AudioScheduler
        self.tempo_map = SimpleTempoMap(95*2)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        # create the metronome:
        self.metro = Metronome(self.sched, self.synth)

        # variables to store options
        self.transposition = 0
        self.style = None
        self.melody = None
        self.chords = None
        self.chord_option = None
        self.perc = None
        self.perc_option = None

        # variables to store screen options
        self.style_selection = StyleSelection(self.update_style_screen)    # screen index 0
        self.key_selection = KeySelection(self.update_key_screen)          # screen index 1
        self.chord_selection = None                                 # screen index 2
        self.perc_selection = None                                  # screen index 3
        self.melody_selection = None                                # screen index 4

        self.active_screen = self.style_selection
        self.screen_index = 0
        self.add_widget(self.active_screen)

    def update_style_screen(self, option):
        self.style = option

        self.change_screens(self.key_selection)
        self.screen_index = 1

    def update_key_screen(self, instance):
        self.transposition = key_to_transpose[instance.text]

        # can now set up melody, chord, percussion settings
        self.melody = transpose_melody(self.style, 1, self.transposition)

        self.chords = transpose_instrument(self.style, "chords", self.transposition)
        self.chord_selection = ChordSelection(self.update_chord_screen, self.sched, self.synth, self.chords)

        self.perc = transpose_instrument(self.style, "percussion", 0)
        self.perc_selection = PercSelection(self.update_perc_screen, self.sched, self.synth, self.perc)

        self.change_screens(self.chord_selection)
        self.screen_index = 2

    def update_chord_screen(self, option):
        self.chord_option = option

        self.change_screens(self.perc_selection)
        self.screen_index = 3
    
    def update_perc_screen(self, option):
        self.perc_option = option

        # can now update our composition screen
        self.melody_selection = MelodySelection(
            self.synth, 
            self.sched, 
            self.chords[self.chord_option], 
            self.perc[self.perc_option],
            self.melody,
            self.change_key_button,
            self.change_chord_button,
            self.change_perc_button,
            self.writer
            )
        self.change_screens(self.melody_selection)
        self.screen_index = 4

    def change_key_button(self, instance):
        self.transposition = key_to_transpose[instance.text]
        self.melody = transpose_melody(self.style, 1, self.transposition)
        self.chords = transpose_instrument(self.style, "chords", self.transposition)

        self.melody_selection.stop()
        self.remove_widget(self.melody_selection)
        self.melody_selection = MelodySelection(
            self.synth, 
            self.sched, 
            self.chords[self.chord_option], 
            self.perc[self.perc_option],
            self.melody,
            self.change_key_button,
            self.change_chord_button,
            self.change_perc_button,
            self.writer
            )
        self.add_widget(self.melody_selection)
        self.active_screen = self.melody_selection

    def change_chord_button(self, instance):
        if self.chord_option == 1:
            option = 2
        else:
            option = 1

        self.chord_option = option

        self.melody_selection.change_chords(self.chords[self.chord_option])

    def change_perc_button(self, instance):
        if self.perc_option == 1:
            option = 2
        else:
            option = 1

        self.perc_option = option

        self.melody_selection.change_perc(self.perc[self.perc_option])

    def change_screens(self, screen):
        self.remove_widget(self.active_screen)
        self.active_screen = screen
        self.add_widget(self.active_screen)

    def on_touch_down(self, touch):
        self.active_screen.on_touch_down(touch)

    def on_touch_move(self, touch):
        self.active_screen.on_touch_move(touch)
    
    def on_key_down(self, keycode, modifiers):
        self.active_screen.on_key_down(keycode, modifiers)
        
        if keycode[1] == 'r':
            self.writer.toggle()

    def on_layout(self, winsize):
        if self.style_selection != None:
            self.style_selection.on_layout(winsize)

        if self.key_selection != None:
            self.key_selection.on_layout(winsize)

        if self.chord_selection != None:
            self.chord_selection.on_layout(winsize)

        if self.perc_selection != None:
            self.perc_selection.on_layout(winsize)

        if self.melody_selection != None:
            self.melody_selection.on_layout(winsize)

    def on_update(self):
        self.audio.on_update()
        self.active_screen.on_update()

if __name__ == "__main__":
    # pass in which MainWidget to run as a command-line arg
    run(eval("MainWidget"))