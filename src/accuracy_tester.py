from src.source import load_midi
from src.parse import quantize_harmony
from src.ground_truth import parse_lilypond_chords
from music21 import harmony
import sys
import os

def test_accuracy(midi_file, mako_file):
    print(f"--- Accuracy Test: {os.path.basename(midi_file)} ---")
    
    # 1. Get Ground Truth
    ground_truth = parse_lilypond_chords(mako_file)
    print(f"Ground Truth Chords: {len(ground_truth)}")
    print(" ".join(ground_truth[:12]) + " ...")
    
    # 2. Run Pipeline
    score = load_midi(midi_file)
    if not score or len(score.parts) == 0:
        print("Failed to load MIDI.")
        return
        
    print(f"\\nAnalyzing MIDI ({len(score.parts)} tracks)...")
    quantized_part = quantize_harmony(score, beats_per_chord=2.0)
    
    # Run the full analysis pipeline so context-aware heuristics are applied
    from src.analyze import detect_local_keys, analyze_progression, guess_jazz_chord
    try:
        local_keys, global_key = detect_local_keys(quantized_part, window_size=16.0)
        chords = list(quantized_part.getElementsByClass('Chord'))
        # This function modifies the chords in place to fix rootless voicings
        analyze_progression(chords, local_keys, window_size=16.0)
    except Exception as e:
        print(f"Analysis failed: {e}")
        chords = list(quantized_part.getElementsByClass('Chord'))
        local_keys = {0.0: global_key} if 'global_key' in locals() else {}
    
    # Extract chords from pipeline
    analyzed_chords = []
    
    for c in chords:
        window_start = (c.offset // 16.0) * 16.0
        current_key = local_keys.get(window_start, list(local_keys.values())[0] if local_keys else None)
        
        # Use our new intelligent jazz chord guesser
        symbol = guess_jazz_chord(c, current_key) if current_key else "?"
        analyzed_chords.append(symbol)
            
    print(f"Analyzed Chords (2-beat buckets): {len(analyzed_chords)}")
    
    # 3. Simple Alignment & Comparison
    print("\\n--- Comparison (First 20 Chords) ---")
    print(f"{'Ground Truth':<20} | {'Analyzed Output':<20}")
    print("-" * 45)
    
    for i in range(min(20, len(ground_truth), len(analyzed_chords))):
        gt = ground_truth[i]
        an = analyzed_chords[i]
        
        match = "Y" if gt == an else "N"
        print(f"{gt:<20} | {an:<20} {match}")

if __name__ == '__main__':
    midi = "data/autumn_leaves_bushgrafts.mid"
    mako = "data/openbook/src/openbook/autumn_leaves.ly.mako"
    test_accuracy(midi, mako)
