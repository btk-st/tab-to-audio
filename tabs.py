import os
from midiutil import MIDIFile
import fluidsynth
import subprocess





def note_to_midi(note):
    note_base = note[0].upper()
    octave = 1
    accidental = 0

    if len(note) == 2:
        if note[1] == '#':
            accidental = 1
        elif note[1] == 'b':
            accidental = -1

    base_notes = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    return base_notes[note_base] + accidental + (12 * octave)


def get_midi_note(tuning, fret):
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    tuning_index = note_names.index(tuning)
    midi_note = (tuning_index + fret) + 12  # Adding 12 to start from MIDI note C0
    return midi_note



def parse_tabs(file_name):
    with open(file_name, 'r') as file:
        lines = file.readlines()

    string_tunings = [line.split("|")[0] for line in lines if line.strip()]
    tab_lines = [line.split("|")[1].strip() for line in lines if line.strip()]
    riff = []
    current_positions = [0]*len(string_tunings)
    
    while True:
        current_notes = [None] * len(tab_lines)
        #check end of line
        f = False
        for i, pos in enumerate(current_positions):
            if len(tab_lines[i]) <= pos:
                f = True
                break
        if f: break
        #parse note (3 or 10) or -
        for i in range(len(tab_lines)):
            cur_string_pos = current_positions[i]
            cur_tab_line = tab_lines[i]
            char = cur_tab_line[cur_string_pos]
            #handle '#'
            if char == '-':
                current_positions[i] += 1
                continue
            #handle note
            if char.isdigit():
                fret = char
                if cur_tab_line[cur_string_pos+1].isdigit():
                    fret = fret + cur_tab_line[cur_string_pos+1]
                    current_positions[i] += 1
                note = get_midi_note(string_tunings[i], int(fret))
                if current_notes[i] is None:
                    current_notes[i] = [(note, 1, 1)]
                else:
                    current_notes[i].append((note, 1, 1))
                current_positions[i] += 1

        time = len(riff)
        chord = [note for note in current_notes if note is not None]
        if len(chord) > 0:
            max_duration = max([note[0][1] for note in chord])
            for note in chord:
                if note[0][1] < max_duration:
                    note[0] = (note[0][0], max_duration, note[0][2])
            for note in zip(*chord):
                riff.append(note)
                
    return riff

                
    


def create_midi(riff, tempo, file_name):
    track = 0
    channel = 0
    time = 0
    duration = 1
    volume = 100

    midi_file = MIDIFile(1)
    midi_file.addTempo(track, time, tempo)
    for note_string in riff:
        if len(note_string) == 1 or note_string == (0, 0.5, 1): #single note or silence
            if len(note_string) == 1:
                note_string = note_string[0]
            pitch, octave, length = note_string
            midi_file.addNote(track, channel, pitch + 12 * (octave + 1), time, length * duration, volume)
            time += length * duration
        else:
            # chord
            chord_start_time = time
            for note in note_string:
                pitch, octave, length = note
                midi_file.addNote(
                    track, channel, pitch + 12 * (octave + 1), time,
                    length * duration, volume
                )
            time = chord_start_time + duration
            

    with open(file_name, "wb") as output_file:
        midi_file.writeFile(output_file)




def midi_to_audio(input_midi, soundfont, output_audio):
    command = f'fluidsynth -ni {soundfont} {input_midi} -F {output_audio} -r 44100 -g 1.0'
    subprocess.call(command, shell=True)




tabs_file = "tabs.txt"
riff = parse_tabs(tabs_file)

tempo = 80
midi_file_name = "eyehategod_riff.mid"
create_midi(riff, tempo, midi_file_name)

soundfont = 'Electric_guitar.SF2'
output_audio = "eyehategod_riff.wav"
midi_to_audio(midi_file_name, soundfont, output_audio)
