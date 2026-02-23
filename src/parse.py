from music21 import chord, stream, instrument, note, harmony

def _reduce_to_tertian_chord(raw_chord):
    """
    Builds a basic triad/seventh chord based on the root and present intervals.
    """
    root = raw_chord.root()
    pitch_classes = set(p.pitchClass for p in raw_chord.pitches)
    
    reduced_pitches = [note.Pitch(root.pitchClass)]
    reduced_pitches[0].octave = 3
    
    # Check 3rd
    has_maj3 = (root.pitchClass + 4) % 12 in pitch_classes
    has_min3 = (root.pitchClass + 3) % 12 in pitch_classes
    if has_maj3:
        p3 = note.Pitch((root.pitchClass + 4) % 12); p3.octave = 4; reduced_pitches.append(p3)
    elif has_min3:
        p3 = note.Pitch((root.pitchClass + 3) % 12); p3.octave = 4; reduced_pitches.append(p3)
        
    # Check 7th
    has_min7 = (root.pitchClass + 10) % 12 in pitch_classes
    has_maj7 = (root.pitchClass + 11) % 12 in pitch_classes
    if has_maj7:
        p7 = note.Pitch((root.pitchClass + 11) % 12); p7.octave = 4; reduced_pitches.append(p7)
    elif has_min7:
        p7 = note.Pitch((root.pitchClass + 10) % 12); p7.octave = 4; reduced_pitches.append(p7)

    # Check 5th
    has_dim5 = (root.pitchClass + 6) % 12 in pitch_classes
    has_aug5 = (root.pitchClass + 8) % 12 in pitch_classes
    has_perf5 = (root.pitchClass + 7) % 12 in pitch_classes
    
    if has_dim5 and not has_perf5:
        p5 = note.Pitch((root.pitchClass + 6) % 12); p5.octave = 4; reduced_pitches.append(p5)
    elif has_aug5 and not has_perf5:
        p5 = note.Pitch((root.pitchClass + 8) % 12); p5.octave = 4; reduced_pitches.append(p5)
    else: 
        p5 = note.Pitch((root.pitchClass + 7) % 12); p5.octave = 4; reduced_pitches.append(p5)
        
    return chord.Chord(reduced_pitches)

def quantize_harmony(score, beats_per_chord=4.0):
    """
    Groups notes from a score into structural chords aligned to a grid.
    """
    quantized_stream = stream.Part()
    # Apply a small offset shift (0.5 beats) to catch 'laid back' jazz entries
    shift = 0.5
    total_length = score.highestTime
    all_elements = score.flatten().notes
    
    current_offset = 4.0 # Start at beat 4 to skip potential intro/pickup
    while current_offset <= total_length:
        window_start = current_offset + shift
        window_end = current_offset + beats_per_chord + shift
        
        # 1. Collect all pitches in this window
        window_pitches = []
        for el in all_elements:
            el_end = el.offset + el.duration.quarterLength
            if el.offset < window_end and el_end > window_start:
                if min(el_end, window_end) - max(el.offset, window_start) >= 0.5:
                    if hasattr(el, 'pitches'): window_pitches.extend(el.pitches)
                    elif hasattr(el, 'pitch'): window_pitches.append(el.pitch)

        if window_pitches:
            # 2. Find the anchor bass (the root)
            # Find the notes that start earliest in this window
            valid_elements = [el for el in all_elements if (hasattr(el, 'pitch') or hasattr(el, 'pitches')) and el.offset < window_end and (el.offset + el.duration.quarterLength) > window_start and (min(el.offset + el.duration.quarterLength, window_end) - max(el.offset, window_start)) >= 0.5]
            
            if valid_elements:
                earliest_offset = min(el.offset for el in valid_elements)
                
                # Allow a small 0.5 beat margin to catch simultaneously struck notes
                earliest_pitches = []
                for el in valid_elements:
                    if el.offset <= earliest_offset + 0.5:
                        if hasattr(el, 'pitches'): earliest_pitches.extend(el.pitches)
                        elif hasattr(el, 'pitch'): earliest_pitches.append(el.pitch)

                if earliest_pitches:
                    earliest_pitches.sort(key=lambda p: p.midi)
                    anchor_bass = earliest_pitches[0]
                else:
                    window_pitches.sort(key=lambda p: p.midi)
                    anchor_bass = window_pitches[0]
            else:
                window_pitches.sort(key=lambda p: p.midi)
                anchor_bass = window_pitches[0]

            unique_pcs = sorted(list(set(p.pitchClass for p in window_pitches)))
            reduced_pitches = []
            for pc in unique_pcs:
                p = note.Pitch(pc)
                p.octave = 3 if pc == anchor_bass.pitchClass else 4
                reduced_pitches.append(p)
            
            raw_chord = chord.Chord(reduced_pitches)
            raw_chord.root(anchor_bass)
            
            clean_chord = _reduce_to_tertian_chord(raw_chord)
            clean_chord.duration.quarterLength = beats_per_chord
            
            try:
                sym = harmony.chordSymbolFigureFromChord(clean_chord)
                if sym != 'Chord Symbol Cannot Be Identified':
                    clean_chord.chord_symbol_figure = sym
            except:
                pass
            
            quantized_stream.insert(current_offset, clean_chord)
            
        current_offset += beats_per_chord
        
    return quantized_stream

def extract_chords(score):
    """
    Extracts chords from a music21 score.
    Returns a list of music21.chord.Chord objects.
    """
    chords = []
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
