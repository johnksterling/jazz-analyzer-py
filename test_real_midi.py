from src.source import load_midi
from src.render import render_to_musicxml, annotate_score
from src.parse import quantize_harmony, get_chord_names
from src.analyze import detect_key, analyze_progression, identify_ii_v_i, identify_tritone_subs
from music21 import instrument, stream
import os
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_real_midi.py <path_to_midi>")
        return

    input_midi = sys.argv[1]
    base_name = os.path.splitext(os.path.basename(input_midi))[0]
    output_xml = f"output/{base_name}_quantized.musicxml"
    
    print(f"Loading {input_midi}...")
    score = load_midi(input_midi)
    
    if score:
        print("Successfully loaded MIDI.")
        print(f"Pitched tracks/parts: {len(score.parts)}")

        if len(score.parts) == 0:
            print("No pitched tracks found. Exiting.")
            return

        # Analyze key
        try:
            key = detect_key(score)
            print(f"Analyzed Key: {key}")
        except Exception as e:
            print(f"Failed to detect key: {e}")
            key = None

        if key:
            # Quantize Harmony
            print("Quantizing harmony into 2-beat buckets...")
            quantized_part = quantize_harmony(score, beats_per_chord=2.0)
            
            # Extract chords from the quantized part
            chords = list(quantized_part.getElementsByClass('Chord'))
            print(f"Detected {len(chords)} quantized chords. Showing first 10:")
            for c in chords[:10]:
                print(f"  - {c.pitchedCommonName} (Offset: {c.offset})")

            # Roman Numeral Analysis
            print("Performing Roman Numeral Analysis...")
            roman_numerals = analyze_progression(chords, key)
            
            # Detect Patterns
            ii_v_i_indices = identify_ii_v_i(roman_numerals)
            print(f"Found {len(ii_v_i_indices)} ii-V-I progressions.")

            tritone_subs = identify_tritone_subs(roman_numerals)
            print(f"Found {len(tritone_subs)} tritone substitutions (ii - subV - I).")

            # Annotate
            # Create a new score for rendering with the quantized part
            render_score = stream.Score()
            render_score.insert(0, quantized_part)
            
            print("Annotating quantized score with guide tones and non-diatonic highlights...")
            try:
                annotated_score = annotate_score(render_score, key)

                print(f"Rendering to {output_xml}...")
                if render_to_musicxml(annotated_score, output_xml):
                    print("Pipeline verification successful!")
                else:
                    print("Pipeline verification failed at rendering step.")
            except Exception as e:
                print(f"Annotation or rendering failed: {e}")
    else:
        print("Pipeline verification failed at loading step.")

if __name__ == "__main__":
    main()
