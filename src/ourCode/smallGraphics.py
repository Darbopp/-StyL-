

import sys
sys.path.append('..')
from common.core import BaseWidget, run, lookup
from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.uix.label import Label
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Triangle, Line
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate


class NoteShape(InstructionGroup):
    def __init__(self, botLeftPos, noteLength):
        super(NoteShape, self).__init__()

        #noteLength passed in incase we want to change shape based on length

        w = Window.width

        self.height = 20
        self.width = 20

        leftX = botLeftPos[0]
        #botY = botLeftPos[1]

        self.shape = Rectangle(pos = botLeftPos, size=(self.width, self.height))

        colorChange = leftX / w
        hue = .6 + .5 * (colorChange) 
        self.color = Color(hsv=(hue, 1, 1), a=1)

        self.add(self.color)
        self.add(self.shape)
