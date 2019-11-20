##########################################
#               Note Values              #
# Written in (pitch, start beat, length) #
##########################################
base_chords = {
    "Chainsmokers": {
        1: {
            "midi" : [
                (37,0,2.5), (44,0,2.5), (53,0,2.5), (56,0,2.5), (63,0,2.5),  
                (39,2.5,1.5), (46,2.5,1.5), (55,2.5,1.5), (58,2.5,1.5), (63,2.5,1.5), 
                (41,4,2.5), (48,4,2.5), (56,4,2.5), (60,4,2.5), (63,4,2.5), 
                (39,6.5,1.5), (46,6.5,1.5), (55,6.5,1.5), (58,6.5,1.5), (63,6.5,1.5),

                (37,8,2.5), (44,8,2.5), (53,8,2.5), (56,8,2.5), (63,8,2.5),  
                (39,10.5,1.5), (46,10.5,1.5), (55,10.5,1.5), (58,10.5,1.5), (63,10.5,1.5), 
                (41,12,2.5), (48,12,2.5), (56,12,2.5), (60,12,2.5), (63,12,2.5), 
                (39,14.5,1.5), (46,14.5,1.5), (55,14.5,1.5), (58,14.5,1.5), (63,14.5,1.5)
            ],
            "pitches": [37, 39, 41, 44, 46, 48, 53, 55, 56, 58, 60, 63]
        },
        2: {
            "midi" : [
                (37,0,1), (44,0,1), (53,0,1), (56,0,1), (63,0,1),
                (39,5,1), (46,5,1), (55,5,1), (58,5,1), (63,5,1),
                (39,6,1), (46,6,1), (55,6,1), (58,6,1), (63,6,1),
                (41,8,1), (48,8,1), (56,8,1), (60,8,1), (63,8,1), 
                (39,13,1), (46,13,1), (55,13,1), (58,13,1), (63,13,1),
                (39,14,1), (46,14,1), (55,14,1), (58,14,1), (63,14,1),
                (39,15,1), (46,15,1), (55,15,1), (58,15,1), (63,15,1)
            ],
            "pitches": [37, 39, 41, 44, 46, 48, 53, 55, 56, 58, 60, 63]
        }
    }
}

base_percussion = {
    "Chainsmokers": {
        1: {
            "midi" : [
                (35,0,1), (35,1,1), (38,1,1), (44,1,1), (35,2.5,.5), (44,2.5,.5), (35,3,.5), (44,3,.5),
                (35,4,1), (35,5,1), (38,5,1), (44,5,1), (35,6.5,.5), (44,6.5,.5), (35,7,.5), (44,7,.5),
                (35,8,1), (35,9,1), (38,9,1), (44,9,1), (35,10.5,.5), (44,10.5,.5), (35,11,.5), (44,11,.5),
                (35,12,1), (35,13,1), (38,13,1), (44,13,1), (35,14.5,.5), (44,14.5,.5), (35,15,.5), (44,15,.5)
            ],
            "pitches": [35, 38, 44]
        },
        2: {
            "midi" : [
                (36,0,1), (36,1,1), (38,2,2), (36,4,1), (36,5,1), (36,5.5,.5), (38,6,1), (38,7,1),
                (36,8,1), (36,9,1), (38,10,2), (36,12,1), (36,13,1), (36,13.5,.5), (38,14,1), (38,15,1),
            ],
            "pitches": [36, 38, 52]
        }
    }
}
'''
base_melody = {
    "Chainsmokers": {
        1: {
            "changes": [(0, 16, [63,68,70,72,75])],
            "pitches": [63,68,70,72,75]
        }
    }
}
A-flat major
68,70,72,73,75,77,79,80
56,58,60,61,63,65,67,68
'''
base_melody = {
    "Chainsmokers": {
        1: {
            "changes": [(0, 16, [63,68,70,72,75])],
            "pitches": [56,58,60,61,63,65,67,68]
        }
    }
}

tempos = {
    "Chainsmokers": 95*2
}

def transpose_instrument(style, instrument, transposition):
    if instrument == "chords":
        data = base_chords[style]
    else: # instrument is percussion
        data = base_percussion[style]

    output = {}
    for option in data:
        midi = []
        pitches = []

        for noteset in data[option]["midi"]:
            pitch = noteset[0] + transposition
            midi.append((pitch, noteset[1], noteset[2]))

        for pitch in data[option]["pitches"]:
            pitches.append(pitch + transposition)

        output[option] = {
            "midi": midi,
            "pitches": pitches
        }

    return output

def transpose_melody(style, option, transposition):
    data = base_melody[style][option]
    changes = []
    pitches = []

    for pitch in data["pitches"]:
        pitches.append(pitch + transposition)
    
    changes.append((data["changes"][0][0], data["changes"][0][1], pitches))
    
    return {
        "changes": changes,
        "pitches": pitches
    }

def chords_to_changes(chords):
    data = chords["midi"] #[(pitch, startBeat, len)]
    output = [] #[(startBeat, len, [allowed pitches])]
    currentStartBeat = None
    allNotes = []
    for note in data:
        if note[0] not in allNotes:
            allNotes.append(note[0])
        if currentStartBeat == None:
            currentStartBeat = note[1]
            output.append((note[1], note[2], []))
        if note[1] == currentStartBeat:
            if note[0] not in output[-1][2]:
                output[-1][2].append(note[0])
        else:
            currentStartBeat = note[1]
            output.append((note[1], note[2], [note[0]]))
    #print("CHORD TO CHANGES output: ",output)
    return (output, allNotes)

def combine_changes_and_scale(changeNotes, scaleNotes):
    changeSet = set(changeNotes)
    scaleSet = set(scaleNotes)

    combinedSet = changeSet | scaleSet
    combinedList = list(combinedSet)
    combinedList.sort()
    return combinedList
