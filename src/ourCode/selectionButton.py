import sys
sys.path.append('..')
# from common.gfxutil import topleft_label, CEllipse, KFAnim, AnimGroup

from kivy.uix.button import Button
# from kivy.graphics.instructions import InstructionGroup
#from kivy.graphics import Color, Ellipse, Rectangle, Triangle, Line
# from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate

import random
from noteSequencer import NoteSequencer

#Get colors of pitches
def color(pitch): 
    red = 0
    blue = 0
    green = 0
    if pitch in [5, 0, 7, 2, 10, 12]: 
        red = 1
    elif pitch == 9 or pitch == 3: 
        red = 0.5
    if pitch in [2, 9, 4, 11, 6]: 
        green = 1
    elif pitch == 7 or pitch == 1: 
        green = 0.5
    if pitch in [6, 1, 8, 3, 10]: 
        blue = 1
    if pitch == 11 or pitch == 5: 
        blue = 0.5
    return (red, green, blue, 1)

class SelectionButton(Button):
    def __init__(self, text, size, pos, onclick_callback, sched, synth, channel, program, notes, velocity, option, systems):
        super(SelectionButton, self).__init__()

        self.notes = notes
        self.systems = systems
        self.noteSeq = NoteSequencer(sched, synth, channel, program, notes, velocity, loop=True)
        self.hovering = False

        # self.button = Button(text=text, size_hint = (None, None), size = size, pos = pos)
        self.text = text
        self.size_hint = (None, None)
        self.size = size
        self.pos = pos
        # self.bind(on_press=onclick_callback)
        self.callback = onclick_callback
        self.option = option

    def play(self):
        self.noteSeq.start()
        for system in self.systems: 
            system.start()

    def stop(self):
        self.noteSeq.stop()
        for system in self.systems: 
            system.stop()
    
    def currently_playing_pitches(self): 
        now = self.noteSeq.sched.get_tick()
        st = self.noteSeq.next_beat

        cp = []
        for note in self.notes: 
            #print(now, note[1] * 480, )
            if note[1] * 480 < (now - st) and (note[1] + note[2]) * 480 > (now - st): 
                cp.append(note[0])
        return cp

    def on_update(self, pos):
        # test if mouse is hovering over button
        x, y = pos

        for i in self.systems: 

            current = self.currently_playing_pitches()
            if (len(current) > 0): 
                i.start_color = color(current[int(random.random()*len(current))] % 12)
            else: 
                i.start_color = (0, 0, 0, 1)

        if self.collide_point(x, y) and not self.hovering:
            self.hovering = True
            self.play()
        elif not self.collide_point(x, y) and self.hovering:
            self.hovering = False
            self.stop()

    def on_touch_down(self, touch):
        x, y = touch.pos
        if self.collide_point(x, y):
            self.callback(self.option)
            self.stop()


class BetterButton(Button):
    def __init__(self, text, size, pos, onclick_callback, callbackThing=None):
        super(BetterButton, self).__init__()

        self.text = text
        self.size_hint = (None, None)
        self.size = size
        self.pos = pos
        self.callback = onclick_callback
        self.callbackThing = callbackThing

        if callbackThing == None:
            self.callbackThing = self.text

    def on_touch_down(self, touch):
        x, y = touch.pos
        if self.collide_point(x, y):
            if self.callbackThing:
                self.callback(self.callbackThing)
            else:
                self.callback()

    def update_callback(self, func):
        self.callback = func

    def on_update(self):
        return