
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
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Triangle, Line
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate

from barPlayer import StaticBarPlayer, ComposeBarPlayer

##########################################
#               Note Values              #
# Written in (pitch, start beat, length) #
##########################################
closerChords = [(37,0,2.5), (44,0,2.5), (53,0,2.5), (56,0,2.5), (63,0,2.5),  
                        (39,2.5,1.5), (46,2.5,1.5), (55,2.5,1.5), (58,2.5,1.5), (63,2.5,1.5), 
                        (41,4,2.5), (48,4,2.5), (56,4,2.5), (60,4,2.5), (63,4,2.5), 
                        (39,6.5,1.5), (46,6.5,1.5), (55,6.5,1.5), (58,6.5,1.5), (63,6.5,1.5),

                        (37,8,2.5), (44,8,2.5), (53,8,2.5), (56,8,2.5), (63,8,2.5),  
                        (39,10.5,1.5), (46,10.5,1.5), (55,10.5,1.5), (58,10.5,1.5), (63,10.5,1.5), 
                        (41,12,2.5), (48,12,2.5), (56,12,2.5), (60,12,2.5), (63,12,2.5), 
                        (39,14.5,1.5), (46,14.5,1.5), (55,14.5,1.5), (58,14.5,1.5), (63,14.5,1.5)]
closerChordPos = [37, 39, 41, 44,46,48,53,55,56,58,60,63] #All possibly values, preferable sorted

closerChords2 = [(37,0,1), (44,0,1), (53,0,1), (56,0,1), (63,0,1),
                    (39,5,1), (46,5,1), (55,5,1), (58,5,1), (63,5,1),
                    (39,6,1), (46,6,1), (55,6,1), (58,6,1), (63,6,1),
                    (41,8,1), (48,8,1), (56,8,1), (60,8,1), (63,8,1), 
                    (39,13,1), (46,13,1), (55,13,1), (58,13,1), (63,13,1),
                    (39,14,1), (46,14,1), (55,14,1), (58,14,1), (63,14,1),
                    (39,15,1), (46,15,1), (55,15,1), (58,15,1), (63,15,1)]
closerChordPos2 = [37, 39, 41, 44, 46, 48, 53, 55, 56, 58, 60, 63]

closerMelody = [(70,0,1), (72,1,1), (68,2,1), (70,3,1), 
                (70,4,1), (72,5,1), (68,6,1), (70,7,1), 
                (70,8,1), (72,9,1), (68,10,1), (70,11,1), 
                (70,12,1), (68,13,1), (68,14,1), (70,15,1)]
closerMelodyPos = [68,70,72]

closerPerc = [(35,0,1), (35,1,1), (38,1,1), (44,1,1), (35,2.5,.5), (44,2.5,.5), (35,3,.5), (44,3,.5),
                (35,4,1), (35,5,1), (38,5,1), (44,5,1), (35,6.5,.5), (44,6.5,.5), (35,7,.5), (44,7,.5),
                (35,8,1), (35,9,1), (38,9,1), (44,9,1), (35,10.5,.5), (44,10.5,.5), (35,11,.5), (44,11,.5),
                (35,12,1), (35,13,1), (38,13,1), (44,13,1), (35,14.5,.5), (44,14.5,.5), (35,15,.5), (44,15,.5)]
closerPercPos = [35, 38, 44]

compChanges2 = [(0, 16, [63,68,70,72,75])]
compPitches2 = [63,68,70,72,75]

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

class Screen1(InstructionGroup):
    def __init__(self, styleCallback):
        super(Screen1, self).__init__()
        w = Window.width
        h = Window.height
        padding = 50

        halfHeight = (h - 4*padding) / 2
        quarterHeight = halfHeight / 2

        b1 = Button(text="Chainsmokers")
        b1.bind(on_press=styleCallback("Chainsmokers"))
        b1.size = (w - 2*padding, h - 2*padding)
        b1.center = (w/2, halfHeight + quarterHeight)
        self.option1 = b1
        self.add(self.option1)


class Screen4(InstructionGroup):
    def __init__(self, synth, sched, chords, perc, melody):
        super(Screen4, self).__init__()
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
        self.compBPlayer = ComposeBarPlayer(compBarPlayerPos, compBarPlayerSize, self.sched, self.synth, 1, (0,0), melody['changes'], melody['pitches'], 110)

        self.add(self.botBPlayer)
        self.add(self.midBPlayer)
        self.add(self.compBPlayer)
    
    def on_touch_down(self, touch):
        self.compBPlayer.on_touch_down(touch)

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
        # self.screen1 = Screen1(self.update_style)
        self.screen2 = None
        self.screen3 = None

        # variables to store options
        self.style = 'Chainsmokers'
        self.chords = 2
        self.perc = 1
        self.melody = 1

        self.screen4 = Screen4(
            self.synth, 
            self.sched, 
            chords[self.style][2], 
            percussion[self.style][1],
            melody[self.style][1]
            )

        self.active_screen = self.screen4
        self.canvas.add(self.active_screen)

    def update_style(self, selection):
        self.style = selection

    def update_chords(self, selection):
        self.chords = selection
    
    def update_perc(self, selection):
        self.perc = selection

    def on_touch_down(self, touch):
        self.active_screen.on_touch_down(touch)
    
    def on_key_down(self, keycode, modifiers):
        self.active_screen.on_key_down(keycode, modifiers)

    def on_update(self):
        self.audio.on_update()
        #self.objects.on_update()

if __name__ == "__main__":
    # pass in which MainWidget to run as a command-line arg
    run(eval('MainWidget'))