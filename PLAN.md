# Jazz Chart Analysis Tool - Implementation Plan

## Overview
Rebuilding the jazz chart analysis tool using a modular Python-based approach to improve extensibility and leverage existing music theory libraries.

## Components

### 1. Source (`src/source.py`)
- Handle ingestion of MIDI files.
- Manage local file storage and metadata for source materials.

### 2. Parsing (`src/parse.py`)
- Utilize `music21` (and potentially `mido` or `pretty_midi`) to parse MIDI data.
- Extract raw chord sequences and timing information.

### 3. Analysis (`src/analyze.py`)
- **Progression Detection:** Algorithms to identify common jazz patterns (ii-V-I, turnarounds, etc.).
- **Diatonic Analysis:** Detect non-diatonic notes relative to the current key/chord.
- **Guide Tone Extraction:** Identify and highlight the 3rd and 7th degrees for focused study.

### 4. Rendering (`src/render.py`)
- Use `music21` to generate human-readable MusicXML or PDF outputs.
- Create chord charts with 2-4 chords per measure.
- Integrate visual annotations based on the analysis (e.g., coloring non-diatonic notes, labeling guide tones).

## Implementation Steps
1. **Initialize Project:** Set up Python virtual environment and `requirements.txt`. (Completed)
2. **Scaffold Modules:** Create the directory structure and empty module files. (Completed)
3. **Core Pipeline:** Implement a basic MIDI-to-MusicXML conversion to verify the toolchain. (Completed)
4. **Harmonic Quantization (Current Focus):** Group unquantized human performances into structural chords.
   - Segment the timeline into "buckets" (e.g., half-measure or beat level).
   - Consolidate pitches within each bucket into a single chord.
   - Discard passing tones or short melody notes to determine the fundamental harmony.
5. **Iterative Feature Addition:** Build out the analysis engine and annotation rendering incrementally.
