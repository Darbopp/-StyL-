import sys
sys.path.append('..')
# from common.gfxutil import topleft_label, CEllipse, KFAnim, AnimGroup

from kivy.uix.button import Button
# from kivy.graphics.instructions import InstructionGroup
# from kivy.graphics import Color, Ellipse, Rectangle, Triangle, Line
# from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate

from noteSequencer import NoteSequencer


class SelectionButton(Button):
    def __init__(self, text, size, pos, onclick_callback, sched, synth, channel, program, notes, velocity):
        super(SelectionButton, self).__init__()

        self.noteSeq = NoteSequencer(sched, synth, channel, program, notes, velocity, loop=True)
        self.hovering = False

        # self.button = Button(text=text, size_hint = (None, None), size = size, pos = pos)
        self.text = text
        self.size_hint = (None, None)
        self.size = size
        self.pos = pos
        # self.bind(on_press=onclick_callback)
        self.callback = onclick_callback

    def play(self):
        self.noteSeq.start()

    def stop(self):
        self.noteSeq.stop()
    
    def on_update(self, pos):
        # test if mouse is hovering over button
        x, y = pos

        if self.collide_point(x, y) and not self.hovering:
            self.hovering = True
            self.play()
        elif not self.collide_point(x, y) and self.hovering:
            self.hovering = False
            self.stop()

    def on_touch_down(self, touch):
        x, y = touch.pos
        if self.collide_point(x, y):
            self.callback(self)
            self.stop()