import re
from music21 import harmony, stream, note

def clean_ocr_chord(ocr_text):
    """
    Attempts to clean up noisy OCR text into a valid jazz chord symbol.
    """
    if not ocr_text:
        return None
        
    text = ocr_text
    
    # Exact or highly specific replacements first
    exact_replacements = {
        'eb7it)': 'Eb7#9',
        'eb7t)': 'Eb7#9',
        'éma7': 'Ebmaj7',
        'abe)': 'Ab7',
        'éua7': 'Ebmaj7',
        'A7be)': 'Ab7',
        'Abuill': 'Abm11',
        "gpa7k’)": 'Gbmaj7',
        "ark)": 'Am7', # Context: likely Am7 or just m7
        'Earls)': 'Emaj7',
        'a7hs)': 'A7#9',
        '¢buid': 'C#m7',
        'eb7%)': 'Eb7#9',
        'Qh': 'Db9',
        'Bp47': 'Bbmaj7',
        'cui7le)': 'Cm7b5',
        'chuid': 'C#m7',
        'abs': 'Ab9',
        'Abui7': 'Abm7',
        'evil': '7#9', 
        'ess': '7#9',
    }
    
    for k, v in exact_replacements.items():
        if k in text:
            text = text.replace(k, v)
            
    # General substring replacements
    general_replacements = {
        'buid': 'bm7',
        'uid': 'm7',
        'ui': 'm',
        'mi9': 'm9',
        'mi': 'm',
        'le': 'b',
        '7H': '7#',
        'ss': '5',
        'gs': '9',
        'eli': '7',
        'p4': 'maj',
        'Bruit': 'Bmin7',
        'eid': 'm7',
        'ehi9': 'Bbmi9', # Common misread in ACB font
        'é7i': 'Eb7',
        '$m': 'Am',
        'Onid': 'Dmi7',
        'Cnii9': 'Cmi9',
        'Abwaed': 'Abmaj7',
        'efuid': 'Ebm7',
        'MA7': 'maj7',
        'ma9': 'M9',
        'maj9': 'M9',
        'Maj7': 'maj7',
    }
    
    for k, v in general_replacements.items():
        if k in text:
            text = text.replace(k, v)
            
    # Remove obvious noise (now excluding parentheses entirely)
    text = re.sub(r'[^a-zA-Z0-9#b\-\ø^]', '', text)
    
    # Clean up any trailing garbage characters that slipped through
    text = text.strip('()')
    
    # Convert flat root notes from 'b' to '-' for music21 compatibility
    # e.g., Bbmaj7 -> B-maj7, Abm7 -> A-m7
    text = re.sub(r'^([A-G])b', r'\1-', text)
        
    # Try to parse with music21 to see if it's valid
    try:
        cs = harmony.ChordSymbol(text)
        if cs.figure and "Cannot" not in cs.figure:
            return cs
    except Exception:
        pass
        
    if text:
        print(f"Failed to parse OCR chord: '{ocr_text}' -> '{text}'")
    return None

def align_chords_to_staves(chords_data, staves_data, barlines_data, start_measure=0):
    """
    A more advanced alignment engine.
    Maps X-coordinates of chords to a timeline using detected barlines.
    """
    s = stream.Part()
    beats_per_measure = 4.0
    
    # Group chords by system
    system_chords = {}
    for c in chords_data:
        sys = c['system']
        if sys not in system_chords:
            system_chords[sys] = []
        system_chords[sys].append(c)
        
    global_measure_count = start_measure
    
    for sys_idx in range(len(staves_data)):
        chords = system_chords.get(sys_idx, [])
        chords.sort(key=lambda c: c['x'])
        
        bars = barlines_data.get(sys_idx, [])
        if len(bars) < 2:
            # Fallback if no barlines detected for this system (assume 4 measures)
            bars = [500, 1000, 1500, 2000, 2500]
            
        for c in chords:
            sym = clean_ocr_chord(c['text'])
            if not sym: continue
            
            # Determine which measure this chord falls into
            measure_index = 0
            for bx in bars:
                # If chord is to the right of the barline (with a small margin)
                if c['x'] > bx - 30:
                    measure_index += 1
            
            # If the chord is before the very first barline, it's measure 0
            if measure_index > 0:
                measure_index -= 1
                
            # Determine offset within the measure (proportional guess)
            bar_start = bars[measure_index] if measure_index < len(bars) else 0
            bar_end = bars[measure_index + 1] if measure_index + 1 < len(bars) else 2500
            bar_width = max(bar_end - bar_start, 1)
            
            relative_x = max(c['x'] - bar_start, 0)
            prop = relative_x / bar_width
            
            # Snap to nearest 2 beats (beats 1 or 3)
            raw_beat = prop * beats_per_measure
            snapped_beat = round(raw_beat / 2.0) * 2.0
            # Ensure it doesn't snap outside the measure
            snapped_beat = min(snapped_beat, beats_per_measure - 0.5)
            
            global_offset = (global_measure_count + measure_index) * beats_per_measure + snapped_beat
            
            # If we already have a chord at this exact offset, shift it slightly to avoid overlap errors in m21
            while s.getElementsByOffset(global_offset):
                global_offset += 2.0
                
            s.insert(global_offset, sym)
            
        # Add visible placeholder notes to every measure so the renderer doesn't collapse them
        num_measures = max(len(bars) - 1, 4)
        for i in range(num_measures):
            # LilyPond drops chords attached to pure rests. We must use a Note.
            # We use a middle C but set its notehead and stem to be invisible.
            n = note.Note('C4', type='whole')
            n.style.hideObjectOnPrint = True # Hide the notehead
            s.insert((global_measure_count + i) * beats_per_measure, n)
            
        # Advance global measure count by the number of measures in this system
        global_measure_count += num_measures
                
    return s, global_measure_count
