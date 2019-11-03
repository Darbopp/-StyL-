#lecture4.py

import sys
sys.path.append('..')
from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.synth import Synth
from common.gfxutil import topleft_label
from common.modifier import Modifier
from common.clock import Clock, SimpleTempoMap, Scheduler, AudioScheduler, tick_str, kTicksPerQuarter
from common.metro import Metronome

import numpy as np
# Let's use fluid synth to play notes
kKeys = '1234567890'
kPitches = (36,60,62,64,65,67,69,71,72,74,76)

# this demonstrates the fluidsynth synthesizer.
class MainWidget1(BaseWidget) :
    def __init__(self):
        super(MainWidget1, self).__init__()

        self.audio = Audio(2)
        self.synth = Synth('../data/FluidR3_GM.sf2')
        self.audio.set_generator(self.synth)

        self.label = topleft_label()
        self.add_widget(self.label)

        cc_range = range(0, 128, 8)
        self.modifier = Modifier()
        self.modifier.add('a', "program", range(128), lambda x: self.synth.program_change(0, x))
        self.modifier.add('s', "vibrato", cc_range, lambda x: self.synth.cc(0, 1, x))
        self.modifier.add('d', "volume",  cc_range, lambda x: self.synth.cc(0, 7, x))
        self.modifier.add('f', "sustain", (0,127), lambda x: self.synth.cc(0, 64, x))
        self.modifier.add('z', "bend",  range(-8192, 8192, 256), lambda x: self.synth.pitch_bend(0, int(x)))

    def on_key_down(self, keycode, modifiers):
        self.modifier.on_key_down(keycode[1])

        pitch = lookup(keycode[1], kKeys, kPitches)
        if pitch:
            self.synth.noteon(0, pitch, 100)

    def on_key_up(self, keycode):
        self.modifier.on_key_up(keycode[1])

        pitch = lookup(keycode[1], kKeys, kPitches)
        if pitch:
            self.synth.noteoff(0, pitch)

    def on_update(self) :
        self.audio.on_update()
        self.modifier.on_update()
        self.label.text = self.modifier.get_txt() + '\n'


# Now, let's test the Clock and SimpleTempoMap classes
class MainWidget2(BaseWidget) :
    def __init__(self):
        super(MainWidget2, self).__init__()

        # create a clock and a tempo map
        self.clock = Clock()
        self.tempo_map = SimpleTempoMap(120)

        # and text to display our status
        self.label = topleft_label()
        self.add_widget(self.label)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == 'c':
            self.clock.toggle()

    def on_update(self) :

        time = self.clock.get_time()
        tick = self.tempo_map.time_to_tick(time)
        bpm = self.tempo_map.get_tempo()

        self.label.text = 'time:{:.2f}\n'.format(time)
        self.label.text += tick_str(tick) + '\n'
        self.label.text += 'bpm:{}\n'.format(bpm)
        self.label.text += 'c: toggle clock\n'


# Now, let's test the scheduler class
class MainWidget3(BaseWidget) :
    def __init__(self):
        super(MainWidget3, self).__init__()

        # create a clock and TempoMap
        self.clock = Clock()
        self.tempo = SimpleTempoMap(120)

        # create a Scheduler
        self.sched = Scheduler(self.clock, self.tempo)

        # and text to display our status
        self.label = topleft_label()
        self.add_widget(self.label)

        # to see accumulated output:
        self.output_text = ''

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == 'c':
            self.clock.toggle()

        if keycode[1] == 'a':
            now = self.sched.get_tick()
            later = now + (2 * kTicksPerQuarter)
            self.output_text += "now={}. post at tick={}\n".format(now, later)
            self.cmd = self.sched.post_at_tick(self._do_it, later, 'hello')

        if keycode[1] == 'b':
            self.sched.remove(self.cmd)

    def _do_it(self, tick, msg):
        self.output_text += "{} (at {})\n".format(msg, tick)

    def on_update(self) :
        # scheduler gets called every frame to process events
        self.sched.on_update()
        self.label.text = self.sched.now_str() + '\n'
        self.label.text += 'c: toggle clock\n'
        self.label.text += 'a: post event\n'
        self.label.text += 'b: remove event\n'
        self.label.text += self.output_text


# Let's test the Metronome class
class MainWidget4(BaseWidget) :
    def __init__(self):
        super(MainWidget4, self).__init__()

        self.audio = Audio(2)
        self.synth = Synth('../data/FluidR3_GM.sf2')
        self.audio.set_generator(self.synth)

        # create clock, tempo_map, scheduler
        self.clock = Clock()
        self.tempo_map  = SimpleTempoMap(120)
        self.sched = Scheduler(self.clock, self.tempo_map)

        # create the metronome:
        self.metro = Metronome(self.sched, self.synth)

        # and text to display our status
        self.label = topleft_label()
        self.add_widget(self.label)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == 'c':
            self.clock.toggle()

        if keycode[1] == 'm':
            self.metro.toggle()

        bpm_adj = lookup(keycode[1], ('up', 'down'), (10, -10))
        if bpm_adj:
            new_tempo = self.tempo_map.get_tempo() + bpm_adj
            self.tempo_map.set_tempo(new_tempo, self.sched.get_time())

    def on_update(self) :
        # scheduler and audio get poked every frame
        self.sched.on_update()
        self.audio.on_update()

        bpm = self.tempo_map.get_tempo()

        self.label.text = self.sched.now_str() + '\n'
        self.label.text += 'Metronome:' + ("ON" if self.metro.playing else "OFF") + '\n'
        self.label.text += 'tempo:{}\n'.format(bpm)
        self.label.text += 'm: toggle Metronome\n'
        self.label.text += 'up/down: change speed\n'        


# Use AudioScheduler for more precise scheduling
class MainWidget5(BaseWidget) :
    def __init__(self):
        super(MainWidget5, self).__init__()

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

        # and text to display our status
        self.label = topleft_label()
        self.add_widget(self.label)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == 'm':
            self.metro.toggle()

        bpm_adj = lookup(keycode[1], ('up', 'down'), (10, -10))
        if bpm_adj:
            new_tempo = self.tempo_map.get_tempo() + bpm_adj
            self.tempo_map.set_tempo(new_tempo, self.sched.get_time())

    def on_update(self) :
        self.audio.on_update()
        bpm = self.tempo_map.get_tempo()

        self.label.text = self.sched.now_str() + '\n'
        self.label.text += 'tempo:{}\n'.format(bpm) 
        self.label.text += 'm: toggle Metronome\n'
        self.label.text += 'up/down: change speed\n'        





# pass in which MainWidget to run as a command-line arg
run(eval('MainWidget' + sys.argv[1]))
