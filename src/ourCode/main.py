
import sys
sys.path.append('..')
from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.synth import Synth
from common.gfxutil import topleft_label
from common.clock import Clock, SimpleTempoMap, AudioScheduler, tick_str, kTicksPerQuarter, quantize_tick_up
from common.metro import Metronome
from common.gfxutil import topleft_label, CEllipse, KFAnim, AnimGroup

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

from barPlayer import StaticBarPlayer, ComposeBarPlayer, LineComposeBarPlayer

##########################################
#               Note Values              #
# Written in (pitch, start beat, length) #
##########################################
chords = {
    "Chainsmokers": {
        1: {
            "midi" : [
                (37,0,2.5), (44,0,2.5), (53,0,2.5), (56,0,2.5), (63,0,2.5),  
                (39,2.5,1.5), (46,2.5,1.5), (55,2.5,1.5), (58,2.5,1.5), (63,2.5,1.5), 
                (41,4,2.5), (48,4,2.5), (56,4,2.5), (60,4,2.5), (63,4,2.5), 
                (39,6.5,1.5), (46,6.5,1.5), (55,6.5,1.5), (58,6.5,1.5), (63,6.5,1.5),

                (37,8,2.5), (44,8,2.5), (53,8,2.5), (56,8,2.5), (63,8,2.5),  
                (39,10.5,1.5), (46,10.5,1.5), (55,10.5,1.5), (58,10.5,1.5), (63,10.5,1.5), 
                (41,12,2.5), (48,12,2.5), (56,12,2.5), (60,12,2.5), (63,12,2.5), 
                (39,14.5,1.5), (46,14.5,1.5), (55,14.5,1.5), (58,14.5,1.5), (63,14.5,1.5)
                ],
            "pitches": [37, 39, 41, 44, 46, 48, 53, 55, 56, 58, 60, 63]
        },
        2: {
            "midi" : [
                (37,0,1), (44,0,1), (53,0,1), (56,0,1), (63,0,1),
                (39,5,1), (46,5,1), (55,5,1), (58,5,1), (63,5,1),
                (39,6,1), (46,6,1), (55,6,1), (58,6,1), (63,6,1),
                (41,8,1), (48,8,1), (56,8,1), (60,8,1), (63,8,1), 
                (39,13,1), (46,13,1), (55,13,1), (58,13,1), (63,13,1),
                (39,14,1), (46,14,1), (55,14,1), (58,14,1), (63,14,1),
                (39,15,1), (46,15,1), (55,15,1), (58,15,1), (63,15,1)
                ],
            "pitches": [37, 39, 41, 44, 46, 48, 53, 55, 56, 58, 60, 63]
        }
    }
}

percussion = {
    "Chainsmokers": {
        1: {
            "midi" : [
                (35,0,1), (35,1,1), (38,1,1), (44,1,1), (35,2.5,.5), (44,2.5,.5), (35,3,.5), (44,3,.5),
                (35,4,1), (35,5,1), (38,5,1), (44,5,1), (35,6.5,.5), (44,6.5,.5), (35,7,.5), (44,7,.5),
                (35,8,1), (35,9,1), (38,9,1), (44,9,1), (35,10.5,.5), (44,10.5,.5), (35,11,.5), (44,11,.5),
                (35,12,1), (35,13,1), (38,13,1), (44,13,1), (35,14.5,.5), (44,14.5,.5), (35,15,.5), (44,15,.5)
                ],
            "pitches": [35, 38, 44]
        }
    }
}

melody = {
    "Chainsmokers": {
        1: {
            "changes": [(0, 16, [63,68,70,72,75])],
            "pitches": [63,68,70,72,75]
        }
    }
}

tempos = {
    "Chainsmokers": 95*2
}

class StyleSelection(FloatLayout):
    def __init__(self, styleCallback):
        super(StyleSelection, self).__init__()
        
        self.label = topleft_label()
        self.label.text = "Select the style of music that you would like to replicate."
        self.add_widget(self.label)

        self.orientation = "vertical"
        #size = (1, .5)

        b1 = Button(text="Chainsmokers", size_hint = (None, None), size = (300, 50), pos = (Window.width/2-150, Window.height/2))
        b1.bind(on_press=styleCallback)
        self.option1 = b1

        b2 = Button(text="Fake", size_hint = (None, None), size = (300, 50), pos = (Window.width/2-150, Window.height/2 - 200))
        # b2.bind(on_press=styleCallback)
        self.option2 = b2
        
        self.add_widget(self.option1)
        self.add_widget(self.option2)

class ChordSelection(FloatLayout):
    def __init__(self, chordCallback):
        super(ChordSelection, self).__init__()
        
        self.orientation = "vertical"

        self.label = topleft_label()
        self.label.text = "Select the chords you would like to use."
        self.add_widget(self.label)

        b1 = Button(text="1", size_hint = (None, None), size = (300, 50), pos = (Window.width/2-150, Window.height/2))
        b1.bind(on_press=chordCallback)
        self.option1 = b1

        b2 = Button(text="2", size_hint = (None, None), size = (300, 50), pos = (Window.width/2-150, Window.height/2 - 200))
        b2.bind(on_press=chordCallback)
        self.option2 = b2
        
        self.add_widget(self.option1)
        self.add_widget(self.option2)

class PercSelection(FloatLayout):
    def __init__(self, percCallback):
        super(PercSelection, self).__init__()
        
        self.orientation = "vertical"
        size = (1, 1)

        self.label = topleft_label()
        self.label.text = "Select the percussion you would like to use."
        self.add_widget(self.label)

        b1 = Button(text="1", size_hint = (None, None), size = (300, 50), pos = (Window.width/2-150, Window.height/2))
        b1.bind(on_press=percCallback)
        self.option1 = b1

        b2 = Button(text="Fake", size_hint = (None, None), size = (300, 50), pos = (Window.width/2-150, Window.height/2 - 200))
        b2.bind(on_press=percCallback)
        self.option2 = b2
        
        self.add_widget(self.option1)
        self.add_widget(self.option2)


class MelodySelection(Widget):
    def __init__(self, synth, sched, chords, perc, melody):
        super(MelodySelection, self).__init__()
        w = Window.width
        h = Window.height
        padding = 50
        
        # Audio Generation
        self.synth = synth
        self.sched = sched

        halfHeight = (h - 4*padding) / 2
        quarterHeight = halfHeight / 2
        paddedWidth = w - 2*padding

        botBarPlayerPos = (padding,padding)
        botBarPlayerSize = (paddedWidth, quarterHeight)
        #def __init__(self, botLeft, size, sched, synth, channel, program, notes, posPitches, velocity):
        self.botBPlayer = StaticBarPlayer(botBarPlayerPos, botBarPlayerSize, self.sched, self.synth, 2, (128,0), perc['midi'], perc['pitches'], 100)

        midBarPlayerPos = (padding, 2*padding + quarterHeight)
        midBarPlayerSize = (paddedWidth, quarterHeight)
        self.midBPlayer = StaticBarPlayer(midBarPlayerPos, midBarPlayerSize, self.sched, self.synth, 1, (0,0), chords['midi'], chords['pitches'], 60)

        #def __init__(self, botLeft, size, sched, synth, channel, program, changes, allPitches, velocity):
        compBarPlayerPos = (padding, 3*padding + 2*quarterHeight)
        compBarPlayerSize = (paddedWidth, halfHeight)
        self.compBPlayer = LineComposeBarPlayer(compBarPlayerPos, compBarPlayerSize, self.sched, self.synth, 1, (0,0), melody['changes'], melody['pitches'], 110)

        self.canvas.add(self.botBPlayer)
        self.canvas.add(self.midBPlayer)
        self.canvas.add(self.compBPlayer)
    
    def on_touch_down(self, touch):
        self.compBPlayer.on_touch_down(touch)
    
    def on_touch_move(self, touch):
        self.compBPlayer.on_touch_move(touch)

    def on_layout(self, win_size):
        w = win_size[0]
        h = win_size[1]
        padding = 50
        halfHeight = (h - 4*padding) / 2
        quarterHeight = halfHeight / 2
        paddedWidth = w - 2*padding


        botBarPlayerPos = (padding,padding)
        botBarPlayerSize = (paddedWidth, quarterHeight)
        #def resize(self, newSize, botLeft):
        self.botBPlayer.resize(botBarPlayerSize, botBarPlayerPos)

        midBarPlayerPos = (padding, 2*padding + quarterHeight)
        midBarPlayerSize = (paddedWidth, quarterHeight)
        self.midBPlayer.resize(midBarPlayerSize, midBarPlayerPos)

        compBarPlayerPos = (padding, 3*padding + 2*quarterHeight)
        compBarPlayerSize = (paddedWidth, halfHeight)
        self.compBPlayer.resize(compBarPlayerSize, compBarPlayerPos)

    def on_key_down(self, keycode, modifiers):
        self.compBPlayer.on_key_down(keycode, modifiers)
        if keycode[1] == 'q':
            self.midBPlayer.play()
            self.botBPlayer.play()
            self.compBPlayer.play()
        elif keycode[1] == 'e':
            self.midBPlayer.toggle()
            self.botBPlayer.toggle()
            self.compBPlayer.toggle()
        elif keycode[1] == 'z':
            self.botBPlayer.clear_note_graphics()
        elif keycode[1] == 'x':
            self.botBPlayer.display_note_graphics()
        elif keycode[1] == 'a':
            self.compBPlayer.process()
        elif keycode[1] == 's':
            self.compBPlayer.clear_raw_notes()
    def on_update(self):
        self.audio.on_update()


class MainWidget(BaseWidget):
    def __init__(self):
        super(MainWidget, self).__init__()

        self.audio = Audio(2)
        self.synth = Synth('../data/FluidR3_GM.sf2')

        # create TempoMap, AudioScheduler
        self.tempo_map = SimpleTempoMap(95*2)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        # create the metronome:
        self.metro = Metronome(self.sched, self.synth)

        # create the different screens
        self.style_selection = StyleSelection(self.update_style)
        self.chord_selection = ChordSelection(self.update_chords)
        self.perc_selection = PercSelection(self.update_perc)

        # variables to store options
        self.style = None
        self.chords = None
        self.perc = None

        self.melody_selection = None

        self.active_screen = self.style_selection
        self.add_widget(self.active_screen)

    def update_style(self, instance):
        self.style = instance.text
        self.change_screens(self.chord_selection)

    def update_chords(self, instance):
        self.chords = int(instance.text)
        self.change_screens(self.perc_selection)
    
    def update_perc(self, instance):
        self.perc = int(instance.text)
        self.remove_widget(self.active_screen)

        self.melody_selection = MelodySelection(
            self.synth, 
            self.sched, 
            chords[self.style][self.chords], 
            percussion[self.style][self.perc],
            melody[self.style][1]
            )

        self.active_screen = self.melody_selection
        self.add_widget(self.active_screen)

    #def on_layout(self, win_size):
        #self.active_screen.on_layout(win_size)

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

    def on_update(self):
        self.audio.on_update()

if __name__ == "__main__":
    # pass in which MainWidget to run as a command-line arg
    run(eval('MainWidget'))