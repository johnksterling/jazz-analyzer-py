import os
from music21 import chord, note

def render_to_musicxml(score, output_path):
    """
    Renders a music21 score to a MusicXML file.
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        score.write('musicxml', fp=output_path)
        print(f"Rendered to {output_path}")
        return True
    except Exception as e:
        print(f"Error rendering to MusicXML: {e}")
        return False

def annotate_score(score, key):
    """
    Annotates the score with guide tones and non-diatonic highlights.
    Modifies the score in place.
    """
    from src.analyze import get_guide_tones, is_diatonic
    
    # Iterate over all elements that are chords or notes
    for el in score.flatten().recurse():
        if isinstance(el, chord.Chord):
            guide_tones = get_guide_tones(el)
            third = guide_tones.get('third')
            seventh = guide_tones.get('seventh')
            
            # Label guide tones in lyrics
            lyrics = []
            if third:
                lyrics.append("3")
            if seventh:
                lyrics.append("7")
            
            if lyrics:
                el.lyric = "/".join(lyrics)
            
            # Color non-diatonic notes within the chord if possible
            # In music21, we can't easily color individual notes within a chord 
            # for all output formats, but we can try to label them.
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
        
        elif isinstance(el, note.Note):
            if not is_diatonic(el.pitch, key):
                el.style.color = 'red'
                el.lyric = "non-dia"
            
    return score
