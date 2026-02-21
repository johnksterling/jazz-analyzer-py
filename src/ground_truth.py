import re
import os

def parse_lilypond_chords(filepath, version='ChordsReal'):
    """
    Parses a LilyPond .ly.mako file to extract chord progressions.
    Returns a clean list of chord symbols representing the ground truth.
    """
    if not os.path.exists(filepath):
        print(f"Error: Could not find ground truth file {filepath}")
        return []

    with open(filepath, 'r') as f:
        content = f.read()

    # Extract the relevant block (e.g., % if part=='ChordsReal': ... % endif)
    block_pattern = re.compile(rf"% if part=='{version}':(.*?)% endif", re.DOTALL)
    match = block_pattern.search(content)
    
    if not match:
        print(f"Could not find {version} section in {filepath}")
        return []

    chord_block = match.group(1)
    
    # LilyPond chords: a-g, optional is/es, optional duration, optional colon and quality
    chord_pattern = re.compile(r'\b([a-g])(is|es)?([\d\*\.]*)(?::([a-zA-Z\d\.\-]+))?\b')
    
    chords = []
    
    # Split by whitespace, pipes, braces, newlines
    tokens = re.split(r'[\s\|\}\{\n]+', chord_block)
    
    for token in tokens:
        if token.startswith('\\') or not token:
            continue
            
        match = chord_pattern.match(token)
        if match:
            root = match.group(1).upper()
            accidental = match.group(2)
            duration = match.group(3)
            quality = match.group(4)
            
            if accidental == 'is':
                root += '#'
            elif accidental == 'es':
                root += 'b'
                
            q_str = ''
            if quality:
                if quality.startswith('m7.5-'):
                    q_str = 'm7b5'
                elif quality.startswith('maj7'):
                    q_str = 'maj7'
                elif quality.startswith('m7'):
                    q_str = 'm7'
                elif quality.startswith('m'):
                    q_str = 'm'
                elif quality.startswith('7.9-'):
                    q_str = '7b9'
                elif quality.startswith('7'):
                    q_str = '7'
                elif quality.startswith('dim'):
                    q_str = 'dim'
                else:
                    q_str = quality
                    
            chords.append(f"{root}{q_str}")

    return chords

if __name__ == '__main__':
    filepath = "data/openbook/src/openbook/autumn_leaves.ly.mako"
    real_chords = parse_lilypond_chords(filepath, version='ChordsReal')
    print("Parsed Ground Truth Chords (Real Book):")
    print(real_chords)
