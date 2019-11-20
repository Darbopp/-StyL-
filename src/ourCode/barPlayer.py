
import sys
sys.path.append('..')
from common.core import BaseWidget, run, lookup
from common.gfxutil import topleft_label, CEllipse, KFAnim, AnimGroup
from common.audio import Audio
from common.synth import Synth
from common.clock import Clock, SimpleTempoMap, AudioScheduler, kTicksPerQuarter, quantize_tick_up
from common.metro import Metronome

from smallGraphics import NoteShape, ComposeNoteShape, BeatBar, SelectionBox
from kivy.graphics import Color, Ellipse, Rectangle, Triangle, Line
from kivy.graphics.instructions import InstructionGroup

from noteSequencer import NoteSequencer

from rules import DownBeatChordToneRule

import numpy as np

def clr(pitch, alpha): 
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
    return (red, green, blue, alpha)


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

class LineComposeBarPlayer(BarPlayer):
    def __init__(self, botLeft, size, sched, synth, channel, program, changes, allPitches, scaleNotes, velocity):
        super(LineComposeBarPlayer, self).__init__(botLeft, size, sched, synth, channel, program)

        self.rawNotes = [] #[(relX, relY, len)]
        self.notes = [] #[(pitch, startBeat, len)]  len is on the -4,-2,-1,-.5,0,.5,1,2,4 scale, negative numbers are rests
        self.graphicNotes = [] #list of all graphic notes so we can remove them if needed
        #a list of all the possible Pitches. Important to sort to get correct relative layout
        self.possiblePitches = sorted(allPitches)
        self.scaleNotes = sorted(scaleNotes)
        self.beatBars = []
        
        
        self.lines = []
        self.discreteLines = []
        self.currLine = None

        self.isClicking = True
        self.isSelecting = False
        self.isMarkedToSelectToggle = False
        self.selectionBox = None
        self.selectedNotes = []


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

        self.create_beat_bars()

        '''
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
        '''


    def play(self):
        self.noteSeq.start()
    
    def toggle(self):
        if len(self.rawNotes) != len(self.notes):
            self.clear_real_notes()
            self.process()

        self.noteSeq.toggle()

    def toggle_select_mode(self):
        if not self.isClicking:
            self.isSelecting = not self.isSelecting
        else:
            self.isMarkedToSelectToggle = not self.isMarkedToSelectToggle


    def process(self):
        self.clear_note_graphics()
        self.resample_lines()
        self.lines_to_notes()
        #self.raw_to_notes()
        self.display_note_graphics()
        self.noteSeq.change_notes(self.notes)

    def set_notes(self, newNotes):
        self.notes = newNotes

    def set_pitches(self, newPitches):
        self.possiblePitches = sorted(newPitches)

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
        self.graphicNotes=[]

    def clear_lines(self):
        self.currLine = None
        for line in self.lines:
            self.remove(line)
        self.lines=[]

    def clear_beat_bars(self):
        for bar in self.beatBars:
            self.remove(bar)
            
    def clear_discrete_lines(self):
        self.discreteLines = []
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
            self.beatBars.append(bar)
        relX = 16*sizePerBeat + startingBeat + 6
        absoluteX = relX + self.botLeft[0]
        absoluteY = self.botLeft[1]
        bar = BeatBar((absoluteX, absoluteY), self.height)
        self.add(bar)
        self.beatBars.append(bar)        
    
    def display_note_graphics(self):
        for note in self.notes: #[(pitch, startBeat, len)]
            beatAndPitch = (note[1], note[0])
            color = clr(note[0] % 12, 0.5)
            relativeNoteCoords = self.note_to_coord(beatAndPitch) #get our relative coords
            absCoords = (relativeNoteCoords[0]+self.botLeft[0], relativeNoteCoords[1]+self.botLeft[1]) # get screen coords
            noteGraphic = NoteShape(absCoords, note[2], note, color = color)

            self.add(noteGraphic)
            self.graphicNotes.append(noteGraphic)

    def display_discrete_lines(self):
        self.add(Color(1,.5,.2))
        for line in self.discreteLines:
            self.add(line)
    
    def hide_discrete_lines(self):
        for line in self.discreteLines:
            self.remove(line)

    def select_notes(self):
        selectPoints = self.selectionBox.get_points()

        for gNote in self.graphicNotes:
            if gNote.does_intersect_points(selectPoints):
                self.selectedNotes.append(gNote)
                gNote.highlight()

    def deselect_notes(self):
        for gNote in self.selectedNotes:
            gNote.unhighlight()
        self.selectedNotes = []
    
    def delete_selected_notes(self):
        #copyOfgNotes = self.graphicNotes.copy()
        self.clear_note_graphics()
        for gNote in self.selectedNotes:
            dataNote = gNote.getNote()
            self.discreteLines.remove(dataNote[3])
            #print("dataNote: ", dataNote)
            #print("notes: ", self.notes)
            self.notes.remove(dataNote)
            #copyOfgNotes.remove(gNote)

        #self.graphicNotes = copyOfgNotes
        self.noteSeq.change_notes(self.notes)
        
        self.display_note_graphics()


    def clear_all(self):
        self.hide_discrete_lines()
        self.clear_note_graphics()
        self.clear_lines()
        self.clear_real_notes()
        self.clear_raw_notes()
        self.clear_discrete_lines()

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
        self.background.pos = self.botLeft
        self.background.size = newSize

    #rounds raw to the nearest roundTo
    def round_to_beat(self, raw, roundTo):
        return roundTo * round(raw/roundTo)



    def first_round_pick_pitch(self, snappedX, rawY, height):
        def get_startBeat(elem):
            return elem[0]
        
        numBuckets = len(self.scaleNotes)
        sizePerBucket = height/numBuckets
        noteBucket = int(rawY // sizePerBucket)
        pitch = self.scaleNotes[noteBucket]

        return pitch

    def resample_lines(self):
        allPoints = []
        for line in self.lines:
            allPoints += line.points
        allX = allPoints[0::2]
        allY = allPoints[1::2]

        resampleSize = 200
        oldSize = len(allY)
        firstX = allX[0]
        lastX = allX[-1]
        xp = np.arange(resampleSize)
        xs = np.arange(firstX, lastX) #range of X's to sample from
        x = np.arange(xs.size) * resampleSize / xs.size

        outX = np.interp(xp, x, xs) #interpolation of x values
        #use the interpolated X values to evaluate Y values
        outY = np.interp(outX, allX, allY)


        #self.add(Color(1,.5,.2))
        #discretize plot
        self.clear_lines()
        threshold = 15 #difference in Y that gets absorbed
        lastYVal = None
        for index,yVal in enumerate(outY):
            xVal = outX[index]
            if lastYVal == None:
                myLine = Line(points=[xVal, yVal], width=2)
                #self.add(myLine)
                self.currLine = myLine
                self.discreteLines.append(myLine)
                lastYVal = yVal
            else:
                if abs(lastYVal-yVal) < threshold:
                    self.currLine.points += [xVal, lastYVal]
                else:
                    myLine = Line(points=[xVal, yVal], width=2)
                    #self.add(myLine)
                    self.currLine = myLine
                    self.discreteLines.append(myLine)
                    lastYVal = yVal

        #for line in self.discreteLines:
        #    self.add(line)

        #plot for testing
        '''
        for index,yVal in enumerate(outY):
            xVal = outX[index]
            dot = CEllipse(cpos=(xVal,yVal), csize=(10,10), segments=40)
            self.add(dot)
        '''


    def lines_to_notes(self):
        leftRightPadding = 20
        topBottomPadding = 10
        numBeats = 4*4
        noteHeight = self.qNoteWidth
        noteWidth = self.qNoteWidth

        xRange = self.width - 2*leftRightPadding
        yRange = self.height - 2*topBottomPadding

        sizePerBeat = xRange / numBeats
        sizePerEigth = sizePerBeat / 2
        startingBeat = 20

        for index, rawLine in enumerate(self.discreteLines):
            '''
            beginX = rawLine.points[0]
            beginY = rawLine.points[1]
            endX = rawLine.points[-2]
            endY = rawLine.points[-1]
            '''

            #print("Raw Y: ", rawLine.points[1]-self.botLeft[1])
            #print("First round Y: ", min(rawLine.points[1],self.height-2*topBottomPadding))
            #print("Second round Y: ", max(min(rawLine.points[1],self.height-2*topBottomPadding), topBottomPadding))

            beginX = max(min(rawLine.points[0]-sizePerBeat,self.width-2*leftRightPadding), leftRightPadding) -10
            beginY = max(min(rawLine.points[1]-self.botLeft[1],self.height-2*topBottomPadding), topBottomPadding)
            endX = max(min(rawLine.points[-2]-sizePerBeat,self.width), leftRightPadding) -10
            endY = max(min(rawLine.points[-1]-self.botLeft[1],self.height-2*topBottomPadding), topBottomPadding)

            eigthBeginX = self.round_to_beat(beginX, sizePerEigth) -10 #- leftRightPadding
            eigthEndX = self.round_to_beat(endX, sizePerEigth) -10 #- leftRightPadding

            pitch = self.first_round_pick_pitch(eigthBeginX, beginY-topBottomPadding, yRange)

            #noteLength = (self.round_to_beat(eigthEndX - eigthBeginX, sizePerEigth))/(2*sizePerEigth)
            noteLength = (self.round_to_beat(endX - beginX, sizePerEigth))/(2*sizePerEigth)

            #snappedBeginBeat = self.round_to_beat(eigthBeginX/sizePerBeat, .5)
            #snappedBeginBeat = self.round_to_beat(beginX/sizePerBeat, .5)
            snappedBeginBeat = eigthBeginX / (2*sizePerEigth)
            snappedBeginBeat = self.round_to_beat(snappedBeginBeat, .5)

            snappedNote = (pitch, snappedBeginBeat-.5, noteLength, rawLine)
            #print("beginX: ", beginX)
            #print("endX: ", endX)
            #print("beginY: ", beginY)
            #print("eigthBeginX: ", eigthBeginX)
            #print("eigthEndX: ", eigthEndX)
            #print("sizePerBeat: ",sizePerBeat)
            #print("noteLength: ", noteLength)
            #print("snappedBeginBeat: ", snappedBeginBeat)
            #print("")

            if noteLength > 0:
                self.notes.append(snappedNote)
        
        #print("notes: ", self.notes)



    def apply_rules(self):
        rule1 = DownBeatChordToneRule(self.notes, self.changes)

        def note_startBeat(elem):
            return elem[1]
        
        self.notes.sort(key=note_startBeat)
        #print("notes in apply: ", self.notes)

        for i in range(len(self.notes)):
            oldPitch = self.notes[i][0]
            newPitch = rule1.new_note(i)
            if oldPitch != newPitch:
                #print("ITS HAPPENING AT INDEX: ", i)
                #print("oldPitch: ", oldPitch)
                #print("newPitch: ", newPitch)
                newNote = ( newPitch, self.notes[i][1], self.notes[i][2], self.notes[i][3])
                #self.notes[i][1] = newPitch
                self.notes[i] = newNote

        #print("notes after rule: ", self.notes)
        #print("changes: ", self.changes)
        

  
    
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
        self.isClicking = True

        #Deselect any currently selected notes
        self.deselect_notes()

        if self.is_touch_on_me(p):
            if self.isSelecting:
                self.selectionBox = SelectionBox(p)
                self.add(self.selectionBox)

            else:
                self.add(Color(rgb=(1,1,1), a=1))
                myLine = Line(points=[p[0], p[1]], width = 2)
                self.add(myLine)
                self.currLine = myLine
                self.lines.append(myLine)
    
    def on_touch_move(self, touch):
        p = touch.pos
        #print("Is Selecting: ", self.isSelecting)
        if self.is_touch_on_me(p):
            if self.isSelecting:
                self.selectionBox.new_end_point(p)
            else:
                if self.currLine != None:
                    self.currLine.points = self.currLine.points + [p[0],p[1]]
    
    def on_touch_up(self, touch):
        print("IM UP OKAY MOM")
        p = touch.pos

        if self.isSelecting:
            #find notes selected and highlight them
            self.select_notes()
            self.remove(self.selectionBox)
            self.selectionBox = None

        self.isClicking = False
        if self.isMarkedToSelectToggle:
            self.isSelecting = not self.isSelecting
            self.isMarkedToSelectToggle = False



    def on_key_down(self, keycode, modifiers):
        noteLen = lookup(keycode[1], '12345678' , (.5, 1, 2, 4, -.5, -1, -2, -4))
        if noteLen is not None:
            self.currNoteLength = noteLen
        
        if keycode[1] == 'c':
            self.clear_lines()
        if keycode[1] == 'v':
            self.resample_lines()
        if keycode[1] == 'b':
            self.lines_to_notes()
            self.display_note_graphics()
        if keycode[1] == 'n':
            self.clear_note_graphics()
            self.apply_rules()
            self.noteSeq.change_notes(self.notes)
            self.display_note_graphics()
        if keycode[1] == 'k':
            self.display_discrete_lines()
        if keycode[1] == 'l':
            self.hide_discrete_lines()
        if keycode[1] == 'f':
            self.toggle_select_mode()
        if keycode[1] == 'd':
            self.delete_selected_notes()
        if keycode[1] == 'm':
            self.resample_lines()
            self.lines_to_notes()
            self.apply_rules()
            self.noteSeq.change_notes(self.notes)
            self.display_note_graphics()
        if keycode[1] == ',':
            self.clear_all()

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

        self.create_beat_bars()

        '''
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
        '''


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
            self.beatBars.append(bar)
        relX = 16*sizePerBeat + startingBeat + 6
        absoluteX = relX + self.botLeft[0]
        absoluteY = self.botLeft[1]
        bar = BeatBar((absoluteX, absoluteY), self.height)
        self.add(bar)
        self.beatBars.append(bar)        
    
    def display_note_graphics(self):
        for note in self.notes: #[(pitch, startBeat, len)]
            beatAndPitch = (note[1], note[0])
            color = clr(note[0] % 12, 0.5)
            relativeNoteCoords = self.note_to_coord(beatAndPitch) #get our relative coords
            absCoords = (relativeNoteCoords[0]+self.botLeft[0], relativeNoteCoords[1]+self.botLeft[1]) # get screen coords
            noteGraphic = NoteShape(absCoords, note[2], color = color)

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
        self.background.pos = self.botLeft
        self.background.size = newSize


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


        #print("notes: ", self.notes)


    
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

        self.background.pos = self.botLeft
        self.background.size = newSize

    '''
    Clears the note graphics. Should be used when notes is changed
    '''
    def clear_note_graphics(self):
        for gNote in self.graphicNotes:
            self.remove(gNote)
    
    def display_note_graphics(self):
        for note in self.notes: #[(pitch, startBeat, len)]
            beatAndPitch = (note[1], note[0])
            color = clr(note[0] % 12, 0.5)
            relativeNoteCoords = self.note_to_coord(beatAndPitch) #get our relative coords
            absCoords = (relativeNoteCoords[0]+self.botLeft[0], relativeNoteCoords[1]+self.botLeft[1]) # get screen coords
            noteGraphic = NoteShape(absCoords, note[2], color = color)

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




