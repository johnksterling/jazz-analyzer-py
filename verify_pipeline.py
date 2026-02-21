from src.source import load_midi
from src.render import render_to_musicxml, annotate_score
from src.parse import extract_chords, get_chord_names
from src.analyze import detect_key, analyze_progression, identify_ii_v_i
import os

def main():
    input_midi = "test_ii_v_i_chromatic.mid"
    output_xml = "output/test_ii_v_i_annotated.musicxml"
    
    print(f"Loading {input_midi}...")
    score = load_midi(input_midi)
    
    if score:
        print("Successfully loaded MIDI.")
        
        # Analyze key
        key = detect_key(score)
        print(f"Analyzed Key: {key}")

        # Parse chords
        chords = extract_chords(score)
        print(f"Detected {len(chords)} chords:")
        for c in chords:
            print(f"  - {c.pitchedCommonName} (Notes: {[n.nameWithOctave for n in c.pitches]})")

        # Roman Numeral Analysis
        roman_numerals = analyze_progression(chords, key)
        print("Roman Numeral Analysis:")
        for rn in roman_numerals:
            print(f"  - {rn.figure} (Scale degrees: {rn.romanNumeral})")

        # Detect Patterns
        ii_v_i_indices = identify_ii_v_i(roman_numerals)
        if ii_v_i_indices:
            print(f"Found ii-V-I progression starting at indices: {ii_v_i_indices}")

        # Annotate
        print("Annotating score with guide tones and non-diatonic highlights...")
        annotated_score = annotate_score(score, key)

        print(f"Rendering to {output_xml}...")
        if render_to_musicxml(annotated_score, output_xml):
            print("Pipeline verification successful!")
        else:
            print("Pipeline verification failed at rendering step.")
    else:
        print("Pipeline verification failed at loading step.")

if __name__ == "__main__":
    main()
