import sys
sys.path.append('..')


class Rule(object):
    def __init__(self, notes, changes):

        def changes_startBeat(elem):
            return elem[0]

        def notes_startBeat(elem):
            return elem[1]

        self.notes = notes #[(pitch, startBeat, len)]
        self.changes = changes #[(startBeat, len, [allowed pitches])]

        self.notes.sort(key=notes_startBeat)
        self.changes.sort(key=changes_startBeat)
    
    def closest_pitch(self, oldPitch, otherPitches):
        bestDiff = 200
        bestPitch = None

        for pitch in otherPitches:
            if bestPitch == None:
                bestPitch = pitch
                bestDiff = abs(pitch-oldPitch)
            else:
                newDiff = abs(pitch-oldPitch)
                if newDiff < bestDiff:
                    bestPitch = pitch
                    bestDiff = newDiff
        return bestPitch



class DownBeatChordToneRule(Rule):
    def __init__(self, notes, changes):
        Rule.__init__(self, notes, changes)

    def new_note(self, index):
        oldNote = self.notes[index]
        oldStartBeat = oldNote[1]
        oldPitch = oldNote[0]

        newPitch = oldPitch

        #if oldNote[1] % 4 == 0:
        if True:
            for index, change in enumerate(self.changes):
                if index == len(self.changes)-1:
                    print("currChange: ", change)
                    newPitch = self.closest_pitch(oldPitch, change[2])                  
                else:
                    if oldStartBeat >= change[0] and oldStartBeat < self.changes[index+1][0]:
                        print("currChange: ", change)
                        newPitch = self.closest_pitch(oldPitch, change[2])
                        break
        if newPitch == None:
            print("Problem in DownBeatChordToneRule")
        
        return newPitch

