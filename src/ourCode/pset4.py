# pset4.py

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
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Triangle, Line
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate

# part 1: create Arpeggiator
class Arpeggiator(object):
    def __init__(self, sched, synth, channel=0, program=(0, 40), callback = None):
        super(Arpeggiator, self).__init__()
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program
        self.callback = callback

        self.pitches = []
        self.playing = False
        self.length = 240
        self.articulation = .75
        self.directionType = 'up'
        self.currDirection = 'up'

        self.cmd = None
        self.noteIndex = 0
        
    # start the arpeggiator
    def start(self):
        if self.playing:
            return

        self.playing = True

         # set up the correct sound (program: bank and preset)
        self.synth.program(self.channel, self.program[0], self.program[1])

        # find the tick of the next beat, and make it "beat aligned"
        now = self.sched.get_tick()
        next_beat = quantize_tick_up(now, self.length)

        # now, post the _noteon function (and remember this command)
        self.cmd = self.sched.post_at_tick(self._noteon, next_beat)
    
    # stop the arpeggiator
    def stop(self):
        if not self.playing:
            return

        self.playing = False

        # cancel anything pending in the future.
        self.sched.remove(self.cmd)

        # reset these so we don't have a reference to old commands.
        self.cmd = None
        #self.noteIndex = 0
    
    # pitches is a list of MIDI pitch values. For example [60 64 67 72]
    def set_pitches(self, pitches, newIndex = 0):
        self.pitches = pitches
        self.noteIndex = newIndex
    
    # length is related to speed of the notes. For example 240 represents 1/8th notes.
    # articulation is a ratio that defines how quickly the note off should follow the note on. 
    # For example, a value of 1 is a full-length note (legato) where the note off will 
    # occur <length> ticks after the note-on. A value of 0.5 will make the note shorter, 
    # where the note off will occur <length>/2 ticks after the note-on.
    def set_rhythm(self, length, articulation):
        self.length = length
        self.articulation = articulation

        #resets so we are on beat
        if self.playing:
            self.stop()
            #self.playing = False
            self.start()

    # dir is either 'up', 'down', or 'updown'
    def set_direction(self, direction):
        self.directionType = direction
        if direction == 'down':
            self.currDirection = 'down'
        else:
            self.currDirection = 'up'

    def _noteon(self, tick, ignore):
        if len(self.pitches) == 0:
            return
        # play the note right now:
        pitch = None
        #determine pitch
        if self.directionType == 'up':
            pitch = self.pitches[self.noteIndex]
            self.noteIndex = (self.noteIndex + 1) % len(self.pitches)
        
        elif self.directionType == 'down':
            pitch = self.pitches[self.noteIndex]
            self.noteIndex += -1
            if self.noteIndex < 0:
                self.noteIndex = len(self.pitches) - 1

        elif self.directionType == 'updown':
            if self.noteIndex >= len(self.pitches):
                self.noteIndex = len(self.pitches)-1
            pitch = self.pitches[self.noteIndex]
            if self.currDirection == 'up':
                if self.noteIndex == len(self.pitches) - 1:
                    self.noteIndex += -1
                    self.currDirection = 'down'
                else:
                    self.noteIndex += 1
            elif self.currDirection == 'down':
                if self.noteIndex <= 0:
                    self.noteIndex += 1
                    self.currDirection = 'up'
                else:
                    self.noteIndex += -1

        #determine length and articulation
        timeTillNextNote = self.length
        timeHeld = self.length * self.articulation

        vel = 100
        self.synth.noteon(self.channel, pitch, vel)
        if self.callback != None:
            self.callback(pitch, self.length * 2)


        # post the note off for half a beat later:
        off_tick = tick + timeHeld
        self.sched.post_at_tick(self._noteoff, off_tick, pitch)

        next_beat = tick + timeTillNextNote
        self.cmd = self.sched.post_at_tick(self._noteon, next_beat)


    def _noteoff(self, tick, pitch):
        # just turn off the currently sounding note.
        self.synth.noteoff(self.channel, pitch)    


# part 1: test your Arpeggiator here
class MainWidget1(BaseWidget) :
    def __init__(self):
        super(MainWidget1, self).__init__()

        self.audio = Audio(2)
        self.synth = Synth('../data/FluidR3_GM.sf2')

        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        # create the metronome:
        self.metro = Metronome(self.sched, self.synth)

        # create the arpeggiator:
        self.arpeg = Arpeggiator(self.sched, self.synth, channel = 1, program = (0,0) )

        # and text to display our status
        self.label = topleft_label()
        self.add_widget(self.label)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == 'm':
            self.metro.toggle()

        if keycode[1] == 'a':
            self.arpeg.start()

        pitches = lookup(keycode[1], 'qwe', ((60, 64, 67, 72), (55, 59, 62, 65, 67, 71), (60, 65, 69)))
        if pitches:
            self.arpeg.set_pitches(pitches)

        rhythm = lookup(keycode[1], 'uiop', ((120, 1), (160, 1), (240, 0.75), (480, 0.25)))
        if rhythm:
            self.arpeg.set_rhythm(*rhythm)

        direction = lookup(keycode[1], '123', ('up', 'down', 'updown'))
        if direction:
            self.arpeg.set_direction(direction)

    def on_key_up(self, keycode):
        if keycode[1] == 'a':
            self.arpeg.stop()

    def on_update(self) :
        self.audio.on_update()
        self.label.text = self.sched.now_str() + '\n'
        self.label.text += 'tempo:%d\n' % self.tempo_map.get_tempo()
        self.label.text += 'm: toggle Metronome\n'
        self.label.text += 'a: Enable Arpeggiator\n'
        self.label.text += 'q w e: Changes pitches\n'
        self.label.text += 'u i o p: Change Rhythm\n'
        self.label.text += '1 2 3: Change Direction\n'


# Part 2
class MainWidget2(BaseWidget) :
    def __init__(self):
        super(MainWidget2, self).__init__()

        self.audio = Audio(2)
        self.synth = Synth('../data/FluidR3_GM.sf2')

        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        # create the metronome:
        self.metro = Metronome(self.sched, self.synth)

        # create the arpeggiator:
        self.arpeg = Arpeggiator(self.sched, self.synth, channel = 1, program = (0,0) )
        self.arpeg.set_direction('updown')
        
        #size of the notes sent to the arpeggiator
        self.arpegSize = 3 
        #all of the notes this program can make. However, only self.arpegSize notes are sent to the arpegiator at a time
        self.allNotes = [50, 53, 55, 56, 57, 60, 62, 65, 67, 68, 69, 72, 74]

        self.lastPitchIndex = None
        self.lastPulseIndex = None

        self.noteLengths = [240, 210, 180, 150, 120, 90, 60]
        self.articulation = .75

        # and text to display our status
        self.label = topleft_label()
        self.add_widget(self.label)

        # and text to display our status
        self.label = topleft_label()
        self.add_widget(self.label)

        self.objects = AnimGroup()
        self.canvas.add(self.objects)

        self.add_lines()
    
    def add_lines(self):
        w = Window.width
        h = Window.height
        numBuckets = len(self.allNotes) - self.arpegSize
        sizeOfBucket = w / numBuckets

        for i in range(numBuckets):
            xVal = i * sizeOfBucket
            line = Line(points=[xVal, 0, xVal, h], width=2)
            self.objects.add(line)

        

        numBuckets = len(self.noteLengths)
        sizeOfBucket = h / numBuckets

        for i in range(numBuckets):
            yVal = i * sizeOfBucket
            line = Line(points=[0, yVal, w, yVal], width=2)
            self.objects.add(line)



    def on_touch_down(self, touch):
        p = touch.pos
        self.update_pitches(p)
        self.update_pulse(p)
        self.arpeg.start()
        

    def on_touch_up(self, touch):
        self.arpeg.stop()

    def on_touch_move(self, touch):
        p = touch.pos
        self.update_pitches(p)
        self.update_pulse(p)

    def update_pitches(self, pos=(0,0)):
        mouseX = pos[0]
        w = Window.width

        numBuckets = len(self.allNotes) - self.arpegSize
        sizeOfBucket = w / numBuckets

        noteBucket = int(mouseX // sizeOfBucket)

        if noteBucket != self.lastPitchIndex:

            arpegNotes = self.allNotes[noteBucket:noteBucket+self.arpegSize]
            self.lastSlice = arpegNotes

            self.arpeg.set_pitches(arpegNotes)
            self.lastPitchIndex = noteBucket

    def update_pulse(self, pos=(0,0)):
        mouseY = pos[1]
        h = Window.height

        numBuckets = len(self.noteLengths)
        sizeOfBucket = h / numBuckets

        pulseBucket = int(mouseY // sizeOfBucket)

        if pulseBucket < len(self.noteLengths) and pulseBucket != self.lastPulseIndex:

            length = self.noteLengths[pulseBucket]
            self.arpeg.set_rhythm(length, self.articulation)
            self.lastPulseIndex = pulseBucket



    def on_update(self) :
        self.audio.on_update()
        self.label.text = self.sched.now_str() + '\n'


class NoteSequencer(object):
    """Plays a single Sequence of notes. The sequence is a python list containing
    notes. Each note is (dur, pitch)."""
    def __init__(self, sched, synth, channel, program, notes, loop=True, callback = None):
        super(NoteSequencer, self).__init__()
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program

        self.callback = callback

        self.notes = notes
        self.loop = loop
        self.playing = False

        self.cmd = None
        self.noteIndex = 0

    def start(self):
        if self.playing:
            return

        self.playing = True

         # set up the correct sound (program: bank and preset)
        self.synth.program(self.channel, self.program[0], self.program[1])

        # find the tick of the next beat, and make it "beat aligned"
        now = self.sched.get_tick()
        next_beat = quantize_tick_up(now, 480)

        # now, post the _noteon function (and remember this command)
        self.cmd = self.sched.post_at_tick(self._noteon, next_beat)

    def stop(self):
        if not self.playing:
            return

        self.playing = False

        # cancel anything pending in the future.
        self.sched.remove(self.cmd)

        # reset these so we don't have a reference to old commands.
        self.cmd = None
        self.noteIndex = 0

    def toggle(self):
        if self.playing:
            self.stop()
        else:
            self.start()
    
    def _noteon(self, tick, ignore):
        # play the note right now:
        pitch = self.notes[self.noteIndex][1]
        vel = 100

        if pitch > 0:
            self.synth.noteon(self.channel, pitch, vel)
            


            # post the note off for half a beat later:
            off_tick = tick + self.notes[self.noteIndex][0]
            self.sched.post_at_tick(self._noteoff, off_tick, pitch)

            if self.callback != None:
                self.callback(pitch, self.notes[self.noteIndex][0])

        if self.noteIndex < len(self.notes) - 1:
            # schedule the next noteon for one beat later
            next_beat = tick + self.notes[self.noteIndex][0]
            self.cmd = self.sched.post_at_tick(self._noteon, next_beat)

            self.noteIndex += 1
        else:
            if self.loop:
                next_beat = tick + self.notes[self.noteIndex][0]
                self.cmd = self.sched.post_at_tick(self._noteon, next_beat)

                self.noteIndex = 0


    def _noteoff(self, tick, pitch):
        # just turn off the currently sounding note.
        self.synth.noteoff(self.channel, pitch)

class NoteShape(InstructionGroup):
    def __init__(self, topLeftPos, height, width):
        super(NoteShape, self).__init__()

        w = Window.width
        h = Window.height

        self.height = height
        self.width = width


        leftX = topLeftPos[0]
        topY = topLeftPos[1]
        bottomY = topLeftPos[1] - height

        self.shape = Rectangle(pos = (leftX, bottomY), size=(width, height))

        colorChange = leftX / w
        hue = .6 + .5 * (colorChange) 
        #hue = .76
        self.color = Color(hsv=(hue, 1, 1), a=1)

        #speed of the song is 2 beats per second.
        #lets say that the height of a quarter note (one beat) is 150.
        #Then I would want that square to travel 2*100 =200 units per second.
        beatsInHeight = h/200
        secondsToTravel = beatsInHeight / 1.7333333
        #print("seconds to travel: ",secondsToTravel)

        self.yPos_anim = KFAnim((0, topY), (secondsToTravel, h))
        #self.alpha_anim = KFAnim((0, 1), (1+decay, 0))

        self.add(self.color)
        self.add(self.shape)

        self.time = 0
        self.on_update(0)

    
    def on_update(self, dt):

        w = Window.width
        h = Window.height

        leftPos = self.shape.pos[0]         
        
        yPos = self.yPos_anim.eval(self.time)
        
        self.shape.pos = (leftPos, yPos-self.height)

        #alpha = self.alpha_anim.eval(self.time)
        #self.color.a = alpha

        self.time += dt

        return yPos < h

class CrossBar(InstructionGroup):
    def __init__(self):
        super(CrossBar, self).__init__()

        w = Window.width
        h = Window.height

        leftX = 0
        bottomY = 0

        self.shape = Line(points=[0,0,w,0], width=2)

        self.color = Color((1, 1, 1), a=1)

        #speed of the song is 104/60 = 1.733333 beats per second.
        #lets say that the height of a quarter note (one beat) is 100.
        #Then I would want that square to travel 2*100 =200 units per second.
        beatsInHeight = h/200
        secondsToTravel = beatsInHeight / 1.7333333
        #print("seconds to travel: ",secondsToTravel)

        self.yPos_anim = KFAnim((0, bottomY), (secondsToTravel, h))
        #self.alpha_anim = KFAnim((0, 1), (1+decay, 0))

        self.add(self.color)
        self.add(self.shape)

        self.time = 0
        self.on_update(0)

    
    def on_update(self, dt):
        w = Window.width
        h = Window.height      
        
        yPos = self.yPos_anim.eval(self.time)
        
        self.shape.points=[0,yPos,w,yPos]

        self.time += dt

        return yPos < h   



# Parts 3 and 4
class MainWidget3(BaseWidget) :
    def __init__(self):
        super(MainWidget3, self).__init__()

        self.audio = Audio(2)
        self.synth = Synth('../data/FluidR3_GM.sf2')

        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(104)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        # create the metronome:
        self.metro = Metronome(self.sched, self.synth)        

        percNotes = [(480,35), (360,42), (120,35), (480,35), (480,42)]

        
        self.base1Notes = [(240,43), (240,43), (240,43), (120,47), (240,41), (240,41), (360,41), (120,40),
                      (360,41), (240,41), (240,41), (120,40), (120,36), (480,-1), (120,40), (240,41), (120,43)]

        self.base2Notes = [(120,-1), (120,45), (240,43), (120,-1), (240,43), (120,40), (480,43), (120,-1), (120,45), (120,45), (120,48),
                      (240,-1), (240,41), (120,-1), (240,41), (120,40), (480,41), (120,-1), (120,45), (120,45), (120,48),
                      (240,-1), (240,45), (120,-1), (240,45), (120,45), (480,45), (240,43), (120,-1), (120,45),
                      (240,-1), (240,45), (120,-1), (240,45), (120,45), (480,45), (120,-1), (120,45), (120,45), (120,48)]  
        
        self.baseNotes = self.base2Notes
        #[40, 41, 43, 45 48,]


        #changes / pitch sutff
        self.changes = [ (1920, [72, 74, 76, 79, 81, 84]),
                    (1920, [69, 72, 74, 81]),
                    (3840, [69, 72, 74, 76, 79, 81, 84])]

        self.changesIndex = 0
        self.curChanges = []
        self.selectSize = 2
        self.lastPitchIndex = None
        self.lastTouch = None


        #Note length stuff
        self.noteLengths = [480, 240, 120]
        self.articulation = 1
        self.lastPulseIndex = 0

        #Declare the players
        self.perc = NoteSequencer(self.sched, self.synth, 1, (128,0), percNotes)
        self.base1 = NoteSequencer(self.sched, self.synth, 2, (0,33), self.base1Notes, callback = self.graphic_callback)
        self.base2 = NoteSequencer(self.sched, self.synth, 2, (0,33), self.base2Notes, callback = self.graphic_callback)
        self.lead = Arpeggiator(self.sched, self.synth, channel = 3, program = (0,65), callback = self.graphic_callback)
        self.lead.set_direction('updown')
        #Start the non-interactive stuff
        now = self.sched.get_tick()
        next_beat = quantize_tick_up(now, 480)
        self.perc.toggle()
        self.base2.toggle()
        self.sched.post_at_tick(self._updateChanges, next_beat) #Update changes as music starts
        self.sched.post_at_tick(self._spawnCrossBar, next_beat)


        # and text to display our status
        #self.label = topleft_label()
        #self.add_widget(self.label)

        #Graphics stuff
        self.objects = AnimGroup()
        self.canvas.add(self.objects)
        #self.allNotes = [40, 41, 43, 45, 48, 900, 69, 72, 74, 76, 79, 81, 84]
        self.allNotes = [36, 40, 41, 43, 45, 47, 48, 900, 69, 72, 74, 76, 79, 81, 84]


    def graphic_callback(self, pitch, length):
        w = Window.width
        numBuckets = len(self.allNotes)
        bucket = self.allNotes.index(pitch)

        widthOfBucket = w/numBuckets
        width = widthOfBucket - 10

        leftX = bucket*widthOfBucket + 5

        height = length/480 * 100

        shape = NoteShape((leftX,0), height, width)
        self.objects.add(shape)

    def _spawnCrossBar(self, tick, ignore):

        shape = CrossBar()
        self.objects.add(shape)

        self.sched.post_at_tick(self._spawnCrossBar, tick+480)

    
    def _updateChanges(self, tick, ignore):
        timeTillNextChange = self.changes[self.changesIndex][0]
        self.curChanges = self.changes[self.changesIndex][1]

        #print("CHANGE OCCURED: ", self.curChanges)

        self.changesIndex = (self.changesIndex + 1) % len(self.changes)

        self.sched.post_at_tick(self._updateChanges, tick+timeTillNextChange)
        self.lastPitchIndex = None

        if self.lastTouch != None:
            self.update_pitches(self.lastTouch)
    
    def changeBaseLine(self):
        self.base1.toggle()
        self.base2.toggle()


    def on_key_down(self, keycode, modifiers):
        obj = lookup(keycode[1], 'm', (self.metro))
        if obj is not None:
            obj.toggle()
        
        if keycode[1] == 'q':
            self.changeBaseLine()

    def on_key_up(self, keycode):
        pass

    def on_touch_down(self, touch):
        p = touch.pos
        self.update_pitches(p)
        self.update_pulse(p)
        self.lead.start()
        self.lastTouch = p
        

    def on_touch_up(self, touch):
        self.lead.stop()

    def on_touch_move(self, touch):
        p = touch.pos
        self.update_pitches(p)
        self.update_pulse(p)
        self.lastTouch = p

    def update_pitches(self, pos=(0,0)):
        mouseX = pos[0]
        w = Window.width

        numBuckets = len(self.curChanges) - self.selectSize + 1
        sizeOfBucket = w / numBuckets

        noteBucket = int(mouseX // sizeOfBucket)


        if noteBucket != self.lastPitchIndex:

            arpegNotes = self.curChanges[noteBucket:noteBucket+self.selectSize]

            self.lead.set_pitches(arpegNotes)
            self.lastPitchIndex = noteBucket

    def update_pulse(self, pos=(0,0)):
        mouseY = pos[1]
        h = Window.height

        numBuckets = len(self.noteLengths)
        sizeOfBucket = h / numBuckets

        pulseBucket = int(mouseY // sizeOfBucket)

        if pulseBucket < len(self.noteLengths) and pulseBucket != self.lastPulseIndex:

            length = self.noteLengths[pulseBucket]
            self.lead.set_rhythm(length, self.articulation)
            self.lastPulseIndex = pulseBucket

    def on_update(self) :
        self.audio.on_update()
        self.objects.on_update()
        #self.label.text = self.sched.now_str() + '\n'


if __name__ == "__main__":
    # pass in which MainWidget to run as a command-line arg
    run(eval('MainWidget' + sys.argv[1]))
