from music21 import roman, chord

def detect_key(score):
    """
    Analyzes the key of the score.
    """
    return score.analyze('key')

def analyze_progression(chords, key):
    """
    Performs Roman Numeral analysis on a list of chords given a key.
    """
    analysis = []
    for c in chords:
        rn = roman.romanNumeralFromChord(c, key)
        analysis.append(rn)
    return analysis

def identify_ii_v_i(roman_numerals):
    """
    Identifies ii-V-I patterns in a list of Roman Numerals.
    Returns a list of indices where a ii-V-I starts.
    """
    patterns = []
    for i in range(len(roman_numerals) - 2):
        r1 = roman_numerals[i]
        r2 = roman_numerals[i+1]
        r3 = roman_numerals[i+2]
        
        # Check for ii - V - I (or variations like ii7 - V7 - I7)
        if (r1.romanNumeral == 'ii' or r1.romanNumeral == 'II') and \
           (r2.romanNumeral == 'V') and \
           (r3.romanNumeral == 'I'):
            patterns.append(i)
    return patterns

def get_guide_tones(c):
    """
    Identifies the 3rd and 7th of a chord.
    Returns a dictionary with 'third' and 'seventh' pitches.
    """
    res = {}
    # Use getChordStep(3) which returns the pitch at that step
    third = c.getChordStep(3)
    seventh = c.getChordStep(7)
    
    if third:
        res['third'] = third
    if seventh:
        res['seventh'] = seventh
    
    return res

def is_diatonic(pitch, key):
    """
    Checks if a pitch is diatonic to the given key.
    """
    return pitch.name in [p.name for p in key.pitches]

def analyze_non_diatonic_notes(chord_obj, key):
    """
    Identifies notes in a chord that are non-diatonic to the key.
    """
    non_diatonic = []
    for p in chord_obj.pitches:
        if not is_diatonic(p, key):
            non_diatonic.append(p)
    return non_diatonic
