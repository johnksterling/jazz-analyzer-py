import os
import cv2
import numpy as np
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import subprocess
from src.pdf_parse import align_chords_to_staves
from music21 import stream, converter

def run_omr(img_path):
    """
    Runs oemer on an image and returns the parsed music21 score.
    """
    print(f"Running OMR on {img_path}...")
    try:
        # Run oemer command with -d to skip problematic deskewing
        subprocess.run(["./venv/bin/oemer", "-d", img_path], check=True, capture_output=True)
        
        # Oemer outputs a musicxml file with the same name as the image
        xml_path = os.path.splitext(img_path)[0] + ".musicxml"
        if os.path.exists(xml_path):
            score = converter.parse(xml_path)
            # Cleanup
            os.remove(xml_path)
            return score
    except Exception as e:
        print(f"OMR failed for {img_path}: {e}")
    return None

def load_pdf(file_path, include_melody=True):
    """
    Loads a scanned PDF lead sheet, extracts staff lines and chord symbols via OCR/OMR,
    and returns a music21 Score object populated with the identified harmony and melody.
    """
    try:
        doc = fitz.open(file_path)
        combined_score = stream.Score()
        
        # We'll use one part for melody and one for chords if OMR is enabled
        melody_part = stream.Part()
        melody_part.id = 'Melody'
        chord_part = stream.Part()
        chord_part.id = 'Chords'
        
        current_measure = 0
        
        for page_idx in range(doc.page_count):
            page = doc[page_idx]
            print(f"Processing page {page_idx + 1}/{doc.page_count}...")
            
            # 1. Render to image
            pix = page.get_pixmap(dpi=300)
            img_path = f"tmp_page_{page_idx}.png"
            pix.save(img_path)
            
            # 2. Detect barlines and systems (needed for OCR alignment)
            img_data = pix.tobytes("png")
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
            
            width = img.shape[1]
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (width // 40, 1))
            detect_horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
            cnts = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = cnts[0] if len(cnts) == 2 else cnts[1]
            
            horizontal_lines = sorted([cv2.boundingRect(c)[1] for c in cnts if cv2.boundingRect(c)[2] > width // 4])
            systems = []
            if horizontal_lines:
                current_system = [horizontal_lines[0]]
                for y in horizontal_lines[1:]:
                    if y - current_system[-1] < 60:
                        current_system.append(y)
                    else:
                        systems.append((current_system[0], current_system[-1]))
                        current_system = [y]
                systems.append((current_system[0], current_system[-1]))
                
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            detect_vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
            cnts = cv2.findContours(detect_vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = cnts[0] if len(cnts) == 2 else cnts[1]
            
            system_bars = {i: [] for i in range(len(systems))}
            for c in cnts:
                x, y, w, h = cv2.boundingRect(c)
                if 40 < h < 300:
                    mid_y = y + (h/2)
                    for i, (sys_top, sys_bot) in enumerate(systems):
                        if sys_top - 20 <= mid_y <= sys_bot + 20:
                            if not any(abs(bx - x) < 20 for bx in system_bars[i]):
                                system_bars[i].append(x)
                            break
            for i in system_bars: system_bars[i].sort()
            
            # 3. OCR Pass
            pil_img = Image.open(io.BytesIO(img_data))
            ocr_data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
            page_chords = []
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                if not text: continue
                x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                
                assigned_system = -1
                for sys_idx, (sys_top, sys_bot) in enumerate(systems):
                    if sys_top - 150 < y < sys_top:
                        assigned_system = sys_idx
                        break
                if assigned_system != -1:
                    page_chords.append({'text': text, 'x': x, 'y': y, 'w': w, 'h': h, 'system': assigned_system})
            
            # 3.5 Grouping and Aligning Chords
            grouped_chords = []
            if page_chords:
                page_chords.sort(key=lambda c: (c['system'], c['x']))
                curr = page_chords[0]
                for nxt in page_chords[1:]:
                    bars = system_bars.get(curr['system'], [])
                    if nxt['system'] == curr['system'] and \
                       not any(curr['x'] + curr['w'] < bx < nxt['x'] for bx in bars) and \
                       nxt['x'] - (curr['x'] + curr['w']) < 40:
                        curr['text'] += nxt['text']
                        curr['w'] = (nxt['x'] + nxt['w']) - curr['x']
                    else:
                        grouped_chords.append(curr)
                        curr = nxt
                grouped_chords.append(curr)
            
            page_chord_part, next_measure = align_chords_to_staves(grouped_chords, systems, system_bars, start_measure=current_measure)
            for el in page_chord_part.flatten():
                chord_part.insert(el.offset, el)
            
            # 4. Optional OMR Pass for Melody
            if include_melody:
                page_score = run_omr(img_path)
                if page_score:
                    # Shift offsets of OMR elements to the current measure
                    shift = current_measure * 4.0
                    for p in page_score.parts:
                        for el in p.flatten():
                            # We don't want to double-insert barlines or metadata
                            if el.classSortOrder >= 0: # Notes, chords, rests, etc.
                                melody_part.insert(el.offset + shift, el)
                                
            # Cleanup temp image
            if os.path.exists(img_path):
                os.remove(img_path)
                
            current_measure = next_measure
            
        combined_score.insert(0, melody_part)
        combined_score.insert(0, chord_part)
        return combined_score
        
    except Exception as e:
        print(f"Error loading PDF file {file_path}: {e}")
        return None

        
    except Exception as e:
        print(f"Error loading PDF file {file_path}: {e}")
        return None
