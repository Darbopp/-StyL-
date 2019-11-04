
import sys
sys.path.append('..')
from common.core import BaseWidget, run, lookup
from common.gfxutil import topleft_label, CEllipse, KFAnim, AnimGroup
from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.uix.label import Label
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Triangle, Line
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate


class NoteShape(InstructionGroup):
    def __init__(self, botLeftPos, noteLength, qNoteLength = 40):
        super(NoteShape, self).__init__()

        #noteLength passed in incase we want to change shape based on length

        w = Window.width

        self.height = qNoteLength * abs(noteLength)
        self.width = qNoteLength * abs(noteLength)

        leftX = botLeftPos[0]
        #botY = botLeftPos[1]

        self.shape = Rectangle(pos = botLeftPos, size=(self.width, self.height))

        colorChange = leftX / w
        hue = .6 + .5 * (colorChange) 
        self.color = Color(hsv=(hue, 1, 1), a=1)

        self.add(self.color)
        self.add(self.shape)

class ComposeNoteShape(InstructionGroup):
    def __init__(self, centerPos, noteLength, quarterNoteWidth):
        super(ComposeNoteShape, self).__init__()

        #noteLength passed in incase we want to change shape based on length
        w = Window.width

        self.height = quarterNoteWidth * abs(noteLength)
        self.width = quarterNoteWidth * abs(noteLength)

        leftX = centerPos[0] - (self.width/2)
        botY = centerPos[1] - (self.height/2)

        self.shape = None

        if noteLength < 0:
            self.shape = Rectangle(pos = (leftX, botY), size=(self.width, self.height))
        else:
            self.shape = CEllipse(cpos=centerPos, csize=(self.width,self.height), segments = 40)

        colorChange = leftX / w
        hue = .6 + .5 * (colorChange) 
        self.color = Color(hsv=(hue, 1, 1), a=1)

        self.add(self.color)
        self.add(self.shape)

class BeatBar(InstructionGroup):
    def __init__(self, botPos, height):
        super(BeatBar, self).__init__()

        #noteLength passed in incase we want to change shape based on length

        self.shape = Line(points=[botPos[0],botPos[1],botPos[0],botPos[1] + height], width=2)

        self.color = Color(rbg=(1, 1, 1), a=1)

        self.add(self.color)
        self.add(self.shape)