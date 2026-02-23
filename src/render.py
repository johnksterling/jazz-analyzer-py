import os
from music21 import chord, note, clef

def render_to_musicxml(score, output_path):
    """
    Renders a music21 score to a MusicXML file.
    Ensures Treble Clef for lead sheet readability.
    """
    try:
        # Explicitly set Treble Clef for all parts
        for p in score.parts:
            p.insert(0, clef.TrebleClef())
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        score.write('musicxml', fp=output_path)
        print(f"Rendered to {output_path}")
        return True
    except Exception as e:
        print(f"Error rendering to MusicXML: {e}")
        return False

def annotate_score(score, key, roman_numerals=None, local_keys=None):
    """
    Annotates the score with guide tones, non-diatonic highlights, Roman Numerals,
    actual Chord Symbols (e.g., Gmin7), and sequence brackets (e.g., ii-V-I).
    Modifies the score in place.
    """
    from src.analyze import get_guide_tones, is_diatonic, guess_jazz_chord, identify_ii_v_i
    from music21 import harmony, spanner, expressions
    
    # Extract chords in the same order they would be analyzed
    chords = list(score.flatten().getElementsByClass(chord.Chord))
    
    # Add sequences if Roman Numerals are provided
    if roman_numerals:
        ii_v_i_indices = identify_ii_v_i(roman_numerals)
        for idx in ii_v_i_indices:
            if idx + 2 < len(chords):
                ii_chord = chords[idx]
                v_chord = chords[idx+1]
                i_chord = chords[idx+2]
                
                # Draw a bracket connecting ii and V
                bracket = spanner.Line(ii_chord, v_chord)
                bracket.lineType = 'solid'
                bracket.startHeight = 15
                bracket.endHeight = 15
                score.insert(0, bracket)
                
                # Draw an arrow (another line) from V to I
                arrow = spanner.Line(v_chord, i_chord)
                arrow.lineType = 'solid'
                # MusicXML rendering of this might vary, but logically it connects them
                score.insert(0, arrow)
                
                # Add text label above the ii chord
                te = expressions.TextExpression("ii-V-I")
                te.style.fontSize = 12
                # Ensure we insert it into the part, not the top level score if possible
                part = score.parts[0] if score.parts else score
                part.insert(ii_chord.offset, te)
    
    for i, el in enumerate(chords):
        # Determine the local key for this chord
        current_key = key
        if local_keys:
            window_start = (el.offset // 16.0) * 16.0
            current_key = local_keys.get(window_start, key)
            
        # 1. Add Chord Symbols (Lead Sheet style) using the intelligent guesser
        try:
            symbol_str = guess_jazz_chord(el, current_key)
            if symbol_str != "?":
                cs = harmony.ChordSymbol(symbol_str)
                # Find the part to insert the chord symbol into (above the staff)
                if score.parts:
                    score.parts[0].insert(el.offset, cs)
                else:
                    score.insert(el.offset, cs)
        except Exception:
            # If identification fails completely, skip the symbol
            pass

        guide_tones = get_guide_tones(el)
        third = guide_tones.get('third')
        seventh = guide_tones.get('seventh')
        
        # Label guide tones in lyrics
        lyrics = []
        if third:
            lyrics.append("3")
        if seventh:
            lyrics.append("7")
            
        if roman_numerals and i < len(roman_numerals):
            # Add the Roman Numeral figure
            lyrics.append(roman_numerals[i].figure)
        
        if lyrics:
            el.lyric = "/".join(lyrics)
        
        # Color non-diatonic notes within the chord if possible
        has_non_diatonic = False
        for p in el.pitches:
            if not is_diatonic(p, key):
                has_non_diatonic = True
                break
        
        if has_non_diatonic:
            el.style.color = 'red'
            if el.lyric:
                el.lyric += " (non-dia)"
            else:
                el.lyric = "non-dia"
    
    # Also color individual notes if they exist (not inside a chord)
    for el in score.flatten().getElementsByClass(note.Note):
        if not is_diatonic(el.pitch, key):
            el.style.color = 'red'
            el.lyric = "non-dia"
            
    return score
