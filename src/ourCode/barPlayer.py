
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
from kivy.core.window import Window
from noteSequencer import NoteSequencer

from rules import DownBeatChordToneRule

import numpy as np

def clr(pitch, alpha, program): 
    if program[0] == 128: 
        return (1, 1, 1, 0.5)
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

        self.botLeft = botLeft
        self.size = size
        self.width = size[0]
        self.height = size[1]

class LineComposeBarPlayer(BarPlayer):
    def __init__(self, botLeft, size, sched, synth, channel, program, changes, allPitches, scaleNotes, velocity, doneCallback):
        super(LineComposeBarPlayer, self).__init__(botLeft, size, sched, synth, channel, program)

        self.rawNotes = [] #[(relX, relY, len)]
        self.notes = [] #[(pitch, startBeat, len)]  len is on the -4,-2,-1,-.5,0,.5,1,2,4 scale, negative numbers are rests
        self.graphicNotes = [] #list of all graphic notes so we can remove them if needed
        #a list of all the possible Pitches. Important to sort to get correct relative layout
        self.possiblePitches = sorted(allPitches)
        self.scaleNotes = sorted(scaleNotes)
        self.beatBars = []

        self.doneCallback = doneCallback
        
        
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


        self.color = Color(hsv=(.1, .1, .1), a=1)
        self.background = Rectangle(pos=self.botLeft, size=self.size)
        self.qNoteWidth = 40

        self.add(self.color)
        self.add(self.background)

        self.display_note_graphics()

        # def __init__(self, sched, synth, channel, program, notes, velocity, loop=True, callback = None):
        self.noteSeq = NoteSequencer(self.sched, self.synth, self.channel, self.program, self.notes, self.velocity, False, self.noteSeq_done_callback)

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

    def noteSeq_done_callback(self):
        self.doneCallback()

    def set_changes(self, changes):
        self.changes = changes

    def set_allPitches(self, allPitches):
        self.possiblePitches = sorted(allPitches)

    def set_scaleNotes(self, scaleNotes):
        self.scaleNotes = sorted(scaleNotes)

    def play(self):
        self.noteSeq.change_notes(self.notes)
        self.noteSeq.start()
    
    def toggle(self):
        self.noteSeq.toggle()

    def stop(self):
        self.noteSeq.stop()

    def toggle_select_mode(self):
        if not self.isClicking:
            self.isSelecting = not self.isSelecting
        else:
            self.isMarkedToSelectToggle = not self.isMarkedToSelectToggle


    def process(self):
        self.clear_note_graphics()
        self.resample_lines()
        self.lines_to_notes()
        self.apply_rules()
        self.noteSeq.change_notes(self.notes)
        self.display_note_graphics()

    def set_notes(self, newNotes):
        self.notes = newNotes

    def set_pitches(self, newPitches):
        self.possiblePitches = sorted(newPitches)

    def clear_raw_notes(self):
        self.rawNotes = []
    
    def clear_real_notes(self):
        self.notes = []

    def update_seq_notes(self):
        self.noteSeq.change_notes(self.notes)

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
            #print(note)
            beatAndPitch = (note[1], note[0])
            color = clr(note[0] % 12, 0.5, self.program)
            relativeNoteCoords = self.note_to_coord(beatAndPitch) #get our relative coords
            absCoords = (relativeNoteCoords[0]+self.botLeft[0], relativeNoteCoords[1]+self.botLeft[1]) # get screen coords
            
            xRange = self.width - 2*20 #+ noteWidth
            sizePerBeat = xRange / 16
            noteGraphic = NoteShape(absCoords, note[2], relativeNoteCoords[2], note, color = color, qNoteLength = sizePerBeat)

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
        if self.selectionBox != None:
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
        
        #numBuckets = len(self.scaleNotes)
        numBuckets = len(self.possiblePitches)
        sizePerBucket = height/numBuckets
        noteBucket = int(rawY // sizePerBucket)
        #print("scale Notes: ", self.scaleNotes)
        # print("Possible Notes: ", self.possiblePitches)
        # print("rawY: ", rawY)
        # print("height: ", height)
        #pitch = self.scaleNotes[noteBucket]
        pitch = self.possiblePitches[noteBucket]
        #print("pitch: ", pitch)

        return pitch

    def resample_lines(self):
        if len(self.lines) == 0: 
            return 

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

        def is_rest(index):
            restThresh = 20
            xVal = outX[index]
            if xVal < allX[0]:
                return True
            for i, x in enumerate(allX):
                if x > xVal:
                    if abs(x-xVal) > restThresh and abs(allX[i-1] - xVal) > restThresh:
                        return True
                    else:
                        return False
            return False
    
        #self.add(Color(1,.5,.2))
        #discretize plot
        self.clear_lines()
        #difference in Y that gets absorbed
        threshold = Window.height / 40
        #threshold = Window.height
        lastYVal = None
        for index,yVal in enumerate(outY):
            xVal = outX[index]
            if is_rest(index):
                if lastYVal is not None:
                    lastYVal = None
            else:
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


        #cull the baddies
        real_discrete_lines = []
        length_thresh = 10
        for line in self.discreteLines:
            points = line.points
            if abs(points[0] - points[-2]) > length_thresh:
                real_discrete_lines.append(line)
        self.discreteLines = real_discrete_lines

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

            # beginX = max(min(rawLine.points[0]-sizePerBeat,self.width-2*leftRightPadding), leftRightPadding) -10
            # beginY = max(min(rawLine.points[1]-self.botLeft[1],self.height-2*topBottomPadding), topBottomPadding)
            # endX = max(min(rawLine.points[-2]-sizePerBeat,self.width), leftRightPadding) -10
            # endY = max(min(rawLine.points[-1]-self.botLeft[1],self.height-2*topBottomPadding), topBottomPadding)

            beginX = max(min(rawLine.points[0],self.width-2*leftRightPadding), leftRightPadding) -10
            beginY = max(min(rawLine.points[1]-self.botLeft[1],self.height-2*topBottomPadding), topBottomPadding)
            endX = max(min(rawLine.points[-2],self.width), leftRightPadding) -10
            endY = max(min(rawLine.points[-1]-self.botLeft[1],self.height-2*topBottomPadding), topBottomPadding)            

            #beginX = max(min(rawLine.points[0]-sizePerEigth,self.width-2*leftRightPadding), leftRightPadding) #-10
            #beginY = max(min(rawLine.points[1]-self.botLeft[1],self.height-2*topBottomPadding), topBottomPadding)
            #endX = max(min(rawLine.points[-2]-sizePerEigth,self.width), leftRightPadding) #-10
            #endY = max(min(rawLine.points[-1]-self.botLeft[1],self.height-2*topBottomPadding), topBottomPadding)

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
        #print("IM UP OKAY MOM")
        p = touch.pos

        if self.isSelecting:
            #find notes selected and highlight them
            if self.selectionBox is not None:
                self.select_notes()
                self.remove(self.selectionBox)
                self.selectionBox = None

        self.isClicking = False
        if self.isMarkedToSelectToggle:
            self.isSelecting = not self.isSelecting
            self.isMarkedToSelectToggle = False

    def do_v_b(self):
        self.resample_lines()
        self.lines_to_notes()
        self.display_note_graphics()

    def do_n(self):
        self.clear_note_graphics()
        self.apply_rules()
        self.noteSeq.change_notes(self.notes)
        self.display_note_graphics()

    def do_m(self):
        self.clear_note_graphics()
        self.resample_lines()
        self.lines_to_notes()
        self.apply_rules()
        self.noteSeq.change_notes(self.notes)
        self.display_note_graphics()

    def on_key_down(self, keycode, modifiers):
        
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
            self.clear_note_graphics()
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
        topBottomPadding = 5
        numBeats = 4*4
        noteHeight = 40 #added to take into account the height when determining ranges
        noteWidth = 40 # added to take into account the width when determining ranges

        xRange = self.width - 2*leftRightPadding
        yRange = self.height - 2*topBottomPadding

        sizePerBeat = xRange / numBeats
        sizePerPitch = yRange / len(self.possiblePitches)


        xVal = (sizePerBeat * beatAndPitch[0]) + leftRightPadding 
        yVal = (sizePerPitch * self.possiblePitches.index(beatAndPitch[1])) + topBottomPadding

        return (xVal, yVal, sizePerPitch)



class StaticBarPlayer(BarPlayer):
    def __init__(self, botLeft, size, sched, synth, channel, program, notes, posPitches, velocity):
        super(StaticBarPlayer, self).__init__(botLeft, size, sched, synth, channel, program)

        self.notes = notes #[(pitch, startBeat, len)]  len is on the -4,-2,-1,-.5,0,.5,1,2,4 scale, negative numbers are rests
        self.graphicNotes = [] #list of all graphic notes so we can remove them if needed
        #a list of all the possible Pitches. Important to get correct relative layout
        self.possiblePitches = sorted(posPitches)
        self.size = size

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

    def stop(self):
        self.noteSeq.stop()

    def set_notes(self, newNotes):
        self.notes = newNotes
        self.noteSeq.change_notes(newNotes)

    def set_pitches(self, newPitches):
        self.possiblePitches = sorted(newPitches)

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
            color = clr(note[0] % 12, 0.5, self.program)
            relativeNoteCoords = self.note_to_coord(beatAndPitch) #get our relative coords
            absCoords = (relativeNoteCoords[0]+self.botLeft[0], relativeNoteCoords[1]+self.botLeft[1]) # get screen coords
            xRange = self.width - 2*20 #+ noteWidth
            sizePerBeat = xRange / 16
            noteGraphic = NoteShape(absCoords, note[2], relativeNoteCoords[2], color = color, qNoteLength = sizePerBeat)

            self.add(noteGraphic)
            self.graphicNotes.append(noteGraphic)

    '''
    Determines where the note should be in relative coords based on what beat the note starts on and the midiPitch
    Input: beatAndPitch - (startBeat, MIDIPitch)
    '''
    def note_to_coord(self, beatAndPitch):
        leftRightPadding = 20
        topBottomPadding = 5
        numBeats = 4*4
        noteHeight = 40 #added to take into account the height when determining ranges
        noteWidth = 40 # added to take into account the width when determining ranges

        xRange = self.size[0] - 2*leftRightPadding #+ noteWidth
        yRange = self.size[1] - 2*topBottomPadding

        sizePerBeat = xRange / numBeats
        sizePerPitch = yRange / len(self.possiblePitches)

        xVal = (sizePerBeat * beatAndPitch[0]) + leftRightPadding 
        yVal = (sizePerPitch * self.possiblePitches.index(beatAndPitch[1])) + topBottomPadding

        return (xVal, yVal,sizePerPitch)




