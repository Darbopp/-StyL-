
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
    def __init__(self, botLeftPos, noteLength, fullNote=None, color = None, qNoteLength = 40):
        super(NoteShape, self).__init__()

        #noteLength passed in incase we want to change shape based on length

        w = Window.width

        self.height = qNoteLength * abs(noteLength)
        self.width = qNoteLength * abs(noteLength)

        self.fullNote = fullNote

        leftX = botLeftPos[0]
        #botY = botLeftPos[1]

        self.shape = Ellipse(pos = botLeftPos, size=(self.width, self.height))

        if not color: 
            colorChange = leftX / w
            hue = .6 + .5 * (colorChange) 
            self.color = Color(hsv=(hue, 1, 1), a=0.5)

        else: 
            self.color = Color(*color)

        self.add(self.color)
        self.add(self.shape)

        self.highlightColor = Color(rgb=(1,1,1), a=0)
        self.centerPos = (botLeftPos[0] + self.width/2 , botLeftPos[1] + self.height/2)
        self.highlightCircle = Line(ellipse=(botLeftPos[0], botLeftPos[1],self.width, self.height), width=2)
        
        self.add(self.highlightColor)
        self.add(self.highlightCircle)


    def highlight(self):
        self.highlightColor.a = 1

    
    def unhighlight(self):
        self.highlightColor.a = 0

    #You might need this. :(
    # https://gamedev.stackexchange.com/questions/109393/how-do-i-check-for-collision-between-an-ellipse-and-a-rectangle
    # circle collision from: http://www.jeffreythompson.org/collision-detection/circle-rect.php
    def does_intersect_points(self, points):
        radius = self.width/2

        rx = points[0]
        ry = points[1]

        cx = self.centerPos[0]
        cy = self.centerPos[1]

        testX = cx
        testY = cy

        if (cx < rx):
            testX = rx
        elif (cx > points[2]):
            testX = points[2]
        
        if (cy < ry):
            testY = ry
        elif (cy > points[3]):
            testY = points[3]
        
        distX = cx-testX
        distY = cy-testY

        distance = ((distX*distX) + (distY*distY))**(.5)
        if ( distance <= radius):
            return True
        
        return False

    def getNote(self):
        return self.fullNote

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

class SelectionBox(InstructionGroup):
    def __init__(self, startPoint):
        super(SelectionBox, self).__init__()

        self.startX = startPoint[0]
        self.startY = startPoint[1]

        self.color = Color(rbg=(.5,1,.5), a=.5)
        self.shape = Rectangle(pos=(self.startX, self.startY),size=(0,0))

        self.add(self.color)
        self.add(self.shape)

    def new_end_point(self, endPoint):
        leftX = min(endPoint[0], self.startX)
        botY = min(endPoint[1], self.startY)

        width = abs(endPoint[0] - self.startX)
        height = abs(endPoint[1] - self.startY)

        self.shape.pos = (leftX, botY)
        self.shape.size = (width, height)

    def get_points(self):
        leftX = self.shape.pos[0]
        botY = self.shape.pos[1]

        rightX = leftX + self.shape.size[0]
        topY = botY + self.shape.size[1]

        return (leftX, botY, rightX, topY)


