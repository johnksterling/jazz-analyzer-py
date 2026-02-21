from music21 import converter

def load_midi(file_path):
    """
    Loads a MIDI file and returns a music21 stream object.
    """
    try:
        score = converter.parse(file_path)
        return score
    except Exception as e:
        print(f"Error loading MIDI file {file_path}: {e}")
        return None
