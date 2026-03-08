from src.pdf_source import load_pdf
from src.render import render_to_musicxml, annotate_score, render_to_pdf
from src.analyze import detect_key, analyze_progression, identify_ii_v_i
from music21 import stream, chord
import os
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_real_pdf.py <path_to_pdf>")
        return
        
    input_pdf = sys.argv[1]
    base_name = os.path.splitext(os.path.basename(input_pdf))[0]
    output_pdf = f"output/{base_name}_annotated.pdf"
    
    print(f"Loading and transcribing {input_pdf} (chords only)...")
    score = load_pdf(input_pdf, include_melody=False)
    
    if score:
        print("Successfully transcribed PDF.")
        
        global_key = detect_key(score)
        print(f"Detected Global Key: {global_key}")

        extracted_symbols = list(score.flatten().getElementsByClass('ChordSymbol'))
        chords_for_rn = [chord.Chord(cs.pitches) for cs in extracted_symbols]
        
        print(f"Extracted {len(extracted_symbols)} chord symbols.")

        roman_numerals = analyze_progression(chords_for_rn, {0.0: global_key})
        
        print("Annotating score with analysis...")
        annotated_score = annotate_score(score, global_key, roman_numerals)

        print(f"Rendering to {output_pdf}...")
        if render_to_pdf(annotated_score, output_pdf):
            print("Pipeline complete!")
            for cs in extracted_symbols:
                print(f"  - Offset {cs.offset}: {cs.figure}")
        else:
            print("Pipeline failed at rendering step.")
    else:
        print("Pipeline failed at loading step.")

if __name__ == "__main__":
    main()
