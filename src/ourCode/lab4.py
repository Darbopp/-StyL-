# lab4.py

import sys
sys.path.append('..')
from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.synth import Synth
from common.gfxutil import topleft_label
from common.clock import Clock, SimpleTempoMap, AudioScheduler, kTicksPerQuarter, quantize_tick_up
from common.metro import Metronome


# Help flesh out the class NoteSequencer - a class that can play a pre-specified sequence of notes.
#
# Specification:
#
# Notes are given as a list of tuples, where each note is (length, pitch)
# See the two examples below kYesterday, and kSomewhere.
#
# NoteSequencer has start/stop/toggle just like Metronome. When it starts, it should play 
# the sequence of notes from the beginning. When stop is called, it should stop playing.
#
# There is an optional loop flag. If loop=True, the sequence should start at the beginning after
# it is done.
#
# When you test this class, make sure to have the metronome running as well so you can hear if
# the notes are coming out with the correct rhythm.

#self.seq1 = NoteSequencer(self.sched, self.synth, 1, (0,65), kYesterday, False)


class NoteSequencer(object):
    """Plays a single Sequence of notes. The sequence is a python list containing
    notes. Each note is (dur, pitch)."""
    def __init__(self, sched, synth, channel, program, notes, loop=True):
        super(NoteSequencer, self).__init__()
        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program

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
        self.synth.noteon(self.channel, pitch, vel)

        # post the note off for half a beat later:
        off_tick = tick + self.notes[self.noteIndex][0]
        self.sched.post_at_tick(self._noteoff, off_tick, pitch)

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




# Test NoteSequencer: a class that plays a sequence of notes.
kYesterday = ((240,67), (240,65), (480*3,65), (480,0), (240,69), (240,71), (240,73), (240,74), (240,76), (240,77), (360,76), (120,74), (480*2, 74), (480,0),)
kSomewhere = ((960, 60), (960, 72), (480, 71), (240, 67), (240, 69), (480, 71), (480, 72), )

class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()

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

        # Note Sequencers
        self.seq1 = NoteSequencer(self.sched, self.synth, 1, (0,65), kYesterday, False)
        self.seq2 = NoteSequencer(self.sched, self.synth, 2, (0,52), kSomewhere, True)

        # and text to display our status
        self.label = topleft_label()
        self.add_widget(self.label)

    def on_key_down(self, keycode, modifiers):

        obj = lookup(keycode[1], 'mas', (self.metro, self.seq1, self.seq2))
        if obj is not None:
            obj.toggle()

        bpm_adj = lookup(keycode[1], ('up', 'down'), (10, -10))
        if bpm_adj:
            new_tempo = self.tempo_map.get_tempo() + bpm_adj
            self.tempo_map.set_tempo(new_tempo, self.sched.get_time())

    def on_update(self) :
        self.audio.on_update()
        self.label.text = self.sched.now_str() + '\n'
        self.label.text += 'tempo:%d\n' % self.tempo_map.get_tempo()
        self.label.text += 'm: toggle Metronome\n'
        self.label.text += 'a: toggle Sequence 1\n'
        self.label.text += 's: toggle Sequence 2\n'
        self.label.text += 'up/down: change speed\n'        


run(MainWidget)

