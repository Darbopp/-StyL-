
import sys
sys.path.append('..')
from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.synth import Synth
from common.gfxutil import topleft_label
from common.clock import Clock, SimpleTempoMap, AudioScheduler, kTicksPerQuarter, quantize_tick_up
from common.metro import Metronome

from smallGraphics import NoteShape
from kivy.graphics import Color, Ellipse, Rectangle, Triangle, Line
from kivy.graphics.instructions import InstructionGroup

from noteSequencer import NoteSequencer

class BarPlayer(InstructionGroup) :

    def __init__(self, botLeft, size, sched, synth, channel=0, program=(0,40)):
        super(BarPlayer, self).__init__()

        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program

        self.currentNoteLength = 1
        self.botLeft = botLeft
        self.size = size
        self.width = size[0]
        self.height = size[1]

       
    '''
    Given any screen coordinate, return that coordinate realtive to me
    My Bottom Left corner is considered relative (0,0)

    This function can return negative values
    '''
    def screen_coords_to_me_coords(self, coord):
        newX = coord[0] - self.botLeft[0]
        newY = coord[1] - self.botLeft[1]
        return (newX, newY)


    def is_touch_on_me(self, touch):
        relCoord = self.screen_coords_to_me_coords(touch)
        if not (relCoord[0] < 0 or relCoord[0] > self.width or 
            relCoord[1] < 0 or relCoord[1] > self.height):
            print("ehhlo")
            #do something


    def on_touch_down(self, touch):

        if self.is_touch_on_me(touch) :
            print("hello")




class StaticBarPlayer(BarPlayer):
    def __init__(self, botLeft, size, sched, synth, channel, program, notes, posPitches, velocity):
        super(StaticBarPlayer, self).__init__(botLeft, size, sched, synth, channel, program)

        self.notes = notes #[(pitch, startBeat, len)]  len is on the -4,-2,-1,-.5,0,.5,1,2,4 scale, negative numbers are rests
        self.graphicNotes = [] #list of all graphic notes so we can remove them if needed
        #a list of all the possible Pitches. Important to get correct relative layout
        self.possiblePitches = sorted(posPitches)

        self.velocity = velocity #volume

        self.color = Color(hsv=(.1, .1, .1), a=1)
        self.background = Rectangle(pos=self.botLeft, size=self.size)

        self.add(self.color)
        self.add(self.background)

        self.display_note_graphics()

        # def __init__(self, sched, synth, channel, program, notes, velocity, loop=True, callback = None):
        self.noteSeq = NoteSequencer(self.sched, self.synth, self.channel, self.program, self.notes, self.velocity)


    def play(self):
        self.noteSeq.start()
    
    def toggle(self):
        self.noteSeq.toggle()

    def set_notes(self, newNotes):
        self.notes = newNotes

    def set_pitches(self, newPitches):
        self.pitches = sorted(newPitches)

    '''
    Clears the note graphics. Should be used when notes is changed
    '''
    def clear_note_graphics(self):
        for gNote in self.graphicNotes:
            self.remove(gNote)
    
    def display_note_graphics(self):
        for note in self.notes: #[(pitch, startBeat, len)]
            beatAndPitch = (note[1], note[0])
            relativeNoteCoords = self.note_to_coord(beatAndPitch) #get our relative coords
            absCoords = (relativeNoteCoords[0]+self.botLeft[0], relativeNoteCoords[1]+self.botLeft[1]) # get screen coords
            noteGraphic = NoteShape(absCoords, note[2])

            self.add(noteGraphic)
            self.graphicNotes.append(noteGraphic)

    '''
    Determines where the note should be in relative coords based on what beat the note starts on and the midiPitch
    Input: beatAndPitch - (startBeat, MIDIPitch)
    '''
    def note_to_coord(self, beatAndPitch):
        leftRightPadding = 20
        topBottomPadding = 10
        numBeats = 4*4
        noteHeight = 20 #added to take into account the height when determining ranges
        noteWidth = 20 # added to take into account the width when determining ranges

        xRange = self.width - 2*leftRightPadding + noteWidth
        yRange = self.height - 2*topBottomPadding - noteHeight

        sizePerBeat = xRange / numBeats
        sizePerPitch = yRange / len(self.possiblePitches)

        xVal = (sizePerBeat * beatAndPitch[0]) + leftRightPadding 
        yVal = (sizePerPitch * self.possiblePitches.index(beatAndPitch[1])) + topBottomPadding

        return (xVal, yVal)




