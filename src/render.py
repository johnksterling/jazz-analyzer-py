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

def annotate_score(score, key, roman_numerals=None):
    """
    Annotates the score with guide tones, non-diatonic highlights, Roman Numerals,
    and actual Chord Symbols (e.g., Gmin7).
    Modifies the score in place.
    """
    from src.analyze import get_guide_tones, is_diatonic
    from music21 import harmony
    
    # Extract chords in the same order they would be analyzed
    chords = list(score.flatten().getElementsByClass(chord.Chord))
    
    for i, el in enumerate(chords):
        # 1. Add Chord Symbols (Lead Sheet style)
        try:
            cs = harmony.chordSymbolFromChord(el)
            # Find the part to insert the chord symbol into (above the staff)
            # In our current pipeline, we only have one part in the score being rendered.
            score.parts[0].insert(el.offset, cs)
        except Exception:
            # If identification fails, skip the symbol
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
