# pset4.py
# Rishabh Chandra
# October 9, 2019

import sys
sys.path.append('..')
from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.synth import Synth
from common.gfxutil import topleft_label
from common.clock import Clock, SimpleTempoMap, AudioScheduler, tick_str, kTicksPerQuarter, quantize_tick_up
from common.metro import Metronome
from common.kivyparticle import ParticleSystem
from kivy.graphics.instructions import InstructionGroup
from kivy.clock import Clock as kivyClock
from common.gfxutil import topleft_label, CRectangle, CEllipse, KFAnim, AnimGroup
from kivy.graphics import Color, Ellipse, Rectangle, Line

from kivy.core.window import Window

from random import random

import numpy as np

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

pitch_dict = {0: "C", 1: "C#/Db", 2: "D", 3: "D#/Eb", 4: "E", 5: "F", 6: "F#/Gb", 7: "G", 8: "G#/Ab", 9: "A", 10: "A#/Bb", 11: "B"}
chord_dict = {36: "I", 41: "IV", 43: "V"}
TRIAD = np.array([0, 4, 7, 10])

#Note Sequencer from Lab with added callback. 
class NoteSequencer(object):
    """Plays a single Sequence of notes. The sequence is a python list containing
    notes. Each note is (dur, pitch)."""
    def __init__(self, sched, synth, channel, program, notes, loop=False, callback = None):
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
        self.idx = 0

    def start(self):
        if self.playing:
            return

        self.playing = True
        self.synth.program(self.channel, self.program[0], self.program[1])

        # start from the beginning
        self.idx = 0

        # post the first note on the next quarter-note:
        now = self.sched.get_tick()
        next_beat = quantize_tick_up(now, kTicksPerQuarter)
        self.cmd = self.sched.post_at_tick(self._note_on, next_beat)

    def stop(self):
        if not self.playing:
            return

        self.playing = False
        self.sched.remove(self.cmd)
        self.cmd = None

    def toggle(self):
        if self.playing:
            self.stop()
        else:
            self.start()

    def _note_on(self, tick, ignore):
        # if looping, go back to beginning
        if self.loop and self.idx >= len(self.notes):
            self.idx = 0

        # play new note if available
        if self.idx < len(self.notes):
            length, pitch = self.notes[self.idx]
            if pitch != 0: # pitch 0 is a rest
                self.synth.noteon(self.channel, pitch, 60)  # play note
                self.sched.post_at_tick(self._note_off, tick + length * .9, pitch) # note off a bit later - slightly detached. 
                if self.callback: 
                    self.callback(self, length, pitch)

            # schedule the next note:
            self.idx += 1
            self.cmd = self.sched.post_at_tick(self._note_on, tick + length)
        else:
            self.playing = False


    def _note_off(self, tick, pitch):
        # terminate current note:
        self.synth.noteoff(self.channel, pitch)

# part 1: create Arpeggiator
class Arpeggiator(object):
    def __init__(self, sched, synth, channel=0, program=(0, 40), callback = None):
        super(Arpeggiator, self).__init__()
        self.pitches = [0, 0]
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program
        self.callback = callback

        self.playing = False

        self.updown = "up"
        self.upward = 1

        self.length = 120
        self.articulation = 1
        self.cmd = None
        self.idx = 0

    # start the arpeggiator
    def start(self):
        if not self.playing: 
            self.playing = True
            self.synth.program(self.channel, self.program[0], self.program[1])

            # start from the beginning
            self.idx = 0

            # post the first note on the next quarter-note:
            now = self.sched.get_tick()
            next_beat = quantize_tick_up(now, kTicksPerQuarter)
            self.cmd = self.sched.post_at_tick(self._note_on, next_beat)
    
    # stop the arpeggiator
    def stop(self):
        if self.playing:
            self.playing = False
            self.sched.remove(self.cmd)
            self.cmd = None
    
    def toggle(self):
        if self.playing:
            self.stop()
        else:
            self.start()

    #note_on derived from lab
    def _note_on(self, tick, ignore):
        # play new note if available
        if self.idx < len(self.pitches):
            pitch = self.pitches[self.idx]
            if pitch != 0: # pitch 0 is a rest
                self.synth.noteon(self.channel, pitch, 80)  # play note
                self.sched.post_at_tick(self._note_off, tick + self.length * self.articulation, pitch) # note off a bit later - slightly detached. 
            
                if self.callback: 
                    self.callback(self, pitch, self.idx)
            
            # schedule the next note, but check direction:
            if self.updown == "up": 
                self.idx += 1
                if self.idx >= len(self.pitches): 
                    self.idx = 0
            elif self.updown == "down": 
                self.idx -= 1
                if self.idx < 0: 
                    self.idx = len(self.pitches) - 1
            elif self.updown == "updown": 
                if self.idx == 0: 
                    self.upward = 1
                elif self.idx == len(self.pitches) - 1: 
                    self.upward = -1

                self.idx += 1 * self.upward

            self.cmd = self.sched.post_at_tick(self._note_on, tick + self.length)
        else:
            self.playing = False


    def _note_off(self, tick, pitch):
        # terminate current note:
        self.synth.noteoff(self.channel, pitch)

    # pitches is a list of MIDI pitch values. For example [60 64 67 72]
    def set_pitches(self, pitches):
        self.pitches = pitches

    # length is related to speed of the notes. For example 240 represents 1/8th notes.
    # articulation is a ratio that defines how quickly the note off should follow the note on. 
    # For example, a value of 1 is a full-length note (legato) where the note off will 
    # occur <length> ticks after the note-on. A value of 0.5 will make the note shorter, 
    # where the note off will occur <length>/2 ticks after the note-on.
    def set_rhythm(self, length, articulation):
        self.length = length 
        self.articulation = articulation

    # dir is either 'up', 'down', or 'updown'
    def set_direction(self, direction):
        self.updown = direction 


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
        self.label.text += 'a: start Arpeggiator\n'
        self.label.text += 'q w e: Changes pitches\n'
        self.label.text += 'u i o p: Change Rhythm\n'
        self.label.text += '1 2 3: Change Direction\n'


# Part 2
class MainWidget2(BaseWidget) :
    def __init__(self):
        super(MainWidget2, self).__init__()

        self.audio = Audio(2)
        self.synth = Synth('../data/FluidR3_GM.sf2')

        self.pitches = [36, 40, 43, 48, 52, 55, 60, 64, 67, 72, 76, 79, 84]

        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)

        #argeggiator
        self.arpeg = Arpeggiator(self.sched, self.synth, channel = 1, program = (0,0) )
        self.arpeg.set_direction("updown")

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        # and text to display our status
        self.label = topleft_label()
        self.add_widget(self.label)

    def on_touch_down(self, touch):
        self.arpeg.start()
        self.on_touch_move(touch)

    def on_touch_up(self, touch):
        self.arpeg.stop()

    def on_touch_move(self, touch):
        #divides the screen into 13 segments, each of which produce 
        #a different scaled arpeggiation
        this_segment = int(touch.pos[0]/Window.width * 13)
        left_end = max(0, this_segment - 3)
        right_end = min(13, this_segment + 4)

        pitches = self.pitches[left_end:right_end]
        self.arpeg.set_pitches(pitches)

        #speed is directly correlated with height onscreen
        self.arpeg.set_rhythm(touch.pos[1], 1)

    def on_update(self) :
        self.audio.on_update()
        self.label.text = self.sched.now_str() + '\n'

#Produces a circle that changes radius for the notes in the module
class NoteCircle(InstructionGroup):
    def __init__(self, pos1, pos2, r, dur, color):
        super(NoteCircle, self).__init__()

        center_x = Window.width/2
        center_y = Window.height/2

        self.dur = dur
        self.radius_anim = KFAnim((0, r), (dur, r), (2*dur, 2*r), (3*dur, 0))
        self.pos_anim = KFAnim((0, pos1[0], pos1[1]), (dur, pos2[0], pos2[1]))

        self.color = Color(*color)
        self.add(self.color)
        
        self.circle = CEllipse(cpos = pos1, size = (2*r, 2*r), segments = 40)
        self.add(self.circle)

        self.time = 0
        self.on_update(0)

    def on_update(self, dt):
        #animate radius
        rad = self.radius_anim.eval(self.time)
        self.circle.csize = (2*rad, 2*rad)

        # animate position
        pos = self.pos_anim.eval(self.time)
        self.circle.cpos = pos

        # advance time
        self.time += dt

        # continue flag
        return self.radius_anim.is_active(self.time)

#Produces a steady, un-size-changing circle for the beat of the module. 
class BeatCircle(InstructionGroup):
    def __init__(self, pos1, pos2, r, dur):
        super(BeatCircle, self).__init__()

        center_x = Window.width/2
        center_y = Window.height/2

        self.dur = dur
        self.pos_anim = KFAnim((0, pos1[0], pos1[1]), (dur/4, pos2[0], pos2[1]))

        self.color = Color(1, 1, 1, 0.7)
        self.add(self.color)
        
        self.circle = CEllipse(cpos = pos1, size = (2*r, 2*r), segments = 40)
        self.add(self.circle)

        self.time = 0
        self.on_update(0)

    def on_update(self, dt):
        # animate position
        pos = self.pos_anim.eval(self.time)
        self.circle.cpos = pos

        # advance time
        self.time += dt
        # continue flag
        return self.time <= self.dur + 0.02

# Parts 3 and 4
class MainWidget3(BaseWidget) :
    def __init__(self):
        super(MainWidget3, self).__init__()

        self.audio = Audio(2)
        self.synth = Synth('../data/FluidR3_GM.sf2')
        
        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(90)
        self.sched = AudioScheduler(self.tempo_map)
        
        #create drum
        self.drum = Arpeggiator(self.sched, self.synth, channel = 1, program = (128, 0), callback = self.on_beat)
        self.drum.set_pitches([35, 44, 44, 44, 38, 44, 44, 35, 44, 44, 35, 44, 38, 44, 44, 44])
        self.drum.set_rhythm(120, 1)

        #chord and key information
        self.chord = np.array([0, 4, 7, 9, 10])
        self.key = 0
        self.onefourfive = 36

        #create bass
        self.bass = Arpeggiator(self.sched, self.synth, channel = 2, program = (0, 34))
        self.bass.set_direction("updown")
        self.bass.set_rhythm(240, 1)
        self.bass.set_pitches(self.chord + 36 + self.key )
        
        self.touch = None #used to get speed and pitch variation for lead
        self.lead = None #only set up on a touch

        self.systems = set()

        # load up the particle systems, set initial emitter point and start it.
        self.psl = ParticleSystem('particle/pbl.pex')
        self.psl.emitter_x = 20.
        self.psl.emitter_y = 20.
        self.psr = ParticleSystem('particle/pbr.pex')
        self.psr.emitter_x = Window.width - 20.
        self.psr.emitter_y = 20.
        self.psul = ParticleSystem('particle/pbul.pex')
        self.psul.emitter_x = 20.
        self.psul.emitter_y = Window.height - 20.
        self.psur = ParticleSystem('particle/pbur.pex')
        self.psur.emitter_x = Window.width - 20.
        self.psur.emitter_y = Window.height - 20.
        self.psc = ParticleSystem('particle/pbc.pex')
        self.psc.emitter_x = Window.width/2
        self.psc.emitter_y = Window.height/2
        self.systems.add(self.psl)
        self.systems.add(self.psr)
        self.systems.add(self.psul)
        self.systems.add(self.psur)
        self.systems.add(self.psc)
        self.stop = True
        self.objects = []

        self.add_widget(self.psl)
        self.add_widget(self.psr)
        self.add_widget(self.psul)
        self.add_widget(self.psur)
        self.add_widget(self.psc)

        #positions for the beat circle
        self.poses = [(Window.width - 100, Window.height/2), (Window.width/2, Window.height - 100), 
                      (100, Window.height/2), (Window.width/2, 100)]
        self.bidx = 0

        #Set initial chords
        self.selection = [0, 4, 7, 10]

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        # and text to display our status
        self.label = topleft_label()
        self.add_widget(self.label)

    #move beat circle every beat
    def on_beat(self, drum, pitch, didx):
        if didx % 4 == 0: 
            pos1 = self.poses[self.bidx]
            self.bidx -= 1
            if self.bidx < 0: 
                self.bidx = 3

            pos2 = self.poses[self.bidx]

            x = BeatCircle(pos1, pos2, 60, 2/3)
            self.canvas.add(x)
            self.objects.append(x)

    #create new note circle for every note in the song
    def on_lead(self, lead, length, pitch): 
        col = color(pitch % 12)
        pos1 = (random()*Window.width, random()*Window.height)
        pos2 = (random()*Window.width, random()*Window.height)

        val = length /480
        x = NoteCircle(pos1, pos2, 20, 2/3 * val, col)
        self.canvas.add(x)
        self.objects.append(x)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == "d": 
            self.drum.toggle()

        if keycode[1] == "b": 
            self.bass.toggle()
            if self.stop: 
                for i in self.systems: 
                    i.start()
                self.stop = False
            else: 
                for i in self.systems: 
                    i.stop()
                self.stop = True

        noi = lookup(keycode[1], 'zxc', (36, 41, 43))

        if noi: #we are changing the bassline
            self.onefourfive = noi
            self.bass.set_pitches(self.chord + self.onefourfive + self.key)
            self.selection = TRIAD + self.onefourfive + self.key
            if self.touch: 
                self.on_touch_move(self.touch)

        k = lookup(keycode[1], '[]', (-1, 1)) #we are changing the key
        if k: 
            self.key += k
            self.bass.set_pitches(self.chord + self.onefourfive + self.key)  
            self.selection = TRIAD + self.onefourfive + self.key
            if self.touch: 
                self.on_touch_move(self.touch)

    def on_touch_down(self, touch):
        self.on_touch_move(touch)

    def on_touch_move(self, touch):
        self.touch = touch
        if self.lead: 
            self.lead.stop() #we will make a new lead

        available_pitches = np.array([0, 0, 2, 4, 4, 5, 7, 7, 9, 9, 10, 10, 12, 12]) + \
            self.onefourfive + 24 + self.key #favor notes in the chord

        #divide screen into 29 segments for more variance in pitch
        segment_pitch = int(touch.pos[0]/Window.width * 29) 
        if segment_pitch < 14: 
            for i in range(segment_pitch - 1, len(available_pitches)): 
                available_pitches[i] -= 12
        elif segment_pitch > 14: 
            for i in range(0, segment_pitch - 14): 
                available_pitches[i] += 12

        selected = []
        for i in range(20): #create random pitches and lengths
            pitch = 0
            rand = int(random()*len(available_pitches) + 1)
            if rand < len(available_pitches): 
                pitch = available_pitches[rand]

            rand = random()
            frac = touch.pos[1]/Window.height #probability of this note being an eighth

            length = 120
            if rand > frac: 
                length = 240

            selected.append((length, pitch))

        #create a lead based on these notes
        self.lead = NoteSequencer(self.sched, self.synth, channel = 3, program = (0, 65), notes = tuple(selected), loop = True, callback = self.on_lead)
        self.lead.start()

    def on_update(self) :
        self.audio.on_update()

        for i in self.systems: 
            i.start_color = color(self.selection[int(random()*len(self.selection))] % 12)


        self.label.text = self.sched.now_str() + '\n'
        self.label.text += 'key: %s ' % pitch_dict[self.key % 12]
        self.label.text += '(%s)\n' % chord_dict[self.onefourfive] 
        self.label.text += 'touch right/left for higher/lower notes \n'
        self.label.text += 'touch up/down for more eighth/quarter notes\n'

        dt = kivyClock.frametime

        #kill objects that are dead
        kill_list = [b for b in self.objects if b.on_update(dt) == False]
        for b in kill_list:
            self.objects.remove(b)
            self.canvas.remove(b)


if __name__ == "__main__":
    # pass in which MainWidget to run as a command-line arg
    run(eval('MainWidget' + sys.argv[1]))
