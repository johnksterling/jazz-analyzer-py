from music21 import chord, stream, instrument, note

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
