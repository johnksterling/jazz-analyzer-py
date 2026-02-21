from music21 import chord, stream, instrument, note

def quantize_harmony(score, beats_per_chord=2.0):
    """
    Groups notes from a score into structural chords aligned to a grid.
    Returns a new Stream containing the quantized chords.
    """
    quantized_stream = stream.Part()
    total_length = score.highestTime
    
    # Flatten the score once for efficient note extraction
    all_notes = score.flatten().getElementsByClass(note.Note)
    
    current_offset = 0.0
    while current_offset < total_length:
        window_end = current_offset + beats_per_chord
        
        # Find all notes that overlap with this window
        window_pitches = []
        for n in all_notes:
            # Check for overlap: note starts before window ends AND ends after window starts
            note_end = n.offset + n.duration.quarterLength
            if n.offset < window_end and note_end > current_offset:
                # Calculate the duration of the overlap within this specific window
                overlap_start = max(n.offset, current_offset)
                overlap_end = min(note_end, window_end)
                overlap_duration = overlap_end - overlap_start
                
                # Only include notes that sustain for a significant portion of the window
                # (e.g., at least 25% of the window or a 16th note, whichever is smaller)
                if overlap_duration > min(0.25, beats_per_chord * 0.25):
                    window_pitches.append(n.pitch)
        
        if window_pitches:
            # Create a unique set of pitch classes to avoid duplicates
            unique_pitch_classes = sorted(list(set(p.pitchClass for p in window_pitches)))
            
            # Map all pitch classes to Octave 4 for a clean, playable cluster
            reduced_pitches = []
            for pc in unique_pitch_classes:
                new_pitch = note.Pitch(pc)
                new_pitch.octave = 4
                reduced_pitches.append(new_pitch)
            
            if reduced_pitches:
                # Sort the pitches within the octave so the chord is structured correctly
                reduced_pitches.sort()
                new_chord = chord.Chord(reduced_pitches)
                new_chord.duration.quarterLength = beats_per_chord
                quantized_stream.insert(current_offset, new_chord)
        
        current_offset += beats_per_chord
        
    return quantized_stream

def extract_chords(score):
    """
    Extracts chords from a music21 score.
    Returns a list of music21.chord.Chord objects.
    """
    chords = []
    
    # We use chordify to combine notes from different tracks into chords
    chords_stream = score.chordify()
    
    for element in chords_stream.recurse():
        if isinstance(element, chord.Chord):
            chords.append(element)
            
    return chords

def get_chord_names(chords):
    """
    Returns a list of common names for the given chords.
    """
    return [c.pitchedCommonName for c in chords]
