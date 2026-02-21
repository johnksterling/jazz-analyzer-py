import mido
from mido import Message, MidiFile, MidiTrack

def generate_ii_v_i_midi(filename="test_ii_v_i_chromatic.mid"):
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Dm7 (D3, F3, A3, C4)
    # G7#11 (G3, B3, D4, F4, C#5) - C# is non-diatonic in C major
    # Cmaj7 (C3, E3, G3, B3)
    chords = [
        [62, 65, 69, 72],       # Dm7
        [67, 71, 74, 77, 73],   # G7 with C# (non-diatonic)
        [60, 64, 67, 71]        # Cmaj7
    ]

    ticks_per_beat = 480
    duration = ticks_per_beat * 4 # 4 beats per chord

    for chord in chords:
        # Note on
        for note in chord:
            track.append(Message('note_on', note=note, velocity=64, time=0))
        
        # Note off (after duration)
        track.append(Message('note_off', note=chord[0], velocity=64, time=duration))
        for note in chord[1:]:
            track.append(Message('note_off', note=note, velocity=64, time=0))

    mid.save(filename)
    print(f"Generated {filename}")

if __name__ == "__main__":
    generate_ii_v_i_midi()
