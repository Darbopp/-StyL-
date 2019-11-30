import sys
sys.path.append('..')
from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.synth import Synth
from common.gfxutil import topleft_label
from common.clock import Clock, SimpleTempoMap, AudioScheduler, kTicksPerQuarter, quantize_tick_up
from common.metro import Metronome



class NoteSequencer(object):
    """Plays a Sequence of notes. The sequence is a python list containing
    notes. Each note is (pitch, startBeat, len). Note len is in terms of beats"""
    def __init__(self, sched, synth, channel, program, notes, velocity, loop=True, callback = None):
        super(NoteSequencer, self).__init__()

        self.sched = sched
        self.synth = synth
        self.channel = channel
        self.program = program

        self.shouldCallBack = False
        self.doneCallback = callback

        def startBeat(elem):
            return elem[1]

        #we sort notes by startBeat because the noteOn needs to know which note it should be playing
        self.notes = notes
        self.notes.sort(key=startBeat)


        self.velocity = velocity
        self.loop = loop # not currently functional
        self.playing = False

        self.cmds = [] #since we support chords now, we need to keep record of all commands
        self.noteIndex = 0


    def start(self):
        if self.playing:
            return

        self.playing = True
        self.noteIndex = 0
        self.shouldCallBack = False

         # set up the correct sound (program: bank and preset)
        self.synth.program(self.channel, self.program[0], self.program[1])

        # find the tick of the next beat, and make it "beat aligned"
        now = self.sched.get_tick()
        next_beat = quantize_tick_up(now, 480)

        #Since we are now supporting chords,
        #all notes need to be scheduled now
        for note in self.notes:
            ticksDeep = 480*note[1]
            cmd = self.sched.post_at_tick(self._noteon, (next_beat + ticksDeep) )
            self.cmds.append(cmd) #remember to remember the commands incase we need to stop
            #print("note is at", note[1])
        cmd = self.sched.post_at_tick(self._killself, (next_beat + 480*16 - 30))
        self.cmds.append(cmd)

    def stop(self):
        if not self.playing:
            return

        self.playing = False

        # cancel anything pending in the future.
        for cmd in self.cmds:
            self.sched.remove(cmd)

        # reset these so we don't have a reference to old commands.
        self.cmds = []
        self.noteIndex = 0

    def toggle(self):
        if self.playing:
            self.stop()
        else:
            self.start()

    def change_notes(self, newNotes):
        self.stop()
        self.notes = newNotes
    
    def _noteon(self, tick, ignore):
        #note: (pitch, startBeat, len)

        # play the note right now:
        pitch = self.notes[self.noteIndex][0]
        length = self.notes[self.noteIndex][2] * 480

        if pitch > 0:
            self.synth.noteon(self.channel, pitch, self.velocity)
            
            # post the note off for length later:
            off_tick = tick + length - 1 #the minus 1 allows the same note to be played twice, otherwise the note off canceles the note on
            self.sched.post_at_tick(self._noteoff, off_tick, pitch)

            # if self.callback != None:
            #     self.callback(pitch, length)

        if self.noteIndex < len(self.notes) - 1:

            # since we scheduled all our notes at the beginning, we dont need this.

            # schedule the next noteon for one beat later
            #next_beat = tick + self.notes[self.noteIndex][0]
            #self.cmd = self.sched.post_at_tick(self._noteon, next_beat)

            self.noteIndex += 1
        else:
            '''
            Currently not supporting looping, but probably would be useful for the static lines
            
            if self.loop:
                next_beat = tick + self.notes[self.noteIndex][0]
                cmd = self.sched.post_at_tick(self._noteon, next_beat)
                self.cmds.append(cmd)
                self.noteIndex = 0
            '''
            if self.doneCallback is not None:
                self.shouldCallBack = True
            self.noteIndex = 0
            #self.stop()


    def _noteoff(self, tick, pitch):
        # just turn off the currently sounding note.
        self.synth.noteoff(self.channel, pitch)

        # if self.shouldCallBack:
        #     self.doneCallback()

    def _killself(self, tick, pitch):
        self.stop()
        if self.shouldCallBack:
            self.doneCallback()