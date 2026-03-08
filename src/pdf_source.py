import os
import cv2
import numpy as np
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import subprocess
from src.pdf_parse import align_chords_to_staves
from src.ai_vision import extract_chords_with_ai
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

def load_pdf(file_path, include_melody=True, use_ai_chords=True):
    """
    Loads a scanned PDF lead sheet, extracts staff lines and chord symbols via OCR/OMR/AI,
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
            
            # 2. Detect barlines and systems (needed for alignment)
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
            
            # 3. Chord Extraction (AI or OCR)
            page_chords = []
            pil_img = Image.open(io.BytesIO(img_data))
            
            for sys_idx, (sys_top, sys_bot) in enumerate(systems):
                # Crop a horizontal slice from 150px above the staff to the top of the staff
                crop_top = max(0, sys_top - 150)
                if sys_idx > 0:
                    crop_top = max(crop_top, systems[sys_idx-1][1] + 10)
                
                crop_box = (0, crop_top, pil_img.width, sys_top)
                sys_slice_path = f"tmp_sys_{page_idx}_{sys_idx}.png"
                pil_img.crop(crop_box).save(sys_slice_path)

                if use_ai_chords and os.environ.get("GEMINI_API_KEY"):
                    print(f"  AI extracting chords for system {sys_idx}...")
                    ai_chords = extract_chords_with_ai(sys_slice_path)
                    for ac in ai_chords:
                        page_chords.append({
                            'text': ac.chord_symbol,
                            'x': ac.horizontal_percentage * pil_img.width,
                            'w': 50, # Approximate width
                            'system': sys_idx
                        })
                else:
                    # Fallback to Tesseract OCR
                    print(f"  OCR extracting chords for system {sys_idx}...")
                    ocr_data = pytesseract.image_to_data(Image.open(sys_slice_path), output_type=pytesseract.Output.DICT)
                    for i in range(len(ocr_data['text'])):
                        text = ocr_data['text'][i].strip()
                        if not text: continue
                        page_chords.append({
                            'text': text,
                            'x': ocr_data['left'][i],
                            'w': ocr_data['width'][i],
                            'system': sys_idx
                        })
                
                if os.path.exists(sys_slice_path):
                    os.remove(sys_slice_path)
            
            # 3.5 Grouping and Aligning Chords
            grouped_chords = []
            if page_chords:
                page_chords.sort(key=lambda c: (c['system'], c['x']))
                curr = page_chords[0]
                for nxt in page_chords[1:]:
                    bars = system_bars.get(curr['system'], [])
                    if nxt['system'] == curr['system'] and \
                       not any(curr['x'] + curr.get('w', 0) < bx < nxt['x'] for bx in bars) and \
                       nxt['x'] - (curr['x'] + curr.get('w', 0)) < 40:
                        curr['text'] += nxt['text']
                        curr['w'] = (nxt['x'] + nxt.get('w', 0)) - curr['x']
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
                    shift = current_measure * 4.0
                    for p in page_score.parts:
                        for el in p.flatten():
                            if el.classSortOrder >= 0:
                                melody_part.insert(el.offset + shift, el)
                                
            if os.path.exists(img_path):
                os.remove(img_path)
                
            current_measure = next_measure
            
        combined_score.insert(0, melody_part)
        combined_score.insert(0, chord_part)
        return combined_score
        
    except Exception as e:
        print(f"Error loading PDF file {file_path}: {e}")
        return None
