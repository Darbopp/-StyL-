
import sys
sys.path.append('..')
from common.core import BaseWidget, run, lookup
from common.gfxutil import topleft_label, CEllipse, KFAnim, AnimGroup
from common.audio import Audio
from common.synth import Synth
from common.clock import Clock, SimpleTempoMap, AudioScheduler, kTicksPerQuarter, quantize_tick_up
from common.metro import Metronome

from smallGraphics import NoteShape, ComposeNoteShape, BeatBar
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

class ComposeBarPlayer(BarPlayer):
    def __init__(self, botLeft, size, sched, synth, channel, program, changes, allPitches, velocity):
        super(ComposeBarPlayer, self).__init__(botLeft, size, sched, synth, channel, program)

        self.rawNotes = [] #[(relX, relY, len)]
        self.notes = [] #[(pitch, startBeat, len)]  len is on the -4,-2,-1,-.5,0,.5,1,2,4 scale, negative numbers are rests
        self.graphicNotes = [] #list of all graphic notes so we can remove them if needed
        #a list of all the possible Pitches. Important to sort to get correct relative layout
        self.possiblePitches = sorted(allPitches)
        self.beatBars = []


        self.changes = changes #[(startBeat, len, [allowed pitches])]

        self.velocity = velocity #volume

        self.currNoteLength = 1

        self.color = Color(hsv=(.1, .1, .1), a=1)
        self.background = Rectangle(pos=self.botLeft, size=self.size)
        self.qNoteWidth = 40

        self.add(self.color)
        self.add(self.background)

        self.display_note_graphics()

        # def __init__(self, sched, synth, channel, program, notes, velocity, loop=True, callback = None):
        self.noteSeq = NoteSequencer(self.sched, self.synth, self.channel, self.program, self.notes, self.velocity)

        leftRightPadding = 20

        xRange = self.width - 2*leftRightPadding #+ noteWidth

        sizePerBeat = xRange / 16
        startingBeat = 20

        for i in range(17):
            relX = i*sizePerBeat + startingBeat
            absoluteX = relX + self.botLeft[0]
            absoluteY = self.botLeft[1]

            bar = BeatBar((absoluteX, absoluteY), self.height)
            self.add(bar)
            self.beatBar.append(bar)
        relX = 16*sizePerBeat + startingBeat + 6
        absoluteX = relX + self.botLeft[0]
        absoluteY = self.botLeft[1]
        bar = BeatBar((absoluteX, absoluteY), self.height)
        self.add(bar)
        self.beatBar.append(bar)


    def play(self):
        self.noteSeq.start()
    
    def toggle(self):
        if len(self.rawNotes) != len(self.notes):
            self.clear_real_notes()
            self.process()

        self.noteSeq.toggle()

    def process(self):
        self.clear_note_graphics()
        self.raw_to_notes()
        self.display_note_graphics()
        self.noteSeq.change_notes(self.notes)

    def set_notes(self, newNotes):
        self.notes = newNotes

    def set_pitches(self, newPitches):
        self.pitches = sorted(newPitches)

    def clear_raw_notes(self):
        self.rawNotes = []
    
    def clear_real_notes(self):
        self.notes = []

    '''
    Clears the note graphics. Should be used when notes is changed
    '''
    def clear_note_graphics(self):
        for gNote in self.graphicNotes:
            self.remove(gNote)

    def clear_beat_bars(self):
        for bar in self.beatBars:
            self.remove(bar)
            
    def create_beat_bars(self):
        leftRightPadding = 20

        xRange = self.width - 2*leftRightPadding #+ noteWidth

        sizePerBeat = xRange / 16
        startingBeat = 20

        for i in range(17):
            relX = i*sizePerBeat + startingBeat
            absoluteX = relX + self.botLeft[0]
            absoluteY = self.botLeft[1]

            bar = BeatBar((absoluteX, absoluteY), self.height)
            self.add(bar)
            self.beatBar.append(bar)
        relX = 16*sizePerBeat + startingBeat + 6
        absoluteX = relX + self.botLeft[0]
        absoluteY = self.botLeft[1]
        bar = BeatBar((absoluteX, absoluteY), self.height)
        self.add(bar)
        self.beatBar.append(bar)        
    
    def display_note_graphics(self):
        for note in self.notes: #[(pitch, startBeat, len)]
            beatAndPitch = (note[1], note[0])
            relativeNoteCoords = self.note_to_coord(beatAndPitch) #get our relative coords
            absCoords = (relativeNoteCoords[0]+self.botLeft[0], relativeNoteCoords[1]+self.botLeft[1]) # get screen coords
            noteGraphic = NoteShape(absCoords, note[2])

            self.add(noteGraphic)
            self.graphicNotes.append(noteGraphic)
    
    def resize(self, newSize, botLeft):

        self.botLeft = botLeft
        self.width = newSize[0]
        self.height = newSize[1]

        #update the displays
        self.clear_real_notes()
        self.clear_note_graphics()
        self.clear_beat_bars()
        #recreate them
        self.display_note_graphics()
        self.create_beat_bars()


    def round_to_beat(self, raw, roundTo):
        return roundTo * round(raw/roundTo)

    def pick_pitch(self, snappedX, rawY, height):
        #find right changes
        #[(startBeat, len, [allowed pitches])]
        def get_startBeat(elem):
            return elem[0]

        self.changes.sort(key=get_startBeat)

        pitch = None

        for index, change in enumerate(self.changes):
            if index == len(self.changes) -1:
                numBuckets = len(change[2])
                sizePerBucket = height/numBuckets

                noteBucket = int(rawY//sizePerBucket)
                '''
                print("Changes: ", change[2])
                print("numBuckets: ", numBuckets)
                print("height: ", height)
                print("rawY: ", rawY)
                print("sizePerBucket: ", sizePerBucket)
                print("noteBucket: ", noteBucket)
                '''

                pitch = change[2][noteBucket]
            else:
                if snappedX >= change[0] and snappedX < self.changes[index+1][0]:
                    #use this change
                    numBuckets = len(change[2])
                    sizePerBucket = height/numBuckets

                    noteBucket = int(rawY//sizePerBucket)

                    pitch = change[2][noteBucket]
        if pitch == None:
            print("why is pitch none?")
        
        return pitch


    def raw_to_notes(self):
        #self.rawNotes = [] #[(relX, relY, len)]
        #self.notes = [] #[(pitch, startBeat, len)]  len is on the -4,-2,-1,-.5,0,.5,1,2,4 scale, negative numbers are rests
        leftRightPadding = 20
        topBottomPadding = 10
        numBeats = 4*4
        noteHeight = self.qNoteWidth #added to take into account the height when determining ranges
        noteWidth = self.qNoteWidth # added to take into account the width when determining ranges

        xRange = self.width - 2*leftRightPadding #+ noteWidth
        yRange = self.height - 2*topBottomPadding #- noteHeight

        sizePerBeat = xRange / numBeats
        sizePerEigth = sizePerBeat / 2
        print("sizePerEigth: ",sizePerEigth)
        startingBeat = 20

        for index, rawNote in enumerate(self.rawNotes):

            boundedX = max(min(rawNote[0],self.width-2*leftRightPadding), leftRightPadding)
            boundedY = max(min(rawNote[1],self.height-2*topBottomPadding), topBottomPadding)
            '''
            print("Width: ", self.width)
            print("Height: ", self.height)
            print("rawX: ", rawNote[0])
            print("boundedX: ", boundedX)
            print("rawY: ", rawNote[1])
            print("boundedY: ", boundedY)
            print("sizePerEigth: ",sizePerEigth)
            '''
            eigthSnappedX = self.round_to_beat(boundedX - 10, sizePerEigth) - leftRightPadding
            print("snappedX: ", eigthSnappedX)
            pitch = self.pick_pitch(eigthSnappedX, boundedY-topBottomPadding, yRange)

            snappedBeat = self.round_to_beat(eigthSnappedX/sizePerBeat, .5)
            print("snappedBeat")

            snappedNote = (pitch, snappedBeat, rawNote[2])
            self.notes.append(snappedNote)


        print("notes: ", self.notes)


    
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
        if not (relCoord[0] < 0 or relCoord[0] > self.width or relCoord[1] < 0 or relCoord[1] > self.height):
            return True
        else:
            return False


    def on_touch_down(self, touch):
        p = touch.pos
        if self.is_touch_on_me(p):
            #def __init__(self, centerPos, noteLength, quarterNoteWidth):
            graphicNote = ComposeNoteShape(p, self.currNoteLength, self.qNoteWidth)
            self.add(graphicNote)
            self.graphicNotes.append(graphicNote)

            relCoord = self.screen_coords_to_me_coords(p)
            self.rawNotes.append((relCoord[0], relCoord[1], self.currNoteLength))
    
    def on_key_down(self, keycode, modifiers):
        noteLen = lookup(keycode[1], '12345678' , (.5, 1, 2, 4, -.5, -1, -2, -4))
        if noteLen is not None:
            self.currNoteLength = noteLen

    '''
    Determines where the note should be in relative coords based on what beat the note starts on and the midiPitch
    Input: beatAndPitch - (startBeat, MIDIPitch)
    '''
    def note_to_coord(self, beatAndPitch):
        leftRightPadding = 20
        topBottomPadding = 10
        numBeats = 4*4
        noteHeight = 40 #added to take into account the height when determining ranges
        noteWidth = 40 # added to take into account the width when determining ranges

        xRange = self.width - 2*leftRightPadding
        yRange = self.height - 2*topBottomPadding - noteHeight

        sizePerBeat = xRange / numBeats
        sizePerPitch = yRange / len(self.possiblePitches)

        xVal = (sizePerBeat * beatAndPitch[0]) + leftRightPadding 
        yVal = (sizePerPitch * self.possiblePitches.index(beatAndPitch[1])) + topBottomPadding

        return (xVal, yVal)



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

    def resize(self, newSize, botLeft):

        self.botLeft = botLeft
        self.width = newSize[0]
        self.height = newSize[1]

        #update the displays
        self.clear_note_graphics()
        #recreate them
        self.display_note_graphics()

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
        noteHeight = 40 #added to take into account the height when determining ranges
        noteWidth = 40 # added to take into account the width when determining ranges

        xRange = self.width - 2*leftRightPadding #+ noteWidth
        yRange = self.height - 2*topBottomPadding - noteHeight

        sizePerBeat = xRange / numBeats
        sizePerPitch = yRange / len(self.possiblePitches)

        xVal = (sizePerBeat * beatAndPitch[0]) + leftRightPadding 
        yVal = (sizePerPitch * self.possiblePitches.index(beatAndPitch[1])) + topBottomPadding

        return (xVal, yVal)




