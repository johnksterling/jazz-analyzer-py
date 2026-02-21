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
    Identifies ii-V-I patterns in a list of Roman Numerals using fuzzy matching.
    Matches based on root motion (scale degrees 2 -> 5 -> 1) OR pure root motion 
    intervals (+5 semitones / Perfect 4th up) to handle complex extensions.
    Returns a list of indices where a ii-V-I starts.
    """
    patterns = []
    for i in range(len(roman_numerals) - 2):
        r1 = roman_numerals[i]
        r2 = roman_numerals[i+1]
        r3 = roman_numerals[i+2]
        
        # Method A: Check for root movement: 2 -> 5 -> 1
        sd1 = getattr(r1, 'scaleDegree', None)
        sd2 = getattr(r2, 'scaleDegree', None)
        sd3 = getattr(r3, 'scaleDegree', None)
        
        if sd1 == 2 and sd2 == 5 and sd3 == 1:
            patterns.append(i)
            continue
            
        # Method B: Root-Motion Fuzzy Matching (Down a 5th / Up a 4th)
        try:
            # Get the pitch classes of the roots
            rt1 = r1.root().pitchClass
            rt2 = r2.root().pitchClass
            rt3 = r3.root().pitchClass
            
            # Up a perfect 4th is +5 semitones (or Down a 5th is -7 == +5 mod 12)
            diff1 = (rt2 - rt1) % 12
            diff2 = (rt3 - rt2) % 12
            
            if diff1 == 5 and diff2 == 5:
                # Found a ii-V-I sequence based on root motion!
                patterns.append(i)
        except Exception:
            # If the chord is too mangled to have a root, skip it
            pass
            
    return patterns

def identify_tritone_subs(roman_numerals):
    """
    Identifies tritone substitutions (subV) resolving to a target chord.
    Specifically looks for ii - subV - I (root motion descending by half steps).
    Returns a list of indices where the pattern starts.
    """
    patterns = []
    for i in range(len(roman_numerals) - 2):
        r1 = roman_numerals[i]
        r2 = roman_numerals[i+1]
        r3 = roman_numerals[i+2]
        
        try:
            # Get the pitch classes of the roots
            rt1 = r1.root().pitchClass
            rt2 = r2.root().pitchClass
            rt3 = r3.root().pitchClass
            
            # A tritone substitution resolving down by half step means 
            # the roots move by -1 semitone (or 11 mod 12).
            # e.g., Dm7 -> Db7 -> Cmaj7 (Roots: 2 -> 1 -> 0)
            diff1 = (rt2 - rt1) % 12
            diff2 = (rt3 - rt2) % 12
            
            if diff1 == 11 and diff2 == 11:
                patterns.append(i)
        except Exception:
            pass
            
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
