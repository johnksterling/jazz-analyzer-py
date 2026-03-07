import os
import cv2
import numpy as np
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from src.pdf_parse import align_chords_to_staves
from music21 import stream

def load_pdf(file_path):
    """
    Loads a scanned PDF lead sheet, extracts staff lines and chord symbols via OCR/OMR,
    and returns a music21 Score object populated with the identified harmony.
    Supports multi-page documents.
    """
    try:
        doc = fitz.open(file_path)
        combined_score = stream.Score()
        full_chord_part = stream.Part()
        current_measure = 0
        
        for page_idx in range(doc.page_count):
            page = doc[page_idx]
            print(f"Processing page {page_idx + 1}/{doc.page_count}...")
            
            # 1. Render to image
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            
            # Load with OpenCV for staff detection
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Use adaptive thresholding to handle variations in scan quality better
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
            
            # 2. Detect horizontal staff lines
            width = img.shape[1]
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (width // 40, 1))
            detect_horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
            
            cnts = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = cnts[0] if len(cnts) == 2 else cnts[1]
            
            horizontal_lines = []
            for c in cnts:
                x, y, w, h = cv2.boundingRect(c)
                if w > width // 4: # Long lines are staff lines
                    horizontal_lines.append(y)
                    
            horizontal_lines.sort()
            
            # Group staff lines into systems
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
                
            # Detect vertical bar lines
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            detect_vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
            
            cnts = cv2.findContours(detect_vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = cnts[0] if len(cnts) == 2 else cnts[1]
            
            bar_lines = []
            for c in cnts:
                x, y, w, h = cv2.boundingRect(c)
                if h > 40 and h < 300: 
                    bar_lines.append((x, y, w, h))
                    
            system_bars = {i: [] for i in range(len(systems))}
            for x, y, w, h in bar_lines:
                mid_y = y + (h/2)
                for i, (sys_top, sys_bot) in enumerate(systems):
                    if sys_top - 20 <= mid_y <= sys_bot + 20:
                        # Merge close barlines to prevent duplicates
                        if not any(abs(bx - x) < 20 for bx in system_bars[i]):
                            system_bars[i].append(x)
                        break
            for i in system_bars:
                system_bars[i].sort()
                
            # 3. OCR for text
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
                    page_chords.append({
                        'text': text,
                        'x': x,
                        'y': y,
                        'system': assigned_system
                    })
            
            # 4. Align OCR'd chords to the timeline for this page
            page_chord_part, next_measure = align_chords_to_staves(page_chords, systems, system_bars, start_measure=current_measure)
            
            # Merge into full part
            for el in page_chord_part.flatten():
                full_chord_part.insert(el.offset, el)
            
            current_measure = next_measure
        
        combined_score.insert(0, full_chord_part)
        return combined_score
        
    except Exception as e:
        print(f"Error loading PDF file {file_path}: {e}")
        return None
