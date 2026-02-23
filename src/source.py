import os
import tempfile
import mido
from music21 import converter, instrument

def load_midi(file_path):
    """
    Loads a MIDI file and returns a music21 stream object.
    Filters out percussion (channel 10) to avoid analysis errors.
    """
    try:
        # 1. Pre-filter percussion using mido
        mid = mido.MidiFile(file_path)
        new_mid = mido.MidiFile(type=mid.type)
        new_mid.ticks_per_beat = mid.ticks_per_beat

        for track in mid.tracks:
            new_track = mido.MidiTrack()
            for msg in track:
                if hasattr(msg, 'channel') and msg.channel == 9: # Channel 10 (0-indexed 9) is percussion
                    continue
                new_track.append(msg)
            new_mid.tracks.append(new_track)

        # Save to a temporary file
        fd, tmp_path = tempfile.mkstemp(suffix='.mid')
        os.close(fd)
        new_mid.save(tmp_path)

        # 2. Parse with music21
        score = converter.parse(tmp_path)
        
        # 3. Clean up and return
        os.remove(tmp_path)
        
        # Partition by instrument to separate channels into tracks (helps music21 structure)
        partitioned = instrument.partitionByInstrument(score)
        if partitioned is not None:
            # Filter to isolate Piano and Bass (and general rhythm section)
            allowed_classes = (
                instrument.KeyboardInstrument,
                instrument.ElectricBass,
                instrument.AcousticBass,
                instrument.FretlessBass,
                instrument.Contrabass,
                instrument.Guitar,
            )
            filtered_score = score.__class__()
            for p in partitioned.parts:
                inst = p.getInstrument()
                if isinstance(inst, allowed_classes):
                    filtered_score.insert(0, p)
            
            # If we successfully isolated rhythm section tracks, use them.
            # Otherwise fallback to the partitioned score (in case of un-labeled tracks).
            if len(filtered_score.parts) > 0:
                score = filtered_score
            else:
                score = partitioned
            
        return score
    except Exception as e:
        print(f"Error loading MIDI file {file_path}: {e}")
        return None
