from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import math
import os
import sys

# Check Python environment on startup
print(f"🐍 Python executable: {sys.executable}")
print(f"🐍 Python version: {sys.version.split()[0]}")
try:
    import reportlab
    print(f"✅ ReportLab available: {reportlab.__version__}")
except ImportError:
    print(f"❌ ReportLab NOT available in current Python environment")
    print(f"⚠️  Make sure to activate virtual environment: source venv/bin/activate")
    print(f"⚠️  Or install ReportLab: pip install reportlab==4.2.5")
from werkzeug.utils import secure_filename
import json
from datetime import datetime
from uuid import uuid4
import re
import statistics
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure file upload
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
COURSES_FOLDER = os.path.join(BASE_DIR, 'courses')  # Store generated courses
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md'}  # Support PDF, TXT, and Markdown

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COURSES_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Store game state
game_state = {
    'areas': {
        'start': {
            'completed': True,  # Start area is completed by default, allowing first area unlock
            'position': {'x': 200, 'y': 400},  # Horizontal layout: starting from left
            'connections': [],  # Initially no connections, waiting for teacher to add courses
            'level': 0,
            'castle_type': random.randint(1, 5),  # Random castle type 1-5
            'learningProgress': 100,  # Start area learning progress 100%
            'learnedPoints': []  # List of learned knowledge point numbers
        }
    },
    'current_area': 'start',
    'max_level': 0
}

def calculate_new_position(current_area_id, branch_index, total_branches):
    """Calculate new area position, horizontal layout from left to right"""
    current_pos = game_state['areas'][current_area_id]['position']
    current_level = game_state['areas'][current_area_id]['level']
    
    # Fixed forward distance (pixels) - horizontal (increased spacing)
    forward_distance = 600  # Horizontal distance between areas (increased from 400 to 600)
    
    # Calculate new x coordinate (move right)
    new_x = current_pos['x'] + forward_distance
    
    # Calculate new y coordinate (distribute above and below current position)
    if total_branches == 1:
        # Single branch: keep on same horizontal line
        new_y = current_pos['y']
    else:
        # Multiple branches: distribute above and below current position
        spread = 150  # Vertical distance between areas (increased from 100 to 150)
        if total_branches == 2:
            # Two branches: symmetric distribution (above and below)
            offset = spread * (-1 if branch_index == 0 else 1)
            new_y = current_pos['y'] + offset
        else:
            # Three branches: one in middle, two above and below
            if branch_index == 0:
                new_y = current_pos['y'] - spread
            elif branch_index == 1:
                new_y = current_pos['y']
            else:
                new_y = current_pos['y'] + spread
    
    return {'x': new_x, 'y': new_y}

def generate_new_area(current_area_id, branch_index, total_branches):
    """Generate new area"""
    area_id = f'area{len(game_state["areas"]) + 1}'
    current_level = game_state['areas'][current_area_id]['level']
    
    return {
        'completed': False,
        'position': calculate_new_position(current_area_id, branch_index, total_branches),
        'connections': [],
        'level': current_level + 1,
        'castle_type': random.randint(1, 5)  # Random castle type 1-5
    }

def generate_new_paths(current_area_id):
    """Generate new paths"""
    current_area = game_state['areas'][current_area_id]
    
    # Reset current area connections
    current_area['connections'] = []
    
    # Determine number of new branches (2-3)
    num_branches = random.randint(2, 3)
    
    # Generate new areas
    for i in range(num_branches):
        new_area_id = f'area{len(game_state["areas"]) + 1}'
        game_state['areas'][new_area_id] = generate_new_area(current_area_id, i, num_branches)
        current_area['connections'].append(new_area_id)
    
    # Update max level
    game_state['max_level'] = max(
        area['level'] for area in game_state['areas'].values()
    )

@app.route('/')
def home():
    return jsonify({"message": "Game server is running", "status": "ok"})

@app.route('/api/game-state', methods=['GET'])
def get_game_state():
    return jsonify(game_state)

@app.route('/api/complete-area/<area_id>', methods=['POST'])
def complete_area(area_id):
    """Complete area - linear map mode, only unlock next unit"""
    if area_id in game_state['areas']:
        game_state['areas'][area_id]['completed'] = True
        game_state['current_area'] = area_id
        
        # Linear map: no longer dynamically generate new paths
        # Paths are pre-created when applying courses
        print(f"✅ Area completed: {area_id}")
        
        # Check if there is a next area
        next_areas = game_state['areas'][area_id].get('connections', [])
        if next_areas:
            print(f"🔓 Next area unlocked: {next_areas[0]}")
        else:
            print(f"🎉 Congratulations! All areas completed!")
        
        all_completed = all(
            area_id_key == 'start' or area_data.get('completed')
            for area_id_key, area_data in game_state['areas'].items()
            if area_id_key != 'start'
        )
        
        return jsonify({
            "message": f"Area {area_id} completed",
            "game_state": game_state,
            "all_completed": all_completed
        })
    else:
        return jsonify({"error": "Area not found"}), 404

@app.route('/api/update-learning-progress/<area_id>', methods=['POST'])
def update_learning_progress(area_id):
    """Update learning progress for area"""
    if area_id not in game_state['areas']:
        return jsonify({"error": "Area not found"}), 404
    
    data = request.get_json()
    learned_points = data.get('learnedPoints', [])  # List of learned knowledge point numbers
    
    # Get total number of knowledge points for this area
    total_points = course_library.get(area_id, {}).get('knowledgePointCount', 5)
    
    # Calculate learning progress
    learned_count = len(learned_points)
    progress = (learned_count / total_points) * 100 if total_points > 0 else 0
    
    # Update game state
    game_state['areas'][area_id]['learnedPoints'] = learned_points
    game_state['areas'][area_id]['learningProgress'] = progress
    
    print(f"📊 Updated learning progress: {area_id} - {learned_count}/{total_points} ({progress:.1f}%)")
    
    return jsonify({
        "message": "Progress updated",
        "area_id": area_id,
        "learnedPoints": learned_points,
        "progress": progress,
        "game_state": game_state
    })

@app.route('/api/claude-chat', methods=['POST'])
def claude_chat():
    """Proxy Claude API calls from frontend to avoid direct browser key usage."""
    try:
        data = request.get_json(silent=True) or {}
        prompt = (data.get('prompt') or '').strip()
        if not prompt:
            return jsonify({'error': 'prompt is required'}), 400

        claude_api_key = os.getenv('CLAUDE_API_KEY', '').strip()
        if not claude_api_key:
            return jsonify({
                'error': 'Claude API key is not configured on backend.',
                'code': 'CLAUDE_KEY_MISSING'
            }), 503

        import requests
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'Content-Type': 'application/json',
                'x-api-key': claude_api_key,
                'anthropic-version': '2023-06-01'
            },
            json={
                'model': 'claude-3-5-sonnet-20241022',
                'max_tokens': 1000,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ]
            },
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({
                'error': 'Claude API request failed',
                'status_code': response.status_code,
                'details': response.text[:500]
            }), 502

        payload = response.json()
        content = payload.get('content', [])
        text = ''
        if isinstance(content, list) and content:
            text = content[0].get('text', '') or ''

        return jsonify({'response': text})
    except requests.Timeout:
        return jsonify({'error': 'Claude API timeout'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/google-chat', methods=['POST'])
def google_chat():
    """Proxy Gemini-style chat: uses Gemini when LLM_PROVIDER / key allow, else Ollama."""
    try:
        data = request.get_json(silent=True) or {}
        prompt = (data.get('prompt') or '').strip()
        if not prompt:
            return jsonify({'error': 'prompt is required'}), 400

        req_model = (data.get('model') or '').strip()
        text = call_llm_text(
            prompt=prompt,
            model=req_model or 'qwen2.5',
            timeout=90,
        )
        prov = _llm_provider_resolved()
        if prov == 'gemini':
            used = _normalize_gemini_model_id(os.getenv('GEMINI_MODEL', _DEFAULT_GEMINI_REST_MODEL) or _DEFAULT_GEMINI_REST_MODEL)
            if req_model and req_model.startswith('gemini-'):
                used = _normalize_gemini_model_id(req_model)
            return jsonify({'response': text, 'provider': 'gemini', 'model': used})
        return jsonify({'response': text, 'provider': 'ollama', 'model': 'qwen2.5'})
    except requests.Timeout:
        return jsonify({'error': 'Local model timeout'}), 504
    except Exception as e:
        return jsonify({'error': f'LLM request failed: {str(e)}'}), 502

def _pymupdf_page_layout_stats(page) -> dict:
    """
    Layout signals for PPT-export PDFs: large centered title, sparse text → section separator slide.
    """
    pw = float(page.rect.width) or 1.0
    ph = float(page.rect.height) or 1.0
    page_area = pw * ph
    full_text = (page.get_text() or '').strip()
    char_count = len(re.sub(r'\s+', '', full_text))
    word_count = len(full_text.split())

    d = page.get_text('dict') or {}
    spans_info = []
    sizes = []

    for block in d.get('blocks') or []:
        if block.get('type') != 0:
            continue
        for line in block.get('lines') or []:
            for sp in line.get('spans') or []:
                text = (sp.get('text') or '').strip()
                if not text:
                    continue
                try:
                    sz = float(sp.get('size') or 0)
                except (TypeError, ValueError):
                    sz = 0.0
                bbox = sp.get('bbox') or (0, 0, 0, 0)
                x0, y0, x1, y1 = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
                area = max(0.0, x1 - x0) * max(0.0, y1 - y0)
                cx = (x0 + x1) / 2.0
                sizes.append(sz)
                spans_info.append({
                    'size': sz,
                    'text': text,
                    'area': area,
                    'cx': cx,
                    'top': y0,
                })

    if not spans_info:
        return {
            'char_count': char_count,
            'word_count': word_count,
            'max_font_size': 0.0,
            'median_font_size': 0.0,
            'density_ratio': 0.0,
            'title_centered': False,
            'title_candidate': '',
            'span_count': 0,
            'is_section_slide': False,
        }

    median_size = float(statistics.median(sizes))
    max_span = max(spans_info, key=lambda s: s['size'])
    max_size = float(max_span['size'])
    title_spans = sorted(
        [s for s in spans_info if s['size'] >= max_size - 1.25],
        key=lambda s: s['top']
    )
    title_candidate = ' '.join(s['text'] for s in title_spans).strip()[:280]

    text_area = sum(s['area'] for s in spans_info)
    density_ratio = min(1.0, text_area / page_area)

    page_cx = pw / 2.0
    title_centered = abs(max_span['cx'] - page_cx) <= 0.18 * pw

    short_page = len(full_text) <= 360
    few_spans = len(spans_info) <= 10
    big_title = max_size >= max(median_size * 1.36, median_size + 3.5, 11.0)
    low_density = density_ratio <= 0.32
    compact_title = len(title_candidate) <= 220

    is_section_slide = (
        short_page
        and big_title
        and low_density
        and compact_title
        and (title_centered or (few_spans and density_ratio <= 0.16))
    )

    lower = full_text.lower()
    noise_markers = (
        'reference', 'references', 'bibliography', 'reading list',
        'suggested reading', 'appendix', 'week ', 'lecture ',
    )
    if any(m in lower for m in noise_markers) and len(full_text) > 100:
        is_section_slide = False

    return {
        'char_count': char_count,
        'word_count': word_count,
        'max_font_size': round(max_size, 2),
        'median_font_size': round(median_size, 2),
        'density_ratio': round(density_ratio, 4),
        'title_centered': title_centered,
        'title_candidate': title_candidate,
        'span_count': len(spans_info),
        'is_section_slide': bool(is_section_slide),
    }


def _text_only_guess_section_slides(norm):
    """Fallback when layout is missing: very short page + dominant first line."""
    idxs = []
    for i, p in enumerate(norm):
        t = (p.get('text') or '').strip()
        if not t or len(t) > 260:
            continue
        fl = _page_first_non_empty_line(t)
        if not fl or len(fl) > 110:
            continue
        ratio = len(fl) / max(len(t), 1)
        if len(t) < 55 or ratio >= 0.52:
            idxs.append(i)
    return idxs


def _sections_from_separator_indices(norm, sep_indices):
    """Build page ranges from separator slide indices (inclusive of separator through page before next)."""
    if not sep_indices:
        return None
    n = len(norm)
    sep_indices = sorted(set(i for i in sep_indices if 0 <= i < n))
    if not sep_indices:
        return None

    sections = []
    first_i = sep_indices[0]
    if first_i > 0:
        ps = int(norm[0]['page'])
        pe = int(norm[first_i - 1]['page'])
        intro = _page_first_non_empty_line(norm[0].get('text') or '') or f'Introduction (pages {ps}–{pe})'
        sections.append({'title': intro[:500], 'page_start': ps, 'page_end': pe})

    for j, si in enumerate(sep_indices):
        pg = int(norm[si]['page'])
        lay = norm[si].get('layout') if isinstance(norm[si].get('layout'), dict) else {}
        title = (lay.get('title_candidate') or '').strip()
        if not title:
            title = _page_first_non_empty_line(norm[si].get('text') or '')
        title = (title or f'Section (page {pg})')[:500]

        if j + 1 < len(sep_indices):
            end_i = sep_indices[j + 1] - 1
        else:
            end_i = n - 1
        pe = int(norm[end_i]['page'])
        sections.append({'title': title, 'page_start': pg, 'page_end': pe})

    return [_enrich_section_page_flags(norm, s) for s in sections]


def _maybe_window_split_long_sections(sections, max_span_pages=40):
    """Split only extremely long sections for teacher UX (optional safety)."""
    out = []
    for sec in sections:
        ps, pe = sec['page_start'], sec['page_end']
        span = pe - ps + 1
        ign = set(sec.get('ignored_pages') or [])
        case_p = set(sec.get('case_study_pages') or [])
        recap_p = set(sec.get('recap_pages') or [])
        stype = sec.get('type') or 'MAIN_SECTION'
        if span <= max_span_pages:
            out.append(dict(sec))
            continue
        cur = ps
        part = 1
        base_title = sec.get('title', 'Part')[:200]
        while cur <= pe:
            end = min(cur + max_span_pages - 1, pe)
            out.append({
                'title': f'{base_title} (part {part}, pages {cur}–{end})'[:500],
                'page_start': cur,
                'page_end': end,
                'type': stype,
                'parent': sec.get('parent'),
                'semantic_role': sec.get('semantic_role'),
                'extraction_strategy': sec.get('extraction_strategy'),
                'knowledge_weight': sec.get('knowledge_weight'),
                'ignored_pages': sorted(p for p in ign if cur <= p <= end),
                'case_study_pages': sorted(p for p in case_p if cur <= p <= end),
                'recap_pages': sorted(p for p in recap_p if cur <= p <= end),
            })
            cur = end + 1
            part += 1
    return out


# Text extraction function
def extract_file_content(file_path):
    """
    Extract text and optional per-page PDF structure.
    Returns (text: str, pdf_pages: list[dict] | None).
    On failure, (error_message_starting_with_Error, None).
    pdf_pages items: {"page": int, "text": str} for PPT/slide-friendly chunking.
    """
    if '.' in file_path:
        file_ext = file_path.rsplit('.', 1)[1].lower()
    else:
        return "Error: File has no extension", None

    try:
        if file_ext in ['txt', 'md']:
            print(f"📄 Reading text file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            print(f"✅ Text read successfully, length: {len(text)} characters")
            return text, None

        if file_ext == 'pdf':
            print(f"📄 Reading PDF file: {file_path}")
            pdf_pages = []
            full_parts = []
            num_pages = 0
            layout_ok = False

            try:
                import fitz
                doc = fitz.open(file_path)
                num_pages = len(doc)
                print(f"📖 PDF has {num_pages} pages (PyMuPDF layout + text)")
                for page_num in range(num_pages):
                    page = doc[page_num]
                    page_text = page.get_text() or ""
                    layout = _pymupdf_page_layout_stats(page)
                    pdf_pages.append({
                        'page': page_num + 1,
                        'text': page_text,
                        'layout': layout,
                    })
                    full_parts.append(page_text)
                    flag = "★section" if layout.get('is_section_slide') else ""
                    print(
                        f"   Page {page_num + 1}/{num_pages}, chars={len(page_text)} "
                        f"{flag} maxPt={layout.get('max_font_size')} dens={layout.get('density_ratio')}"
                    )
                doc.close()
                layout_ok = True
            except ImportError:
                print("⚠️  pymupdf not installed, falling back to PyPDF2 (no layout)")
            except Exception as e:
                print(f"⚠️  PyMuPDF read failed ({e}), falling back to PyPDF2")

            if not layout_ok:
                pdf_pages = []
                full_parts = []
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        num_pages = len(pdf_reader.pages)
                        print(f"📖 PDF has {num_pages} pages (PyPDF2)")
                        for page_num in range(num_pages):
                            page = pdf_reader.pages[page_num]
                            page_text = page.extract_text() or ""
                            pdf_pages.append({'page': page_num + 1, 'text': page_text})
                            full_parts.append(page_text)
                            print(f"   Page {page_num + 1}/{num_pages}, extracted {len(page_text)} characters")
                except ImportError:
                    return "Error: Install pymupdf or PyPDF2 (pip install pymupdf PyPDF2)", None

            text = "\n\n".join(full_parts)
            print(f"✅ PDF read successfully, total {len(text)} characters ({num_pages} pages)")
            return text, pdf_pages

        return f"Error: Unsupported file format {file_ext}", None

    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='gbk') as file:
                text = file.read()
            print("✅ Successfully read using GBK encoding")
            return text, None
        except Exception:
            return "Error: Unable to identify file encoding, please use UTF-8 or GBK encoding", None

    except Exception as e:
        return f"Error: Unable to extract text - {str(e)}", None


def extract_text_from_file(file_path):
    """Extract plain text only (supports PDF, TXT, MD)."""
    text, _ = extract_file_content(file_path)
    return text


def normalize_pdf_pages_payload(raw):
    """Validate client-provided pdf_pages for generate-course APIs."""
    if not raw or not isinstance(raw, list):
        return None
    out = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        t = item.get('text')
        if t is None:
            continue
        t = str(t).strip()
        if not t:
            continue
        p = item.get('page', i + 1)
        try:
            p = int(p)
        except (TypeError, ValueError):
            p = i + 1
        entry = {'page': p, 'text': t}
        sn = item.get('source_name')
        if isinstance(sn, str) and sn.strip():
            entry['source_name'] = sn.strip()[:500]
        lay = item.get('layout')
        if isinstance(lay, dict):
            entry['layout'] = lay
        out.append(entry)
    return out or None


def build_llm_chunks_from_pdf_pages(pdf_pages, max_chars=1000, overlap_chars=120):
    """
    One primary chunk per PDF page (slide), sub-split long pages with split_text_into_chunks.
    pdf_pages: list of dicts with keys page (int), text (str), optional source_name (str).
    """
    if not pdf_pages:
        return []
    chunks = []
    for entry in pdf_pages:
        if not isinstance(entry, dict):
            continue
        raw = entry.get('text') or ''
        text = clean_text_for_chunking(str(raw))
        if not text.strip():
            continue
        try:
            page = int(entry.get('page', len(chunks) + 1))
        except (TypeError, ValueError):
            page = len(chunks) + 1
        source = str(entry.get('source_name', '') or '').strip()
        src = f"{source}, " if source else ""

        if len(text) <= max_chars:
            chunks.append(f"[{src}PDF page {page}]\n\n{text}")
            continue
        sub = split_text_into_chunks(text, max_chars=max_chars, overlap_chars=overlap_chars)
        total_sub = len(sub)
        for si, piece in enumerate(sub, start=1):
            if total_sub > 1:
                header = f"[{src}PDF page {page} — part {si}/{total_sub}]\n\n"
            else:
                header = f"[{src}PDF page {page}]\n\n"
            chunks.append(f"{header}{piece}")
    return chunks


def _page_first_non_empty_line(page_text: str) -> str:
    if not page_text:
        return ''
    for ln in str(page_text).split('\n'):
        s = ln.strip()
        if s:
            return s[:220]
    return ''


def _normalize_heading_key(s: str) -> str:
    if not s:
        return ''
    t = re.sub(r'\s+', ' ', s.strip().lower())
    return t[:200]


# --- Section ontology: type = hierarchy only; semantic_role = pedagogy only ---
SECTION_TYPES = frozenset({'MAIN_SECTION', 'SUBSECTION'})
LEGACY_HIERARCHY_TYPES = frozenset({'CASE_STUDY', 'RECAP', 'REFERENCE'})
LEGACY_TYPE_TO_SEMANTIC = {
    'CASE_STUDY': 'case_study',
    'RECAP': 'recap_reinforcement',
    'REFERENCE': 'reference_material',
}

# Per-slide child chunks (pedagogy defaults, not section hierarchy types)
_CHILD_SLIDE_SEMANTIC_DEFAULTS = {
    'case_slide': ('case_study', 'case_analysis', 0.55),
    'recap_slide': ('recap_reinforcement', 'recap_linking', 0.2),
}


def _parse_knowledge_weight(val, default=1.0):
    try:
        w = float(val)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(w, 2.0))


def _sanitize_ontology_token(s, max_len=72):
    if not isinstance(s, str):
        return ''
    t = s.strip().lower().replace(' ', '_')
    if not t:
        return ''
    t = re.sub(r'[^a-z0-9_\-]', '', t)
    return t[:max_len] if t else ''


# semantic_role → extraction pipeline (always derived server-side; not teacher-edited)
ROLE_TO_STRATEGY = {
    'theory_domain': 'concept_dense',
    'application_domain': 'application_mapping',
    'case_study': 'case_analysis',
    'recap_reinforcement': 'recap_linking',
    'reference_material': 'reference_light',
    'general': 'concept_dense',
}


def strategy_for_semantic_role(role: str) -> str:
    token = _sanitize_ontology_token(role) if isinstance(role, str) and role.strip() else ''
    if not token:
        token = 'theory_domain'
    return ROLE_TO_STRATEGY.get(token, 'concept_dense')


def _defaults_for_semantic_role(role: str, sec_type: str) -> tuple:
    """(extraction_strategy, knowledge_weight) defaults; strategy is always ROLE_TO_STRATEGY[role]."""
    r = (role or 'theory_domain').strip().lower()
    token = _sanitize_ontology_token(r) if r else ''
    if not token:
        token = 'theory_domain'
    strat = strategy_for_semantic_role(token)
    if token == 'theory_domain':
        w = 1.0 if sec_type == 'MAIN_SECTION' else 0.8
        return strat, w
    fixed_w = {
        'case_study': 0.55,
        'application_domain': 0.65,
        'recap_reinforcement': 0.25,
        'reference_material': 0.0,
        'general': 0.75,
    }
    return strat, fixed_w.get(token, 0.8)


def _resolve_section_ontology(sec_type: str, item: dict) -> dict:
    """semantic_role + knowledge_weight from payload; extraction_strategy always derived from role."""
    typ = sec_type if sec_type in SECTION_TYPES else 'MAIN_SECTION'
    raw_role = item.get('semantic_role') if isinstance(item.get('semantic_role'), str) else None
    raw_w = item.get('knowledge_weight')

    role = _sanitize_ontology_token(raw_role) if raw_role and raw_role.strip() else ''
    if not role:
        role = 'theory_domain'

    strat = strategy_for_semantic_role(role)
    _st, w_d = _defaults_for_semantic_role(role, typ)

    w = _parse_knowledge_weight(raw_w, w_d) if raw_w is not None else float(w_d)

    if role == 'reference_material':
        w = 0.0
    elif role == 'recap_reinforcement':
        w = min(w, 0.3)

    return {'semantic_role': role, 'extraction_strategy': strat, 'knowledge_weight': w}


def _read_knowledge_weight_from_hctx(ctx: dict) -> float:
    if not isinstance(ctx, dict):
        return 1.0
    v = ctx.get('knowledge_weight')
    if v is None or v == '':
        return 1.0
    try:
        return max(0.0, min(float(str(v).replace(',', '').strip()), 2.0))
    except (TypeError, ValueError):
        return 1.0


def _extraction_task_instructions(strategy: str, semantic_role: str, knowledge_weight: float) -> str:
    """Strategy-specific extraction instructions (pedagogical context)."""
    s = (strategy or 'concept_dense').strip().lower()
    role = (semantic_role or '').strip().lower()
    w = _parse_knowledge_weight(knowledge_weight, 1.0)
    weight_note = (
        f"Graph importance weight for this chunk: {w:.2f} (0=peripheral, 1=core). "
        f"Prefer fewer, higher-precision items when weight is low."
    )

    if s == 'case_analysis':
        body = """
Focus (case / application material):
- Organizations, products, people, or settings named in the chunk.
- Problem context, intervention, and stated outcomes.
- Concrete mechanisms linking back to theoretical ideas (as measurable claims, not loose analogy).

Still output using the JSON schema below. Use type=concept for stable takeaway ideas; type=example for narrative evidence.
"""
    elif s == 'recap_linking':
        body = """
Focus (recap / reinforcement):
- Concepts explicitly listed as reviewed or summarized.
- Restatements of definitions or relationships (reinforcement, contrast, prerequisite reminders).

Still output using the JSON schema below. Prefer concepts that re-anchor the parent section's vocabulary.
"""
    elif s == 'reference_light':
        body = """
Focus (reference / reading list):
- Bibliographic items, URLs, or reading titles if present.
- Do not invent citations. Skip dense theory extraction if the chunk is only references.

Still output using the JSON schema below; use few items.
"""
    elif s == 'application_mapping':
        body = """
Focus (application / sector mapping — links theory to contexts):
- Industry, sector, or adoption patterns named in the material.
- How abstract ideas apply in stated settings (no invented companies or facts).
- Measurable claims and examples only when explicitly in the chunk.

Still output using the JSON schema below.
"""
    else:
        body = """
Focus (theory / main exposition — concept_dense):
- Core concepts, definitions, principles, and measurable facts.
- Prerequisites or assumptions explicitly stated.

Still output using the JSON schema below.
"""

    role_line = f"Semantic role hint: {role}.\n" if role else ''
    return f"{weight_note}\n{role_line}{body}"


# Gameplay-oriented node kinds for maps / student path (aligned with derived extraction_strategy)
NODE_TYPE_BY_STRATEGY = {
    'concept_dense': 'core_concept',
    'application_mapping': 'applied_exploration',
    'case_analysis': 'side_quest',
    'recap_linking': 'review',
    'reference_light': 'library',
}

# Inverse of ROLE_TO_STRATEGY: merged concepts carry extraction_strategy, not semantic_role.
STRATEGY_TO_SEMANTIC_ROLE = {
    'concept_dense': 'theory_domain',
    'application_mapping': 'application_domain',
    'case_analysis': 'case_study',
    'recap_linking': 'recap_reinforcement',
    'reference_light': 'reference_material',
}

_NODE_TYPE_RANK = {
    'core_concept': 5,
    'applied_exploration': 4,
    'review': 3,
    'side_quest': 3,
    'library': 1,
}


def _rank_node_type(nt):
    return _NODE_TYPE_RANK.get(str(nt or 'core_concept'), 2)


def _chunk_hierarchy_context_block(hctx: dict) -> str:
    hierarchy_lines = []
    if hctx.get('parent_section'):
        hierarchy_lines.append(f"Parent section: {hctx.get('parent_section')}")
    if hctx.get('section'):
        hierarchy_lines.append(f"Current section: {hctx.get('section')}")
    if hctx.get('child_semantic_role'):
        hierarchy_lines.append(f"Child semantic role: {hctx.get('child_semantic_role')}")
    if hctx.get('child_type'):
        hierarchy_lines.append(f"Current child type: {hctx.get('child_type')}")
    if hctx.get('parent_topic'):
        hierarchy_lines.append(f"Parent topic: {hctx.get('parent_topic')}")
    if hctx.get('parent'):
        hierarchy_lines.append(f"Parent: {hctx.get('parent')}")
    if hctx.get('pages'):
        hierarchy_lines.append(f"Pages: {hctx.get('pages')}")
    if hctx.get('child_slide_page'):
        hierarchy_lines.append(f"Child slide page: {hctx.get('child_slide_page')}")
    if hctx.get('semantic_role'):
        hierarchy_lines.append(f"Semantic role: {hctx.get('semantic_role')}")
    return "\n".join(hierarchy_lines) if hierarchy_lines else "No explicit hierarchy metadata."


def _dedupe_graph_relationships(rels, implicit_source=None):
    """Dedupe relationship dicts. Node-local rels omit source_concept; pass implicit_source."""
    if not isinstance(rels, list):
        return []
    seen = set()
    out = []
    for r in rels:
        if not isinstance(r, dict):
            continue
        t = str(r.get('type', 'other')).strip().lower()
        tgt = str(r.get('target_concept', '')).strip()
        ev = str(r.get('evidence_quote', r.get('evidence', ''))).strip()
        src = str(r.get('source_concept', implicit_source or '')).strip()
        sk = normalize_concept_key(src)
        if not tgt:
            continue
        sig = (sk, normalize_concept_key(tgt), t, ev[:120])
        if sig in seen:
            continue
        seen.add(sig)
        entry = {
            'type': t,
            'target_concept': tgt,
            'evidence_quote': ev,
        }
        if src:
            entry['source_concept'] = src
        out.append(entry)
    return out


def _append_relationship(concept_node: dict, target_concept: str, rel_type: str, evidence: str):
    if not concept_node or not target_concept:
        return
    rels = concept_node.setdefault('relationships', [])
    if not isinstance(rels, list):
        rels = []
        concept_node['relationships'] = rels
    rels.append({
        'type': rel_type,
        'target_concept': str(target_concept).strip(),
        'evidence_quote': str(evidence or '').strip(),
    })
    concept_node['relationships'] = _dedupe_graph_relationships(
        rels, implicit_source=concept_node.get('concept')
    )


def _base_concept_node(concept: str, chunk_kw: float, node_type: str, extraction_strategy: str):
    return {
        'concept': concept,
        'nodeType': node_type,
        'extraction_strategy': extraction_strategy,
        'definition': {'text': '', 'source_quotes': []},
        'examples': [],
        'key_facts': [],
        'relationships': [],
        'misconceptions': [],
        'knowledge_weight': float(chunk_kw),
    }


def _extract_concept_dense_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw):
    """Theory-focused schema: core concepts, prerequisite edges, misconceptions."""
    hierarchy_context = _chunk_hierarchy_context_block(hctx)
    wnote = _extraction_task_instructions('concept_dense', hctx.get('semantic_role') or '', chunk_kw)
    prompt = f"""
You are a knowledge modeling extractor for THEORY / CONCEPT-DENSE material.
Process only CHUNK {chunk_idx}/{total_chunks}.

Pedagogical hierarchy context:
{hierarchy_context}

{wnote}

Rules:
- Extract only what is supported by quotes from the chunk; do not invent citations.
- prerequisite_edges: "from_concept" is the concept that DEPENDS ON "to_concept" (to_concept is prerequisite knowledge).
- misconceptions: common wrong beliefs the slide/text warns against, if present.
- No slide titles as concepts.

Output JSON only:
{{
  "chunk_index": {chunk_idx},
  "core_concepts": [
    {{
      "concept": "name",
      "definition": "text",
      "definition_quote": "exact quote",
      "key_facts": [{{"fact": "", "numbers": [], "source_quote": ""}}]
    }}
  ],
  "prerequisite_edges": [
    {{"from_concept": "dependent concept name", "to_concept": "prerequisite concept name", "source_quote": "evidence"}}
  ],
  "misconceptions": [
    {{"misconception": "wrong belief", "correction": "right idea", "linked_concept": "optional concept name", "source_quote": ""}}
  ]
}}

CHUNK:
\"\"\"
{chunk_text}
\"\"\"
"""
    llm_text = call_llm_text(
        prompt=prompt, model='qwen2.5', timeout=90, options={'response_mime_json': True}
    )
    parsed = extract_first_json_object(llm_text)
    if not parsed:
        return None
    concepts_raw = parsed.get('core_concepts')
    if not isinstance(concepts_raw, list):
        concepts_raw = []
    node_type = NODE_TYPE_BY_STRATEGY.get('concept_dense', 'core_concept')
    concept_map = {}
    for c in concepts_raw:
        if not isinstance(c, dict):
            continue
        name = str(c.get('concept', '')).strip()
        if not name or looks_like_non_concept_label(name):
            continue
        k = normalize_concept_key(name)
        if k not in concept_map:
            concept_map[k] = _base_concept_node(name, chunk_kw, node_type, 'concept_dense')
        node = concept_map[k]
        d = str(c.get('definition', '')).strip()
        dq = str(c.get('definition_quote', '')).strip()
        if len(d) > len(node['definition'].get('text', '')):
            node['definition']['text'] = d
        node['definition']['source_quotes'] = _dedupe_str_list(
            node['definition'].get('source_quotes', []) + [dq]
        )
        for f in c.get('key_facts', []) or []:
            if not isinstance(f, dict):
                continue
            fact = str(f.get('fact', '')).strip()
            sq = str(f.get('source_quote', '')).strip()
            if fact or sq:
                node['key_facts'].append({
                    'fact': fact,
                    'numbers': _dedupe_str_list(f.get('numbers', []) if isinstance(f.get('numbers'), list) else []),
                    'source_quote': sq,
                })

    for e in parsed.get('prerequisite_edges', []) or []:
        if not isinstance(e, dict):
            continue
        fc = str(e.get('from_concept', '')).strip()
        tc = str(e.get('to_concept', '')).strip()
        q = str(e.get('source_quote', '')).strip()
        if not fc or not tc:
            continue
        fk = normalize_concept_key(fc)
        if fk not in concept_map:
            concept_map[fk] = _base_concept_node(fc, chunk_kw, node_type, 'concept_dense')
        _append_relationship(concept_map[fk], tc, 'depends-on', q)

    for m in parsed.get('misconceptions', []) or []:
        if not isinstance(m, dict):
            continue
        mic = str(m.get('misconception', '')).strip()
        if not mic:
            continue
        entry = {
            'misconception': mic,
            'correction': str(m.get('correction', '')).strip(),
            'source_quote': str(m.get('source_quote', '')).strip(),
        }
        lc = str(m.get('linked_concept', '')).strip()
        if lc:
            lk = normalize_concept_key(lc)
            if lk not in concept_map:
                concept_map[lk] = _base_concept_node(lc, chunk_kw, node_type, 'concept_dense')
            concept_map[lk].setdefault('misconceptions', []).append(entry)
        elif concept_map:
            first = next(iter(concept_map.values()))
            first.setdefault('misconceptions', []).append(entry)

    normalized = list(concept_map.values())
    for n in normalized:
        n['relationships'] = _dedupe_graph_relationships(
            n.get('relationships', []), implicit_source=n.get('concept')
        )
    if not normalized:
        return None
    return {'chunk_index': chunk_idx, 'concepts': normalized, 'resource_nodes': [], 'extraction_strategy': 'concept_dense'}


def _extract_application_mapping_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw):
    """Applied / sector mapping: same schema as theory, different pedagogy + node kind for maps."""
    hierarchy_context = _chunk_hierarchy_context_block(hctx)
    wnote = _extraction_task_instructions('application_mapping', hctx.get('semantic_role') or '', chunk_kw)
    prompt = f"""
You are a knowledge modeling extractor for APPLICATION / SECTOR-MAPPING material (not free-form case narrative).
Process only CHUNK {chunk_idx}/{total_chunks}.

Pedagogical hierarchy context:
{hierarchy_context}

{wnote}

Rules:
- Extract only what is supported by quotes from the chunk; do not invent citations.
- prerequisite_edges: optional links from applied claims back to named theoretical constructs when explicit.
- Focus on how stated contexts instantiate or constrain concepts from the parent section.

Output JSON only:
{{
  "chunk_index": {chunk_idx},
  "core_concepts": [
    {{
      "concept": "name",
      "definition": "text",
      "definition_quote": "exact quote",
      "key_facts": [{{"fact": "", "numbers": [], "source_quote": ""}}]
    }}
  ],
  "prerequisite_edges": [
    {{"from_concept": "dependent concept name", "to_concept": "prerequisite concept name", "source_quote": "evidence"}}
  ],
  "misconceptions": [
    {{"misconception": "wrong belief", "correction": "right idea", "linked_concept": "optional concept name", "source_quote": ""}}
  ]
}}

CHUNK:
\"\"\"
{chunk_text}
\"\"\"
"""
    llm_text = call_llm_text(
        prompt=prompt, model='qwen2.5', timeout=90, options={'response_mime_json': True}
    )
    parsed = extract_first_json_object(llm_text)
    if not parsed:
        return None
    concepts_raw = parsed.get('core_concepts')
    if not isinstance(concepts_raw, list):
        concepts_raw = []
    node_type = NODE_TYPE_BY_STRATEGY.get('application_mapping', 'applied_exploration')
    strat = 'application_mapping'
    concept_map = {}
    for c in concepts_raw:
        if not isinstance(c, dict):
            continue
        name = str(c.get('concept', '')).strip()
        if not name or looks_like_non_concept_label(name):
            continue
        k = normalize_concept_key(name)
        if k not in concept_map:
            concept_map[k] = _base_concept_node(name, chunk_kw, node_type, strat)
        node = concept_map[k]
        d = str(c.get('definition', '')).strip()
        dq = str(c.get('definition_quote', '')).strip()
        if len(d) > len(node['definition'].get('text', '')):
            node['definition']['text'] = d
        node['definition']['source_quotes'] = _dedupe_str_list(
            node['definition'].get('source_quotes', []) + [dq]
        )
        for f in c.get('key_facts', []) or []:
            if not isinstance(f, dict):
                continue
            fact = str(f.get('fact', '')).strip()
            sq = str(f.get('source_quote', '')).strip()
            if fact or sq:
                node['key_facts'].append({
                    'fact': fact,
                    'numbers': _dedupe_str_list(f.get('numbers', []) if isinstance(f.get('numbers'), list) else []),
                    'source_quote': sq,
                })

    for e in parsed.get('prerequisite_edges', []) or []:
        if not isinstance(e, dict):
            continue
        fc = str(e.get('from_concept', '')).strip()
        tc = str(e.get('to_concept', '')).strip()
        q = str(e.get('source_quote', '')).strip()
        if not fc or not tc:
            continue
        fk = normalize_concept_key(fc)
        if fk not in concept_map:
            concept_map[fk] = _base_concept_node(fc, chunk_kw, node_type, strat)
        _append_relationship(concept_map[fk], tc, 'depends-on', q)

    for m in parsed.get('misconceptions', []) or []:
        if not isinstance(m, dict):
            continue
        mic = str(m.get('misconception', '')).strip()
        if not mic:
            continue
        entry = {
            'misconception': mic,
            'correction': str(m.get('correction', '')).strip(),
            'source_quote': str(m.get('source_quote', '')).strip(),
        }
        lc = str(m.get('linked_concept', '')).strip()
        if lc:
            lk = normalize_concept_key(lc)
            if lk not in concept_map:
                concept_map[lk] = _base_concept_node(lc, chunk_kw, node_type, strat)
            concept_map[lk].setdefault('misconceptions', []).append(entry)
        elif concept_map:
            first = next(iter(concept_map.values()))
            first.setdefault('misconceptions', []).append(entry)

    normalized = list(concept_map.values())
    for n in normalized:
        n['relationships'] = _dedupe_graph_relationships(
            n.get('relationships', []), implicit_source=n.get('concept')
        )
    if not normalized:
        return None
    return {'chunk_index': chunk_idx, 'concepts': normalized, 'resource_nodes': [], 'extraction_strategy': strat}


def _extract_case_analysis_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw):
    hierarchy_context = _chunk_hierarchy_context_block(hctx)
    wnote = _extraction_task_instructions('case_analysis', hctx.get('semantic_role') or '', chunk_kw)
    prompt = f"""
You are extracting CASE / APPLICATION material (not abstract theory slides).
Process only CHUNK {chunk_idx}/{total_chunks}.

Pedagogical hierarchy context:
{hierarchy_context}

{wnote}

Extract organizations, settings, applications, and stated outcomes. Link to theory only when explicitly stated in text.

Output JSON only:
{{
  "chunk_index": {chunk_idx},
  "cases": [
    {{
      "name": "company, product, or case title",
      "application": "what they did / context",
      "outcome": "stated result or learning",
      "linked_concepts": ["optional theory concepts named in chunk"],
      "source_quote": "short supporting quote"
    }}
  ]
}}

CHUNK:
\"\"\"
{chunk_text}
\"\"\"
"""
    llm_text = call_llm_text(
        prompt=prompt, model='qwen2.5', timeout=90, options={'response_mime_json': True}
    )
    parsed = extract_first_json_object(llm_text)
    if not parsed:
        return None
    cases = parsed.get('cases', [])
    if not isinstance(cases, list):
        cases = []
    node_type = NODE_TYPE_BY_STRATEGY.get('case_analysis', 'side_quest')
    concept_map = {}
    for cs in cases:
        if not isinstance(cs, dict):
            continue
        name = str(cs.get('name', '')).strip()
        if not name:
            continue
        k = normalize_concept_key(name)
        if k not in concept_map:
            concept_map[k] = _base_concept_node(name, chunk_kw, node_type, 'case_analysis')
        node = concept_map[k]
        app = str(cs.get('application', '')).strip()
        out = str(cs.get('outcome', '')).strip()
        body = ' '.join(x for x in [app, out] if x).strip()
        q = str(cs.get('source_quote', '')).strip()
        if len(body) > len(node['definition'].get('text', '')):
            node['definition']['text'] = body
        node['definition']['source_quotes'] = _dedupe_str_list(
            node['definition'].get('source_quotes', []) + [q]
        )
        if q:
            node['examples'].append({'text': app or out or name, 'source_quote': q})
        for lc in cs.get('linked_concepts', []) or []:
            t = str(lc).strip()
            if t:
                _append_relationship(node, t, 'illustrates', q)
        node['relationships'] = _dedupe_graph_relationships(
            node.get('relationships', []), implicit_source=node.get('concept')
        )

    normalized = list(concept_map.values())
    if not normalized:
        return None
    return {'chunk_index': chunk_idx, 'concepts': normalized, 'resource_nodes': [], 'extraction_strategy': 'case_analysis'}


def _extract_recap_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw):
    hierarchy_context = _chunk_hierarchy_context_block(hctx)
    wnote = _extraction_task_instructions('recap_linking', hctx.get('semantic_role') or '', chunk_kw)
    prompt = f"""
You are extracting RECAP / REVIEW material: reinforcement and concept chains, not new theory.
Process only CHUNK {chunk_idx}/{total_chunks}.

Pedagogical hierarchy context:
{hierarchy_context}

{wnote}

Rules:
- Only concepts explicitly reviewed or summarized here.
- reinforcement_links: pedagogical relation between two named concepts (reinforces, contrasts, prerequisite_reminder).
- review_chains: ordered lists of concept names as they appear in recap flow.

Output JSON only:
{{
  "chunk_index": {chunk_idx},
  "reinforced_concepts": [
    {{"concept": "name", "summary": "short recap phrase", "source_quote": ""}}
  ],
  "reinforcement_links": [
    {{"from_concept": "", "to_concept": "", "relation": "reinforces|contrasts|prerequisite_reminder", "source_quote": ""}}
  ],
  "review_chains": [["concept_a", "concept_b"]]
}}

CHUNK:
\"\"\"
{chunk_text}
\"\"\"
"""
    llm_text = call_llm_text(
        prompt=prompt, model='qwen2.5', timeout=90, options={'response_mime_json': True}
    )
    parsed = extract_first_json_object(llm_text)
    if not parsed:
        return None
    node_type = NODE_TYPE_BY_STRATEGY.get('recap_linking', 'review')
    concept_map = {}
    for rc in parsed.get('reinforced_concepts', []) or []:
        if not isinstance(rc, dict):
            continue
        name = str(rc.get('concept', '')).strip()
        if not name or looks_like_non_concept_label(name):
            continue
        k = normalize_concept_key(name)
        if k not in concept_map:
            concept_map[k] = _base_concept_node(name, chunk_kw, node_type, 'recap_linking')
        node = concept_map[k]
        summ = str(rc.get('summary', '')).strip()
        q = str(rc.get('source_quote', '')).strip()
        if len(summ) > len(node['definition'].get('text', '')):
            node['definition']['text'] = summ
        node['definition']['source_quotes'] = _dedupe_str_list(
            node['definition'].get('source_quotes', []) + [q]
        )

    rel_map = {
        'reinforces': 'reinforces',
        'contrasts': 'contrasts',
        'prerequisite_reminder': 'prerequisite_reminder',
    }
    for lk in parsed.get('reinforcement_links', []) or []:
        if not isinstance(lk, dict):
            continue
        a = str(lk.get('from_concept', '')).strip()
        b = str(lk.get('to_concept', '')).strip()
        rt = rel_map.get(str(lk.get('relation', '')).strip().lower(), 'reinforces')
        q = str(lk.get('source_quote', '')).strip()
        if not a or not b:
            continue
        ak = normalize_concept_key(a)
        if ak not in concept_map:
            concept_map[ak] = _base_concept_node(a, chunk_kw, node_type, 'recap_linking')
        _append_relationship(concept_map[ak], b, rt, q)

    chains_meta = []
    for ch in parsed.get('review_chains', []) or []:
        if isinstance(ch, list) and len(ch) >= 2:
            clean = [str(x).strip() for x in ch if str(x).strip()]
            if len(clean) >= 2:
                chains_meta.append(clean)

    normalized = list(concept_map.values())
    for n in normalized:
        n['relationships'] = _dedupe_graph_relationships(
            n.get('relationships', []), implicit_source=n.get('concept')
        )

    out = {'chunk_index': chunk_idx, 'concepts': normalized, 'resource_nodes': [], 'extraction_strategy': 'recap_linking'}
    if chains_meta:
        out['review_chains'] = chains_meta
    if not normalized and not chains_meta:
        return None
    if not normalized and chains_meta:
        for ch in chains_meta:
            for nm in ch:
                k = normalize_concept_key(nm)
                if k not in concept_map:
                    concept_map[k] = _base_concept_node(nm, chunk_kw, node_type, 'recap_linking')
        out['concepts'] = list(concept_map.values())
    return out if out.get('concepts') else None


def _extract_reference_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw):
    hierarchy_context = _chunk_hierarchy_context_block(hctx)
    wnote = _extraction_task_instructions('reference_light', hctx.get('semantic_role') or '', chunk_kw)
    prompt = f"""
You are extracting REFERENCE / READING-LIST style content only.
Process only CHUNK {chunk_idx}/{total_chunks}.

Pedagogical hierarchy context:
{hierarchy_context}

{wnote}

Do not invent bibliographic entries. Skip if no readings or references appear.

Output JSON only:
{{
  "chunk_index": {chunk_idx},
  "resources": [
    {{"title": "", "citation_or_url": "", "source_quote": ""}}
  ]
}}

CHUNK:
\"\"\"
{chunk_text}
\"\"\"
"""
    llm_text = call_llm_text(
        prompt=prompt, model='qwen2.5', timeout=90, options={'response_mime_json': True}
    )
    parsed = extract_first_json_object(llm_text)
    if not parsed:
        return None
    resources = []
    for r in parsed.get('resources', []) or []:
        if not isinstance(r, dict):
            continue
        title = str(r.get('title', '')).strip()
        cit = str(r.get('citation_or_url', '')).strip()
        q = str(r.get('source_quote', '')).strip()
        if not title and not cit:
            continue
        resources.append({
            'nodeType': 'library',
            'title': title or cit,
            'citation_or_url': cit,
            'source_quote': q,
            'knowledge_weight': float(chunk_kw),
            'extraction_strategy': 'reference_light',
        })
    if not resources:
        return None
    return {
        'chunk_index': chunk_idx,
        'concepts': [],
        'resource_nodes': resources,
        'extraction_strategy': 'reference_light',
    }


def _legacy_items_extract_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw):
    """Fallback: original item-based schema for unknown/failed strategy paths."""
    hierarchy_context = _chunk_hierarchy_context_block(hctx)
    node_type = NODE_TYPE_BY_STRATEGY.get('concept_dense', 'core_concept')
    prompt = f"""
You are a knowledge modeling extractor.
Process only CHUNK {chunk_idx}/{total_chunks}.

Pedagogical hierarchy context:
{hierarchy_context}

Task:
1) Classify chunk items as concept|example|question|section.
2) Keep all extracted items in output with explicit type.
3) For examples, set belongs_to to the related concept.
4) Preserve concrete details and numbers exactly from chunk.
5) No topic classification. Do not invent cross-chunk relationships.

Output JSON only:
{{
  "chunk_index": {chunk_idx},
  "items": [
    {{
      "type": "concept|example|question|section",
      "concept": "concept name when type=concept",
      "belongs_to": "concept name when type=example",
      "definition": "definition text when type=concept",
      "definition_quote": "exact supporting quote",
      "example_text": "example text when type=example",
      "example_quote": "exact quote for example",
      "key_facts": [
        {{"fact": "factual statement", "numbers": [], "source_quote": "exact supporting quote"}}
      ]
    }}
  ]
}}

CHUNK:
\"\"\"
{chunk_text}
\"\"\"
"""
    llm_text = call_llm_text(
        prompt=prompt, model='qwen2.5', timeout=90, options={'response_mime_json': True}
    )
    parsed = extract_first_json_object(llm_text)
    if not parsed:
        return None
    items = parsed.get('items', [])
    if not isinstance(items, list):
        items = []
    concept_map = {}
    pending_examples = []
    for c in items:
        if not isinstance(c, dict):
            continue
        item_type = str(c.get('type', '')).strip().lower()
        if item_type == 'concept':
            concept = str(c.get('concept', '')).strip()
            if not concept or looks_like_non_concept_label(concept):
                continue
            key = normalize_concept_key(concept)
            if key not in concept_map:
                concept_map[key] = _base_concept_node(concept, chunk_kw, node_type, 'concept_dense')
            definition = str(c.get('definition', '')).strip()
            definition_quote = str(c.get('definition_quote', '')).strip()
            if len(definition) > len(concept_map[key]['definition'].get('text', '')):
                concept_map[key]['definition']['text'] = definition
            concept_map[key]['definition']['source_quotes'] = _dedupe_str_list(
                concept_map[key]['definition'].get('source_quotes', []) + [definition_quote]
            )
            for f in c.get('key_facts', []) or []:
                if not isinstance(f, dict):
                    continue
                fact = str(f.get('fact', '')).strip()
                src = str(f.get('source_quote', '')).strip()
                nums = f.get('numbers', [])
                if not isinstance(nums, list):
                    nums = []
                if fact or src:
                    concept_map[key]['key_facts'].append({
                        'fact': fact,
                        'numbers': _dedupe_str_list(nums),
                        'source_quote': src,
                    })
        elif item_type == 'example':
            pending_examples.append({
                'belongs_to': str(c.get('belongs_to', '')).strip(),
                'text': str(c.get('example_text', '')).strip(),
                'source_quote': str(c.get('example_quote', '')).strip(),
            })
    for ex in pending_examples:
        belongs_to = ex.get('belongs_to', '')
        text = ex.get('text', '')
        quote = ex.get('source_quote', '')
        if not belongs_to or (not text and not quote):
            continue
        key = normalize_concept_key(belongs_to)
        if key in concept_map:
            concept_map[key]['examples'].append({'text': text, 'source_quote': quote})
    normalized = list(concept_map.values())
    if not normalized:
        return None
    return {'chunk_index': chunk_idx, 'concepts': normalized, 'resource_nodes': [], 'extraction_strategy': 'concept_dense'}


def _slide_title_guess(p: dict) -> str:
    if not isinstance(p, dict):
        return ''
    lay = p.get('layout')
    if isinstance(lay, dict):
        tc = (lay.get('title_candidate') or '').strip()
        if tc:
            return tc[:500]
    return _page_first_non_empty_line(p.get('text') or '')


def _camel_case_brand_title(title: str) -> bool:
    """Heuristic: short title with several TitleCase tokens (case-study cover slide)."""
    t = (title or '').strip()
    if not t or len(t) > 72 or len(t) < 6:
        return False
    compact = re.sub(r'\s+', '', t)
    if re.search(r'^[A-Z][a-z]+(?:[A-Z][a-z]+){2,}$', compact):
        return True
    words = [w for w in re.split(r'[\s\-–]+', t) if w.isalpha() and len(w) >= 2]
    if 3 <= len(words) <= 8 and all(w[:1].isupper() for w in words):
        return True
    return False


# Course headings that denote theory domains — do NOT treat as case-study slides / case ontology.
_THEORY_HEADLINE_GUARD_RE = re.compile(
    r'\b('
    r'platform\s+ecosystem|sharing\s+economy|user\s+innovation|open\s+innovation|'
    r'lead\s+users?|network\s+effects?|two-?sided\s+market|multi-?sided\s+platform|'
    r'disruptive\s+innovation|dominant\s+design|platform\s+business(es)?|'
    r'main\s+players\s+in|different\s+forms\s+of\s+platform'
    r')\b',
    re.I,
)

# Known instance / company tokens in titles (after em dash or as focus)
_CASE_COMPANY_TOKENS_RE = re.compile(
    r'\b(apple|google|amazon|microsoft|meta|facebook|uber|lyft|airbnb|netflix|tesla|'
    r'spotify|salesforce|slack|stripe|shopify|starbucks|nike|ibm|oracle|samsung|sony|lego)\b',
    re.I,
)


def _theory_headline_guard(title: str) -> bool:
    t = str(title or '').strip()
    if not t:
        return False
    return bool(_THEORY_HEADLINE_GUARD_RE.search(t))


def _case_instance_slide_title(title: str) -> bool:
    """
    True for explicit case / company-instance cover lines (not generic theory headings).
    E.g. 'Platform economy – Apple', 'Case study: Uber'.
    """
    t = str(title or '').strip()
    if not t:
        return False
    if _theory_headline_guard(t):
        return False
    low = t.lower()
    if re.search(r'case\s+stud', low):
        return True
    # Subtitle with em/en dash pointing to a concrete entity
    if re.search(r'\s[–—-]\s*.+', t) and _CASE_COMPANY_TOKENS_RE.search(t):
        return True
    if re.search(r'\bplatform\s+economy\s*[–—-]', low) and _CASE_COMPANY_TOKENS_RE.search(t):
        return True
    return False


def _page_is_case_study_for_chunking(title: str, body: str, is_sep: bool) -> bool:
    """
    Tight case-slide detection for case_study_pages (child chunks).
    Avoids counting dense theory slides whose first line is Title Case.
    """
    t = str(title or '').strip()
    bh = (t + '\n' + (body or '')[:2000]).lower()
    if _theory_headline_guard(t):
        if not re.search(r'case\s+stud|案例分析|案例研究', bh):
            if not _case_instance_slide_title(t):
                return False
    if re.search(r'case\s+stud|案例分析|案例研究', bh):
        return True
    if _case_instance_slide_title(t):
        return True
    # Brand-like separator cover with little body (company intro slide)
    if is_sep and _camel_case_brand_title(t) and not _theory_headline_guard(t):
        if len((body or '').strip()) < 550:
            return True
    return False


def _application_domain_section_signals(title: str, body_sample: str) -> bool:
    """Sector / adoption / 'transformed industries' style exposition (still concept-dense)."""
    if _theory_headline_guard(title):
        return False
    blob = f"{title or ''}\n{body_sample or ''}"[:8000].lower()
    return bool(
        re.search(
            r'\bindustr(y|ies)\s+(being\s+)?transformed|sectors?\s+being\s+transformed|'
            r'adoption\s+in\s+industr|real-?world\s+applications?\b',
            blob,
        )
    )


def _classify_slide_semantic(title: str, full_text: str) -> str:
    """
    Slide-level signal for boundary suppression / per-page flags (not section hierarchy type).
    Returns: MAIN_SECTION | RECAP | CASE_STUDY | REFERENCE | SUBSECTION
    """
    t = (title or '').strip()
    body = (full_text or '').strip()
    blob_head = (t + '\n' + body[:1200]).lower()

    if re.search(
        r'suggested\s+reading|reading\s+list|bibliography|further\s+reading'
        r'|\breferences?\s*$|\breferences?\s*\n',
        blob_head,
        re.MULTILINE,
    ):
        return 'REFERENCE'

    if re.search(
        r'^\s*recap\b|^\s*recap\s*:|^\s*summary\s*:|chapter\s+review|quick\s+recap'
        r'|learning\s+check|wrap[\s-]*up|本节回顾|章节小结|内容回顾',
        blob_head,
    ):
        return 'RECAP'

    if re.search(r'case\s+stud|案例研究|案例分析', blob_head) or _case_instance_slide_title(t):
        return 'CASE_STUDY'

    if re.search(
        r'^\s*example[s]?\s*[:\.]?|^\s*demo\s*[:\.]?|worked\s+example|for\s+example\s*$',
        blob_head,
    ):
        return 'SUBSECTION'

    return 'MAIN_SECTION'


def _reference_body_page(body: str) -> bool:
    """Non-separator page that is mostly references / reading list."""
    b = (body or '').strip()
    if not b or len(b) > 4500:
        return False
    low = b.lower()
    if re.search(r'suggested\s+reading|reading\s+list|bibliography|further\s+reading', low[:800]):
        return True
    lines = [ln.strip() for ln in b.split('\n') if ln.strip()]
    if not lines:
        return False
    if re.match(r'^references?$', lines[0].lower()) and len(b) < 2500:
        return True
    return False


def _is_separator_candidate(norm_entry: dict, index: int, text_guess_indices: set) -> bool:
    lay = norm_entry.get('layout') if isinstance(norm_entry.get('layout'), dict) else {}
    if lay.get('is_section_slide'):
        return True
    return index in text_guess_indices


def _collect_main_separator_indices(norm, text_guess_indices):
    """Boundary suppression: only MAIN_SECTION separators start a new section."""
    main_idx = []
    tg = set(text_guess_indices) if text_guess_indices else set()
    layout_sep_indices = {
        j for j, x in enumerate(norm)
        if isinstance(x.get('layout'), dict) and x['layout'].get('is_section_slide')
    }
    for i, p in enumerate(norm):
        if not _is_separator_candidate(p, i, tg):
            continue
        title = _slide_title_guess(p)
        body = (p.get('text') or '').strip()
        sem = _classify_slide_semantic(title, body)
        if sem != 'MAIN_SECTION':
            continue
        if i in tg and i not in layout_sep_indices and len(body) > 300:
            continue
        main_idx.append(i)
    return sorted(set(main_idx))


def _enrich_section_page_flags(norm, section: dict) -> dict:
    """Per-page flags for chunking only (ignored / case / recap slides). Does not assign hierarchy or pedagogy."""
    try:
        ps = int(section.get('page_start', 1))
        pe = int(section.get('page_end', ps))
    except (TypeError, ValueError):
        return dict(section)
    if pe < ps:
        ps, pe = pe, ps

    by_page = {}
    for p in norm:
        try:
            pn = int(p.get('page', 0))
        except (TypeError, ValueError):
            continue
        if pn >= 1:
            by_page[pn] = p

    ignored = []
    case_pages = []
    recap_pages = []

    for pg in range(ps, pe + 1):
        p = by_page.get(pg)
        if not p:
            continue
        title = _slide_title_guess(p)
        body = (p.get('text') or '').strip()
        lay = p.get('layout') if isinstance(p.get('layout'), dict) else {}
        is_sep = bool(lay.get('is_section_slide'))

        sem = _classify_slide_semantic(title, body)
        if sem == 'REFERENCE' or _reference_body_page(body):
            ignored.append(pg)
            continue
        if _page_is_case_study_for_chunking(title, body, is_sep):
            case_pages.append(pg)
        elif sem == 'RECAP' and is_sep:
            recap_pages.append(pg)

    section = dict(section)
    section['ignored_pages'] = sorted(set(ignored))
    section['case_study_pages'] = sorted(set(case_pages))
    section['recap_pages'] = sorted(set(recap_pages))
    return section


def _section_body_sample(norm, ps, pe, skip_pages=None, max_chars=5500):
    """Concatenate text from pages in [ps, pe], skipping reference-style pages."""
    skip_pages = skip_pages if isinstance(skip_pages, (set, frozenset)) else set(skip_pages or [])
    by_page = {}
    for p in norm:
        try:
            pn = int(p.get('page', 0))
        except (TypeError, ValueError):
            continue
        if pn >= 1:
            by_page[pn] = p
    parts = []
    total = 0
    for pg in range(ps, pe + 1):
        if pg in skip_pages:
            continue
        ent = by_page.get(pg)
        if not ent:
            continue
        t = (ent.get('text') or '').strip()
        if not t:
            continue
        parts.append(t)
        total += len(t)
        if total >= max_chars:
            break
    blob = '\n\n'.join(parts)
    return blob[:max_chars] if blob else ''


# --- Curriculum sanitation: lecture / discourse noise (no ontology row, graph, or chunks) ---
# Teaching interaction (e.g. class activity) may later map to interaction_nodes — for now, skip entirely.
NOISE_TITLE_PATTERNS = (
    'the university of sydney',
    'university of sydney',
    'overview',
    'introductions',
    'class activity',
    'pause',
    'questions',
    'xkcd',
    'references',
    'suggested reading',
    'and on to',
)


def _normalize_title_for_noise_match(title: str) -> str:
    t = str(title or '').strip().lower()
    t = re.sub(r'[^a-z0-9\s]+', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def _noise_title_pattern_hit(normalized_title: str, pat: str) -> bool:
    if not normalized_title or not pat:
        return False
    nt = normalized_title
    if ' ' in pat:
        return pat in nt
    if nt == pat:
        return True
    if len(nt) <= 36 and nt.startswith(pat + ' '):
        return True
    if len(nt) <= 28 and nt.endswith(' ' + pat):
        return True
    return False


def is_noise_section(title: str, body=None) -> bool:
    """
    Deterministic lecture-noise gate: branding, transitions, activities, generic scaffolding, link slides.
    If True: do not emit a curriculum section, do not chunk for extraction, do not add to concept graph.
    """
    nt = _normalize_title_for_noise_match(title)
    if not nt:
        return True
    for pat in NOISE_TITLE_PATTERNS:
        if _noise_title_pattern_hit(nt, pat):
            return True
    if len(nt) <= 24 and nt.count(' ') <= 3:
        if re.match(
            r'^(welcome|thanks?|thank you|agenda|housekeeping|todays?\s+plan|any questions)\b',
            nt,
        ):
            return True
    if body is not None and str(body).strip():
        sample = str(body)[:2000].lower()
        if 'xkcd.com' in sample or re.search(r'\bxkcd\b.*\b(link|comic)\b', sample):
            return True
    return False


# --- Deterministic staged curriculum ontology (rule tables; single pass) ---

_REFERENCE_SECTION_TITLE_RE = re.compile(
    r'suggested\s+reading|further\s+reading|bibliography|\breferences?\s*$',
    re.I,
)

_RECAP_SECTION_TITLE_RE = re.compile(
    r'^\s*(recap|review|summary)\b|chapter\s+review|quick\s+recap|learning\s+check|'
    r'wrap[\s-]*up|本节回顾|章节小结|内容回顾',
    re.I,
)

_MAIN_SECTION_TITLE_PATTERNS = (
    r'^user\s+innovation(\b|[,:;\s]|$)',
    r'^platform\s+ecosystem(\b|[,:;\s]|$)',
    r'^sharing\s+economy(\b|[,:;\s]|$)',
    r'^open\s+innovation(\b|[,:;\s]|$)',
    r'^disruptive\s+innovation(\b|[,:;\s]|$)',
    r'^digital\s+platforms?\b',
    r'^two-?sided\s+markets?\b',
    r'^network\s+effects?\b',
    r'^introduction\b',
    r'^course\s+outline\b',
)
_MAIN_SECTION_TITLE_RES = tuple(re.compile(p, re.I) for p in _MAIN_SECTION_TITLE_PATTERNS)


def _title_is_reference_heading(title_raw: str) -> bool:
    t = str(title_raw or '').strip()
    return bool(t and _REFERENCE_SECTION_TITLE_RE.search(t))


def _title_signals_main_domain_section(title_norm: str) -> bool:
    if not title_norm:
        return False
    return any(r.search(title_norm) for r in _MAIN_SECTION_TITLE_RES)


def _title_signals_satellite_under_main(title_raw: str) -> bool:
    """Structural cues for subordinate blocks (not semantic_role); requires a parent MAIN in the parser loop."""
    t = str(title_raw or '').strip()
    if not t:
        return False
    if _REFERENCE_SECTION_TITLE_RE.search(t):
        return True
    if _RECAP_SECTION_TITLE_RE.search(t):
        return True
    if _case_instance_slide_title(t):
        return True
    return False


def _lexical_subordinate_heading(parent_norm: str, title_norm: str, title_raw: str) -> bool:
    if not parent_norm or not title_norm:
        return False
    if re.search(r'[–—-]\s*(apple|google|amazon|microsoft|uber|airbnb|netflix|tesla|lego)\b', title_norm):
        return False
    if re.search(r'\blead\s+users?\b', title_norm) and (
        'innovat' in parent_norm or 'user' in parent_norm
    ):
        return True
    if re.search(r'\bmain\s+players\s+in\b', title_norm) and 'platform' in parent_norm:
        return True
    if (
        re.search(r'\bdifferent\s+forms\s+of\s+platform\b', title_norm)
        and 'ecosystem' in parent_norm
    ):
        return True
    if (
        re.search(r'\bindustr(y|ies)\s+(being\s+)?transformed\b', title_norm)
        and 'platform' in parent_norm
    ):
        return True
    if re.search(r'\btypes?\s+of\s+platform\b', title_norm) and 'platform' in parent_norm:
        return True
    return False


# Example / case / application / industry blocks: not new theory domains; stay under current MAIN.
_DOMAIN_SATELLITE_BLOCK_TITLE_RE = re.compile(
    r'\b(examples?|applications?|industr(?:y|ies)|cases?|case\s+stud(?:y|ies))\b',
    re.I,
)


def _title_signals_domain_satellite_block(title_norm: str) -> bool:
    tn = (title_norm or '').strip()
    return bool(tn and _DOMAIN_SATELLITE_BLOCK_TITLE_RE.search(tn))


def _title_signals_case_study_semantic(title_raw: str) -> bool:
    t = str(title_raw or '').strip()
    if not t:
        return False
    if _theory_headline_guard(t):
        return False
    low = t.lower()
    if re.search(r'case\s+stud|案例分析|案例研究', low):
        return True
    if _case_instance_slide_title(t):
        return True
    if _CASE_COMPANY_TOKENS_RE.search(t) and re.search(r'\s[–—-]\s*', t):
        return True
    return False


def _detect_semantic_role_deterministic(title_raw: str, body_sample: str) -> str:
    """
    Fixed order: reference → recap → case_study → domain-satellite titles → application_domain from body
    → theory_domain. (Case vs application is semantic_role only; type stays MAIN/SUB.)
    """
    t = str(title_raw or '').strip()
    bp = (body_sample or '')[:3500]
    blob_head = (t + '\n' + bp[:2000]).lower()

    if _REFERENCE_SECTION_TITLE_RE.search(t) or re.search(
        r'suggested\s+reading|reading\s+list|bibliography|further\s+reading|\breferences?\s*$',
        blob_head[:1200],
        re.MULTILINE,
    ):
        return 'reference_material'

    if _RECAP_SECTION_TITLE_RE.search(t):
        return 'recap_reinforcement'

    if _title_signals_case_study_semantic(t):
        return 'case_study'

    t_norm = _normalize_heading_key(t)
    if _title_signals_domain_satellite_block(t_norm):
        return 'application_domain'

    if _application_domain_section_signals(t, bp):
        return 'application_domain'

    return 'theory_domain'


def _detect_hierarchy_type_deterministic(
    idx: int,
    title_raw: str,
    title_norm: str,
    span: int,
    has_parent_main: bool,
    parent_norm: str,
) -> str:
    """
    MAIN vs SUB from structural rules only (no semantic_role input).
    """
    if idx == 0:
        return 'MAIN_SECTION'
    if has_parent_main and _title_signals_domain_satellite_block(title_norm):
        return 'SUBSECTION'
    if _title_signals_main_domain_section(title_norm):
        return 'MAIN_SECTION'
    if has_parent_main and _title_signals_satellite_under_main(title_raw):
        return 'SUBSECTION'
    if has_parent_main and _lexical_subordinate_heading(parent_norm, title_norm, title_raw):
        return 'SUBSECTION'
    if has_parent_main and span <= 3:
        return 'SUBSECTION'
    if (
        has_parent_main
        and _camel_case_brand_title(title_raw)
        and span <= 6
        and not _theory_headline_guard(title_raw)
    ):
        return 'SUBSECTION'
    if (
        has_parent_main
        and title_norm
        and parent_norm
        and (title_norm in parent_norm or parent_norm in title_norm)
        and span <= 8
    ):
        return 'SUBSECTION'
    return 'MAIN_SECTION'


def _ontology_validate_and_repair(sec: dict, idx: int, anchor_main_title) -> list:
    """Enforce invariants; return human-readable violation codes (may be empty)."""
    violations = []
    typ = sec.get('type')
    if typ == 'MAIN_SECTION' and sec.get('parent'):
        violations.append('main_had_parent')
        sec['parent'] = None
    if typ == 'SUBSECTION':
        p = sec.get('parent')
        if (not p or not str(p).strip()) and anchor_main_title:
            sec['parent'] = str(anchor_main_title).strip()[:500]
        elif not sec.get('parent'):
            violations.append('subsection_missing_parent')

    role_tok = _sanitize_ontology_token(str(sec.get('semantic_role') or '')) or 'theory_domain'
    sec['semantic_role'] = role_tok
    if role_tok == 'reference_material':
        sec['knowledge_weight'] = 0.0
    elif role_tok == 'recap_reinforcement':
        try:
            w = float(sec.get('knowledge_weight', 0.3))
        except (TypeError, ValueError):
            w = 0.3
        sec['knowledge_weight'] = min(w, 0.3)
    sec['extraction_strategy'] = strategy_for_semantic_role(role_tok)

    if role_tok == 'application_domain' and typ == 'MAIN_SECTION' and idx > 0:
        violations.append('application_domain_marked_main')

    return violations


def _staged_assign_course_ontology(norm, sections: list) -> list:
    """
    Sanitation (noise sections dropped) → page flags → semantic → hierarchy → strategy/weight → validate.
    """
    if not sections:
        return []

    out = []
    current_main_title = None
    current_main_norm = ''

    for idx, sec in enumerate(sections):
        s = _enrich_section_page_flags(norm, dict(sec))
        title_raw = str(s.get('title') or '').strip()[:500]
        title_norm = _normalize_heading_key(title_raw)
        try:
            ps = int(s.get('page_start', 1))
            pe = int(s.get('page_end', ps))
        except (TypeError, ValueError):
            ps, pe = 1, 1
        if pe < ps:
            ps, pe = pe, ps
        ign = set(s.get('ignored_pages') or [])
        body = _section_body_sample(norm, ps, pe, ign)
        span = pe - ps + 1

        if is_noise_section(title_raw, body):
            continue

        kept_ix = len(out)
        semantic = _detect_semantic_role_deterministic(title_raw, body)
        has_main = bool(current_main_title)
        htype = _detect_hierarchy_type_deterministic(
            kept_ix, title_raw, title_norm, span, has_main, current_main_norm,
        )
        s['type'] = htype
        if htype == 'MAIN_SECTION':
            s['parent'] = None
        else:
            s['parent'] = current_main_title

        strat, w = _defaults_for_semantic_role(semantic, htype)
        s['semantic_role'] = semantic
        s['extraction_strategy'] = strat
        s['knowledge_weight'] = float(w)

        viol = _ontology_validate_and_repair(s, kept_ix, current_main_title)
        if s['type'] == 'SUBSECTION' and (not s.get('parent')) and current_main_title:
            s['parent'] = current_main_title
        s['ontology_violations'] = viol

        advance_main = s['type'] == 'MAIN_SECTION' and not _title_is_reference_heading(title_raw)
        if advance_main:
            current_main_title = title_raw
            current_main_norm = title_norm

        out.append(s)

    return out


def _propose_sections_firstline_fallback(norm):
    """Legacy: rare short first-line changes; single huge blob → fixed windows."""
    n = len(norm)
    if n == 0:
        return []

    first_lines = []
    keys = []
    for p in norm:
        fl = _page_first_non_empty_line(p.get('text') or '')
        first_lines.append(fl)
        k = _normalize_heading_key(fl) if fl and len(fl) <= 120 else ''
        keys.append(k)

    key_counts = {}
    for k in keys:
        if k:
            key_counts[k] = key_counts.get(k, 0) + 1
    repeat_thr = max(3, max(1, n // 4))
    repeated = {k for k, v in key_counts.items() if v >= repeat_thr}

    sections = []
    start_page = int(norm[0]['page'])
    fk0 = _normalize_heading_key(first_lines[0])
    if first_lines[0].strip() and fk0 not in repeated:
        t0 = first_lines[0].strip()[:200]
    else:
        t0 = f'Document start (page {start_page})'
    title = t0

    for i in range(1, n):
        k = keys[i]
        fl = first_lines[i]
        rare = k and k not in repeated
        short = bool(fl) and len(fl) <= 120
        changed = k and k != keys[i - 1]
        if rare and short and changed:
            end_page = int(norm[i - 1]['page'])
            sections.append({
                'title': title[:500],
                'page_start': start_page,
                'page_end': end_page
            })
            start_page = int(norm[i]['page'])
            title = fl.strip()[:200] or f'Section (pages {start_page})'

    sections.append({
        'title': title[:500],
        'page_start': start_page,
        'page_end': int(norm[-1]['page'])
    })

    if len(sections) == 1 and (sections[0]['page_end'] - sections[0]['page_start'] + 1) > 14:
        ps0, pe0 = sections[0]['page_start'], sections[0]['page_end']
        window = 12
        sections = []
        cur = ps0
        part = 1
        while cur <= pe0:
            end = min(cur + window - 1, pe0)
            sections.append({
                'title': f'Part {part} (pages {cur}–{end})',
                'page_start': cur,
                'page_end': end
            })
            cur = end + 1
            part += 1

    return [_enrich_section_page_flags(norm, dict(s)) for s in sections]


# --- Semantic split protection (curriculum domain boundaries > page continuity) ---
# When adjacent sections would merge, or a MAIN title encodes multiple topic families,
# keep separate MAIN_SECTION rows instead of gluing titles and page spans.

try:
    _SEMANTIC_DOMAIN_SPLIT_MIN = max(2, int(os.getenv('SEMANTIC_DOMAIN_SPLIT_MIN_BUCKETS', '2')))
except (TypeError, ValueError):
    _SEMANTIC_DOMAIN_SPLIT_MIN = 2

# Longer / more specific phrases first for non-overlapping span picks.
_CURRICULUM_DOMAIN_REGEX_ORDERED = (
    ('sharing_economy', re.compile(r'sharing\s+economy|shareconomy', re.I)),
    ('open_source', re.compile(r'open\s*source|\bfoss\b', re.I)),
    ('platform_ecosystem', re.compile(r'platform\s+ecosystem', re.I)),
    ('two_sided_market', re.compile(r'two[\s-]sided(?:\s+market)?', re.I)),
    ('user_innovation', re.compile(r'user\s+innovation', re.I)),
    ('lead_user', re.compile(r'lead\s+users?', re.I)),
    ('digital_transformation', re.compile(r'digital\s+transformation', re.I)),
    ('governance', re.compile(r'\bgovernance\b|regulatory\s+framework', re.I)),
    ('ecosystem', re.compile(r'\becosystems?\b', re.I)),
    ('platform', re.compile(r'\bplatforms?\b', re.I)),
    ('innovation', re.compile(r'\binnovation\b|\binnovators?\b', re.I)),
)

_DOMAIN_KEY_TO_COARSE = {
    'sharing_economy': 'sharing_economy',
    'open_source': 'open_source',
    'governance': 'governance',
    'platform_ecosystem': 'platform',
    'two_sided_market': 'platform',
    'user_innovation': 'innovation',
    'lead_user': 'innovation',
    'digital_transformation': 'innovation',
    'ecosystem': 'platform',
    'platform': 'platform',
    'innovation': 'innovation',
}


def _normalize_title_for_domain_glues(title: str) -> str:
    t = title or ''
    t = re.sub(r'([a-z])([A-Z])', r'\1 \2', t)
    t = re.sub(r'[\s_]+', ' ', t).strip()
    return t


def _domain_spans_non_overlapping(text: str):
    """Greedy longest-first non-overlapping domain spans in original string indices."""
    if not text or not str(text).strip():
        return []
    candidates = []
    for key, rx in _CURRICULUM_DOMAIN_REGEX_ORDERED:
        for m in rx.finditer(text):
            candidates.append((m.start(), m.end(), key, m.end() - m.start()))
    candidates.sort(key=lambda x: (-x[3], x[0]))
    picked = []
    for start, end, key, _ in candidates:
        if any(not (end <= ps or start >= pe) for ps, pe, _k in picked):
            continue
        picked.append((start, end, key))
    picked.sort(key=lambda x: x[0])
    return picked


def _coarse_bucket_for_domain_key(key: str) -> str:
    return _DOMAIN_KEY_TO_COARSE.get(key, key)


def _distinct_coarse_bucket_count(title: str) -> int:
    t = _normalize_title_for_domain_glues(title)
    spans = _domain_spans_non_overlapping(t)
    if not spans:
        return 0
    return len({_coarse_bucket_for_domain_key(k) for _s, _e, k in spans})


def _merge_title_like_normalize(last_title: str, sec_title: str) -> str:
    if not sec_title or sec_title in last_title:
        return last_title
    return f'{last_title}; {sec_title}'[:500]


def _semantic_split_blocks_adjacent_merge(last_sec: dict, next_sec: dict) -> bool:
    """
    If True, do not merge next into last even when pages are adjacent/overlapping.
    Semantic boundaries outrank page continuity and merge heuristics.
    """
    try:
        min_b = int(os.getenv('SEMANTIC_DOMAIN_SPLIT_MIN_BUCKETS', str(_SEMANTIC_DOMAIN_SPLIT_MIN)))
    except (TypeError, ValueError):
        min_b = _SEMANTIC_DOMAIN_SPLIT_MIN
    min_b = max(2, min_b)

    lt = last_sec.get('title') or ''
    nt = next_sec.get('title') or ''
    if _distinct_coarse_bucket_count(lt) >= min_b:
        return True
    if _distinct_coarse_bucket_count(nt) >= min_b:
        return True
    merged = _merge_title_like_normalize(str(lt), str(nt))
    if _distinct_coarse_bucket_count(merged) >= min_b:
        return True
    # Distinct single-bucket signatures on each side (e.g. innovation vs platform).
    bl = {_coarse_bucket_for_domain_key(k) for _a, _b, k in _domain_spans_non_overlapping(_normalize_title_for_domain_glues(lt))}
    bn = {_coarse_bucket_for_domain_key(k) for _a, _b, k in _domain_spans_non_overlapping(_normalize_title_for_domain_glues(nt))}
    if bl and bn and bl.isdisjoint(bn):
        return True
    return False


def _fragment_to_coarse_runs(fragment: str):
    """
    Split one title fragment into (subtitle, coarse_bucket) runs.
    Coarse may be None if no domain hit (attach later).
    """
    frag = (fragment or '').strip()
    if not frag:
        return []
    norm = _normalize_title_for_domain_glues(frag)
    spans = _domain_spans_non_overlapping(norm)
    if not spans:
        return [(frag, None)]
    coarses = [_coarse_bucket_for_domain_key(k) for _a, _b, k in spans]
    if len(set(coarses)) < 2:
        c0 = coarses[0] if coarses else None
        return [(frag, c0)]

    # Different coarse buckets inside one fragment: cut norm string at span boundaries.
    runs = []
    cur_start = 0
    cur_coarse = coarses[0]
    for i in range(1, len(spans)):
        if coarses[i] != cur_coarse:
            cut = (spans[i - 1][1] + spans[i][0]) // 2
            piece = norm[cur_start:cut].strip(' ;|')
            if piece:
                runs.append((piece, cur_coarse))
            cur_start = cut
            cur_coarse = coarses[i]
    tail = norm[cur_start:].strip(' ;|')
    if tail:
        runs.append((tail, cur_coarse))
    return runs if len({c for _, c in runs if c}) >= 2 else [(frag, coarses[0])]


def _expand_main_section_row_by_domains(sec: dict):
    """
    If a MAIN_SECTION title encodes multiple curriculum domain buckets, split into
    several MAIN rows with contiguous page sub-ranges (semantic boundary > span glue).
    """
    if str(sec.get('type', '')).strip().upper() != 'MAIN_SECTION':
        return [sec]
    try:
        min_b = int(os.getenv('SEMANTIC_DOMAIN_SPLIT_MIN_BUCKETS', str(_SEMANTIC_DOMAIN_SPLIT_MIN)))
    except (TypeError, ValueError):
        min_b = _SEMANTIC_DOMAIN_SPLIT_MIN
    min_b = max(2, min_b)

    title = str(sec.get('title', '') or '').strip()
    if not title:
        return [sec]
    if _distinct_coarse_bucket_count(_normalize_title_for_domain_glues(title)) < min_b:
        return [sec]

    pieces = re.split(r'\s*[;|]\s*', title)
    runs = []
    for p in pieces:
        runs.extend(_fragment_to_coarse_runs(p))

    if not runs:
        return [sec]

    # Forward-fill None coarse with next non-None, then previous.
    for i, (tx, bc) in enumerate(runs):
        if bc is None:
            nxt = next((runs[j][1] for j in range(i + 1, len(runs)) if runs[j][1]), None)
            if nxt:
                runs[i] = (tx, nxt)
    for i in range(len(runs) - 1, -1, -1):
        tx, bc = runs[i]
        if bc is None:
            prv = next((runs[j][1] for j in range(i - 1, -1, -1) if runs[j][1]), None)
            runs[i] = (tx, prv)

    grouped = []
    for tx, bc in runs:
        bc = bc or 'general'
        if grouped and grouped[-1][0] == bc:
            grouped[-1][1].append(tx)
        else:
            grouped.append((bc, [tx]))

    topic_buckets = {b for b, _ in grouped if b != 'general'}
    if len(topic_buckets) < min_b:
        return [sec]

    try:
        ps = int(sec['page_start'])
        pe = int(sec['page_end'])
    except (TypeError, ValueError, KeyError):
        return [sec]
    if pe < ps:
        ps, pe = pe, ps
    n_pages = pe - ps + 1
    k = len(grouped)
    if k < 2 or n_pages < k:
        return [sec]

    out_secs = []
    for i, (bucket, texts) in enumerate(grouped):
        a = ps + (i * n_pages) // k
        b = ps + ((i + 1) * n_pages) // k - 1
        sub_title = '; '.join(t for t in texts if t).strip()[:500] or bucket.replace('_', ' ').title()
        stub = {
            'title': sub_title,
            'semantic_role': sec.get('semantic_role'),
            'knowledge_weight': sec.get('knowledge_weight'),
        }
        ont = _resolve_section_ontology('MAIN_SECTION', stub)
        out_secs.append({
            'title': sub_title,
            'page_start': a,
            'page_end': b,
            'type': 'MAIN_SECTION',
            'parent': None,
            'ignored_pages': list(sec.get('ignored_pages') or []),
            'case_study_pages': list(sec.get('case_study_pages') or []),
            'recap_pages': list(sec.get('recap_pages') or []),
            'semantic_role': ont['semantic_role'],
            'extraction_strategy': ont['extraction_strategy'],
            'knowledge_weight': ont['knowledge_weight'],
        })
    print(
        f"🧱 Semantic split protection: split MAIN_SECTION ({k} domain groups) "
        f"pages {ps}-{pe} → {len(out_secs)} row(s); buckets={sorted(topic_buckets)}"
    )
    return out_secs


def _expand_multi_domain_main_sections(sections: list) -> list:
    if not sections:
        return sections
    acc = []
    for sec in sections:
        if not isinstance(sec, dict):
            continue
        if str(sec.get('type', '')).strip().upper() == 'MAIN_SECTION':
            acc.extend(_expand_main_section_row_by_domains(sec))
        else:
            acc.append(sec)
    return acc


def propose_sections_from_pdf_pages(pdf_pages):
    """
    Section boundaries for slide PDFs:
    1) Layout / text-guess separator candidates, then boundary suppression (only MAIN_SECTION).
    2) Legacy first-line rarity heuristic if no main separators.
    3) Deterministic staged ontology: hierarchy (MAIN/SUB) + semantic_role + strategy/weight + validation.
    """
    norm = normalize_pdf_pages_payload(pdf_pages)
    if not norm:
        return []
    norm.sort(key=lambda x: int(x.get('page', 0)))

    text_guess = set(_text_only_guess_section_slides(norm))
    main_idx = _collect_main_separator_indices(norm, text_guess)

    sections = None
    if len(main_idx) >= 1:
        sections = _sections_from_separator_indices(norm, main_idx)

    if not sections:
        sections = _propose_sections_firstline_fallback(norm)

    if not sections:
        return []

    sections = _maybe_window_split_long_sections(sections, max_span_pages=44)
    sections = _staged_assign_course_ontology(norm, sections)
    n_layout = sum(
        1 for p in norm
        if isinstance(p.get('layout'), dict) and p['layout'].get('is_section_slide')
    )
    print(
        f"📑 Proposed {len(sections)} section(s); layout candidates={n_layout}, "
        f"main boundaries={len(main_idx)} (recap/case/ref slides suppressed as splits); "
        f"deterministic staged ontology applied."
    )
    return sections


def normalize_course_sections_payload(raw, max_page):
    """Validate, clamp, sort, and merge adjacent/overlapping course sections."""

    def _parse_int_list(val):
        if not isinstance(val, list):
            return []
        acc = []
        for x in val:
            try:
                acc.append(int(x))
            except (TypeError, ValueError):
                continue
        return acc

    def _clamp_list(pages, a, b):
        return sorted({p for p in pages if a <= p <= b})

    if not raw or not isinstance(raw, list):
        return None
    try:
        mp = int(max_page)
    except (TypeError, ValueError):
        mp = 1
    mp = max(1, mp)

    out = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        title = str(item.get('title', '') or '').strip() or 'Untitled section'
        if is_noise_section(title, None):
            continue
        try:
            ps = int(item.get('page_start', 1))
            pe = int(item.get('page_end', ps))
        except (TypeError, ValueError):
            continue
        ps = max(1, min(ps, mp))
        pe = max(ps, min(pe, mp))
        typ = str(item.get('type', 'MAIN_SECTION') or 'MAIN_SECTION').strip().upper()
        raw_typ = typ
        legacy_sem = None
        if raw_typ in LEGACY_HIERARCHY_TYPES:
            typ = 'SUBSECTION'
            legacy_sem = LEGACY_TYPE_TO_SEMANTIC.get(raw_typ)
        elif typ not in SECTION_TYPES:
            typ = 'MAIN_SECTION'
        item_for_ont = dict(item)
        sr_existing = item.get('semantic_role') if isinstance(item.get('semantic_role'), str) else ''
        if legacy_sem and not (sr_existing and sr_existing.strip()):
            item_for_ont['semantic_role'] = legacy_sem
        parent = item.get('parent')
        if parent is None:
            parent_str = None
        else:
            p = str(parent).strip()
            parent_str = p[:500] if p else None
        ign = _clamp_list(_parse_int_list(item.get('ignored_pages')), ps, pe)
        casep = _clamp_list(_parse_int_list(item.get('case_study_pages')), ps, pe)
        recap = _clamp_list(_parse_int_list(item.get('recap_pages')), ps, pe)
        ont = _resolve_section_ontology(typ, item_for_ont)
        out.append({
            'title': title[:500],
            'page_start': ps,
            'page_end': pe,
            'type': typ,
            'parent': parent_str,
            'ignored_pages': ign,
            'case_study_pages': casep,
            'recap_pages': recap,
            'semantic_role': ont['semantic_role'],
            'extraction_strategy': ont['extraction_strategy'],
            'knowledge_weight': ont['knowledge_weight'],
        })

    if not out:
        return None
    out.sort(key=lambda x: (x['page_start'], x['page_end']))
    # Split jammed MAIN titles before adjacent merge (semantic domain > page glue).
    out = _expand_multi_domain_main_sections(out)
    out.sort(key=lambda x: (x['page_start'], x['page_end']))

    merged = []
    for sec in out:
        if not merged:
            merged.append(sec)
            continue
        last = merged[-1]
        if sec['page_start'] <= last['page_end'] + 1:
            if _semantic_split_blocks_adjacent_merge(last, sec):
                print(
                    f"🧱 Semantic split protection: blocked merge — "
                    f"'{str(last.get('title', ''))[:48]}...' | "
                    f"'{str(sec.get('title', ''))[:48]}...' "
                    f"(pages {last['page_start']}-{last['page_end']} vs {sec['page_start']}-{sec['page_end']})"
                )
                adj = dict(sec)
                bump_to = last['page_end'] + 1
                if adj['page_start'] <= last['page_end'] and bump_to <= adj['page_end']:
                    adj['page_start'] = bump_to
                merged.append(adj)
                continue
            last['page_end'] = max(last['page_end'], sec['page_end'])
            if sec['title'] and sec['title'] not in last['title']:
                last['title'] = f"{last['title']}; {sec['title']}"[:500]
            last['ignored_pages'] = sorted(set(last.get('ignored_pages', [])) | set(sec.get('ignored_pages', [])))
            last['case_study_pages'] = sorted(set(last.get('case_study_pages', [])) | set(sec.get('case_study_pages', [])))
            last['recap_pages'] = sorted(set(last.get('recap_pages', [])) | set(sec.get('recap_pages', [])))
            lw = float(last.get('knowledge_weight', 0) or 0)
            sw = float(sec.get('knowledge_weight', 0) or 0)
            if sec.get('type') == 'MAIN_SECTION':
                last['type'] = 'MAIN_SECTION'
                last['parent'] = None
                last['semantic_role'] = sec.get('semantic_role', last.get('semantic_role'))
            elif sw >= lw:
                last['semantic_role'] = sec.get('semantic_role', last.get('semantic_role'))
            last['knowledge_weight'] = max(lw, sw)
            if not last.get('parent') and sec.get('parent'):
                last['parent'] = sec.get('parent')
        else:
            merged.append(sec)

    # Resolve/validate parent links after merge.
    current_main_title = None
    main_titles = set()
    for sec in merged:
        if sec.get('type') == 'MAIN_SECTION':
            current_main_title = sec.get('title')
            sec['parent'] = None
            if current_main_title:
                main_titles.add(current_main_title)
        else:
            p = sec.get('parent')
            if isinstance(p, str) and p.strip():
                p = p.strip()
            else:
                p = current_main_title
            if p not in main_titles:
                p = current_main_title
            sec['parent'] = p if p else None

    for si, sec in enumerate(merged, start=1):
        sid = str(sec.get('section_id') or '').strip()
        sec['section_id'] = (sid or f'sec_{si:04d}')[:80]

    for sec in merged:
        ps, pe = sec['page_start'], sec['page_end']
        sec['ignored_pages'] = _clamp_list(sec.get('ignored_pages', []), ps, pe)
        sec['case_study_pages'] = _clamp_list(sec.get('case_study_pages', []), ps, pe)
        sec['recap_pages'] = _clamp_list(sec.get('recap_pages', []), ps, pe)
        sr_tok = _sanitize_ontology_token(str(sec.get('semantic_role') or '')) or 'theory_domain'
        sec['semantic_role'] = sr_tok
        sec['extraction_strategy'] = strategy_for_semantic_role(sr_tok)

    return merged


def build_llm_chunks_from_course_sections(sections, pdf_pages, max_chars=1000, overlap_chars=120):
    """
    Merge PDF pages per section, then sub-split. Skips reference_material sections and ignored_pages.
    MAIN_SECTION uses larger max_chars when MAIN_SECTION_MAX_CHARS is set.
    """
    if not sections or not pdf_pages:
        return []

    try:
        main_max = int(os.getenv('MAIN_SECTION_MAX_CHARS', '2000'))
    except ValueError:
        main_max = 2000
    main_max = max(900, min(main_max, 12000))

    norm = normalize_pdf_pages_payload(pdf_pages)
    if not norm:
        return []

    page_map = {}
    source_by_page = {}
    for entry in norm:
        try:
            pn = int(entry.get('page', 0))
        except (TypeError, ValueError):
            continue
        if pn < 1:
            continue
        raw_t = entry.get('text') or ''
        if pn in page_map:
            page_map[pn] = f"{page_map[pn]}\n\n{raw_t}"
        else:
            page_map[pn] = raw_t
        sn = entry.get('source_name')
        if isinstance(sn, str) and sn.strip():
            source_by_page[pn] = sn.strip()[:500]

    chunks = []
    for sec in sections:
        if not isinstance(sec, dict):
            continue
        st = str(sec.get('type') or 'MAIN_SECTION').strip().upper()
        if st not in SECTION_TYPES:
            st = 'MAIN_SECTION'

        title = str(sec.get('title', 'Section') or 'Section').strip()[:500]
        parent = sec.get('parent')
        parent = str(parent).strip()[:500] if isinstance(parent, str) and parent.strip() else None
        try:
            ps = int(sec.get('page_start', 1))
            pe = int(sec.get('page_end', ps))
        except (TypeError, ValueError):
            continue
        if pe < ps:
            ps, pe = pe, ps

        body_snip = ''
        for pg in range(ps, pe + 1):
            body_snip += (page_map.get(pg) or '') + '\n'
            if len(body_snip) >= 1600:
                break
        if is_noise_section(title, body_snip):
            continue

        skip_pages = set(sec.get('ignored_pages') or [])
        child_case_pages = set(sec.get('case_study_pages') or [])
        child_recap_pages = set(sec.get('recap_pages') or [])
        child_pages = (child_case_pages | child_recap_pages) - skip_pages
        max_for_sec = main_max if st == 'MAIN_SECTION' else min(main_max, 1300)

        ont = _resolve_section_ontology(st, sec)
        if ont.get('semantic_role') == 'reference_material':
            continue
        sr = ont['semantic_role']
        es = ont['extraction_strategy']
        kw = ont['knowledge_weight']

        body_parts = []
        for pg in range(ps, pe + 1):
            if pg in skip_pages:
                continue
            if pg in child_pages:
                continue
            if pg in page_map:
                body_parts.append(page_map[pg])
        body = clean_text_for_chunking('\n\n'.join(body_parts))

        src = source_by_page.get(ps) or source_by_page.get(pe) or ''
        src_prefix = f"{src}, " if src else ''
        range_note = ps if ps == pe else f'{ps}-{pe}'
        meta_bits = []
        cp = sec.get('case_study_pages') or []
        rp = sec.get('recap_pages') or []
        if cp:
            meta_bits.append(f'case_slides={cp}')
        if rp:
            meta_bits.append(f'recap_slides={rp}')
        if parent:
            meta_bits.append(f'parent={parent}')
        meta_bits.append(f'semantic_role={sr}')
        meta_bits.append(f'extraction_strategy={es}')
        meta_bits.append(f'knowledge_weight={kw}')
        sid = str(sec.get('section_id') or '').strip()
        if sid:
            meta_bits.append(f'section_id={sid}')
        meta_suffix = f" | {' | '.join(meta_bits)}" if meta_bits else ''
        head_base = f"[{src_prefix}Section: {title} | Pages {range_note}{meta_suffix}]"

        # Parent/main body chunk (excluding child pages) for hierarchy-aware extraction.
        if body.strip():
            if len(body) <= max_for_sec:
                chunks.append(f"{head_base}\n\n{body}")
            else:
                sub = split_text_into_chunks(body, max_chars=max_for_sec, overlap_chars=overlap_chars)
                total_sub = len(sub)
                for si, piece in enumerate(sub, start=1):
                    if total_sub > 1:
                        head = f"[{src_prefix}Section: {title} | Pages {range_note} — part {si}/{total_sub}{meta_suffix}]\n\n"
                    else:
                        head = f"{head_base}\n\n"
                    chunks.append(f"{head}{piece}")

        # Child chunks: keep subsection/case/recap tied to parent context.
        for pg in sorted(child_pages):
            raw = page_map.get(pg, '')
            child_text = clean_text_for_chunking(raw)
            if not child_text:
                continue
            if pg in child_case_pages:
                cro, crs, cwdef = _CHILD_SLIDE_SEMANTIC_DEFAULTS['case_slide']
            else:
                cro, crs, cwdef = _CHILD_SLIDE_SEMANTIC_DEFAULTS['recap_slide']
            child_max = min(max_for_sec, 1200)
            pw = _parse_knowledge_weight(sec.get('knowledge_weight'), kw)
            child_w = min(pw, float(cwdef))
            child_head = (
                f"[{src_prefix}Parent Section: {title}"
                f" | child_semantic_role={cro}"
                f" | Child Slide Page: {pg}"
                f"{f' | Parent Topic: {parent}' if parent else ''}"
                f" | semantic_role={cro} | extraction_strategy={crs} | knowledge_weight={child_w}"
                f"{f' | section_id={sid}' if sid else ''}]"
            )
            if len(child_text) <= child_max:
                chunks.append(f"{child_head}\n\n{child_text}")
                continue
            child_sub = split_text_into_chunks(child_text, max_chars=child_max, overlap_chars=overlap_chars)
            total_child = len(child_sub)
            for ci, piece in enumerate(child_sub, start=1):
                if total_child > 1:
                    chead = f"{child_head[:-1]} | part {ci}/{total_child}]\n\n"
                else:
                    chead = f"{child_head}\n\n"
                chunks.append(f"{chead}{piece}")
    return chunks


def extract_hierarchy_context_from_chunk(chunk_text: str) -> dict:
    """
    Parse hierarchy context encoded in chunk header lines like:
    [Section: X | Pages 1-5 | parent=Y | semantic_role=theory_domain | extraction_strategy=concept_dense | knowledge_weight=1.0]
    [Parent Section: X | child_semantic_role=case_study | Child Slide Page: 12 | semantic_role=case_study | ...]
    """
    if not chunk_text:
        return {}
    first_line = str(chunk_text).split('\n', 1)[0].strip()
    if not (first_line.startswith('[') and first_line.endswith(']')):
        return {}
    inside = first_line[1:-1]
    parts = [p.strip() for p in inside.split('|') if p.strip()]
    ctx = {}
    for part in parts:
        if ':' in part:
            k, v = part.split(':', 1)
            key = k.strip().lower().replace(' ', '_')
            val = v.strip()
            if key and val:
                ctx[key] = val
        elif '=' in part:
            k, v = part.split('=', 1)
            key = k.strip().lower().replace(' ', '_')
            val = v.strip()
            if key and val:
                ctx[key] = val
    return ctx


def build_chunk_index_to_section_id(chunks):
    """Map 1-based chunk_index (as emitted by extractors) -> section_id from chunk header."""
    if not chunks:
        return {}
    out = {}
    for i, ch in enumerate(chunks, start=1):
        ctx = extract_hierarchy_context_from_chunk(ch)
        sid = str(ctx.get('section_id', '') or '').strip()
        out[i] = sid or 'sec_root'
    return out


# Parse structured TXT file
def parse_structured_txt(text_content):
    """Parse structured TXT file format (supports Chinese/English metadata and chapter markers)"""
    metadata = {}
    materials = []

    lines = text_content.split('\n')
    in_metadata = False
    in_content = False
    current_chapter = ""

    # Supported headers (English only, but can parse Chinese legacy formats)
    meta_headers = {'# Course Meta Information'}
    content_headers = {'# Course Content'}

    # Metadata key mapping (English only, but can parse Chinese legacy formats)
    key_map = {
        'Course Name': 'subject',
        'Category': 'category',
        'Difficulty': 'difficulty',
        'Description': 'description',
        # Legacy Chinese support (for backwards compatibility with old files)
        '课程名称': 'subject',
        '类别': 'category',
        '难度': 'difficulty',
        '描述': 'description',
    }

    for line in lines:
        line = line.strip()

        # Detect metadata section
        if line in meta_headers:
            in_metadata = True
            in_content = False
            continue
        elif line in content_headers:
            in_metadata = False
            in_content = True
            continue

        # Parse metadata
        if in_metadata and ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            mapped = key_map.get(key)
            if mapped:
                metadata[mapped] = value

        # Parse course content
        if in_content:
            # Chapter title
            if line.startswith('## '):
                current_chapter = line[3:].strip()
            # Knowledge point/entry
            elif line.startswith('### '):
                point_title = line[4:].strip()
                materials.append(point_title)

    return metadata, materials

def clean_text_for_chunking(text: str) -> str:
    """Lightweight cleanup before chunking."""
    lines = text.splitlines()
    cleaned = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        # Drop obvious noise
        if "http://" in s or "https://" in s:
            continue
        if len(s) < 3:
            continue
        cleaned.append(s)
    return "\n".join(cleaned)

def split_text_into_chunks(text: str, max_chars: int = 2200, overlap_chars: int = 220):
    """
    Split text into semantically friendlier chunks for local small LLMs.
    Preference order: paragraph -> sentence -> fixed windows.
    """
    text = clean_text_for_chunking(text)
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    def push_chunk(content: str):
        content = content.strip()
        if content:
            chunks.append(content)

    for para in paragraphs:
        # If a single paragraph is too large, split by sentence first
        if len(para) > max_chars:
            sentences = re.split(r'(?<=[\.\!\?。！？])\s+', para)
            tmp = ""
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                if len(tmp) + len(sent) + 1 <= max_chars:
                    tmp = f"{tmp} {sent}".strip()
                else:
                    if tmp:
                        push_chunk(tmp)
                    # If one sentence is still too long, hard split
                    if len(sent) > max_chars:
                        start = 0
                        while start < len(sent):
                            end = min(start + max_chars, len(sent))
                            push_chunk(sent[start:end])
                            start = end
                        tmp = ""
                    else:
                        tmp = sent
            if tmp:
                # merge with current if room allows
                if len(current) + len(tmp) + 2 <= max_chars:
                    current = f"{current}\n\n{tmp}".strip() if current else tmp
                else:
                    push_chunk(current)
                    current = tmp
            continue

        # Normal paragraph packing
        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}".strip() if current else para
        else:
            push_chunk(current)
            current = para

    if current:
        push_chunk(current)

    # Add lightweight overlap to preserve local context
    if overlap_chars > 0 and len(chunks) > 1:
        overlapped = []
        for i, ch in enumerate(chunks):
            if i == 0:
                overlapped.append(ch)
                continue
            prev_tail = chunks[i - 1][-overlap_chars:]
            merged = f"{prev_tail}\n\n{ch}"
            overlapped.append(merged)
        chunks = overlapped

    return chunks

def _extract_balanced_json_slice(s: str, start: int):
    """Return substring from start (index of '{') through matching '}' using JSON-ish string rules."""
    depth = 0
    in_str = False
    esc = False
    i = start
    while i < len(s):
        ch = s[i]
        if esc:
            esc = False
            i += 1
            continue
        if in_str:
            if ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            i += 1
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
        i += 1
    return None


def _parse_first_json_object_from_string(s: str):
    """Try json.loads on first balanced {...} object in s."""
    if not s:
        return None
    pos = 0
    while True:
        start = s.find('{', pos)
        if start < 0:
            break
        chunk = _extract_balanced_json_slice(s, start)
        if chunk:
            try:
                return json.loads(chunk)
            except Exception:
                pass
        pos = start + 1
    return None


def extract_first_json_object(text: str):
    """Best-effort JSON extraction from LLM responses (markdown fences, Gemini prose wrappers)."""
    if not text:
        return None
    s = str(text).strip()
    if not s:
        return None

    m_fence = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', s, re.IGNORECASE)
    if m_fence:
        inner = m_fence.group(1).strip()
        got = _parse_first_json_object_from_string(inner)
        if got is not None:
            return got

    got = _parse_first_json_object_from_string(s)
    if got is not None:
        return got

    match = re.search(r'\{[\s\S]*\}', s)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except Exception:
        return None

def normalize_concept_key(name: str) -> str:
    s = (name or '').strip().lower()
    s = re.sub(r'[\s\-_]+', ' ', s)
    s = re.sub(r'[^\w\s]', '', s)
    return s


_ONT_TRAILING_PARENS = re.compile(r'\(([^)]+)\)\s*$')
_ONT_IRREGULAR_PLURAL = {
    'technologies': 'technology',
    'purposes': 'purpose',
    'studies': 'study',
    'analyses': 'analysis',
    'criteria': 'criterion',
    'phenomena': 'phenomenon',
    'matrices': 'matrix',
    'indices': 'index',
    'vertices': 'vertex',
    'leaves': 'leaf',
}


def _ontology_split_trailing_acronym(title: str):
    """Split display title into core text and optional trailing parenthetical acronym."""
    t = (title or '').strip()
    m = _ONT_TRAILING_PARENS.search(t)
    if not m:
        return t, None
    core = t[: m.start()].strip()
    return core, m.group(1).strip()


def _ontology_normalize_acronym_token(inner: str) -> str:
    """Normalize acronym for matching (e.g. GPTs / APIs -> gpt / api); keep CSS, CLASS intact."""
    if not inner:
        return ''
    alnum = re.sub(r'[^A-Za-z0-9]', '', inner.strip())
    if not alnum:
        return ''
    # Typical plural short acronyms: GPTs, APIs, LLMs (2–3 letter core + s)
    if re.match(r'^[A-Za-z]{2,3}s$', alnum, re.I):
        alnum = alnum[:-1]
    u = alnum.upper()
    if u.isalpha() and len(u) >= 2:
        return u.lower()
    return alnum.lower()


def _ontology_singularize_token(tok: str) -> str:
    w = (tok or '').lower()
    if len(w) <= 2:
        return w
    if w in _ONT_IRREGULAR_PLURAL:
        return _ONT_IRREGULAR_PLURAL[w]
    if w.endswith('ies') and len(w) > 3:
        return w[:-3] + 'y'
    for suf in ('ches', 'shes', 'sses', 'xes', 'zes', 'oes'):
        if w.endswith(suf) and len(w) > len(suf) + 1:
            return w[: -len(suf)]
    if w.endswith('s') and not w.endswith('ss') and len(w) > 3:
        if w.endswith(('us', 'is', 'as', 'os')):
            return w
        return w[:-1]
    return w


def _ontology_title_fingerprint(title: str) -> str:
    """
    Deterministic signature for duplicate detection: core words (light singularization)
    + normalized trailing acronym token.
    """
    core, acr_raw = _ontology_split_trailing_acronym(title)
    core_key = normalize_concept_key(core)
    toks = [_ontology_singularize_token(x) for x in core_key.split() if x]
    fp_core = ' '.join(toks)
    acr = _ontology_normalize_acronym_token(acr_raw) if acr_raw else ''
    if acr:
        return f'{fp_core} {acr}'.strip()
    return fp_core


def _ontology_fp_token_sets(fp: str):
    return {t for t in (fp or '').split() if len(t) > 1}


def _ontology_token_overlap_metrics(sa, sb):
    if not sa or not sb:
        return 0.0, 0.0
    inter = len(sa & sb)
    uni = len(sa | sb)
    jacc = inter / uni if uni else 0.0
    ovl = inter / min(len(sa), len(sb)) if (sa and sb) else 0.0
    return jacc, ovl


def _ontology_char_ngram_counts(s: str, n: int = 3):
    t = re.sub(r'[^a-z0-9]+', ' ', (s or '').lower())
    t = f' {t.strip()} '
    grams = {}
    i = 0
    lim = len(t) - n
    while i <= lim:
        g = t[i : i + n]
        if '  ' not in g:
            grams[g] = grams.get(g, 0) + 1
        i += 1
    return grams


def _ontology_cosine_sparse_dict(a: dict, b: dict) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    if len(a) <= len(b):
        for k, va in a.items():
            vb = b.get(k)
            if vb is not None:
                dot += va * vb
    else:
        for k, vb in b.items():
            va = a.get(k)
            if va is not None:
                dot += va * vb
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def _ontology_char_ngram_cosine(a: str, b: str) -> float:
    return _ontology_cosine_sparse_dict(
        _ontology_char_ngram_counts(a), _ontology_char_ngram_counts(b)
    )


def _ontology_openai_embeddings_matrix(titles):
    """
    Optional embedding similarity (cosine). Requires OPENAI_API_KEY; returns None on failure.
    """
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key or len(titles) > 300:
        return None
    url = 'https://api.openai.com/v1/embeddings'
    model = os.environ.get('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small').strip() or 'text-embedding-3-small'
    all_vecs = []
    batch = 32
    try:
        for i in range(0, len(titles), batch):
            chunk = titles[i : i + batch]
            r = requests.post(
                url,
                headers={
                    'Authorization': f'Bearer {key}',
                    'Content-Type': 'application/json',
                },
                json={'model': model, 'input': chunk},
                timeout=90,
            )
            r.raise_for_status()
            data = r.json().get('data') or []
            data.sort(key=lambda x: x.get('index', 0))
            for row in data:
                emb = row.get('embedding')
                if isinstance(emb, list):
                    all_vecs.append(emb)
            if len(all_vecs) != i + len(data):
                return None
        n = len(all_vecs)
        if n != len(titles):
            return None
        mat = [[0.0] * n for _ in range(n)]
        for ii in range(n):
            vi = all_vecs[ii]
            for jj in range(ii + 1, n):
                vj = all_vecs[jj]
                dot = sum(x * y for x, y in zip(vi, vj))
                na = math.sqrt(sum(x * x for x in vi))
                nb = math.sqrt(sum(y * y for y in vj))
                c = dot / (na * nb) if na and nb else 0.0
                mat[ii][jj] = mat[jj][ii] = c
        return mat
    except Exception as e:
        print(f'⚠️ Ontology dedup: embedding pass skipped ({e})')
        return None


def _ontology_canonical_member_key(c: dict):
    """Prefer shorter / less plural display titles; tie-break by richer content."""
    title = str(c.get('concept', '') or '')
    core, _ = _ontology_split_trailing_acronym(title)
    core_l = core.strip().lower()
    plural_bias = 0
    if 'technologies' in core_l:
        plural_bias += 3
    if re.search(r'\b\w+ies\b', core_l):
        plural_bias += 1
    def_len = len(str((c.get('definition') or {}).get('text', '') or ''))
    return (len(core.strip()), plural_bias, -def_len, -len(c.get('key_facts') or []), title.lower())


def _merge_unique_definition_blocks(texts):
    blocks = []
    seen = set()
    for t in texts:
        s = str(t).strip()
        if not s:
            continue
        k = normalize_concept_key(s)
        if len(k) >= 12 and k in seen:
            continue
        if len(k) >= 12:
            seen.add(k)
        blocks.append(s)
    blocks.sort(key=len, reverse=True)
    return '\n\n'.join(blocks)


def _dedupe_str_list(items):
    seen = set()
    out = []
    for it in items:
        s = str(it).strip()
        if not s:
            continue
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
    return out

_SINGLE_WORD_TITLE_NOISE = frozenset({
    'introduction', 'overview', 'conclusion', 'summary', 'objectives',
    'references', 'bibliography', 'acknowledgements', 'acknowledgments',
    'appendix', 'agenda', 'outline', 'background',
})


def _is_fallback_noise(text: str) -> bool:
    """
    Returns True if a candidate concept title extracted by heuristic fallback
    should be discarded as noise / PDF artefact.
    """
    if not text:
        return True
    t = text.strip()

    # File separator banners like "===== SOURCE FILE 1: ... ====="
    if t.startswith('=') or t.startswith('-' * 4):
        return True
    if re.search(r'={4,}|[-]{4,}', t):
        return True

    # Bullet-fragment lines – start with punctuation noise
    if re.match(r'^[•·►▪■□●\-\*]+', t):
        return True

    # Lines that start with a PDF keyword prefix but have no real noun/sentence
    # e.g. "Method: s: • APIs", "Model: ) • Identify is this"
    if re.match(r'^(Method|Model|Section|Figure|Table|Appendix|Note|Source|Page|Slide)\s*[:：\d]', t, re.IGNORECASE):
        # Allow only if the rest looks like a real sentence (≥3 alpha words, no bullets)
        rest = re.sub(r'^[^:：]+[:：]\s*', '', t)
        words = [w for w in re.split(r'\W+', rest) if len(w) >= 3 and w.isalpha()]
        has_bullets_in_rest = bool(re.search(r'[•·►▪■□●]', rest))
        if len(words) < 3 or has_bullets_in_rest:
            return True

    # Truncated fragments: end in abbreviation mid-word (last word < 4 chars and not a full stop)
    if re.search(r'\s\S{1,3}$', t) and not t.endswith(('.', ')', '?', '!')):
        return True

    # Too many bullet chars / slash / pipe symbols – it's a list not a concept title
    noise_chars = sum(1 for c in t if c in '•·►▪■□●|/\\')
    if noise_chars >= 3:
        return True

    # Minimum meaningful alpha content (allow one long scholarly head noun, e.g. topic hubs)
    alpha_words = [w for w in re.split(r'\W+', t) if len(w) >= 3 and w.isalpha()]
    if len(alpha_words) < 2:
        if len(alpha_words) == 1 and 10 <= len(alpha_words[0]) <= 48:
            lw = alpha_words[0].lower()
            if lw not in _SINGLE_WORD_TITLE_NOISE:
                return False
        return True

    return False


def looks_like_non_concept_label(text: str) -> bool:
    s = (text or '').strip().lower()
    if not s:
        return True
    if s.endswith('?'):
        return True
    blocked_prefixes = [
        'why ', 'what ', 'how ', 'question', 'questions', 'discussion',
        'case study', 'case studies', 'summary', 'overview', 'agenda',
        'learning objective', 'learning objectives', 'chapter ', 'section '
    ]
    for p in blocked_prefixes:
        if s.startswith(p):
            return True
    return False


_ONTOLOGY_PLACEHOLDER_KEYS = frozenset({
    'n/a', 'na', 'n a', 'tbd', 'tba', 'none', 'null', 'nil',
    'unknown', 'untitled', 'placeholder', 'no title', 'blank', 'empty',
    'insert title here', 'title goes here', 'add title', 'new slide',
    'slide', 'slides', 'todo', 'lorem ipsum', 'test', 'testing',
    'xxx', 'yyy', '...', '-', '--', '—',
})

_ONTOLOGY_COURSE_HEADER_RES = (
    re.compile(
        r'^(course|module|week|lecture|class|tutorial|session|lab|seminar|workshop)\s*[:#]?\s*\d+\b',
        re.I,
    ),
    re.compile(r'^(week|module|lecture|session|tutorial|class)\s+\d+\s*$', re.I),
    re.compile(
        r'^(week|module|lecture|session|tutorial|class)\s+\d+\s*[:.\-–—]\s*\S',
        re.I,
    ),
    re.compile(r'^(comp|info|csce|ece|math|stat|fin|acct|mgmt)\d{3,4}\s*$', re.I),
    re.compile(r'^\d+\s*[\.\)]\s*(introduction|overview|background|outline|agenda)\b', re.I),
    re.compile(r'\bcopyright\s*©?\s*\d{4}', re.I),
    re.compile(r"^today'?s?\s+(outline|agenda|plan)\b", re.I),
    re.compile(r'^syllabus\b', re.I),
    re.compile(r'^reading\s+list\b', re.I),
)

_ONTOLOGY_INSTITUTIONAL_META_RES = (
    re.compile(
        r'\b(university|college|polytechnic|institute of technology|faculty of|school of|'
        r'department of|dean\'?s office|registrar)\b',
        re.I,
    ),
    re.compile(
        r'\b(professor|prof\.|associate\s+professor|assistant\s+professor|'
        r'dr\.|lecturer|instructor|teaching\s+staff|course\s+coordinator|unit\s+chair)\b',
        re.I,
    ),
    re.compile(
        r'\b(prepared\s+by|submitted\s+by|author\s*:|written\s+by|presented\s+by|'
        r'compiled\s+by|designed\s+by)\b',
        re.I,
    ),
    re.compile(r'[@][a-z0-9.\-]+\.(edu|edu\.[a-z]{2}|ac\.[a-z.]+)\b', re.I),
    re.compile(r'\b(room|building|campus|office\s+hours)\s+[a-z0-9][a-z0-9\-]{0,15}\b', re.I),
    re.compile(r'\bstudent\s+id\b|\bstudent\s+number\b', re.I),
)

_ONTOLOGY_SLIDE_SHELL_RES = (
    re.compile(r'^(slide|page|fig\.?|figure|table|chart)\s*\d+\s*$', re.I),
    re.compile(r'^(slide|page)\s*\d+\s*[/\\]\s*\d+\s*$', re.I),
    re.compile(r'^(slide|page)\s*\d+\s*[:.\-]\s*\S', re.I),
)

_ONTOLOGY_READING_APPARATUS_RES = re.compile(
    r'^(references|bibliography|further\s+reading|footnotes|appendix|'
    r'acknowledg|glossary|index)\b',
    re.I,
)


def _ontology_title_is_placeholder(title: str) -> bool:
    raw = (title or '').strip()
    if not raw:
        return True
    k = normalize_concept_key(raw)
    if not k:
        return True
    if k in _ONTOLOGY_PLACEHOLDER_KEYS:
        return True
    return False


def _ontology_title_is_course_or_syllabus_header(title: str) -> bool:
    t = (title or '').strip()
    if not t:
        return True
    if len(t) > 220:
        return False
    for rx in _ONTOLOGY_COURSE_HEADER_RES:
        if rx.search(t):
            return True
    return False


def _ontology_title_is_institutional_metadata(title: str) -> bool:
    t = (title or '').strip()
    if not t:
        return True
    if len(t) > 260:
        return False
    for rx in _ONTOLOGY_INSTITUTIONAL_META_RES:
        if rx.search(t):
            return True
    return False


def _ontology_title_is_slide_or_page_shell(title: str) -> bool:
    t = (title or '').strip()
    if not t:
        return True
    if len(t) > 120:
        return False
    for rx in _ONTOLOGY_SLIDE_SHELL_RES:
        if rx.match(t):
            return True
    return False


def _ontology_title_substance_word_count(title: str) -> int:
    return sum(
        1 for w in re.split(r'\W+', (title or '').lower())
        if len(w) >= 4 and w.isalpha()
    )


def _ontology_concept_supporting_mass(concept_row: dict) -> int:
    """Rough signal of non-title content: definitions, facts, examples, links, misconceptions."""
    score = 0
    d = concept_row.get('definition')
    if isinstance(d, dict):
        score += len(str(d.get('text', '') or '').strip())
    elif isinstance(d, str):
        score += len(d.strip())
    sm = concept_row.get('summary')
    if isinstance(sm, str):
        score += len(sm.strip())
    for f in concept_row.get('key_facts') or []:
        if isinstance(f, dict):
            score += min(120, len(str(f.get('fact', '') or '').strip()) * 2)
    for ex in concept_row.get('examples') or []:
        if isinstance(ex, dict):
            score += min(
                80,
                len(str(ex.get('text', '') or ex.get('source_quote', '') or '').strip()),
            )
    score += min(200, len(concept_row.get('relationships') or []) * 45)
    for m in concept_row.get('misconceptions') or []:
        if isinstance(m, dict):
            score += min(
                100,
                len(str(m.get('misconception', '') or '').strip())
                + len(str(m.get('correction', '') or '').strip()),
            )
    return score


def _ontology_acronym_like_title(title: str) -> bool:
    t = re.sub(r'[^A-Za-z0-9]', '', (title or '').strip())
    return 2 <= len(t) <= 8 and t.isupper()


def _ontology_concept_low_pedagogical_signal(concept_row: dict) -> bool:
    """
    True if the row has little explanatory payload beyond a bare label (metadata / fluff).
    """
    title = str(concept_row.get('concept', '') or '').strip()
    mass = _ontology_concept_supporting_mass(concept_row)
    subs = _ontology_title_substance_word_count(title)
    nt = str(concept_row.get('nodeType', '') or '').lower()

    if _ontology_acronym_like_title(title) and mass >= 12:
        return False
    if mass >= 40:
        return False
    if mass >= 22 and subs >= 2:
        return False
    if mass >= 24 and subs >= 1:
        return False
    if subs >= 3 and mass >= 12:
        return False
    # Applied / case nodes may be shorter but should still carry *some* substance
    if nt in ('side_quest', 'applied_exploration', 'review') and mass >= 18:
        return False
    return True


def _ontology_concept_should_reject(concept_row: dict) -> bool:
    """
    Filter out syllabus noise, placeholders, and concept-shaped rows with no teaching value.
    """
    title = str(concept_row.get('concept', '') or '').strip()
    if not title:
        return True
    if looks_like_non_concept_label(title):
        return True
    if not _ontology_acronym_like_title(title) and _is_fallback_noise(title):
        return True
    if _ontology_title_is_placeholder(title):
        return True
    if _ontology_title_is_course_or_syllabus_header(title):
        return True
    if _ontology_title_is_institutional_metadata(title):
        return True
    if _ontology_title_is_slide_or_page_shell(title):
        return True
    if _ONTOLOGY_READING_APPARATUS_RES.match(title.strip()):
        return True
    if _ontology_concept_low_pedagogical_signal(concept_row):
        return True
    return False


def _ontology_filter_concept_nodes(nodes):
    """Drop low-quality concepts and prune edges to removed targets; fix dangling parent ids."""
    if not nodes:
        return []
    kept = [n for n in nodes if isinstance(n, dict) and not _ontology_concept_should_reject(n)]
    allow_title = {normalize_concept_key(n.get('concept', '')) for n in kept}
    allow_id = {str(n.get('id', '')).strip() for n in kept if str(n.get('id', '')).strip()}
    out = []
    for n in kept:
        n2 = dict(n)
        rels = []
        for r in n2.get('relationships') or []:
            if not isinstance(r, dict):
                continue
            tk = normalize_concept_key(str(r.get('target_concept', '') or ''))
            if tk and tk in allow_title:
                rels.append(r)
        n2['relationships'] = _dedupe_graph_relationships(
            rels, implicit_source=n2.get('concept')
        )
        pid = n2.get('parent_concept_id')
        if pid is not None and str(pid).strip() not in allow_id:
            n2.pop('parent_concept_id', None)
        out.append(n2)
    return out


def _ontology_quality_filtered_chunk_output(out: dict):
    """Apply ontology quality filter to a chunk extraction dict; may return None if empty."""
    if not isinstance(out, dict):
        return out
    concepts = out.get('concepts')
    if isinstance(concepts, list) and concepts:
        out = dict(out)
        out['concepts'] = _ontology_filter_concept_nodes(concepts)
    cts = out.get('concepts') or []
    rnodes = out.get('resource_nodes') or []
    chains = out.get('review_chains') or []
    if not cts and not rnodes and not chains:
        return None
    return out


def _google_ai_api_key() -> str:
    return (os.getenv('GOOGLE_AI_API_KEY') or os.getenv('GEMINI_API_KEY') or '').strip()


# Default REST id when GEMINI_MODEL is unset: Gemini 3.1 Flash‑Lite (stable, cost‑efficient for many chunk calls).
# Override with GEMINI_MODEL or bulk fallback with GEMINI_FALLBACK_MODEL.
_DEFAULT_GEMINI_REST_MODEL = (os.getenv('GEMINI_FALLBACK_MODEL') or 'gemini-3.1-flash-lite').strip() or 'gemini-3.1-flash-lite'

# Studio / marketing labels and discontinued 1.x–2.x slugs → v1beta :generateContent ids
# Ref: https://ai.google.dev/gemini-api/docs/models/gemini
_GEMINI_MODEL_API_ALIASES = {
    'gemini-1.5-pro': _DEFAULT_GEMINI_REST_MODEL,
    'gemini-1.5-pro-latest': _DEFAULT_GEMINI_REST_MODEL,
    'gemini-1.5-flash': _DEFAULT_GEMINI_REST_MODEL,
    'gemini-1.5-flash-latest': _DEFAULT_GEMINI_REST_MODEL,
    'gemini-2.0-flash': _DEFAULT_GEMINI_REST_MODEL,
    'gemini-2.0-flash-lite': _DEFAULT_GEMINI_REST_MODEL,
    'gemini-pro': _DEFAULT_GEMINI_REST_MODEL,
    'gemini-pro-vision': _DEFAULT_GEMINI_REST_MODEL,
    # Gemini 3 names as shown in Google AI Studio (no API suffix)
    'gemini-3.1-pro': 'gemini-3.1-pro-preview',
    'gemini-3-pro': 'gemini-3.1-pro-preview',
    'gemini-3-pro-preview': 'gemini-3.1-pro-preview',
    'gemini-3-flash': 'gemini-3-flash-preview',
    'gemini-3.1-flash': 'gemini-3-flash-preview',
    'gemini-3-flash-lite': 'gemini-3.1-flash-lite-preview',
}
_GEMINI_MODEL_REMAP_LOGGED = set()


def _normalize_gemini_model_id(model_id: str) -> str:
    """Map legacy or UI model labels to REST ids for generativelanguage v1beta :generateContent."""
    mid = (model_id or '').strip()
    mid = mid.replace('models/', '', 1).strip()
    if not mid:
        return _DEFAULT_GEMINI_REST_MODEL
    key = mid.lower()
    mapped = _GEMINI_MODEL_API_ALIASES.get(key)
    if mapped:
        if key not in _GEMINI_MODEL_REMAP_LOGGED and mapped.lower() != key:
            _GEMINI_MODEL_REMAP_LOGGED.add(key)
            print(
                f"ℹ️ Gemini model id '{mid}' → '{mapped}' for REST API. "
                f"Set GEMINI_MODEL explicitly to silence this hint."
            )
        return mapped
    return mid


_teacher_llm_lock = threading.Lock()
# None = follow process env (LLM_PROVIDER). Set to 'gemini' | 'ollama' | 'auto' from teacher UI without restart.
_teacher_llm_provider_override = None


def _get_teacher_llm_provider_override():
    with _teacher_llm_lock:
        return _teacher_llm_provider_override


def _set_teacher_llm_provider_override(mode):
    """mode: None to clear (use env), or 'gemini'|'ollama'|'auto'."""
    global _teacher_llm_provider_override
    with _teacher_llm_lock:
        if mode is None or (
            isinstance(mode, str) and mode.strip().lower() in ('', 'inherit', 'env', 'reset', 'default', 'clear')
        ):
            _teacher_llm_provider_override = None
        else:
            _teacher_llm_provider_override = str(mode).strip().lower()


def _llm_provider_resolved() -> str:
    """
    ollama — local Ollama only (default).
    gemini — Google Generative Language API when a key is set; otherwise falls back to ollama.
    auto — gemini if GOOGLE_AI_API_KEY / GEMINI_API_KEY is set, else ollama.

    Teacher portal can override via POST /api/teacher/llm-settings (no server restart).
    """
    ovr = _get_teacher_llm_provider_override()
    if ovr in ('gemini', 'ollama', 'auto'):
        raw = ovr
    else:
        raw = (os.getenv('LLM_PROVIDER') or 'ollama').strip().lower()
    if raw == 'auto':
        return 'gemini' if _google_ai_api_key() else 'ollama'
    if raw == 'gemini':
        if not _google_ai_api_key():
            print('⚠️ LLM_PROVIDER=gemini but no GOOGLE_AI_API_KEY/GEMINI_API_KEY; using Ollama.')
            return 'ollama'
        return 'gemini'
    return 'ollama'


@app.route('/api/teacher/llm-settings', methods=['GET', 'POST'])
def teacher_llm_settings():
    """Runtime LLM routing for course generation (Gemini vs local Ollama)."""
    if request.method == 'GET':
        env_raw = (os.getenv('LLM_PROVIDER') or 'ollama').strip().lower()
        ovr = _get_teacher_llm_provider_override()
        eff = _llm_provider_resolved()
        return jsonify({
            'env_llm_provider': env_raw,
            'override': ovr,
            'effective_provider': eff,
            'has_gemini_key': bool(_google_ai_api_key()),
            'ollama_default_model': 'qwen2.5',
            'gemini_model': _normalize_gemini_model_id(
                os.getenv('GEMINI_MODEL', _DEFAULT_GEMINI_REST_MODEL) or _DEFAULT_GEMINI_REST_MODEL
            ),
        })
    try:
        data = request.get_json(silent=True) or {}
        mode = str(data.get('llm_provider') or data.get('provider') or '').strip().lower()
        if mode in ('inherit', 'env', 'reset', 'default', 'clear', ''):
            _set_teacher_llm_provider_override(None)
            return jsonify({
                'ok': True,
                'override': None,
                'effective_provider': _llm_provider_resolved(),
            })
        if mode not in ('gemini', 'ollama', 'auto'):
            return jsonify({'error': 'llm_provider must be gemini, ollama, auto, or inherit/env to clear'}), 400
        _set_teacher_llm_provider_override(mode)
        print(f"🧠 Teacher LLM override set to: {mode} (effective={_llm_provider_resolved()})")
        return jsonify({
            'ok': True,
            'override': mode,
            'effective_provider': _llm_provider_resolved(),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def call_gemini_text(
    prompt: str,
    model: str = None,
    timeout: int = 90,
    options: dict = None,
) -> str:
    """Single-turn text via Gemini REST (no extra Python deps)."""
    options = options or {}
    key = _google_ai_api_key()
    if not key:
        raise RuntimeError('Missing GOOGLE_AI_API_KEY or GEMINI_API_KEY for Gemini.')
    model_id = _normalize_gemini_model_id(model or os.getenv('GEMINI_MODEL', _DEFAULT_GEMINI_REST_MODEL) or _DEFAULT_GEMINI_REST_MODEL)
    try:
        temperature = float(options.get('temperature', 0.3))
    except (TypeError, ValueError):
        temperature = 0.3
    try:
        top_p = float(options.get('top_p', 0.95))
    except (TypeError, ValueError):
        top_p = 0.95

    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent'
    gen_cfg = {
        'temperature': min(max(temperature, 0.0), 2.0),
        'topP': min(max(top_p, 0.0), 1.0),
    }
    if options.get('response_mime_json'):
        gen_cfg['responseMimeType'] = 'application/json'
    body = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': gen_cfg,
    }
    resp = requests.post(url, params={'key': key}, json=body, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f'Gemini HTTP {resp.status_code}: {resp.text[:1200]}')
    data = resp.json()
    cands = data.get('candidates') or []
    if not cands:
        fb = data.get('promptFeedback') or data.get('error') or data
        raise RuntimeError(f'Gemini returned no candidates: {str(fb)[:800]}')
    parts = ((cands[0].get('content') or {}).get('parts')) or []
    out_chunks = []
    for p in parts:
        if isinstance(p, dict) and p.get('text'):
            out_chunks.append(str(p['text']))
    return ''.join(out_chunks).strip()


def call_llm_text(prompt: str, model: str = 'qwen2.5', timeout: int = 90, options: dict = None) -> str:
    """Route text generation to Gemini or Ollama based on LLM_PROVIDER and API keys."""
    opts = dict(options or {})
    if _llm_provider_resolved() == 'gemini':
        gem_default = _normalize_gemini_model_id(os.getenv('GEMINI_MODEL', _DEFAULT_GEMINI_REST_MODEL) or _DEFAULT_GEMINI_REST_MODEL)
        gem_model = gem_default
        if model and (model.startswith('gemini-') or model.startswith('models/')):
            gem_model = _normalize_gemini_model_id(model.replace('models/', '', 1))
        return call_gemini_text(prompt=prompt, model=gem_model, timeout=timeout, options=opts)
    opts.pop('response_mime_json', None)
    return call_ollama_text(prompt=prompt, model=model, timeout=timeout, options=opts)


def call_ollama_text(prompt: str, model: str = 'qwen2.5', timeout: int = 90, options: dict = None):
    """
    Call Ollama with endpoint compatibility:
    1) legacy /api/generate
    2) OpenAI-compatible /v1/chat/completions
    """
    options = options or {}
    base_urls = [
        os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').rstrip('/'),
        'http://ollama:11434'
    ]

    last_error = None
    for base_url in base_urls:
        try:
            resp = requests.post(
                f'{base_url}/api/generate',
                json={'model': model, 'prompt': prompt, 'stream': False, 'options': options},
                timeout=timeout
            )
            if resp.status_code == 200:
                return resp.json().get('response', '')

            # Some environments expose only the OpenAI-compatible path.
            if resp.status_code == 404:
                compat_resp = requests.post(
                    f'{base_url}/v1/chat/completions',
                    json={
                        'model': model,
                        'messages': [{'role': 'user', 'content': prompt}],
                        'temperature': options.get('temperature', 0.3),
                        'stream': False
                    },
                    timeout=timeout
                )
                if compat_resp.status_code == 200:
                    payload = compat_resp.json()
                    return (((payload.get('choices') or [{}])[0]).get('message') or {}).get('content', '')
                last_error = f"{base_url} /v1/chat/completions returned {compat_resp.status_code}"
            else:
                last_error = f"{base_url} /api/generate returned {resp.status_code}"
        except Exception as e:
            last_error = str(e)
            continue

    raise RuntimeError(f'Ollama call failed: {last_error}')

def extract_atomic_concepts_from_chunk_llm(chunk_text: str, chunk_idx: int, total_chunks: int):
    """
    Strategy-aware extraction: routing uses semantic_role from chunk header (via strategy_for_semantic_role).
    Returns dict with chunk_index, concepts (may be empty), resource_nodes (may be empty).
    """
    hctx = extract_hierarchy_context_from_chunk(chunk_text)
    chunk_kw = _read_knowledge_weight_from_hctx(hctx)
    sr_raw = hctx.get('semantic_role') or 'theory_domain'
    strat = strategy_for_semantic_role(str(sr_raw))
    try:
        if strat == 'reference_light':
            out = _extract_reference_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw)
            return _ontology_quality_filtered_chunk_output(out) if out else None
        if strat == 'case_analysis':
            out = _extract_case_analysis_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw)
            if out:
                return _ontology_quality_filtered_chunk_output(out)
            out = _legacy_items_extract_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw)
            return _ontology_quality_filtered_chunk_output(out) if out else None
        if strat == 'recap_linking':
            out = _extract_recap_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw)
            if out:
                return _ontology_quality_filtered_chunk_output(out)
            out = _legacy_items_extract_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw)
            return _ontology_quality_filtered_chunk_output(out) if out else None
        if strat == 'application_mapping':
            out = _extract_application_mapping_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw)
            if out:
                return _ontology_quality_filtered_chunk_output(out)
            out = _legacy_items_extract_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw)
            return _ontology_quality_filtered_chunk_output(out) if out else None
        if strat == 'concept_dense':
            out = _extract_concept_dense_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw)
            if out:
                return _ontology_quality_filtered_chunk_output(out)
            out = _legacy_items_extract_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw)
            return _ontology_quality_filtered_chunk_output(out) if out else None
        out = _legacy_items_extract_chunk_llm(chunk_text, chunk_idx, total_chunks, hctx, chunk_kw)
        return _ontology_quality_filtered_chunk_output(out) if out else None
    except Exception as e:
        print(f"⚠️ Chunk {chunk_idx} extraction failed: {e}")
        return None

def deterministic_merge_concepts(chunk_summaries, chunk_index_to_section_id=None):
    """
    Stage 2a deterministic merge (code, not LLM): dedupe + preserve details.
    chunk_index_to_section_id: map chunk_index -> section_id (from chunk headers).
    """
    idx_map = chunk_index_to_section_id if isinstance(chunk_index_to_section_id, dict) else {}

    def _section_for_summary(summary):
        idx = summary.get('chunk_index')
        try:
            idx = int(idx) if idx is not None else 0
        except (TypeError, ValueError):
            idx = 0
        sid = idx_map.get(idx)
        if sid is None and idx:
            sid = idx_map.get(str(idx))
        sid = str(sid or '').strip() or 'sec_root'
        return sid

    merged = {}
    for summary in chunk_summaries:
        sid_chunk = _section_for_summary(summary)
        for c in summary.get('concepts', []):
            concept = str(c.get('concept', '')).strip()
            if not concept:
                continue
            if _ontology_concept_should_reject(c):
                continue
            key = normalize_concept_key(concept)
            if key not in merged:
                merged[key] = {
                    'id': f'concept_{uuid4().hex[:10]}',
                    'concept': concept,
                    'nodeType': str(c.get('nodeType') or 'core_concept'),
                    'extraction_strategy': str(c.get('extraction_strategy') or 'concept_dense'),
                    'topic': 'General',
                    'level': 'intermediate',
                    'definition': {'text': '', 'source_quotes': []},
                    'examples': [],
                    'key_facts': [],
                    'relationships': [],
                    'misconceptions': [],
                    'knowledge_weight': float(c.get('knowledge_weight', 1.0) or 0),
                    'source_section_id': sid_chunk,
                    'source_section_ids': [sid_chunk],
                }
            item = merged[key]
            if sid_chunk:
                lst = item.setdefault('source_section_ids', [])
                if sid_chunk not in lst:
                    lst.append(sid_chunk)
            try:
                incoming_w = float(c.get('knowledge_weight', 0) or 0)
            except (TypeError, ValueError):
                incoming_w = 0.0
            item['knowledge_weight'] = max(
                float(item.get('knowledge_weight', 0) or 0),
                incoming_w,
            )
            inc_nt = str(c.get('nodeType') or 'core_concept')
            if _rank_node_type(inc_nt) > _rank_node_type(item.get('nodeType')):
                item['nodeType'] = inc_nt
                item['extraction_strategy'] = str(c.get('extraction_strategy') or item.get('extraction_strategy'))
            # Keep longer definition text
            new_def = c.get('definition', {})
            if isinstance(new_def, dict):
                new_def_text = str(new_def.get('text', '')).strip()
                if len(new_def_text) > len(item['definition'].get('text', '')):
                    item['definition']['text'] = new_def_text
                old_quotes = item['definition'].get('source_quotes', [])
                new_quotes = new_def.get('source_quotes', [])
                if not isinstance(old_quotes, list):
                    old_quotes = []
                if not isinstance(new_quotes, list):
                    new_quotes = []
                item['definition']['source_quotes'] = _dedupe_str_list(old_quotes + new_quotes)

            # Merge key facts deterministically by normalized fact text
            existing_fact_keys = set()
            for f in item.get('key_facts', []):
                existing_fact_keys.add(normalize_concept_key(str(f.get('fact', ''))))
            for f in c.get('key_facts', []):
                if not isinstance(f, dict):
                    continue
                fact_text = str(f.get('fact', '')).strip()
                fact_key = normalize_concept_key(fact_text)
                if not fact_key:
                    continue
                if fact_key in existing_fact_keys:
                    # enrich existing numbers/quotes
                    for ef in item['key_facts']:
                        if normalize_concept_key(str(ef.get('fact', ''))) == fact_key:
                            ef_nums = ef.get('numbers', [])
                            ef_quote = ef.get('source_quote', '')
                            f_nums = f.get('numbers', [])
                            if not isinstance(ef_nums, list):
                                ef_nums = []
                            if not isinstance(f_nums, list):
                                f_nums = []
                            ef['numbers'] = _dedupe_str_list(ef_nums + f_nums)
                            if len(str(f.get('source_quote', ''))) > len(str(ef_quote)):
                                ef['source_quote'] = str(f.get('source_quote', '')).strip()
                            break
                else:
                    item['key_facts'].append({
                        'fact': fact_text,
                        'numbers': _dedupe_str_list(f.get('numbers', [])),
                        'source_quote': str(f.get('source_quote', '')).strip()
                    })
                    existing_fact_keys.add(fact_key)

            # Merge examples deterministically
            existing_example_keys = set()
            for ex in item.get('examples', []):
                existing_example_keys.add(normalize_concept_key(str(ex.get('text', ''))))
            for ex in c.get('examples', []):
                if not isinstance(ex, dict):
                    continue
                ex_text = str(ex.get('text', '')).strip()
                ex_quote = str(ex.get('source_quote', '')).strip()
                ex_key = normalize_concept_key(ex_text or ex_quote)
                if not ex_key:
                    continue
                if ex_key in existing_example_keys:
                    # enrich quote if longer
                    for e0 in item['examples']:
                        if normalize_concept_key(str(e0.get('text', '') or e0.get('source_quote', ''))) == ex_key:
                            if len(ex_quote) > len(str(e0.get('source_quote', ''))):
                                e0['source_quote'] = ex_quote
                            break
                else:
                    item['examples'].append({'text': ex_text, 'source_quote': ex_quote})
                    existing_example_keys.add(ex_key)

            # Misconceptions (theory chunks)
            seen_m = {normalize_concept_key(str(x.get('misconception', ''))) for x in item.get('misconceptions', []) if isinstance(x, dict)}
            for m in c.get('misconceptions', []) or []:
                if not isinstance(m, dict):
                    continue
                mk = normalize_concept_key(str(m.get('misconception', '')))
                if not mk or mk in seen_m:
                    continue
                seen_m.add(mk)
                item.setdefault('misconceptions', []).append({
                    'misconception': str(m.get('misconception', '')).strip(),
                    'correction': str(m.get('correction', '')).strip(),
                    'source_quote': str(m.get('source_quote', '')).strip(),
                })

            # Pedagogical / prerequisite edges from chunk extraction
            er = c.get('relationships', [])
            if isinstance(er, list) and er:
                item['relationships'] = _dedupe_graph_relationships(
                    (item.get('relationships') or []) + er,
                    implicit_source=item.get('concept'),
                )
    return list(merged.values())


class _OntologyUnionFind:
    __slots__ = ('parent',)

    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def _ontology_title_jaccard(title_a: str, title_b: str) -> float:
    sa = {t for t in normalize_concept_key(title_a or '').split() if len(t) > 2}
    sb = {t for t in normalize_concept_key(title_b or '').split() if len(t) > 2}
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _dedupe_key_facts_list(kfs):
    seen = set()
    out = []
    for f in kfs or []:
        if not isinstance(f, dict):
            continue
        fk = normalize_concept_key(str(f.get('fact', '')))
        if fk and fk not in seen:
            seen.add(fk)
            out.append(f)
    return out


def _dedupe_examples_list(exs):
    seen = set()
    out = []
    for ex in exs or []:
        if not isinstance(ex, dict):
            continue
        ek = normalize_concept_key(str(ex.get('text', '') or ex.get('source_quote', '')))
        if ek and ek not in seen:
            seen.add(ek)
            out.append(ex)
    return out


def _collapse_concept_member_group(members, canonical):
    """Merge a duplicate group onto canonical row (deterministic)."""
    out = dict(canonical)
    sids = []
    for m in members:
        for s in (m.get('source_section_ids') or []):
            if isinstance(s, str) and s.strip() and s.strip() not in sids:
                sids.append(s.strip())
        sx = m.get('source_section_id')
        if isinstance(sx, str) and sx.strip() and sx.strip() not in sids:
            sids.append(sx.strip())
    all_kf, all_ex, all_rel = [], [], []
    all_mis = []
    def_texts = []
    summaries = []
    kw_union = []
    titles = []
    max_kw = 0.0
    best_nt = str(out.get('nodeType') or 'core_concept')
    for m in members:
        all_kf.extend(m.get('key_facts') or [])
        all_ex.extend(m.get('examples') or [])
        all_rel.extend(m.get('relationships') or [])
        all_mis.extend(m.get('misconceptions') or [])
        dt = (m.get('definition') or {})
        if isinstance(dt, dict):
            tx = str(dt.get('text', '')).strip()
            if tx:
                def_texts.append(tx)
        elif isinstance(dt, str) and dt.strip():
            def_texts.append(dt.strip())
        sm = m.get('summary')
        if isinstance(sm, str) and sm.strip():
            summaries.append(sm.strip())
        kws = m.get('keywords')
        if isinstance(kws, list):
            for k in kws:
                ks = str(k).strip()
                if ks:
                    kw_union.append(ks)
        t = str(m.get('concept', '')).strip()
        if t:
            titles.append(t)
        try:
            max_kw = max(max_kw, float(m.get('knowledge_weight', 0) or 0))
        except (TypeError, ValueError):
            pass
        nt = str(m.get('nodeType') or 'core_concept')
        if _rank_node_type(nt) > _rank_node_type(best_nt):
            best_nt = nt
    out['nodeType'] = best_nt
    out['knowledge_weight'] = max(
        float(out.get('knowledge_weight', 0) or 0),
        max_kw,
    )
    out['key_facts'] = _dedupe_key_facts_list(all_kf)
    out['examples'] = _dedupe_examples_list(all_ex)
    out['relationships'] = _dedupe_graph_relationships(all_rel, implicit_source=out.get('concept'))
    out['source_section_ids'] = sids
    out['source_section_id'] = sids[0] if sids else out.get('source_section_id')

    for t in titles:
        if t and t.lower() != str(out.get('concept', '')).strip().lower():
            kw_union.append(t)
    out['keywords'] = _dedupe_str_list(kw_union)

    merged_def = _merge_unique_definition_blocks(def_texts)
    if not isinstance(out.get('definition'), dict):
        out['definition'] = {'text': '', 'source_quotes': []}
    if merged_def:
        out['definition']['text'] = merged_def
    all_quotes = []
    for m in members:
        dq = (m.get('definition') or {}).get('source_quotes', [])
        if isinstance(dq, list):
            all_quotes.extend(dq)
    if all_quotes:
        out['definition']['source_quotes'] = _dedupe_str_list(
            [str(q).strip() for q in all_quotes if str(q).strip()]
        )

    if summaries:
        merged_sum = ' '.join(_dedupe_str_list(summaries))
        out['summary'] = merged_sum

    seen_m = set()
    mis_out = []
    for x in all_mis:
        if not isinstance(x, dict):
            continue
        mk = normalize_concept_key(str(x.get('misconception', '')))
        if mk and mk not in seen_m:
            seen_m.add(mk)
            mis_out.append(x)
    if mis_out:
        out['misconceptions'] = mis_out

    return out


def _ontology_stage_canonicalize_duplicates(concepts):
    """Stage A: collapse near-duplicate titles (lexical fingerprint, overlap, n-grams, optional embeddings)."""
    concepts = [c for c in (concepts or []) if str(c.get('concept', '')).strip()]
    n = len(concepts)
    if n < 2:
        return concepts
    titles = [str(c.get('concept', '')).strip() for c in concepts]
    fps = [_ontology_title_fingerprint(t) for t in titles]
    emb_mat = _ontology_openai_embeddings_matrix(titles)
    if emb_mat:
        print('🧬 Ontology dedup: using embedding similarity (OPENAI_API_KEY)')

    uf = _OntologyUnionFind()
    for i in range(n):
        uf.parent.setdefault(f'i{i}', f'i{i}')

    for i in range(n):
        for j in range(i + 1, n):
            fpa, fpb = fps[i], fps[j]
            ta, tb = titles[i], titles[j]
            if fpa == fpb:
                uf.union(f'i{i}', f'i{j}')
                continue
            ka, kb = normalize_concept_key(ta), normalize_concept_key(tb)
            if ka and kb and ka == kb:
                uf.union(f'i{i}', f'i{j}')
                continue
            if ka and kb and (ka in kb or kb in ka) and min(len(ka), len(kb)) >= 5:
                uf.union(f'i{i}', f'i{j}')
                continue
            sa, sb = _ontology_fp_token_sets(fpa), _ontology_fp_token_sets(fpb)
            jacc_fp, ovl_fp = _ontology_token_overlap_metrics(sa, sb)
            if jacc_fp >= 0.58 or ovl_fp >= 0.86:
                uf.union(f'i{i}', f'i{j}')
                continue
            if _ontology_title_jaccard(ta, tb) >= 0.62:
                uf.union(f'i{i}', f'i{j}')
                continue
            if fpa and fpb:
                if (fpa in fpb or fpb in fpa) and min(len(fpa), len(fpb)) >= 12:
                    uf.union(f'i{i}', f'i{j}')
                    continue
                ng = _ontology_char_ngram_cosine(fpa, fpb)
                if ng >= 0.88 and max(jacc_fp, ovl_fp) >= 0.25:
                    uf.union(f'i{i}', f'i{j}')
                    continue
            if emb_mat:
                if emb_mat[i][j] >= 0.86 and max(jacc_fp, ovl_fp) >= 0.2:
                    uf.union(f'i{i}', f'i{j}')

    buckets = {}
    for i in range(n):
        r = uf.find(f'i{i}')
        buckets.setdefault(r, []).append(concepts[i])

    alias = {}
    out = []
    for _root, mem in buckets.items():
        if not mem:
            continue
        canon = min(mem, key=_ontology_canonical_member_key)
        merged = _collapse_concept_member_group(mem, canon)
        ck = normalize_concept_key(merged.get('concept', ''))
        for m in mem:
            mk = normalize_concept_key(m.get('concept', ''))
            if mk:
                alias[mk] = merged.get('concept')
        out.append(merged)

    for c in out:
        rels = []
        src_k = normalize_concept_key(c.get('concept', ''))
        for r in c.get('relationships') or []:
            if not isinstance(r, dict):
                continue
            rr = dict(r)
            tk = normalize_concept_key(str(rr.get('target_concept', '')))
            if tk in alias:
                rr['target_concept'] = alias[tk]
            if normalize_concept_key(str(rr.get('target_concept', ''))) == src_k:
                continue
            rels.append(rr)
        c['relationships'] = _dedupe_graph_relationships(rels, implicit_source=c.get('concept'))
    return out


def _ontology_assign_primary_source_section(concepts, section_order):
    order_rank = {sid: i for i, sid in enumerate(section_order)}
    fallback = section_order[0] if section_order else 'sec_root'
    for c in concepts:
        ids = list(c.get('source_section_ids') or [])
        ps = c.get('source_section_id')
        if isinstance(ps, str) and ps.strip() and ps.strip() not in ids:
            ids.insert(0, ps.strip())
        ids = [x for x in ids if isinstance(x, str) and x.strip()]
        if not ids:
            c['source_section_id'] = fallback
            c['source_section_ids'] = [fallback]
            continue
        best = min(ids, key=lambda x: order_rank.get(x, 9999))
        c['source_section_id'] = best
        c['source_section_ids'] = _dedupe_str_list(ids)


def _parent_tree_would_cycle(by_id: dict, child_id: str, parent_id: str) -> bool:
    """True if assigning parent_id as parent of child_id would create a parent pointer cycle."""
    if not child_id or not parent_id or child_id == parent_id:
        return True
    cur, seen = parent_id, set()
    for _ in range(len(by_id) + 4):
        if not cur:
            return False
        if cur == child_id:
            return True
        if cur in seen:
            return True
        seen.add(cur)
        node = by_id.get(cur)
        if not node:
            return False
        cur = str(node.get('parent_concept_id') or '').strip()
    return True


def _prune_mutual_prerequisites_on_concepts(concepts):
    """
    Anti-symmetric rule for prerequisite: forbid A→B and B→A simultaneously (graph contradiction).
    Keeps the first prerequisite direction encountered in stable concept/relationship order.
    """
    if not concepts:
        return
    ordered_edges = []
    for c in concepts:
        sk = normalize_concept_key(str(c.get('concept', '')))
        for r in (c.get('relationships') or []):
            if not isinstance(r, dict):
                continue
            if _map_raw_rel_to_pedagogical(str(r.get('type', ''))) != 'prerequisite':
                continue
            tk = normalize_concept_key(str(r.get('target_concept', '')).strip())
            if sk and tk and sk != tk:
                ordered_edges.append((sk, tk))
    first_kept = {}
    for sk, tk in ordered_edges:
        a, b = tuple(sorted((sk, tk)))
        if (a, b) not in first_kept:
            first_kept[(a, b)] = (sk, tk)
    all_dir = set(ordered_edges)
    drop_pairs = set()
    for sk, tk in ordered_edges:
        a, b = tuple(sorted((sk, tk)))
        if (tk, sk) in all_dir and (sk, tk) in all_dir:
            if first_kept.get((a, b)) != (sk, tk):
                drop_pairs.add((sk, tk))
    for c in concepts:
        sk = normalize_concept_key(str(c.get('concept', '')))
        rels = c.get('relationships')
        if not isinstance(rels, list) or not rels:
            continue
        new_rels = []
        for r in rels:
            if not isinstance(r, dict):
                new_rels.append(r)
                continue
            if _map_raw_rel_to_pedagogical(str(r.get('type', ''))) != 'prerequisite':
                new_rels.append(r)
                continue
            tk = normalize_concept_key(str(r.get('target_concept', '')).strip())
            if (sk, tk) in drop_pairs:
                continue
            new_rels.append(r)
        c['relationships'] = _dedupe_graph_relationships(new_rels, implicit_source=c.get('concept'))


def _ontology_stage_parent_from_prerequisites(concepts):
    """Fill parent_concept_id from a single primary prerequisite target when still unset."""
    if not concepts:
        return
    by_id = {str(c.get('id', '')).strip(): c for c in concepts if str(c.get('id', '')).strip()}
    key_to_id = {}
    for c in concepts:
        ck = normalize_concept_key(str(c.get('concept', '')))
        cid = str(c.get('id', '')).strip()
        if ck and cid:
            key_to_id[ck] = cid
    for c in concepts:
        if c.get('parent_concept_id'):
            continue
        cid = str(c.get('id', '')).strip()
        if not cid:
            continue
        cands = []
        sk = normalize_concept_key(str(c.get('concept', '')))
        for r in (c.get('relationships') or []):
            if not isinstance(r, dict):
                continue
            if _map_raw_rel_to_pedagogical(str(r.get('type', ''))) != 'prerequisite':
                continue
            tk = normalize_concept_key(str(r.get('target_concept', '')).strip())
            tid = key_to_id.get(tk)
            if not tid or tid == cid or tid not in by_id:
                continue
            tw = float(by_id[tid].get('knowledge_weight', 0) or 0)
            cands.append((tw, tid, tk))
        if not cands:
            continue
        cands.sort(key=lambda x: (-x[0], x[1]))
        for tw, tid, tk in cands:
            if sk == tk:
                continue
            par = by_id.get(tid)
            if par and not _semantic_hierarchy_allows_parent_child(par, c):
                continue
            if not _parent_tree_would_cycle(by_id, cid, tid):
                c['parent_concept_id'] = tid
                break


def _ontology_stage_fallback_parent_chain_by_section(concepts):
    """Last-resort tree edges: within each source_section_id, chain by level then name (no new cycles)."""
    if not concepts:
        return
    by_id = {str(c.get('id', '')).strip(): c for c in concepts if str(c.get('id', '')).strip()}
    level_rank = {'beginner': 0, 'intermediate': 1, 'advanced': 2}
    from collections import defaultdict

    sec_map = defaultdict(list)
    for c in concepts:
        sid = str(c.get('source_section_id', 'sec_root')).strip() or 'sec_root'
        sec_map[sid].append(c)
    for sid, group in sec_map.items():
        group.sort(
            key=lambda c: (
                level_rank.get(str(c.get('level', 'intermediate')).strip().lower(), 1),
                len(normalize_concept_key(str(c.get('concept', '')))),
                str(c.get('concept', '')).lower(),
            )
        )
        for i in range(1, len(group)):
            child = group[i]
            if child.get('parent_concept_id'):
                continue
            prev = group[i - 1]
            cid = str(child.get('id', '')).strip()
            pid = str(prev.get('id', '')).strip()
            if not cid or not pid or cid == pid:
                continue
            if not _parent_tree_would_cycle(by_id, cid, pid):
                if _semantic_hierarchy_allows_parent_child(prev, child):
                    child['parent_concept_id'] = pid


def _ontology_stage_semantic_hierarchy_enforce(concepts):
    """
    Strip parent edges that violate semantic ontology rules (Rules 1–3).
    Rule 4: non-theory_domain roots prefer a theory_domain parent in the same section when legal.
    """
    if not concepts:
        return
    from collections import defaultdict

    by_id = {str(c.get('id', '')).strip(): c for c in concepts if str(c.get('id', '')).strip()}
    for c in concepts:
        pid = str(c.get('parent_concept_id') or '').strip()
        if not pid:
            continue
        p = by_id.get(pid)
        if not p or not _semantic_hierarchy_allows_parent_child(p, c):
            c.pop('parent_concept_id', None)

    sec_map = defaultdict(list)
    for c in concepts:
        sid = str(c.get('source_section_id', 'sec_root')).strip() or 'sec_root'
        sec_map[sid].append(c)
    for _sid, group in sec_map.items():
        theory_anchors = [x for x in group if _concept_effective_semantic_role(x) == 'theory_domain']
        theory_anchors.sort(
            key=lambda x: (
                -float(x.get('knowledge_weight', 0) or 0),
                str(x.get('concept', '')).lower(),
            )
        )
        for c in group:
            if c.get('parent_concept_id'):
                continue
            if _concept_effective_semantic_role(c) == 'theory_domain':
                continue
            cid = str(c.get('id', '')).strip()
            if not cid:
                continue
            for t in theory_anchors:
                if t is c:
                    continue
                tid = str(t.get('id', '')).strip()
                if not tid:
                    continue
                if not _semantic_hierarchy_allows_parent_child(t, c):
                    continue
                if not _parent_tree_would_cycle(by_id, cid, tid):
                    c['parent_concept_id'] = tid
                    break


def _ontology_stage_infer_hierarchy(concepts):
    """
    Stage B: build a learning-tree parent for map progression (not a semantic web).
    Uses topic labels as umbrellas when a concept title matches the classified topic,
    plus token containment / substring / definition mentions within section & topic scope.
    """
    if not concepts:
        return
    by_id = {str(c.get('id', '')).strip(): c for c in concepts if str(c.get('id', '')).strip()}
    for c in concepts:
        c.pop('parent_concept_id', None)

    def nk(c):
        return normalize_concept_key(str(c.get('concept', ''))) if c else ''

    def bucket(key_fn):
        out = {}
        for c in concepts:
            out.setdefault(key_fn(c), []).append(c)
        return out

    g_topic_sec = bucket(
        lambda c: (
            str(c.get('topic', 'General')).strip() or 'General',
            str(c.get('source_section_id', 'sec_root')).strip() or 'sec_root',
        )
    )
    g_topic = bucket(lambda c: str(c.get('topic', 'General')).strip() or 'General')
    g_sec = bucket(lambda c: str(c.get('source_section_id', 'sec_root')).strip() or 'sec_root')

    def topic_hub_concept(topic, pool):
        tkn = normalize_concept_key(topic)
        gen = normalize_concept_key('General')
        if not tkn or tkn == gen:
            return None
        for c in pool:
            if nk(c) == tkn:
                return c
        return None

    def score_parent_edge(child, parent):
        if child is parent:
            return 0
        ck, pk = nk(child), nk(parent)
        pt = str(parent.get('concept', '')).strip()
        ct = str(child.get('concept', '')).strip()
        if not ck or not pk or pk == ck:
            return 0
        p_tokens = {t for t in pk.split() if len(t) > 2}
        c_tokens = {t for t in ck.split() if len(t) > 2}
        def_blob = str((child.get('definition') or {}).get('text', '')).lower()
        top = str(child.get('topic', 'General')).strip()
        tkn = normalize_concept_key(top)
        gen = normalize_concept_key('General')

        if len(pk) > len(ck) + 2 and pk not in ck and ck not in pk:
            if not (tkn and tkn != gen and pk == tkn):
                return 0

        s = 0
        if tkn and tkn != gen and pk == tkn:
            s = 5000 + len(pk)
        elif p_tokens and p_tokens <= c_tokens:
            if len(p_tokens) >= 2 or (len(p_tokens) == 1 and max(len(t) for t in p_tokens) >= 5):
                s = 3000 + len(pk)
        elif len(pk) >= 3 and pk != ck and pk in ck:
            s = 2000 + len(pk)
        elif len(pt) >= 5 and pt.lower() in def_blob and len(def_blob) >= max(48, len(pt) * 3):
            s = 500 + len(pk)
        return s

    def best_parent(child, pools):
        cid = str(child.get('id', '')).strip()
        best_p, best_s = None, 0
        for pool in pools:
            for p in pool:
                if not _semantic_hierarchy_allows_parent_child(p, child):
                    continue
                sc = score_parent_edge(child, p)
                if sc > best_s:
                    best_p, best_s = p, sc
            if best_s >= 4500:
                break
        if not best_p:
            return None
        if not _semantic_hierarchy_allows_parent_child(best_p, child):
            return None
        pid = str(best_p.get('id', '')).strip()
        if not pid or _parent_tree_would_cycle(by_id, cid, pid):
            return None
        return best_p

    ordered = sorted(concepts, key=lambda c: len(nk(c)), reverse=True)
    for child in ordered:
        cid = str(child.get('id', '')).strip()
        if not cid:
            continue
        t = str(child.get('topic', 'General')).strip() or 'General'
        s = str(child.get('source_section_id', 'sec_root')).strip() or 'sec_root'
        pool_ts = g_topic_sec.get((t, s), concepts)
        pool_t = g_topic.get(t, concepts)
        pool_sec = g_sec.get(s, concepts)
        hub = topic_hub_concept(t, pool_ts) or topic_hub_concept(t, pool_t)

        par = best_parent(child, [pool_ts, pool_t, pool_sec])
        if par is None and hub is not None and hub is not child:
            hid = str(hub.get('id', '')).strip()
            if (
                hid
                and not _parent_tree_would_cycle(by_id, cid, hid)
                and _semantic_hierarchy_allows_parent_child(hub, child)
            ):
                par = hub
        if par is None or par is child:
            continue
        pid = str(par.get('id', '')).strip()
        if (
            pid
            and not _parent_tree_would_cycle(by_id, cid, pid)
            and _semantic_hierarchy_allows_parent_child(par, child)
        ):
            child['parent_concept_id'] = pid


_EXTENDS_LEX = re.compile(r'\b(builds on|builds upon|extends|generalizes|based on)\b', re.I)
# Learning graph (narrow): no generic semantic-web edges.
_ALLOWED_PED_RELATIONS = frozenset({
    'prerequisite', 'example_of', 'extends', 'application_of',
})
_ALLOWED_GRAPH_RELATIONS = _ALLOWED_PED_RELATIONS


def _map_raw_rel_to_pedagogical(raw: str) -> str:
    t = (raw or 'other').strip().lower().replace('-', '_').replace(' ', '_')
    mp = {
        'depends-on': 'prerequisite',
        'depends_on': 'prerequisite',
        'prerequisite': 'prerequisite',
        'prerequisites': 'prerequisite',
        'prereq': 'prerequisite',
        'requires': 'prerequisite',
        'required': 'prerequisite',
        'needs': 'prerequisite',
        'causes': '',
        'part-of': '',
        'part_of': '',
        'is-a': '',
        'is_a': '',
        'uses': '',
        'use': '',
        'relies_on': '',
        'related': '',
        'related_to': '',
        'other': '',
        'contrasts': '',
        'contrast': '',
        'contrasts_with': '',
        'explains': 'extends',
        'reinforces': 'extends',
        'reinforce': 'extends',
        'example': 'example_of',
        'instance': 'example_of',
        'example_of': 'example_of',
        'illustrates': 'example_of',
        'case': 'example_of',
        'extends': 'extends',
        'generalizes': 'extends',
        'application': 'application_of',
        'application_of': 'application_of',
        'applies': 'application_of',
        'applied': 'application_of',
        'instantiates': 'application_of',
        'prerequisite_reminder': 'prerequisite',
    }
    out = mp.get(t)
    if out in _ALLOWED_PED_RELATIONS:
        return out
    if 'contrast' in t:
        return ''
    if t in ('',):
        return ''
    return ''


def _ontology_stage_pedagogical_relationships(concepts):
    """Stage C: normalize to learning-graph edges only; drop unmapped / weak types."""
    by_key = {normalize_concept_key(c.get('concept')): c for c in concepts if c.get('concept')}
    for c in concepts:
        ck = normalize_concept_key(c.get('concept'))
        ct = str(c.get('concept', ''))
        def_txt = str((c.get('definition') or {}).get('text', ''))
        def_low = def_txt.lower()
        node_type = str(c.get('nodeType', 'core_concept'))
        topic = str(c.get('topic', 'General'))
        built = []
        seen = set()

        def add_edge(tgt_title, rel_type, ev):
            if not tgt_title or rel_type not in _ALLOWED_PED_RELATIONS:
                return
            ttk = normalize_concept_key(tgt_title)
            if not ttk or ttk == ck or ttk not in by_key:
                return
            canon_tgt = str(by_key[ttk].get('concept', '')).strip()
            sig = (ck, ttk, rel_type)
            if sig in seen:
                return
            seen.add(sig)
            built.append({
                'type': rel_type,
                'target_concept': canon_tgt,
                'evidence_quote': (ev or '')[:400],
            })

        for r in (c.get('relationships') or []):
            if not isinstance(r, dict):
                continue
            raw_type = str(r.get('type', 'other'))
            mapped = _map_raw_rel_to_pedagogical(raw_type)
            if not mapped:
                continue
            tgt = str(r.get('target_concept', '')).strip()
            ev = str(r.get('evidence_quote', r.get('evidence', ''))).strip()
            add_edge(tgt, mapped, ev or 'extraction')

        if node_type in ('side_quest', 'review', 'library'):
            for other in concepts:
                if other is c:
                    continue
                if str(other.get('nodeType', '')) == 'core_concept' and str(other.get('topic', '')) == topic:
                    add_edge(str(other.get('concept', '')), 'example_of', 'case_or_review_anchor')
                    break
        elif node_type == 'applied_exploration':
            for other in concepts:
                if other is c:
                    continue
                if str(other.get('nodeType', '')) == 'core_concept' and str(other.get('topic', '')) == topic:
                    add_edge(str(other.get('concept', '')), 'application_of', 'applied_to_theory_same_topic')
                    break

        if _EXTENDS_LEX.search(def_txt):
            for other in concepts:
                if other is c:
                    continue
                if str(other.get('topic', '')) != topic:
                    continue
                ot = str(other.get('concept', ''))
                if len(ot) < 5:
                    continue
                if ot.lower() not in def_low:
                    continue
                if _ontology_title_jaccard(ct, ot) < 0.38:
                    continue
                add_edge(ot, 'extends', 'lexical_cue')

        c['relationships'] = _dedupe_graph_relationships(built, implicit_source=c.get('concept'))


def _learning_biome_for_semantic_role(semantic_role: str) -> str:
    sr = _sanitize_ontology_token(str(semantic_role or '')) or 'theory_domain'
    return {
        'theory_domain': 'foundations_plateau',
        'application_domain': 'application_territory',
        'case_study': 'field_site',
        'recap_reinforcement': 'recap_grove',
        'reference_material': 'archive_basin',
        'general': 'neutral_meadow',
    }.get(sr, 'neutral_meadow')


def _section_token_overlap(concept_title: str, concept_summary: str, section_title: str) -> float:
    blob = f"{concept_title} {concept_summary}".lower()
    words = {w for w in re.split(r'\W+', normalize_concept_key(section_title)) if len(w) > 2}
    if not words:
        return 0.0
    hits = sum(1 for w in words if w in blob)
    return hits / len(words)


def _export_graph_relation_type(raw: str) -> str:
    """Map internal relationship labels to graph export vocabulary (learning graph only)."""
    t = _map_raw_rel_to_pedagogical(raw)
    if t in _ALLOWED_PED_RELATIONS:
        return t
    return ''


def _prune_bidirectional_prerequisite_edges(graph_edges):
    """
    Exported graph: drop reverse prerequisite so A→B and B→A cannot both exist.
    First prerequisite edge per unordered pair wins (stable list order).
    """
    if not graph_edges:
        return graph_edges
    prereq = []
    other = []
    for e in graph_edges:
        if not isinstance(e, dict):
            continue
        if str(e.get('relation', '')).strip() == 'prerequisite':
            prereq.append(e)
        else:
            other.append(e)
    first_dir = {}
    kept = []
    for e in prereq:
        a = str(e.get('source_concept_id', '')).strip()
        b = str(e.get('target_concept_id', '')).strip()
        if not a or not b or a == b:
            continue
        key = tuple(sorted((a, b)))
        if key not in first_dir:
            first_dir[key] = (a, b)
            kept.append(e)
            continue
        ka, kb = first_dir[key]
        if (a, b) == (ka, kb):
            continue
        if (a, b) == (kb, ka):
            continue
    return other + kept


def refine_ontology_deterministic(
    concepts,
    sections_normalized=None,
    *,
    run_stage_a=True,
    run_stage_bcd=True,
):
    """
    Deterministic ontology refinement after chunk merge + (optional) LLM classification/edges.
    Set run_stage_a before topic/LLM classification; run_stage_bcd after relationship inference.
    """
    sections_normalized = sections_normalized or []
    section_order = []
    for s in sections_normalized:
        if isinstance(s, dict):
            sid = str(s.get('section_id') or '').strip()
            if sid:
                section_order.append(sid)
    if not section_order:
        section_order = ['sec_root']

    if not concepts:
        return concepts
    concepts = _ontology_filter_concept_nodes(
        [c for c in concepts if isinstance(c, dict)]
    )
    if not concepts:
        return concepts
    n0 = len(concepts)
    if run_stage_a:
        concepts = _ontology_stage_canonicalize_duplicates(concepts)
    if run_stage_bcd:
        _ontology_assign_primary_source_section(concepts, section_order)
        _ontology_stage_infer_hierarchy(concepts)
        _ontology_stage_pedagogical_relationships(concepts)
        _prune_mutual_prerequisites_on_concepts(concepts)
        _ontology_stage_parent_from_prerequisites(concepts)
        _ontology_stage_fallback_parent_chain_by_section(concepts)
        _ontology_stage_semantic_hierarchy_enforce(concepts)
        _ontology_assign_primary_source_section(concepts, section_order)
        concepts = _ontology_filter_concept_nodes(concepts)
        n_par = sum(1 for c in concepts if c.get('parent_concept_id'))
        print(f"🌲 Learning tree: {n_par}/{len(concepts)} concept(s) with parent_concept_id")
    if run_stage_a and run_stage_bcd:
        n1 = len(concepts)
        print(f"🧬 Ontology refine (full): {n0} → {n1} concept(s); sections={len(section_order)}")
    elif run_stage_bcd:
        print(f"🧬 Ontology refine (post-LLM): hierarchy + pedagogical edges; concepts={len(concepts)}")
    return concepts


def deterministic_merge_resource_nodes(chunk_summaries):
    """Merge bibliography-style resources (reference_light); not part of main concept graph."""
    merged = {}
    for summary in chunk_summaries:
        for r in summary.get('resource_nodes', []) or []:
            if not isinstance(r, dict):
                continue
            title = str(r.get('title', '')).strip()
            cit = str(r.get('citation_or_url', '')).strip()
            if not title and not cit:
                continue
            k = normalize_concept_key(f'{title}|{cit}')
            if k not in merged:
                merged[k] = {
                    'id': f'res_{uuid4().hex[:10]}',
                    'nodeType': 'library',
                    'title': title or cit,
                    'citation_or_url': cit,
                    'source_quote': str(r.get('source_quote', '')).strip(),
                    'knowledge_weight': float(r.get('knowledge_weight', 0) or 0),
                    'extraction_strategy': str(r.get('extraction_strategy') or 'reference_light'),
                }
            else:
                ex = merged[k]
                nq = str(r.get('source_quote', '')).strip()
                if len(nq) > len(ex.get('source_quote', '')):
                    ex['source_quote'] = nq
                try:
                    ex['knowledge_weight'] = max(
                        float(ex.get('knowledge_weight', 0) or 0),
                        float(r.get('knowledge_weight', 0) or 0),
                    )
                except (TypeError, ValueError):
                    pass
    return list(merged.values())


def _merge_review_chains(chunk_summaries):
    seen = set()
    out = []
    for s in chunk_summaries:
        for ch in s.get('review_chains', []) or []:
            if not isinstance(ch, list) or len(ch) < 2:
                continue
            tup = tuple(normalize_concept_key(str(x)) for x in ch if str(x).strip())
            if len(tup) < 2 or tup in seen:
                continue
            seen.add(tup)
            out.append([str(x).strip() for x in ch if str(x).strip()])
    return out

def classify_topics_levels_with_llm(concepts, file_name):
    """
    Stage 2b LLM only for topic/level classification (no merging).
    """
    if not concepts:
        return {'subject': 'General Course', 'difficulty': 'medium', 'category': 'General', 'labels': []}
    brief = []
    for c in concepts[:300]:
        brief.append({
            'concept': c.get('concept', ''),
            'definition': c.get('definition', {}).get('text', '')
        })
    prompt = f"""
Classify concepts by topic and level.
Do not rewrite definitions. Do not merge.

Return JSON only:
{{
  "subject": "course subject",
  "difficulty": "easy|medium|hard",
  "category": "short category",
  "labels": [
    {{"concept": "exact concept name", "topic": "topic label", "level": "beginner|intermediate|advanced"}}
  ]
}}

FILE: {file_name}
CONCEPTS:
{json.dumps(brief, ensure_ascii=False)}
"""
    try:
        llm_text = call_llm_text(
            prompt=prompt, model='qwen2.5', timeout=90, options={'response_mime_json': True}
        )
        parsed = extract_first_json_object(llm_text)
        if not parsed:
            return {'subject': 'General Course', 'difficulty': 'medium', 'category': 'General', 'labels': []}
        labels = parsed.get('labels', [])
        if not isinstance(labels, list):
            labels = []
        return {
            'subject': parsed.get('subject', 'General Course'),
            'difficulty': parsed.get('difficulty', 'medium'),
            'category': parsed.get('category', 'General'),
            'labels': labels
        }
    except Exception:
        return {'subject': 'General Course', 'difficulty': 'medium', 'category': 'General', 'labels': []}

def infer_relationships_with_llm(concepts):
    """
    Stage 3 LLM for relationships among core theory nodes only (excludes side_quest/review/library).
    """
    if not concepts:
        return []
    core = [
        c for c in concepts
        if str(c.get('nodeType', 'core_concept')).strip() == 'core_concept'
    ]
    if not core:
        return []
    brief = []
    for c in core[:220]:
        brief.append({
            'concept': c.get('concept', ''),
            'definition': c.get('definition', {}).get('text', '')
        })
    prompt = f"""
Build relationships between CORE THEORY concepts only.
Use ONLY relationships supported by the definitions below; do not invent cross-document facts.
No classification, no rewriting definitions.

Return JSON only:
{{
  "relationships": [
    {{"source_concept": "A", "type": "prerequisite|example_of|extends|application_of", "target_concept": "B", "evidence": "short phrase from definitions only"}}
  ]
}}

Rules:
- prerequisite: A requires understanding B first (cite overlapping terms in definitions).
- example_of: A is a concrete instance of abstract B.
- extends: A builds on or generalizes B in the same topic.
- application_of: A applies theory B in a domain (same topic preferred).
- Omit edges you cannot justify from the text; do not guess.

CONCEPTS:
{json.dumps(brief, ensure_ascii=False)}
"""
    try:
        llm_text = call_llm_text(
            prompt=prompt, model='qwen2.5', timeout=90, options={'response_mime_json': True}
        )
        parsed = extract_first_json_object(llm_text)
        if not parsed:
            return []
        rels = parsed.get('relationships', [])
        return rels if isinstance(rels, list) else []
    except Exception:
        return []

def build_topics_from_concepts(concepts):
    topics_map = {}
    for c in concepts:
        topic = str(c.get('topic', 'General')).strip() or 'General'
        level = str(c.get('level', 'intermediate')).strip().lower()
        if level not in ['beginner', 'intermediate', 'advanced']:
            level = 'intermediate'
        if topic not in topics_map:
            topics_map[topic] = {'beginner': [], 'intermediate': [], 'advanced': []}
        topics_map[topic][level].append(c.get('concept', ''))
    topics = []
    for topic, levels in topics_map.items():
        topics.append({
            'topic': topic,
            'levels': {
                'beginner': _dedupe_str_list(levels.get('beginner', [])),
                'intermediate': _dedupe_str_list(levels.get('intermediate', [])),
                'advanced': _dedupe_str_list(levels.get('advanced', []))
            }
        })
    return topics

def build_structured_materials(concepts, max_items: int = 200):
    materials = []
    for c in concepts[:max_items]:
        materials.append({
            'id': c.get('id'),
            'concept': c.get('concept'),
            'nodeType': str(c.get('nodeType', 'core_concept')),
            'topic': c.get('topic', 'General'),
            'level': c.get('level', 'intermediate'),
            'definition': c.get('definition', {}).get('text', ''),
            'facts': c.get('key_facts', [])
        })
    return materials

def _infer_course_code(subject: str, file_name: str) -> str:
    candidates = [subject or '', file_name or '']
    for text in candidates:
        m = re.search(r'([A-Za-z]{4}\d{4})', text or '')
        if m:
            return m.group(1).upper()
    cleaned = re.sub(r'[^A-Za-z0-9]+', '_', (subject or 'course').strip()).strip('_')
    return cleaned.upper() or 'COURSE'

def _normalize_graph_relation_type(raw: str) -> str:
    """Normalize legacy relation strings to the learning-graph vocabulary."""
    k = (raw or '').strip().lower().replace(' ', '_').replace('-', '_')
    legacy = _map_raw_rel_to_pedagogical(k)
    if legacy in _ALLOWED_PED_RELATIONS:
        return legacy
    if k in ('depends_on', 'depends-on', 'prerequisite', 'prerequisites'):
        return 'prerequisite'
    if k in ('example', 'example_of', 'illustrates'):
        return 'example_of'
    if k in ('extends', 'explains', 'reinforces', 'generalizes'):
        return 'extends'
    if k in ('application', 'application_of', 'applies', 'applied', 'uses', 'part_of', 'part-of', 'is_a', 'is-a'):
        return 'application_of'
    return ''


def _semantic_role_from_merged_concept(c: dict) -> str:
    strat = str(c.get('extraction_strategy') or 'concept_dense').strip().lower()
    return STRATEGY_TO_SEMANTIC_ROLE.get(strat, 'theory_domain')


def _concept_effective_semantic_role(c: dict) -> str:
    """Pedagogical semantic_role for ontology rules (explicit field wins, else strategy/nodeType)."""
    r = c.get('semantic_role')
    if isinstance(r, str) and r.strip():
        t = _sanitize_ontology_token(r.strip())
        if t:
            return t
    strat = str(c.get('extraction_strategy') or '').strip().lower()
    if strat in STRATEGY_TO_SEMANTIC_ROLE:
        return STRATEGY_TO_SEMANTIC_ROLE[strat]
    nt = str(c.get('nodeType') or 'core_concept').strip().lower()
    return {
        'core_concept': 'theory_domain',
        'applied_exploration': 'application_domain',
        'side_quest': 'case_study',
        'review': 'recap_reinforcement',
        'library': 'reference_material',
    }.get(nt, 'theory_domain')


def _semantic_hierarchy_allows_parent_child(parent_c: dict, child_c: dict) -> bool:
    """
    Ontology legality for learning-tree ownership (parent owns child in map progression).
    Rule 1: case_study cannot own theory_domain.
    Rule 2: application_domain cannot own theory_domain.
    Rule 3: theory_domain may own theory_domain, case_study, application_domain (plus recap/reference for slides).
    """
    pr = _concept_effective_semantic_role(parent_c)
    cr = _concept_effective_semantic_role(child_c)
    if pr == 'case_study' and cr == 'theory_domain':
        return False
    if pr == 'application_domain' and cr == 'theory_domain':
        return False
    if pr == 'theory_domain':
        return cr in (
            'theory_domain',
            'case_study',
            'application_domain',
            'recap_reinforcement',
            'reference_material',
            'general',
        )
    return True


def _importance_float_from_merged_concept(c: dict) -> float:
    try:
        kw = float(c.get('knowledge_weight', 1.0) or 0)
    except (TypeError, ValueError):
        kw = 1.0
    lv = str(c.get('level', 'intermediate')).lower()
    bump = 0.0
    if lv == 'advanced':
        bump = 0.1
    elif lv == 'beginner':
        bump = -0.05
    return max(0.0, min(1.0, (kw / 2.0) + bump))


def _build_curriculum_sections_payload(sections, subject: str, max_page: int):
    """Curriculum-only sections: hierarchy + pedagogy + page span; no gameplay fields."""
    try:
        mp = max(1, int(max_page))
    except (TypeError, ValueError):
        mp = 1
    subj = (subject or 'Course').strip() or 'Course'
    if not sections:
        return [{
            'section_id': 'sec_root',
            'title': subj,
            'type': 'MAIN_SECTION',
            'semantic_role': 'theory_domain',
            'parent_section_id': None,
            'page_start': 1,
            'page_end': mp,
        }]
    parsed_rows = []
    for i, sec in enumerate(sections):
        if not isinstance(sec, dict):
            continue
        sid_explicit = str(sec.get('section_id') or '').strip()
        sid = sid_explicit or f'sec_{i + 1:04d}'
        title = str(sec.get('title', '') or '').strip() or f'Section {i + 1}'
        try:
            ps = int(sec.get('page_start', 1))
            pe = int(sec.get('page_end', ps))
        except (TypeError, ValueError):
            ps, pe = 1, mp
        ps = max(1, min(ps, mp))
        pe = max(ps, min(pe, mp))
        typ = str(sec.get('type', 'MAIN_SECTION') or 'MAIN_SECTION').strip().upper()
        if typ not in SECTION_TYPES:
            typ = 'MAIN_SECTION'
        sr = _sanitize_ontology_token(str(sec.get('semantic_role') or '')) or 'theory_domain'
        parsed_rows.append((sid, title[:500], typ, sr, ps, pe, sec))

    title_to_id = {}
    for sid, title, _typ, _sr, _ps, _pe, _sec in parsed_rows:
        if title not in title_to_id:
            title_to_id[title] = sid

    out = []
    for sid, title, typ, sr, ps, pe, sec in parsed_rows:
        parent = sec.get('parent')
        parent_sid = None
        if parent is not None:
            pt = str(parent).strip()
            if pt:
                parent_sid = title_to_id.get(pt)
        out.append({
            'section_id': sid,
            'title': title,
            'type': typ,
            'semantic_role': sr,
            'parent_section_id': parent_sid,
            'page_start': ps,
            'page_end': pe,
        })
    if not out:
        return _build_curriculum_sections_payload(None, subj, mp)
    return out


def build_layered_course_document(subject, file_name, concepts, topics, sections=None, max_page=None):
    """
    Canonical persisted course shape (v2): curriculum + concept graph + clusters.
    Map positions, NPCs, quizzes, and tasks are not stored here — derive at runtime if needed.
    """
    course_code = _infer_course_code(subject, file_name)
    try:
        mp = max(1, int(max_page or 1))
    except (TypeError, ValueError):
        mp = 1

    curriculum_sections = _build_curriculum_sections_payload(sections, subject, mp)
    concepts = concepts or []
    valid_concept_ids = {str(c.get('id', '')).strip() for c in concepts if str(c.get('id', '')).strip()}
    topic_to_concepts = {}
    for c in concepts:
        topic = str(c.get('topic', 'General')).strip() or 'General'
        topic_to_concepts.setdefault(topic, []).append(c)

    level_rank = {'beginner': 1, 'intermediate': 2, 'advanced': 3}
    concept_id_map = {}
    graph_concepts = []

    for topic in sorted(topic_to_concepts.keys(), key=lambda x: x.lower()):
        concept_list = sorted(
            topic_to_concepts[topic],
            key=lambda c: (
                level_rank.get(str(c.get('level', 'intermediate')).lower(), 2),
                str(c.get('concept', '')).lower(),
            ),
        )
        for c in concept_list:
            title = str(c.get('concept', '')).strip()
            if not title:
                continue
            key = normalize_concept_key(title)
            cid = str(c.get('id', '')).strip() or f'concept_{uuid4().hex[:10]}'
            concept_id_map[key] = cid
            definition = str((c.get('definition') or {}).get('text', '')).strip()
            facts = c.get('key_facts', []) if isinstance(c.get('key_facts'), list) else []
            keywords = _dedupe_str_list(
                [title] + [str(f.get('fact', '')).strip() for f in facts if isinstance(f, dict)]
            )
            ek = c.get('keywords', [])
            if isinstance(ek, list):
                keywords = _dedupe_str_list(
                    keywords + [str(x).strip() for x in ek if str(x).strip()]
                )
            keywords = keywords[:24]

            src_sec = str(c.get('source_section_id') or '').strip() or 'sec_root'
            raw_pid = c.get('parent_concept_id')
            pid_out = None
            if raw_pid is not None:
                ps = str(raw_pid).strip()
                if ps in valid_concept_ids:
                    pid_out = ps

            graph_concepts.append({
                'concept_id': cid,
                'title': title,
                'summary': (definition[:500] + '...') if len(definition) > 500 else definition,
                'keywords': keywords,
                'importance': round(_importance_float_from_merged_concept(c), 4),
                'semantic_role': _semantic_role_from_merged_concept(c),
                'source_section_id': src_sec,
                'parent_concept_id': pid_out,
            })

    graph_relationships = []
    seen_edges = set()
    for c in concepts:
        src_key = normalize_concept_key(c.get('concept', ''))
        src_id = concept_id_map.get(src_key)
        if not src_id:
            continue
        rels = c.get('relationships', [])
        if not isinstance(rels, list):
            continue
        for r in rels:
            if not isinstance(r, dict):
                continue
            target = str(r.get('target_concept', '')).strip()
            tgt_id = concept_id_map.get(normalize_concept_key(target))
            if not tgt_id or tgt_id == src_id:
                continue
            relation = _export_graph_relation_type(str(r.get('type', '')))
            if not relation:
                continue
            key = (src_id, tgt_id, relation)
            if key in seen_edges:
                continue
            seen_edges.add(key)
            graph_relationships.append({
                'source_concept_id': src_id,
                'target_concept_id': tgt_id,
                'relation': relation,
            })

    graph_relationships = _prune_bidirectional_prerequisite_edges(graph_relationships)

    known_section_ids = {str(s.get('section_id') or '').strip() for s in curriculum_sections if str(s.get('section_id') or '').strip()}
    sid_to_cids = {}
    for gc in graph_concepts:
        sid = str(gc.get('source_section_id') or 'sec_root').strip() or 'sec_root'
        sid_to_cids.setdefault(sid, []).append(gc['concept_id'])

    clusters = []
    for ord_i, cs in enumerate(curriculum_sections):
        sid = str(cs.get('section_id') or f'sec_{ord_i + 1:04d}').strip()
        role = str(cs.get('semantic_role') or 'theory_domain')
        cids = _dedupe_str_list(sid_to_cids.get(sid, []))
        clusters.append({
            'cluster_id': f'cl_{sid}',
            'title': str(cs.get('title') or 'Learning region')[:240],
            'section_id': sid,
            'biome': _learning_biome_for_semantic_role(role),
            'learning_order': ord_i,
            'concept_ids': cids,
        })

    stray_ids = []
    for sid, cids in sid_to_cids.items():
        if sid not in known_section_ids:
            stray_ids.extend(cids)
    stray_ids = _dedupe_str_list(stray_ids)

    assigned = {x for cl in clusters for x in cl['concept_ids']}
    orphans = [gc['concept_id'] for gc in graph_concepts if gc['concept_id'] not in assigned]
    orphans = _dedupe_str_list(orphans + stray_ids)
    if orphans and clusters:
        for oid in orphans:
            gc = next((g for g in graph_concepts if g['concept_id'] == oid), None)
            if not gc:
                continue
            best_idx = 0
            best_sc = -1.0
            for ci, cl in enumerate(clusters):
                sc = _section_token_overlap(gc['title'], gc.get('summary', ''), cl['title'])
                if sc > best_sc:
                    best_sc = sc
                    best_idx = ci
            if best_sc > 0.08:
                clusters[best_idx]['concept_ids'].append(oid)
            else:
                clusters[0]['concept_ids'].append(oid)
        for cl in clusters:
            cl['concept_ids'] = _dedupe_str_list(cl['concept_ids'])

    clusters = [cl for cl in clusters if cl.get('concept_ids')]
    for i, cl in enumerate(clusters):
        cl['learning_order'] = i
    if not clusters and graph_concepts:
        sec0 = curriculum_sections[0] if curriculum_sections and isinstance(curriculum_sections[0], dict) else {}
        root_sid = str(sec0.get('section_id') or 'sec_root').strip() or 'sec_root'
        root_title = str(sec0.get('title') or subject or 'Course').strip() or 'Course'
        role0 = str(sec0.get('semantic_role') or 'theory_domain')
        clusters = [{
            'cluster_id': f'cl_{root_sid}',
            'title': root_title[:240],
            'section_id': root_sid,
            'biome': _learning_biome_for_semantic_role(role0),
            'learning_order': 0,
            'concept_ids': _dedupe_str_list([gc['concept_id'] for gc in graph_concepts]),
        }]

    return {
        'schema_version': 2,
        'course': course_code,
        'curriculum': {'sections': curriculum_sections},
        'graph': {
            'concepts': graph_concepts,
            'relationships': graph_relationships,
            'clusters': clusters,
        },
    }


def build_course_path_json(subject, file_name, concepts, topics, sections=None, max_page=None):
    """Backward-compatible name: returns layered v2 document (not legacy areas JSON)."""
    return build_layered_course_document(
        subject, file_name, concepts, topics, sections=sections, max_page=max_page
    )


def build_course_path_schema_template():
    """Schema template for teacher-side agent output contract (layered v2)."""
    return {
        'schema_version': 2,
        'course': 'INFO4444',
        'curriculum': {
            'sections': [
                {
                    'section_id': 'sec_0001',
                    'title': 'Week 1 — Foundations',
                    'type': 'MAIN_SECTION',
                    'semantic_role': 'theory_domain',
                    'parent_section_id': None,
                    'page_start': 1,
                    'page_end': 12,
                }
            ]
        },
        'graph': {
            'concepts': [
                {
                    'concept_id': 'concept_ab12cd34ef',
                    'title': 'Dominant design',
                    'summary': 'Short plain-language summary.',
                    'keywords': ['standard', 'adoption'],
                    'importance': 0.72,
                    'semantic_role': 'theory_domain',
                    'source_section_id': 'sec_0001',
                    'parent_concept_id': None,
                }
            ],
            'relationships': [
                {
                    'source_concept_id': 'concept_ab12cd34ef',
                    'target_concept_id': 'concept_other01',
                    'relation': 'prerequisite',
                }
            ],
            'clusters': [
                {
                    'cluster_id': 'cl_sec_0001',
                    'title': 'AI strategy',
                    'section_id': 'sec_0001',
                    'biome': 'foundations_plateau',
                    'learning_order': 0,
                    'concept_ids': ['concept_ab12cd34ef'],
                }
            ],
        },
    }


def build_teacher_course_path_prompt(subject, file_name):
    course_code = _infer_course_code(subject, file_name)
    return (
        "You are a teacher-side curriculum architect.\n"
        "Generate JSON only (no markdown, no explanation) for the layered course model (v2).\n"
        "Hard constraints:\n"
        "1) Root: schema_version=2, course (short code), curriculum, graph.\n"
        "2) curriculum.sections[]: section_id, title, type (MAIN_SECTION|SUBSECTION), semantic_role, "
        "parent_section_id (nullable), page_start, page_end.\n"
        "3) graph.concepts[]: concept_id, title, summary, keywords[], importance in [0,1], "
        "semantic_role, source_section_id (required), parent_concept_id (optional).\n"
        "4) graph.relationships[]: source_concept_id, target_concept_id, relation "
        "(prerequisite|example_of|extends|application_of).\n"
        "5) graph.clusters[]: cluster_id, title, section_id, biome, learning_order, concept_ids[] "
        "(curriculum-aligned learning regions).\n"
        "6) Do not include nodeType, quiz, npc, tasks, or map positions in the JSON.\n"
        f"Target course code: {course_code}\n"
    )


def validate_legacy_course_path_json(course_path):
    """Validate legacy v1 payload: course -> areas -> concept_nodes (RPG-heavy)."""
    errors = []
    if not isinstance(course_path, dict):
        return False, ['course_path must be an object']
    if not isinstance(course_path.get('course'), str) or not course_path.get('course', '').strip():
        errors.append('course must be a non-empty string')
    areas = course_path.get('areas')
    if not isinstance(areas, list):
        errors.append('areas must be an array')
        return False, errors

    concept_ids = set()
    prereq_refs = []
    for ai, area in enumerate(areas):
        if not isinstance(area, dict):
            errors.append(f'areas[{ai}] must be an object')
            continue
        for key in ['id', 'name', 'description']:
            if not isinstance(area.get(key), str) or not area.get(key, '').strip():
                errors.append(f'areas[{ai}].{key} must be a non-empty string')
        if not isinstance(area.get('difficulty'), int):
            errors.append(f'areas[{ai}].difficulty must be integer')
        pos = area.get('position')
        if not isinstance(pos, dict) or not isinstance(pos.get('x'), int) or not isinstance(pos.get('y'), int):
            errors.append(f'areas[{ai}].position must be {{x:int,y:int}}')
        nodes = area.get('concept_nodes')
        if not isinstance(nodes, list):
            errors.append(f'areas[{ai}].concept_nodes must be an array')
            continue
        for ci, node in enumerate(nodes):
            if not isinstance(node, dict):
                errors.append(f'areas[{ai}].concept_nodes[{ci}] must be an object')
                continue
            cid = str(node.get('concept_id', '')).strip()
            if not cid:
                errors.append(f'areas[{ai}].concept_nodes[{ci}].concept_id must be non-empty')
            else:
                concept_ids.add(cid)
            for key in ['title', 'summary']:
                if not isinstance(node.get(key), str):
                    errors.append(f'areas[{ai}].concept_nodes[{ci}].{key} must be string')
            if not isinstance(node.get('importance'), int):
                errors.append(f'areas[{ai}].concept_nodes[{ci}].importance must be integer')
            if not isinstance(node.get('prerequisites'), list):
                errors.append(f'areas[{ai}].concept_nodes[{ci}].prerequisites must be array')
            else:
                for pid in node.get('prerequisites', []):
                    if isinstance(pid, str) and pid.strip():
                        prereq_refs.append(pid.strip())
            for key in ['keywords', 'quiz', 'tasks']:
                if not isinstance(node.get(key), list):
                    errors.append(f'areas[{ai}].concept_nodes[{ci}].{key} must be array')
            if not isinstance(node.get('npc'), dict):
                errors.append(f'areas[{ai}].concept_nodes[{ci}].npc must be object')

    for pid in prereq_refs:
        if pid not in concept_ids:
            errors.append(f'prerequisite reference not found: {pid}')

    return len(errors) == 0, errors


def validate_course_path_json(course_path):
    """Dispatch: layered v2 or legacy v1."""
    if isinstance(course_path, dict) and course_path.get('schema_version') == 2:
        return validate_layered_course_document(course_path)
    return validate_legacy_course_path_json(course_path)


def validate_layered_course_document(doc):
    errors = []
    if not isinstance(doc, dict):
        return False, ['document must be an object']
    if doc.get('schema_version') != 2:
        errors.append('schema_version must be 2')
    if not isinstance(doc.get('course'), str) or not doc.get('course', '').strip():
        errors.append('course must be a non-empty string')
    curr = doc.get('curriculum')
    if not isinstance(curr, dict) or not isinstance(curr.get('sections'), list):
        errors.append('curriculum.sections must be an array')
        return False, errors
    for si, sec in enumerate(curr.get('sections', [])):
        if not isinstance(sec, dict):
            errors.append(f'curriculum.sections[{si}] must be an object')
            continue
        for key in ('section_id', 'title', 'type', 'semantic_role'):
            if not isinstance(sec.get(key), str) or not str(sec.get(key, '')).strip():
                errors.append(f'curriculum.sections[{si}].{key} must be a non-empty string')
        ps, pe = sec.get('page_start'), sec.get('page_end')
        if not isinstance(ps, int) or not isinstance(pe, int):
            errors.append(f'curriculum.sections[{si}].page_start/page_end must be integers')
        elif ps < 1 or pe < ps:
            errors.append(f'curriculum.sections[{si}] has invalid page span')
        pid = sec.get('parent_section_id')
        if pid is not None and (not isinstance(pid, str) or not pid.strip()):
            errors.append(f'curriculum.sections[{si}].parent_section_id must be string or null')

    g = doc.get('graph')
    if not isinstance(g, dict):
        errors.append('graph must be an object')
        return False, errors
    concepts = g.get('concepts')
    rels = g.get('relationships')
    clusters = g.get('clusters')
    if not isinstance(concepts, list):
        errors.append('graph.concepts must be an array')
    if not isinstance(rels, list):
        errors.append('graph.relationships must be an array')
    if not isinstance(clusters, list):
        errors.append('graph.clusters must be an array')
    if not isinstance(concepts, list) or not isinstance(rels, list) or not isinstance(clusters, list):
        return False, errors

    concept_ids = set()
    for ci, c in enumerate(concepts):
        if not isinstance(c, dict):
            errors.append(f'graph.concepts[{ci}] must be an object')
            continue
        cid = str(c.get('concept_id', '')).strip()
        if not cid:
            errors.append(f'graph.concepts[{ci}].concept_id must be non-empty')
        else:
            concept_ids.add(cid)
        if not isinstance(c.get('title'), str) or not c.get('title', '').strip():
            errors.append(f'graph.concepts[{ci}].title must be a non-empty string')
        if not isinstance(c.get('summary'), str):
            errors.append(f'graph.concepts[{ci}].summary must be a string')
        if not isinstance(c.get('keywords'), list):
            errors.append(f'graph.concepts[{ci}].keywords must be an array')
        imp = c.get('importance')
        if not isinstance(imp, (int, float)) or imp < 0 or imp > 1:
            errors.append(f'graph.concepts[{ci}].importance must be a number in [0,1]')
        if not isinstance(c.get('semantic_role'), str) or not c.get('semantic_role', '').strip():
            errors.append(f'graph.concepts[{ci}].semantic_role must be a non-empty string')
        ssid = c.get('source_section_id')
        if not isinstance(ssid, str) or not str(ssid).strip():
            errors.append(f'graph.concepts[{ci}].source_section_id must be a non-empty string')
        pid = c.get('parent_concept_id')
        if pid is not None and (not isinstance(pid, str) or not str(pid).strip()):
            errors.append(f'graph.concepts[{ci}].parent_concept_id must be string or null')

    for ri, r in enumerate(rels):
        if not isinstance(r, dict):
            errors.append(f'graph.relationships[{ri}] must be an object')
            continue
        for key in ('source_concept_id', 'target_concept_id', 'relation'):
            if not isinstance(r.get(key), str) or not r.get(key, '').strip():
                errors.append(f'graph.relationships[{ri}].{key} must be a non-empty string')
        rel = str(r.get('relation', '')).strip()
        if rel and rel not in _ALLOWED_GRAPH_RELATIONS:
            errors.append(f'graph.relationships[{ri}].relation invalid: {rel}')

    for ki, cl in enumerate(clusters):
        if not isinstance(cl, dict):
            errors.append(f'graph.clusters[{ki}] must be an object')
            continue
        if not isinstance(cl.get('cluster_id'), str) or not cl.get('cluster_id', '').strip():
            errors.append(f'graph.clusters[{ki}].cluster_id must be a non-empty string')
        if not isinstance(cl.get('title'), str) or not cl.get('title', '').strip():
            errors.append(f'graph.clusters[{ki}].title must be a non-empty string')
        cids = cl.get('concept_ids')
        if not isinstance(cids, list):
            errors.append(f'graph.clusters[{ki}].concept_ids must be an array')
            continue
        for x in cids:
            if not isinstance(x, str) or not x.strip():
                errors.append(f'graph.clusters[{ki}].concept_ids must be non-empty strings')
        if 'section_id' in cl and cl.get('section_id') is not None:
            if not isinstance(cl.get('section_id'), str) or not str(cl.get('section_id')).strip():
                errors.append(f'graph.clusters[{ki}].section_id must be a non-empty string when set')
        if 'biome' in cl and cl.get('biome') is not None and not isinstance(cl.get('biome'), str):
            errors.append(f'graph.clusters[{ki}].biome must be a string when set')
        if 'learning_order' in cl and cl.get('learning_order') is not None:
            if not isinstance(cl.get('learning_order'), int):
                errors.append(f'graph.clusters[{ki}].learning_order must be an integer when set')

    for ci, c in enumerate(concepts):
        if not isinstance(c, dict):
            continue
        pid = c.get('parent_concept_id')
        if pid is None:
            continue
        ps = str(pid).strip()
        if ps and ps not in concept_ids:
            errors.append(f'graph.concepts[{ci}].parent_concept_id references unknown concept_id: {ps}')

    for r in rels:
        if not isinstance(r, dict):
            continue
        for end in ('source_concept_id', 'target_concept_id'):
            cid = r.get(end)
            if cid and cid not in concept_ids:
                errors.append(f'relationship references unknown concept_id: {cid}')
    for cl in clusters:
        if not isinstance(cl, dict):
            continue
        for cid in cl.get('concept_ids', []) or []:
            if isinstance(cid, str) and cid and cid not in concept_ids:
                errors.append(f'cluster references unknown concept_id: {cid}')

    return len(errors) == 0, errors


def ensure_valid_course_path(candidate, subject, file_name, concepts, topics, sections=None, max_page=None):
    fallback = build_layered_course_document(
        subject, file_name, concepts, topics, sections=sections, max_page=max_page
    )
    if isinstance(candidate, dict) and candidate.get('schema_version') == 2:
        ok, errs = validate_layered_course_document(candidate)
        if ok:
            return candidate, []
        return fallback, errs
    return fallback, ['replaced non-v2 or invalid course_path with generated layered document']

# Use LLM to analyze PDF content and generate course
def generate_course_from_text(
    text_content, file_name, progress_callback=None, pdf_pages=None, course_sections=None
):
    """Use LLM to analyze PDF content and generate detailed course knowledge points"""
    thinking_trace = []
    pdf_pages = normalize_pdf_pages_payload(pdf_pages)
    max_page = 1
    if pdf_pages:
        max_page = max(int(p.get('page', 1)) for p in pdf_pages)
    sections_resolved = None
    if pdf_pages is not None and course_sections is not None:
        sections_resolved = normalize_course_sections_payload(course_sections, max_page)

    def emit_progress(progress, stage, detail=None):
        if progress_callback:
            try:
                progress_callback(progress, stage, detail)
            except Exception:
                pass
    
    print(f"\n{'='*60}")
    print(f"🔍 Starting file content analysis")
    print(f"📄 File name: {file_name}")
    print(f"📏 Total characters: {len(text_content)}")
    if pdf_pages:
        print(f"📑 PDF page records: {len(pdf_pages)}")
    if sections_resolved:
        print(f"📚 Course sections (teacher): {len(sections_resolved)} section(s)")
    print(f"📝 Content preview:\n{text_content[:300]}")
    print(f"{'='*60}\n")
    emit_progress(5, "Preparing content", "Initialized extraction pipeline.")
    
    # Check if it's structured TXT format (supports English markers)
    if (
        ('# Course Meta Information' in text_content and '# Course Content' in text_content)
    ):
        emit_progress(15, "Parsing structured content", "Detected structured TXT format.")
        thinking_trace.append("Detected structured course text format; using deterministic parser.")
        print("✨ Detected structured TXT format, using dedicated parser...")
        metadata, materials_titles = parse_structured_txt(text_content)
        
        if metadata and materials_titles:
            print(f"✅ Parsing successful!")
            print(f"   - Course name: {metadata.get('subject', 'Not specified')}")
            print(f"   - Category: {metadata.get('category', 'Not specified')}")
            print(f"   - Difficulty: {metadata.get('difficulty', 'medium')}")
            print(f"   - Number of knowledge points: {len(materials_titles)}")
            
            # Extract detailed content
            detailed_materials = []
            lines = text_content.split('\n')
            current_point = None
            current_content = []
            
            for line in lines:
                line_stripped = line.strip()
                
                # Detect knowledge point title
                if line_stripped.startswith('### '):
                    # Save previous knowledge point
                    if current_point and current_content:
                        detail = ' '.join(current_content).strip()
                        if len(detail) > 20:
                            detailed_materials.append(f"{current_point}: {detail}")
                        else:
                            detailed_materials.append(current_point)
                    
                    # Start new knowledge point
                    current_point = line_stripped[4:].strip()
                    current_content = []
                
                # Collect knowledge point content
                elif current_point and line_stripped and not line_stripped.startswith('#'):
                    current_content.append(line_stripped)
            
            # Save last knowledge point
            if current_point and current_content:
                detail = ' '.join(current_content).strip()
                if len(detail) > 20:
                    detailed_materials.append(f"{current_point}: {detail}")
                else:
                    detailed_materials.append(current_point)
            
            print(f"\n📚 Number of detailed knowledge points extracted: {len(detailed_materials)}")
            structured_concepts = []
            for title in (detailed_materials if detailed_materials else materials_titles):
                concept_name = title.split(':', 1)[0].strip()
                definition_text = title.split(':', 1)[1].strip() if ':' in title else ''
                if concept_name:
                    lv_raw = str(metadata.get('difficulty', 'medium')).strip().lower()
                    lv_map = {'easy': 'beginner', 'medium': 'intermediate', 'hard': 'advanced'}
                    structured_concepts.append({
                        'id': f'concept_{uuid4().hex[:10]}',
                        'concept': concept_name,
                        'nodeType': 'core_concept',
                        'extraction_strategy': 'concept_dense',
                        'knowledge_weight': 1.0,
                        'topic': metadata.get('category', 'General'),
                        'level': lv_map.get(lv_raw, 'intermediate'),
                        'definition': {
                            'text': definition_text,
                            'source_quotes': [definition_text] if definition_text else []
                        },
                        'examples': [],
                        'key_facts': [],
                        'relationships': []
                    })
            
            structured_concepts = refine_ontology_deterministic(structured_concepts, sections_resolved)
            structured_topics = build_topics_from_concepts(structured_concepts)
            course_path_candidate = build_course_path_json(
                metadata.get('subject', 'General Course'),
                file_name,
                structured_concepts,
                structured_topics,
                sections=sections_resolved,
                max_page=max_page,
            )
            course_path, course_path_errors = ensure_valid_course_path(
                course_path_candidate,
                metadata.get('subject', 'General Course'),
                file_name,
                structured_concepts,
                structured_topics,
                sections=sections_resolved,
                max_page=max_page,
            )
            if course_path_errors:
                thinking_trace.append(
                    f"Course path validation fallback applied ({len(course_path_errors)} issues fixed)."
                )

            return {
                'subject': metadata.get('subject', 'General Course'),
                'materials': build_structured_materials(structured_concepts, max_items=200),
                'difficulty': metadata.get('difficulty', 'medium'),
                'category': metadata.get('category', 'General'),
                'topics': structured_topics,
                'knowledge_structure': {
                    'pipeline': ['chunk', 'concept_extraction', 'merge', 'structuring', 'ontology_refine_v1'],
                    'concept_index': structured_concepts,
                    'topics': structured_topics,
                    'graph': course_path.get('graph'),
                    'curriculum': course_path.get('curriculum'),
                },
                'course_path': course_path,
                'course_path_agent': {
                    'prompt_template': build_teacher_course_path_prompt(metadata.get('subject', 'General Course'), file_name),
                    'schema': build_course_path_schema_template(),
                    'validation_errors': course_path_errors
                },
                'thinking_trace': thinking_trace
            }
    
    print("📋 Using chunked LLM extraction flow...")
    emit_progress(20, "Chunking content", "Splitting content into model-friendly chunks.")
    thinking_trace.append("Starting chunk-based extraction flow for local model.")
    try:
        if sections_resolved and pdf_pages:
            chunks = build_llm_chunks_from_course_sections(
                sections_resolved, pdf_pages, max_chars=1000, overlap_chars=120
            )
            thinking_trace.append(
                f"Section-level chunking: {len(sections_resolved)} section(s) → {len(chunks)} LLM chunk(s)."
            )
            emit_progress(
                30,
                "Chunking content",
                f"Sections: {len(chunks)} chunk(s) from {len(sections_resolved)} section(s).",
            )
            print(f"🧩 Section-level: {len(sections_resolved)} sections → {len(chunks)} LLM chunks")
            if not chunks:
                thinking_trace.append("Section assembly produced no text; falling back to page-level chunking.")
                chunks = build_llm_chunks_from_pdf_pages(pdf_pages, max_chars=1000, overlap_chars=120)
                thinking_trace.append(
                    f"PDF page-level chunking: {len(pdf_pages)} source page(s) → {len(chunks)} LLM chunk(s)."
                )
                emit_progress(30, "Chunking content", f"Page-level fallback: {len(chunks)} chunk(s).")
        elif pdf_pages:
            chunks = build_llm_chunks_from_pdf_pages(pdf_pages, max_chars=1000, overlap_chars=120)
            thinking_trace.append(
                f"PDF page-level chunking: {len(pdf_pages)} source page(s) → {len(chunks)} LLM chunk(s)."
            )
            emit_progress(30, "Chunking content", f"Page-level: {len(chunks)} chunk(s) from {len(pdf_pages)} page(s).")
            print(f"🧩 Page-level: {len(pdf_pages)} PDF pages → {len(chunks)} LLM chunks")
            if not chunks:
                thinking_trace.append("No text left after page cleanup; falling back to full-text chunking.")
                chunks = split_text_into_chunks(text_content, max_chars=1000, overlap_chars=120)
                thinking_trace.append(f"Fallback split material into {len(chunks)} chunks.")
                emit_progress(30, "Chunking content", f"Fallback: {len(chunks)} text chunk(s).")
                print(f"🧩 Fallback: {len(chunks)} chunks from full text")
        else:
            chunks = split_text_into_chunks(text_content, max_chars=1000, overlap_chars=120)
            thinking_trace.append(f"Split material into {len(chunks)} chunks.")
            emit_progress(30, "Chunking content", f"Generated {len(chunks)} chunks.")
            print(f"🧩 Generated {len(chunks)} chunks for local model understanding")

        if not chunks:
            print("⚠️ No chunks generated, falling back")
            return generate_course_fallback(text_content, file_name)

        chunk_idx_to_sid = build_chunk_index_to_section_id(chunks)

        total_chunks = max(len(chunks), 1)
        try:
            _raw_workers = int(os.getenv('CHUNK_EXTRACT_MAX_WORKERS', '4'))
        except ValueError:
            _raw_workers = 4
        max_workers = min(max(1, _raw_workers), len(chunks))
        if max_workers > 1:
            print(f"🧵 Chunk extraction parallel workers: {max_workers} (set CHUNK_EXTRACT_MAX_WORKERS to change)")

        emit_progress(
            30,
            "Extracting concepts",
            f"Starting extraction ({max_workers} worker{'s' if max_workers != 1 else ''}, {total_chunks} chunks).",
        )

        results_by_idx = {}
        progress_lock = threading.Lock()
        completed = 0

        def run_chunk_extract(idx, chunk):
            print(f"🔍 Summarizing chunk {idx}/{total_chunks} (chars={len(chunk)})")
            return idx, extract_atomic_concepts_from_chunk_llm(chunk, idx, total_chunks)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(run_chunk_extract, idx, chunk): idx
                for idx, chunk in enumerate(chunks, start=1)
            }
            for fut in as_completed(future_to_idx):
                idx = future_to_idx[fut]
                try:
                    res_idx, summary = fut.result()
                except Exception as e:
                    print(f"⚠️ Chunk {idx} extraction worker error: {e}")
                    res_idx, summary = idx, None
                with progress_lock:
                    results_by_idx[res_idx] = summary
                    completed += 1
                    emit_progress(
                        30 + int(completed / total_chunks * 50),
                        "Extracting concepts",
                        f"Completed {completed}/{total_chunks} chunks.",
                    )
                if summary and (summary.get('concepts') or summary.get('resource_nodes')):
                    n_c = len(summary.get('concepts') or [])
                    n_r = len(summary.get('resource_nodes') or [])
                    print(f"✅ Chunk {res_idx}: concepts={n_c}, resources={n_r}")
                else:
                    print(f"⚠️ Chunk {res_idx}: no valid extraction")

        chunk_summaries = []
        for idx in range(1, total_chunks + 1):
            summary = results_by_idx.get(idx)
            thinking_trace.append(f"Analyzing chunk {idx}/{total_chunks}.")
            if summary and (summary.get('concepts') or summary.get('resource_nodes')):
                chunk_summaries.append(summary)
                nc = len(summary.get('concepts') or [])
                nr = len(summary.get('resource_nodes') or [])
                thinking_trace.append(
                    f"Chunk {idx}: extracted {nc} concept node(s), {nr} resource(s)."
                )
            else:
                thinking_trace.append(f"Chunk {idx}: no stable extraction, skipped.")

        if not chunk_summaries:
            print("⚠️ No chunk summaries extracted, falling back")
            return generate_course_fallback(text_content, file_name)

        print(f"🧠 Merging {len(chunk_summaries)} chunk summaries (deterministic)...")
        emit_progress(82, "Merging concepts", "Deterministic merge and deduplication.")
        thinking_trace.append("Merged chunk outputs with deterministic deduplication (code-based).")

        merged_concepts = deterministic_merge_concepts(chunk_summaries, chunk_idx_to_sid)
        merged_resources = deterministic_merge_resource_nodes(chunk_summaries)
        review_chains_merged = _merge_review_chains(chunk_summaries)
        if merged_concepts:
            thinking_trace.append(f"Deterministic merge retained {len(merged_concepts)} unique concept nodes.")
        if merged_resources:
            thinking_trace.append(f"Resource merge retained {len(merged_resources)} bibliography item(s).")
        if review_chains_merged:
            thinking_trace.append(f"Collected {len(review_chains_merged)} recap chain(s).")

        if not merged_concepts and not merged_resources:
            print("⚠️ No concepts or resources after merge, falling back")
            return generate_course_fallback(text_content, file_name)

        if not merged_concepts and chunk_summaries:
            print(
                "⚠️ No concept nodes after merge despite chunk summaries "
                "(e.g. Gemini markdown / JSON drift or resources-only extraction). "
                "Using heuristic extraction fallback instead of an empty graph."
            )
            return generate_course_fallback(text_content, file_name)

        cls = {'subject': 'General Course', 'difficulty': 'medium', 'category': 'General', 'labels': []}
        topics = []
        materials = []
        course_path = build_layered_course_document(
            'General Course', file_name, [], [], sections=sections_resolved, max_page=max_page
        )
        course_path_errors = []

        if merged_concepts:
            merged_concepts = refine_ontology_deterministic(
                merged_concepts, sections_resolved, run_stage_a=True, run_stage_bcd=False
            )
            emit_progress(88, "Classifying concepts", "Classifying topic and level for each concept.")
            cls = classify_topics_levels_with_llm(merged_concepts, file_name)
            labels_map = {}
            for lb in cls.get('labels', []):
                if not isinstance(lb, dict):
                    continue
                labels_map[normalize_concept_key(str(lb.get('concept', '')))] = {
                    'topic': str(lb.get('topic', 'General')).strip() or 'General',
                    'level': str(lb.get('level', 'intermediate')).strip().lower()
                }
            for c in merged_concepts:
                k = normalize_concept_key(c.get('concept', ''))
                label = labels_map.get(k)
                if label:
                    c['topic'] = label.get('topic', 'General')
                    lv = label.get('level', 'intermediate')
                    c['level'] = lv if lv in ['beginner', 'intermediate', 'advanced'] else 'intermediate'

            emit_progress(93, "Building relationships", "Inferring concept relationships.")
            rels = infer_relationships_with_llm(merged_concepts)
            by_source = {}
            for r in rels:
                if not isinstance(r, dict):
                    continue
                source = normalize_concept_key(str(r.get('source_concept', '')))
                if not source:
                    continue
                by_source.setdefault(source, []).append({
                    'type': str(r.get('type', 'other')).strip() or 'other',
                    'target_concept': str(r.get('target_concept', '')).strip(),
                    'evidence_quote': str(r.get('evidence', '')).strip()
                })
            for c in merged_concepts:
                ck = normalize_concept_key(c.get('concept', ''))
                existing = list(c.get('relationships') or [])
                if str(c.get('nodeType', 'core_concept')) != 'core_concept':
                    c['relationships'] = _dedupe_graph_relationships(
                        existing, implicit_source=c.get('concept')
                    )
                    continue
                llm_edges = []
                for r in by_source.get(ck, []):
                    llm_edges.append({
                        'type': r.get('type', 'other'),
                        'target_concept': r.get('target_concept', ''),
                        'evidence_quote': r.get('evidence_quote', ''),
                    })
                c['relationships'] = _dedupe_graph_relationships(
                    existing + llm_edges,
                    implicit_source=c.get('concept'),
                )

            merged_concepts = refine_ontology_deterministic(
                merged_concepts, sections_resolved, run_stage_a=False, run_stage_bcd=True
            )
            topics = build_topics_from_concepts(merged_concepts)
            materials = build_structured_materials(merged_concepts, max_items=200)

        if merged_concepts or merged_resources:
            thinking_trace.append(
                f"Structured output: {len(merged_concepts)} concept nodes, "
                f"{len(merged_resources)} resources, {len(topics)} topics."
            )
            print(f"✅ Structured extraction: {cls.get('subject', 'General Course')}")
            print(f"📚 Concept nodes: {len(merged_concepts)}, resources: {len(merged_resources)}")
            course_path_candidate = build_course_path_json(
                cls.get('subject', 'General Course'),
                file_name,
                merged_concepts,
                topics,
                sections=sections_resolved,
                max_page=max_page,
            )
            course_path, course_path_errors = ensure_valid_course_path(
                course_path_candidate,
                cls.get('subject', 'General Course'),
                file_name,
                merged_concepts,
                topics,
                sections=sections_resolved,
                max_page=max_page,
            )
            if course_path_errors:
                thinking_trace.append(
                    f"Course path validation fallback applied ({len(course_path_errors)} issues fixed)."
                )

            return {
                'subject': cls.get('subject', 'General Course'),
                'materials': materials,
                'difficulty': cls.get('difficulty', 'medium'),
                'category': cls.get('category', 'General'),
                'topics': topics,
                'knowledge_structure': {
                    'pipeline': ['chunk', 'strategy_extraction', 'merge', 'structuring', 'ontology_refine_v1'],
                    'concept_index': merged_concepts,
                    'resource_index': merged_resources,
                    'review_chains': review_chains_merged,
                    'topics': topics,
                    'graph': course_path.get('graph'),
                    'curriculum': course_path.get('curriculum'),
                },
                'course_path': course_path,
                'course_path_agent': {
                    'prompt_template': build_teacher_course_path_prompt(cls.get('subject', 'General Course'), file_name),
                    'schema': build_course_path_schema_template(),
                    'validation_errors': course_path_errors
                },
                'thinking_trace': thinking_trace
            }

        print("⚠️ Merge step failed, switching to heuristic merge fallback")
        # Heuristic merge fallback without second LLM pass
        seen = set()
        flattened = []
        for c in chunk_summaries:
            for p in c.get('concepts', []):
                concept = str(p.get('concept', '')).strip()
                topic = str(p.get('topic_guess', 'General')).strip() or 'General'
                level = str(p.get('level_guess', 'intermediate')).strip().lower()
                definition_obj = p.get('definition', {})
                definition = ''
                if isinstance(definition_obj, dict):
                    definition = str(definition_obj.get('text', '')).strip()
                key = concept.lower()
                if concept and key not in seen:
                    seen.add(key)
                    if definition:
                        flattened.append(f"{topic} - {level.title()}: {concept} ({definition})")
                    else:
                        flattened.append(f"{topic} - {level.title()}: {concept}")

        if flattened:
            thinking_trace.append(
                f"Used heuristic merge fallback with {len(flattened[:30])} consolidated points."
            )
            course_path, course_path_errors = ensure_valid_course_path(
                None,
                "General Course",
                file_name,
                [],
                [],
                sections=sections_resolved,
                max_page=max_page,
            )
            return {
                'subject': "General Course",
                'materials': [{'id': f'fallback_{i+1}', 'concept': x, 'topic': 'General', 'level': 'intermediate', 'definition': '', 'facts': []} for i, x in enumerate(flattened[:30])],
                'difficulty': 'medium',
                'category': 'General',
                'topics': [],
                'knowledge_structure': {
                    'pipeline': ['chunk', 'concept_extraction', 'merge', 'structuring', 'ontology_refine_v1'],
                    'concept_index': [],
                    'topics': [],
                    'graph': course_path.get('graph'),
                    'curriculum': course_path.get('curriculum'),
                },
                'course_path': course_path,
                'course_path_agent': {
                    'prompt_template': build_teacher_course_path_prompt("General Course", file_name),
                    'schema': build_course_path_schema_template(),
                    'validation_errors': course_path_errors
                },
                'thinking_trace': thinking_trace
            }
    except Exception as e:
        thinking_trace.append(f"Chunk flow failed: {e}")
        print(f"⚠️ Chunked flow failed: {e}")
    
    # If LLM fails, use intelligent extraction based on PDF content
    print("\n🔄 Using intelligent extraction algorithm to analyze PDF content...")
    emit_progress(92, "Fallback extraction", "LLM flow unavailable; using heuristic extraction.")
    return generate_course_fallback(text_content, file_name)

def generate_course_fallback(text_content, file_name):
    """When LLM is unavailable, intelligently extract knowledge points based on PDF content"""
    
    print(f"\n{'='*60}")
    print(f"📊 Intelligent extraction algorithm starting")
    print(f"📄 Text length to analyze: {len(text_content)} characters")
    print(f"{'='*60}\n")
    
    # Simple course topic recognition
    keywords_map = {
        # English keywords (primary)
        'python': ('Python Programming', 'easy', 'Programming Language'),
        'java': ('Java Programming', 'medium', 'Programming Language'),
        'mathematics': ('Elementary Mathematics', 'easy', 'Basic Mathematics'),
        'math': ('Elementary Mathematics', 'easy', 'Basic Mathematics'),
        'network': ('Computer Networks', 'easy', 'Networking'),
        'data structure': ('Data Structures and Algorithms', 'medium', 'Algorithms'),
        'algorithm': ('Data Structures and Algorithms', 'medium', 'Algorithms'),
        'operating system': ('Operating Systems', 'medium', 'Systems'),
        'database': ('Database Systems', 'medium', 'Data Management'),
        'machine learning': ('Machine Learning Basics', 'hard', 'AI'),
        'artificial intelligence': ('Artificial Intelligence', 'hard', 'AI'),
        'software engineering': ('Software Engineering', 'medium', 'Software Engineering'),
        # Legacy Chinese keyword support (for backwards compatibility)
        '网络': ('Computer Networks', 'easy', 'Networking'),
        '数据结构': ('Data Structures and Algorithms', 'medium', 'Algorithms'),
        '算法': ('Data Structures and Algorithms', 'medium', 'Algorithms'),
        '操作系统': ('Operating Systems', 'medium', 'Systems'),
        '数据库': ('Database Systems', 'medium', 'Data Management'),
        '机器学习': ('Machine Learning Basics', 'hard', 'AI'),
        '人工智能': ('Artificial Intelligence', 'hard', 'AI'),
        '软件工程': ('Software Engineering', 'medium', 'Software Engineering'),
    }
    
    subject = "General Course"
    difficulty = "medium"
    category = "General"
    
    # Identify course topic
    text_lower = text_content.lower()
    for keyword, (subj, diff, cat) in keywords_map.items():
        if keyword.lower() in text_lower or keyword.lower() in file_name.lower():
            subject = subj
            difficulty = diff
            category = cat
            break
    
    # Pre-clean: strip multi-file separator banners before any extraction
    text_content = re.sub(r'={3,}[^\n]*={3,}', '', text_content)
    text_content = re.sub(r'-{3,}[^\n]*-{3,}', '', text_content)

    # Intelligently extract knowledge points
    materials = []
    
    print("📋 Step 1: Extract titles and structured content...")
    
    # 1. Try to extract titles and key sentences (starting with numbers, bullets, or keywords)
    lines = text_content.split('\n')
    for line in lines:
        line = line.strip()
        # Match title patterns: starting with numbers, bullets, or containing keywords
        if (re.match(r'^\d+[\.\)、]', line) or 
            re.match(r'^[•·►▪■□]', line) or
            re.match(r'^(Chapter|chapter|第)[\s一二三四五六七八九十\d]+[章节:]', line, re.IGNORECASE) or
            any(kw in line.lower() for kw in ['definition', 'concept', 'principle', 'technique', 'algorithm', 'protocol', 'feature', 'advantage', 'introduction', 'overview'])):
            if 15 < len(line) < 150:  # Appropriate length
                clean_line = re.sub(r'^[\d\.\)、•·►▪■□\s]+', '', line)  # Remove prefix
                if (clean_line and not clean_line.lower().startswith('chapter')
                        and not re.match(r'^第', clean_line)
                        and not _is_fallback_noise(clean_line)):
                    materials.append(clean_line)
    
    print(f"   ✓ Extracted {len(materials)} structured content items")
    
    # 2. If extraction is insufficient, extract meaningful sentences from text
    if len(materials) < 10:
        print("📝 Step 2: Extract key sentences...")
        sentences = re.split(r'[。！？\n]+', text_content)
        for sent in sentences:
            sent = sent.strip()
            # Filter sentences containing key terms
            if (30 < len(sent) < 200 and 
                any(kw in sent.lower() for kw in ['is', 'are', 'refers', 'includes', 'consists', 'mainly', 'can', 'able', 'used', 'implement', 'through', 'define', 'definition', 'concept', 'principle'])
                    and not _is_fallback_noise(sent)):
                materials.append(sent)
                if len(materials) >= 15:
                    break
        
        print(f"   ✓ Now have {len(materials)} knowledge points")
    
    # 3. If still insufficient, extract first sentence of paragraphs
    if len(materials) < 10:
        print("📄 Step 3: Extract paragraph first sentences...")
        paragraphs = text_content.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if para:
                first_sent = re.split(r'[。！？]', para)[0].strip()
                if 20 < len(first_sent) < 150 and not _is_fallback_noise(first_sent):
                    materials.append(first_sent)
                    if len(materials) >= 15:
                        break
        
        print(f"   ✓ Now have {len(materials)} knowledge points")
    
    # 4. Deduplicate and clean
    print("🧹 Step 4: Deduplicate and clean...")
    seen = set()
    unique_materials = []
    for m in materials:
        # Remove special characters and extra spaces
        m_clean = re.sub(r'\s+', ' ', m).strip()
        if m_clean and m_clean not in seen and len(m_clean) > 10 and not _is_fallback_noise(m_clean):
            seen.add(m_clean)
            unique_materials.append(m_clean)
    
    print(f"   ✓ After deduplication: {len(unique_materials)} unique knowledge points")
    
    # 5. If still insufficient, add descriptive knowledge points based on PDF content
    if len(unique_materials) < 10:
        print("🔍 Step 5: Search keyword patterns...")
        # Extract keywords to generate knowledge points
        key_terms = []
        # Only use safe keywords that don't produce fragment titles
        for keyword in ['definition', 'concept', 'principle', 'algorithm', 'protocol', 'architecture', 'feature', 'application']:
            pattern = rf'\b{keyword}\b\s*(?:of|for|in|is|:)?\s*([A-Z][^.!?\n]{{15,80}})'
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches[:2]:
                candidate = match.strip()
                if not _is_fallback_noise(candidate):
                    key_terms.append(candidate)
        
        unique_materials.extend(key_terms[:10 - len(unique_materials)])
        print(f"   ✓ Added {len(key_terms)} keyword matches")
    
    # 6. If still insufficient, extract most valuable content fragments from PDF
    if len(unique_materials) < 10:
        print("⭐ Step 6: Score and extract sentences by importance...")
        # Score by length and keyword density, select most valuable sentences
        all_sentences = re.split(r'[。！？\n]', text_content)
        scored_sentences = []
        for sent in all_sentences:
            sent = sent.strip()
            if 30 < len(sent) < 200 and not _is_fallback_noise(sent):
                score = sum(1 for kw in ['technique', 'system', 'algorithm', 'architecture', 'protocol', 'mechanism'] if kw in sent.lower())
                if score > 0:
                    scored_sentences.append((score, sent))
        
        scored_sentences.sort(reverse=True)
        for score, sent in scored_sentences[:15]:
            if sent not in seen:
                unique_materials.append(sent)
                seen.add(sent)
        
        print(f"   ✓ Now have {len(unique_materials)} knowledge points")
    
    # Ensure at least 10 knowledge points
    final_materials = unique_materials[:15] if len(unique_materials) >= 10 else unique_materials
    
    print(f"\n📊 Extraction result statistics:")
    print(f"   - Original extraction count: {len(materials)}")
    print(f"   - After deduplication: {len(unique_materials)}")
    print(f"   - Final knowledge points: {len(final_materials)}")
    
    if len(final_materials) < 10:
        print("⚠️ Less than 10 knowledge points, adding supplementary content...")
        # Final fallback: generate descriptive knowledge points
        final_materials.extend([
            f"{subject}: Core content and learning objectives of this course",
            f"{subject}: Basic concepts and theoretical framework",
            f"{subject}: Key technologies and implementation methods",
            f"{subject}: Real-world application scenarios and case analysis",
            f"{subject}: Common issues and solutions",
            f"{subject}: Best practices and design principles",
            f"{subject}: Performance optimization and improvement strategies",
            f"{subject}: Development trends and future prospects",
            f"{subject}: Comprehensive exercises and practical projects",
            f"{subject}: Summary and knowledge system construction"
        ][:10 - len(final_materials)])
    
    print(f"\n✅ Intelligent extraction completed!")
    print(f"   - Course name: {subject}")
    print(f"   - Number of knowledge points: {len(final_materials[:15])}")
    print(f"   - Difficulty level: {difficulty}")
    print(f"   - Course category: {category}")
    print(f"{'='*60}\n")
    
    # Print first 3 knowledge points as preview
    print("📚 Extracted knowledge points preview:")
    for i, point in enumerate(final_materials[:3], 1):
        print(f"   {i}. {point[:80]}{'...' if len(point) > 80 else ''}")
    print()
    
    fallback_concepts = []
    for i, point in enumerate(final_materials[:15], start=1):
        fallback_concepts.append({
            'id': f'concept_{uuid4().hex[:10]}',
            'concept': point,
            'nodeType': 'core_concept',
            'extraction_strategy': 'concept_dense',
            'knowledge_weight': 0.5,
            'topic': category,
            'level': 'intermediate',
            'definition': {'text': '', 'source_quotes': []},
            'examples': [],
            'key_facts': [],
            'relationships': []
        })
    fallback_concepts = refine_ontology_deterministic(fallback_concepts, None)
    fallback_topics = build_topics_from_concepts(fallback_concepts)

    course_path_candidate = build_course_path_json(subject, file_name, fallback_concepts, fallback_topics)
    course_path, course_path_errors = ensure_valid_course_path(
        course_path_candidate,
        subject,
        file_name,
        fallback_concepts,
        fallback_topics
    )

    return {
        'subject': subject,
        'materials': [
            {
                'id': f'fallback_{i+1}',
                'concept': point,
                'topic': category,
                'level': 'intermediate',
                'definition': '',
                'facts': []
            }
            for i, point in enumerate(final_materials[:15])
        ],
        'difficulty': difficulty,
        'category': category,
        'topics': fallback_topics,
        'knowledge_structure': {
            'pipeline': ['chunk', 'concept_extraction', 'merge', 'structuring', 'ontology_refine_v1'],
            'concept_index': fallback_concepts,
            'topics': fallback_topics,
            'graph': course_path.get('graph'),
            'curriculum': course_path.get('curriculum'),
        },
        'course_path': course_path,
        'course_path_agent': {
            'prompt_template': build_teacher_course_path_prompt(subject, file_name),
            'schema': build_course_path_schema_template(),
            'validation_errors': course_path_errors
        }
    }

# Teacher Portal API - Upload PDF
@app.route('/api/upload-pdf', methods=['POST'])
def upload_file():
    """Upload file and extract text (supports PDF, TXT, MD)"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF, TXT, or MD files allowed'}), 400
    
    try:
        # Save file
        original_filename = file.filename
        print(f"📥 Original filename: {original_filename}")
        
        # Get file extension
        if '.' in original_filename:
            file_ext = original_filename.rsplit('.', 1)[1].lower()
            base_name = original_filename.rsplit('.', 1)[0]
        else:
            return jsonify({'error': 'File has no extension'}), 400
        
        # Process filename (preserve extension)
        safe_basename = secure_filename(base_name)
        
        # If secure_filename removed all characters (Chinese filename), use timestamp
        if not safe_basename:
            safe_basename = "course"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{safe_basename}.{file_ext}"
        
        print(f"🔒 Processed filename: {filename}")
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"💾 Save path: {file_path}")
        
        file.save(file_path)
        
        print(f"\n{'='*60}")
        print(f"📤 File upload successful: {filename}")
        print(f"{'='*60}")
        
        # Extract text (and per-page structure for PDFs)
        text_content, pdf_pages = extract_file_content(file_path)
        
        if isinstance(text_content, str) and text_content.startswith('Error:'):
            print(f"❌ {text_content}")
            return jsonify({'error': text_content}), 500
        
        print(f"\n✅ Text extraction successful!")
        print(f"📄 Text length: {len(text_content)} characters")
        print(f"📝 First 500 characters preview:")
        print(f"{text_content[:500]}")
        print(f"{'='*60}\n")
        
        payload = {
            'message': 'File upload successful',
            'file_path': file_path,
            'file_name': filename,
            'text_content': text_content,
            'text_length': len(text_content)
        }
        if pdf_pages is not None:
            payload['pdf_pages'] = pdf_pages
            proposed = propose_sections_from_pdf_pages(pdf_pages)
            if proposed:
                payload['proposed_sections'] = proposed
                try:
                    payload['max_page'] = max(int(p['page']) for p in pdf_pages)
                except (TypeError, ValueError, KeyError):
                    payload['max_page'] = len(pdf_pages)

        return jsonify(payload)
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n❌ Upload error:")
        print(error_trace)
        return jsonify({'error': f'Upload failed: {str(e)}', 'trace': error_trace}), 500

@app.route('/api/propose-sections', methods=['POST'])
def propose_sections_api():
    """Build heuristic section boundaries from pdf_pages (same logic as upload)."""
    try:
        data = request.get_json() or {}
        pdf_pages = data.get('pdf_pages')
        norm = normalize_pdf_pages_payload(pdf_pages)
        if not norm:
            return jsonify({'error': 'pdf_pages must be a non-empty list'}), 400
        max_page = max(int(p['page']) for p in norm)
        sections = propose_sections_from_pdf_pages(pdf_pages)
        return jsonify({
            'sections': sections,
            'max_page': max_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Teacher Portal API - Generate course
@app.route('/api/generate-course', methods=['POST'])
def generate_course():
    """Use LLM to analyze PDF content and generate course knowledge points"""
    try:
        data = request.get_json()
        text_content = data.get('text_content', '')
        file_name = data.get('file_name', 'unknown.pdf')
        pdf_pages = data.get('pdf_pages')
        course_sections = data.get('course_sections')
        
        if not text_content:
            return jsonify({'error': 'PDF text content is empty'}), 400
        
        print(f"🤖 Starting course generation, text length: {len(text_content)}")
        if pdf_pages:
            print(f"   pdf_pages: {len(pdf_pages)} page object(s)")
        if course_sections:
            print(f"   course_sections: {len(course_sections)} section(s)")
        
        # Use LLM to generate course
        course_data = generate_course_from_text(
            text_content, file_name, pdf_pages=pdf_pages, course_sections=course_sections
        )
        thinking_trace = course_data.pop('thinking_trace', [])
        
        print(f"✅ Course generation successful: {course_data.get('subject')}")
        print(f"📚 Number of knowledge points: {len(course_data.get('materials', []))}")
        
        # Add additional information
        course_data['id'] = f"course_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        course_data['fileName'] = file_name
        course_data['generatedAt'] = datetime.now().isoformat()
        course_data['knowledgePointCount'] = len(course_data.get('materials', []))
        
        # 💾 Save course to file
        save_course_to_file(course_data)
        if thinking_trace:
            course_data['thinking_trace'] = thinking_trace
        
        return jsonify(course_data)
    
    except Exception as e:
        return jsonify({'error': f'Failed to generate course: {str(e)}'}), 500

def _init_generation_job(job_id):
    with generation_jobs_lock:
        generation_jobs[job_id] = {
            'job_id': job_id,
            'status': 'queued',  # queued | processing | completed | failed
            'progress': 0,
            'stage': 'queued',
            'detail': 'Waiting for worker',
            'thinking_trace': [],
            'result': None,
            'error': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

def _update_generation_job(job_id, **kwargs):
    with generation_jobs_lock:
        job = generation_jobs.get(job_id)
        if not job:
            return
        for k, v in kwargs.items():
            if k == 'thinking_append' and isinstance(v, str) and v.strip():
                trace = job.setdefault('thinking_trace', [])
                trace.append(v.strip())
            elif k in ['thinking_append']:
                continue
            else:
                job[k] = v
        job['updated_at'] = datetime.now().isoformat()

def _run_generation_job(job_id, text_content, file_name, pdf_pages=None, course_sections=None):
    try:
        _update_generation_job(
            job_id,
            status='processing',
            progress=1,
            stage='processing',
            detail='Started course generation worker.',
            thinking_append='Worker started for asynchronous extraction.'
        )

        def progress_cb(progress, stage, detail=None):
            _update_generation_job(
                job_id,
                status='processing',
                progress=max(1, min(99, int(progress))),
                stage=stage,
                detail=detail or stage,
                thinking_append=detail if detail else stage
            )

        course_data = generate_course_from_text(
            text_content,
            file_name,
            progress_callback=progress_cb,
            pdf_pages=pdf_pages,
            course_sections=course_sections,
        )
        thinking_trace = course_data.pop('thinking_trace', [])

        course_data['id'] = f"course_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        course_data['fileName'] = file_name
        course_data['generatedAt'] = datetime.now().isoformat()
        course_data['knowledgePointCount'] = len(course_data.get('materials', []))

        save_course_to_file(course_data)
        if thinking_trace:
            course_data['thinking_trace'] = thinking_trace

        _update_generation_job(
            job_id,
            status='completed',
            progress=100,
            stage='completed',
            detail='Course generation finished.',
            result=course_data,
            thinking_append='Course generation completed and saved.'
        )
    except Exception as e:
        _update_generation_job(
            job_id,
            status='failed',
            progress=100,
            stage='failed',
            detail='Course generation failed.',
            error=str(e),
            thinking_append=f"Generation failed: {e}"
        )

@app.route('/api/generate-course-async', methods=['POST'])
def generate_course_async():
    """Start async course generation and return a job ID for realtime polling."""
    try:
        data = request.get_json()
        text_content = data.get('text_content', '')
        file_name = data.get('file_name', 'unknown.pdf')
        pdf_pages = data.get('pdf_pages')
        course_sections = data.get('course_sections')

        if not text_content:
            return jsonify({'error': 'PDF text content is empty'}), 400

        job_id = f"job_{uuid4().hex}"
        _init_generation_job(job_id)

        worker = threading.Thread(
            target=_run_generation_job,
            args=(job_id, text_content, file_name, pdf_pages, course_sections),
            daemon=True
        )
        worker.start()

        return jsonify({
            'job_id': job_id,
            'status': 'queued'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to start generation: {str(e)}'}), 500

@app.route('/api/generate-course-progress/<job_id>', methods=['GET'])
def generate_course_progress(job_id):
    """Poll async generation progress."""
    with generation_jobs_lock:
        job = generation_jobs.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        return jsonify(job)

# Store course data (should use database in production)
course_library = {}

# Store student answer records (for generating learning reports)
# Structure: { student_id: [{ area_id, question, answer, is_correct, knowledge_point, timestamp }, ...] }
battle_records = {}

# Store student learning report history
# Structure: { student_id: [ { report_id, type, area_id, area_name, generated_at, analysis, ai_summary, title, subtitle }, ... ] }
student_reports = {}

# Async generation jobs for realtime progress in teacher portal
generation_jobs = {}
generation_jobs_lock = threading.Lock()

# Course persistence function
def _is_strict_course_path_payload(data):
    return isinstance(data, dict) and isinstance(data.get('course'), str) and isinstance(data.get('areas'), list)


def _is_layered_course_payload(data):
    if not isinstance(data, dict):
        return False
    if data.get('schema_version') == 2:
        return True
    return isinstance(data.get('curriculum'), dict) and isinstance(data.get('graph'), dict)


def _convert_layered_course_to_runtime(layered, course_id, generated_at=None):
    """Hydrate runtime course dict (materials, topics, knowledge_structure) from layered v2 file."""
    course_code = str(layered.get('course', 'COURSE')).strip() or 'COURSE'
    g = layered.get('graph') or {}
    concepts = g.get('concepts') or []
    relationships = g.get('relationships') or []
    clusters = g.get('clusters') or []

    by_id = {}
    for c in concepts:
        if not isinstance(c, dict):
            continue
        cid = str(c.get('concept_id', '')).strip()
        if cid:
            by_id[cid] = c

    topic_by_cid = {}
    for cl in clusters:
        if not isinstance(cl, dict):
            continue
        t = str(cl.get('title', 'General')).strip() or 'General'
        for cid in cl.get('concept_ids') or []:
            if isinstance(cid, str) and cid.strip():
                topic_by_cid.setdefault(cid.strip(), t)

    rels_into_concept = {cid: [] for cid in by_id}
    for r in relationships:
        if not isinstance(r, dict):
            continue
        sid = str(r.get('source_concept_id', '')).strip()
        tid = str(r.get('target_concept_id', '')).strip()
        rel = str(r.get('relation', 'related_to') or 'related_to')
        if sid not in by_id or tid not in by_id:
            continue
        tgt_title = str(by_id[tid].get('title', '')).strip()
        if not tgt_title:
            continue
        rel_type = rel.replace('_', '-')
        rels_into_concept.setdefault(sid, []).append({
            'type': rel_type,
            'target_concept': tgt_title,
            'evidence_quote': '',
        })

    materials = []
    concept_index = []
    topics_map = {}
    for cid, c in by_id.items():
        title = str(c.get('title', '')).strip()
        if not title:
            continue
        topic = topic_by_cid.get(cid, 'General')
        try:
            impf = float(c.get('importance', 0.5))
        except (TypeError, ValueError):
            impf = 0.5
        level = 'intermediate'
        if impf >= 0.65:
            level = 'advanced'
        elif impf <= 0.35:
            level = 'beginner'
        summary = str(c.get('summary', '')).strip()
        materials.append({
            'id': cid,
            'concept': title,
            'topic': topic,
            'level': level,
            'definition': summary,
            'facts': []
        })
        kws = c.get('keywords', [])
        if not isinstance(kws, list):
            kws = []
        key_facts = [{'fact': str(k).strip(), 'numbers': [], 'source_quote': ''} for k in kws if str(k).strip()]
        sem = str(c.get('semantic_role', '') or '').strip() or 'theory_domain'
        concept_index.append({
            'id': cid,
            'concept': title,
            'topic': topic,
            'level': level,
            'definition': {'text': summary, 'source_quotes': []},
            'examples': [],
            'key_facts': key_facts[:12],
            'relationships': rels_into_concept.get(cid, []),
            'extraction_strategy': strategy_for_semantic_role(sem),
            'source_section_id': str(c.get('source_section_id') or 'sec_root'),
            'parent_concept_id': c.get('parent_concept_id'),
        })
        topics_map.setdefault(topic, {'beginner': [], 'intermediate': [], 'advanced': []})
        topics_map[topic][level].append(title)

    topics = []
    for topic, lv in topics_map.items():
        topics.append({
            'topic': topic,
            'levels': {
                'beginner': _dedupe_str_list(lv.get('beginner', [])),
                'intermediate': _dedupe_str_list(lv.get('intermediate', [])),
                'advanced': _dedupe_str_list(lv.get('advanced', []))
            }
        })

    return {
        'id': course_id,
        'subject': course_code,
        'materials': materials,
        'difficulty': 'medium',
        'category': topics[0]['topic'] if topics else 'General',
        'topics': topics,
        'knowledge_structure': {
            'pipeline': ['layered_course_v2_import'],
            'concept_index': concept_index,
            'topics': topics,
            'graph': g,
            'curriculum': layered.get('curriculum'),
        },
        'course_path': layered,
        'generatedAt': generated_at or datetime.now().isoformat(),
        'knowledgePointCount': len(materials)
    }

def _convert_strict_course_to_runtime(strict_data, course_id, generated_at=None):
    """
    Convert strict 3-layer payload (course->areas->concept_nodes) into
    runtime-compatible shape for existing frontend/game logic.
    """
    course_code = str(strict_data.get('course', 'COURSE')).strip() or 'COURSE'
    areas = strict_data.get('areas', []) if isinstance(strict_data.get('areas'), list) else []

    materials = []
    concept_index = []
    topics_map = {}
    total_difficulty = 0
    diff_count = 0

    for area in areas:
        if not isinstance(area, dict):
            continue
        topic = str(area.get('name', 'General')).strip() or 'General'
        d = area.get('difficulty')
        if isinstance(d, int):
            total_difficulty += d
            diff_count += 1
        nodes = area.get('concept_nodes', [])
        if not isinstance(nodes, list):
            continue
        topics_map.setdefault(topic, {'beginner': [], 'intermediate': [], 'advanced': []})

        for node in nodes:
            if not isinstance(node, dict):
                continue
            title = str(node.get('title', '')).strip()
            if not title:
                continue
            cid = str(node.get('concept_id', '')).strip() or f'concept_{uuid4().hex[:8]}'
            summary = str(node.get('summary', '')).strip()
            importance = node.get('importance', 3)
            if not isinstance(importance, int):
                importance = 3
            level = 'intermediate'
            if importance <= 2:
                level = 'beginner'
            elif importance >= 5:
                level = 'advanced'

            materials.append({
                'id': cid,
                'concept': title,
                'topic': topic,
                'level': level,
                'definition': summary,
                'facts': []
            })

            concept_index.append({
                'id': cid,
                'concept': title,
                'topic': topic,
                'level': level,
                'definition': {'text': summary, 'source_quotes': []},
                'examples': [],
                'key_facts': [],
                'relationships': []
            })

            topics_map[topic][level].append(title)

    topics = []
    for topic, lv in topics_map.items():
        topics.append({
            'topic': topic,
            'levels': {
                'beginner': _dedupe_str_list(lv.get('beginner', [])),
                'intermediate': _dedupe_str_list(lv.get('intermediate', [])),
                'advanced': _dedupe_str_list(lv.get('advanced', []))
            }
        })

    avg_difficulty = (total_difficulty / diff_count) if diff_count else 2
    if avg_difficulty < 1.7:
        difficulty = 'easy'
    elif avg_difficulty > 2.3:
        difficulty = 'hard'
    else:
        difficulty = 'medium'

    return {
        'id': course_id,
        'subject': course_code,
        'materials': materials,
        'difficulty': difficulty,
        'category': topics[0]['topic'] if topics else 'General',
        'topics': topics,
        'knowledge_structure': {
            'pipeline': ['strict_course_path_import'],
            'concept_index': concept_index,
            'topics': topics
        },
        'course_path': strict_data,
        'generatedAt': generated_at or datetime.now().isoformat(),
        'knowledgePointCount': len(materials)
    }

def save_course_to_file(course_data):
    """Save course to file"""
    try:
        course_id = course_data['id']
        file_path = os.path.join(COURSES_FOLDER, f"{course_id}.json")

        # Persist canonical course_path: layered v2 preferred, else legacy strict areas payload.
        strict_payload = course_data.get('course_path')
        if _is_layered_course_payload(strict_payload):
            to_save = strict_payload
        elif _is_strict_course_path_payload(strict_payload):
            to_save = strict_payload
        else:
            to_save = {
                'schema_version': 2,
                'course': _infer_course_code(course_data.get('subject', ''), course_data.get('fileName', '')),
                'curriculum': {'sections': []},
                'graph': {'concepts': [], 'relationships': [], 'clusters': []},
            }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(to_save, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Course saved: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to save course: {str(e)}")
        return False

def load_all_courses():
    """Load all courses from files"""
    courses = []
    try:
        # Read from current canonical folder + legacy relative folder (if service used old cwd-based path).
        candidate_folders = [COURSES_FOLDER]
        legacy_courses_folder = os.path.join(os.getcwd(), 'courses')
        if legacy_courses_folder not in candidate_folders:
            candidate_folders.append(legacy_courses_folder)

        seen_ids = set()
        for folder in candidate_folders:
            if not os.path.exists(folder):
                continue
            for filename in os.listdir(folder):
                if not filename.endswith('.json'):
                    continue
                file_path = os.path.join(folder, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        loaded_data = json.load(f)
                        course_id = loaded_data.get('id') if isinstance(loaded_data, dict) else None
                        course_id = course_id or filename.replace('.json', '')
                        if course_id in seen_ids:
                            continue
                        seen_ids.add(course_id)
                        if _is_layered_course_payload(loaded_data) and not loaded_data.get('subject'):
                            generated_at = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                            runtime_course = _convert_layered_course_to_runtime(
                                loaded_data,
                                course_id=course_id,
                                generated_at=generated_at
                            )
                            courses.append(runtime_course)
                        elif _is_strict_course_path_payload(loaded_data) and not loaded_data.get('subject'):
                            generated_at = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                            runtime_course = _convert_strict_course_to_runtime(
                                loaded_data,
                                course_id=course_id,
                                generated_at=generated_at
                            )
                            courses.append(runtime_course)
                        else:
                            courses.append(loaded_data)
                except Exception as e:
                    print(f"⚠️  Failed to load course file: {filename}, {str(e)}")
        
        # Sort by generation time in descending order (newest first)
        courses.sort(key=lambda x: x.get('generatedAt', ''), reverse=True)
        print(f"📚 Successfully loaded {len(courses)} courses")
        return courses
    except Exception as e:
        print(f"❌ Failed to load course list: {str(e)}")
        return []

def delete_course_file(course_id):
    """Delete course file"""
    try:
        file_path = os.path.join(COURSES_FOLDER, f"{course_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️  Course deleted: {course_id}")
            return True
        return False
    except Exception as e:
        print(f"❌ Failed to delete course: {str(e)}")
        return False

# Teacher Portal API - Reset game map (clear all course areas)
@app.route('/api/reset-game-map', methods=['POST'])
def reset_game_map():
    """Reset game map, only keep start point, and clear all battle records and reports"""
    global game_state, course_library, battle_records, student_reports
    
    print(f"\n{'='*60}")
    print(f"🔄 Resetting game map and all student data")
    print(f"{'='*60}\n")
    
    # Save old state for logging
    old_area_count = len(game_state['areas'])
    old_course_count = len(course_library)
    old_battle_records_count = sum(len(records) for records in battle_records.values())
    old_reports_count = sum(len(reports) for reports in student_reports.values())
    old_students_count = len(battle_records)
    
    # Reset game state
    game_state = {
        'areas': {
            'start': {
                'completed': True,  # Start area is completed by default
                'position': {'x': 200, 'y': 400},
                'connections': [],
                'level': 0,
                'castle_type': random.randint(1, 5),
                'learningProgress': 100,
                'learnedPoints': []
            }
        },
        'current_area': 'start',
        'max_level': 0
    }
    
    # Clear course library
    course_library = {}
    
    # Clear all battle records for all students
    battle_records.clear()
    
    # Clear all student reports for all students
    student_reports.clear()
    
    print(f"✅ Map and data reset successful!")
    print(f"   Deleted areas: {old_area_count - 1}")
    print(f"   Cleared courses: {old_course_count}")
    print(f"   Cleared battle records: {old_battle_records_count} records from {old_students_count} student(s)")
    print(f"   Cleared reports: {old_reports_count} reports")
    print(f"{'='*60}\n")
    
    return jsonify({
        'message': 'Game map has been reset',
        'deleted_areas': old_area_count - 1,
        'cleared_courses': old_course_count,
        'cleared_battle_records': old_battle_records_count,
        'cleared_reports': old_reports_count,
        'cleared_students': old_students_count
    })

# Teacher Portal API - Apply course to game map
# Teacher Portal API - Get all courses
@app.route('/api/courses', methods=['GET'])
def get_all_courses():
    """Get all saved courses"""
    try:
        courses = load_all_courses()
        return jsonify({
            'courses': courses,
            'total': len(courses)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get course list: {str(e)}'}), 500

# Teacher Portal API - Delete course
@app.route('/api/courses/<course_id>', methods=['DELETE'])
def delete_course(course_id):
    """Delete specified course"""
    try:
        success = delete_course_file(course_id)
        if success:
            return jsonify({'message': f'Course {course_id} deleted'})
        else:
            return jsonify({'error': 'Course file not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to delete course: {str(e)}'}), 500

@app.route('/api/apply-course-to-game', methods=['POST'])
def apply_course_to_game():
    """Apply course knowledge points to game map, create Areas by chapter"""
    try:
        data = request.get_json()
        course_id = data.get('course_id')
        course_data = data.get('course_data')
        replace_existing = data.get('replace_existing', False)  # Whether to replace existing courses
        
        if not course_data:
            return jsonify({'error': 'Course data is empty'}), 400
        
        print(f"\n{'='*60}")
        print(f"🎮 Applying course to game map")
        print(f"📚 Course: {course_data.get('subject')}")
        print(f"🔄 Replace mode: {replace_existing}")
        print(f"{'='*60}\n")
        
        # If replace is selected, reset map first
        if replace_existing:
            print(f"⚠️  Replace mode: clearing existing map...")
            reset_game_map()
            print(f"✅ Map cleared, starting to add new course\n")
        
        # Parse course structure, group knowledge points by chapter
        raw_materials = course_data.get('materials', [])
        subject = course_data.get('subject', 'Course')

        def _flatten_material_item(item):
            """
            One display line per knowledge point. Prefer 'Concept: Definition' without repeating
            the same topic prefix on every line (topic is often a coarse bucket like 'Innovation Models').
            """
            if isinstance(item, str):
                return (item or '').strip()
            if not isinstance(item, dict):
                return str(item).strip()
            concept = str(item.get('concept', '')).strip()
            definition = str(item.get('definition', '')).strip()
            topic = str(item.get('topic', 'General')).strip() or 'General'
            if 'concept' in item:
                if concept and definition:
                    return f'{concept}: {definition}'
                if concept:
                    if topic and topic != 'General' and topic.lower() not in concept.lower():
                        return f'{topic}: {concept}'
                    return concept
            if 'Section Title' in item:
                return str(item.get('Section Title') or '').strip()
            parts = []
            for k, v in item.items():
                parts.append(f'{k}: {v}')
            return ' | '.join(parts).strip() if parts else ''

        materials = []
        for item in raw_materials:
            line = _flatten_material_item(item)
            if line:
                materials.append(line)

        # Drop exact duplicates (can happen when course merges overlap concepts).
        _seen_mat = set()
        _deduped = []
        for m in materials:
            key = m.strip().lower()
            if key in _seen_mat:
                continue
            _seen_mat.add(key)
            _deduped.append(m)
        materials = _deduped

        category = course_data.get('category', 'General')
        difficulty = course_data.get('difficulty', 'medium')
        
        # Analyze chapter structure
        chapters = {}
        # Default chapter label in English for non-marked materials
        current_chapter = "Chapter 1"
        chapter_num = 1
        
        for material in materials:
            # Check if it's a new chapter marker
            is_chapter_marker = False
            if re.search(r'(Chapter|chapter)[\s\d]+', material, re.IGNORECASE) or (re.search(r'第[\d一二三四五六七八九十]+[章节]', material)):
                # Extract chapter name
                chapter_match = re.search(r'(Chapter|chapter)[\s\d]+', material, re.IGNORECASE)
                if chapter_match:
                    # Extract number from chapter match (cannot use backslash in f-string expression)
                    number_match = re.search(r'\d+', chapter_match.group())
                    chapter_num = number_match.group() if number_match else '1'
                    current_chapter = f"Chapter {chapter_num}"
                    is_chapter_marker = True
                else:
                    legacy_match = re.search(r'第[\d一二三四五六七八九十]+[章节]', material)
                    if legacy_match:
                        # Convert Chinese chapter to English
                        number_match = re.search(r'\d+', legacy_match.group())
                        chapter_num = number_match.group() if number_match else '1'
                        current_chapter = f"Chapter {chapter_num}"
                        is_chapter_marker = True
            
            # Initialize chapter if not exists
            if current_chapter not in chapters:
                chapters[current_chapter] = []
            
            # Only add material to chapter if it's NOT a chapter marker
            # Chapter markers should not be included as knowledge points
            if not is_chapter_marker:
                chapters[current_chapter].append(material)
        
        # If no chapters detected, evenly distribute all knowledge points
        if len(chapters) == 1 and len(chapters[current_chapter]) == len(materials):
            # Redistribute: 5 knowledge points per chapter
            chapters = {}
            points_per_chapter = 5
            for i in range(0, len(materials), points_per_chapter):
                chapter_name = f"Chapter {i // points_per_chapter + 1}"
                chapters[chapter_name] = materials[i:i + points_per_chapter]
        
        print(f"📖 Detected {len(chapters)} chapters:")
        for chapter_name, points in chapters.items():
            print(f"   - {chapter_name}: {len(points)} knowledge points")
            print(f"     First 3 points: {points[:3] if len(points) > 0 else 'N/A'}")
        
        # Create one Area for each chapter
        new_areas = {}
        area_count = len(game_state['areas'])
        
        # Find last completed area
        last_completed_area = None
        for area_id, area in game_state['areas'].items():
            if area['completed'] or area_id == 'start':
                last_completed_area = area_id
        
        if not last_completed_area:
            last_completed_area = 'start'
        
        # 【Linear map】: Create areas in order, each area only connects to next
        last_area = game_state['areas'][last_completed_area]
        last_area['connections'] = []  # Clear existing connections
        
        # Get starting position and level
        previous_position = last_area['position']
        previous_level = last_area['level']
        
        previous_area_id = last_completed_area
        chapter_index = 0
        
        forward_distance = 600  # Horizontal distance between areas
        
        for chapter_name, chapter_materials in chapters.items():
            area_id = f"area{area_count + 1 + chapter_index}"
            area_name = f"{subject}: {chapter_name}"
            
            # 【Linear layout】: Calculate position directly, don't rely on calculate_new_position
            # Move horizontally to the right, Y coordinate remains constant
            position = {
                'x': previous_position['x'] + forward_distance,
                'y': previous_position['y']
            }
            
            # Create new Area
            new_areas[area_id] = {
                'completed': False,
                'position': position,
                'connections': [],  # Initially empty, will connect in next iteration
                'level': previous_level + 1,
                # If you added more castle images (castle6.png, castle7.png, ...),
                # increase the upper bound accordingly (default supports 1..10)
                'castle_type': random.randint(1, 10),
                'name': area_name,  # Add name
                'learningProgress': 0,  # Initialize learning progress to 0%
                'learnedPoints': []  # List of learned knowledge points
            }
            
            # 【Linear connection】: Previous area only connects to current area
            if previous_area_id in game_state['areas']:
                game_state['areas'][previous_area_id]['connections'] = [area_id]
            else:
                new_areas[previous_area_id]['connections'] = [area_id]
            
            # Store course materials and cognitive architecture (if present on course)
            course_library[area_id] = {
                'subject': area_name,
                'materials': chapter_materials,
                'difficulty': difficulty,
                'category': category,
                'knowledgePointCount': len(chapter_materials),
                'chapter': chapter_name,
                'parent_course': subject,
                # Attach the full course-level cognitive architecture so the
                # student dialog can configure a dedicated agent for this course.
                'cognitive_architecture': course_data.get('cognitive_architecture')
            }
            
            print(f"✅ Created area: {area_id} - {area_name}")
            print(f"   Position: x={position['x']}, y={position['y']}")
            print(f"   Connection: {previous_area_id} → {area_id}")
            print(f"   Knowledge points: {len(chapter_materials)}")
            print(f"   Materials preview: {chapter_materials[:2] if chapter_materials else 'N/A'}")
            print(f"   Stored in course_library[{area_id}]")
            
            # Update to be "previous area" for next iteration
            previous_area_id = area_id
            previous_position = position
            previous_level += 1
            chapter_index += 1
        
        print(f"📊 Finished creating {len(chapters)} chapter areas")
        print(f"   Last area ID: {previous_area_id}")
        print(f"   Last position: x={previous_position['x']}, y={previous_position['y']}")
        print(f"   Current new_areas count: {len(new_areas)}")
        
        # Create final destination area for this subject (unlocked when all chapters are completed)
        # Use a cleaner final area ID
        print(f"🎯 Starting final destination creation for subject: {subject}")
        final_area_id = f"final_{subject.replace(' ', '_').replace(':', '_').lower()}"
        print(f"   Generated final_area_id: {final_area_id}")
        final_area_name = f"{subject} - Final Destination"
        final_position = {
            'x': previous_position['x'] + forward_distance,
            'y': previous_position['y']
        }
        
        # Get all chapter area IDs for this subject (exclude start area)
        chapter_area_ids = [aid for aid in new_areas.keys() if aid != 'start']
        print(f"   Chapter area IDs: {chapter_area_ids}")
        print(f"   Number of chapters: {len(chapter_area_ids)}")
        
        print(f"   Creating final area at position: x={final_position['x']}, y={final_position['y']}")
        new_areas[final_area_id] = {
            'completed': False,
            'position': final_position,
            'connections': [],
            'level': previous_level + 1,
            'castle_type': random.randint(1, 10),
            'name': final_area_name,
            'learningProgress': 0,
            'learnedPoints': [],
            'type': 'final_destination',
            'parent_subject': subject,
            'required_areas': chapter_area_ids  # All chapter areas must be completed
        }
        
        # Last chapter area connects to final destination (but final is locked until all chapters completed)
        if previous_area_id in game_state['areas']:
            game_state['areas'][previous_area_id]['connections'] = [final_area_id]
        else:
            new_areas[previous_area_id]['connections'] = [final_area_id]
        
        print(f"✅ Created final destination area: {final_area_id} - {final_area_name}")
        print(f"   Position: x={final_position['x']}, y={final_position['y']}")
        print(f"   Requires {len(chapter_area_ids)} chapter areas to be completed: {chapter_area_ids}")
        print(f"   Type: final_destination")
        print(f"   Parent subject: {subject}")
        
        # Add new areas to game state
        print(f"📦 Before update: game_state has {len(game_state['areas'])} areas")
        print(f"📦 new_areas dictionary has {len(new_areas)} areas: {list(new_areas.keys())}")
        game_state['areas'].update(new_areas)
        print(f"📦 After update: game_state has {len(game_state['areas'])} areas")
        game_state['max_level'] = max(area['level'] for area in game_state['areas'].values())
        
        print(f"\n✅ Successfully applied course to game map!")
        print(f"   📊 Summary:")
        print(f"     - Chapters in course: {len(chapters)}")
        print(f"     - Chapter areas created: {len(chapter_area_ids)}")
        print(f"     - Final destination created: {final_area_id}")
        print(f"     - Total new_areas: {len(new_areas)} (should be {len(chapters) + 1})")
        print(f"     - New areas list: {list(new_areas.keys())}")
        print(f"   📦 Game state update:")
        print(f"     - Before: {len(game_state['areas']) - len(new_areas)} areas")
        print(f"     - After: {len(game_state['areas'])} areas")
        print(f"     - All area IDs: {list(game_state['areas'].keys())}")
        print(f"     - Final area exists: {final_area_id in game_state['areas']}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'message': f'Successfully applied course to game map',
            'new_areas': list(new_areas.keys()),
            'chapter_count': len(chapters),
            'final_area_id': final_area_id,
            'game_state': game_state
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n❌ Failed to apply course:")
        print(error_trace)
        return jsonify({'error': f'Application failed: {str(e)}'}), 500

# API - Get course library (for frontend to fetch course materials)
@app.route('/api/course-library/<area_id>', methods=['GET'])
def get_course_library(area_id):
    """Get course materials for specified area"""
    print(f"\n📚 API Request: /api/course-library/{area_id}")
    if area_id in course_library:
        data = course_library[area_id]
        print(f"✅ Found course data for {area_id}")
        print(f"   Subject: {data.get('subject')}")
        print(f"   Chapter: {data.get('chapter')}")
        print(f"   Knowledge points count: {data.get('knowledgePointCount')}")
        print(f"   First 2 materials: {data.get('materials', [])[:2]}")
        return jsonify(data)
    else:
        print(f"⚠️  No course data found for {area_id}, returning defaults")
        # Return default course materials (if not added from teacher portal)
        return jsonify({
            'subject': f'{area_id} Area',
            'materials': [
                'This is default knowledge point 1',
                'This is default knowledge point 2',
                'This is default knowledge point 3',
                'This is default knowledge point 4',
                'This is default knowledge point 5'
            ],
            'difficulty': 'medium',
            'category': 'General',
            'knowledgePointCount': 5
        })

# ==================== Learning Report Related APIs ====================

@app.route('/api/save-battle-record', methods=['POST'])
def save_battle_record():
    """Save answer record"""
    try:
        data = request.get_json()
        student_id = data.get('student_id', 'default_student')  # Default student ID
        area_id = data.get('area_id')
        question = data.get('question')
        answer = data.get('answer')
        is_correct = data.get('is_correct')
        knowledge_point = data.get('knowledge_point', '')
        
        if not all([area_id, question, answer is not None, is_correct is not None]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Initialize student records
        if student_id not in battle_records:
            battle_records[student_id] = []
        
        # Add answer record
        record = {
            'area_id': area_id,
            'question': question,
            'answer': answer,
            'is_correct': is_correct,
            'knowledge_point': knowledge_point,
            'timestamp': datetime.now().isoformat()
        }
        
        battle_records[student_id].append(record)
        
        print(f"📝 Saved answer record: {student_id} - {area_id} - {'✅' if is_correct else '❌'}")
        
        return jsonify({
            'message': 'Record saved successfully',
            'total_records': len(battle_records[student_id])
        })
    
    except Exception as e:
        print(f"❌ Failed to save answer record: {str(e)}")
        return jsonify({'error': f'Failed to save record: {str(e)}'}), 500

@app.route('/api/get-battle-records/<student_id>', methods=['GET'])
def get_battle_records(student_id):
    """Get student's answer records"""
    records = battle_records.get(student_id, [])
    return jsonify({
        'student_id': student_id,
        'total_battles': len(records),
        'records': records
    })

def analyze_battle_data(records, group_by_subject_chapter=False):
    """Analyze battle records for report generation"""
    if not records:
        return None
    
    total_questions = len(records)
    correct_count = sum(1 for r in records if r['is_correct'])
    accuracy = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    knowledge_point_stats = {}
    for record in records:
        kp = record.get('knowledge_point', 'Uncategorized')
        if kp not in knowledge_point_stats:
            knowledge_point_stats[kp] = {'total': 0, 'correct': 0, 'incorrect': 0}
        
        knowledge_point_stats[kp]['total'] += 1
        if record['is_correct']:
            knowledge_point_stats[kp]['correct'] += 1
        else:
            knowledge_point_stats[kp]['incorrect'] += 1
    
    for kp, stats in knowledge_point_stats.items():
        stats['error_rate'] = (stats['incorrect'] / stats['total'] * 100) if stats['total'] > 0 else 0
        stats['accuracy'] = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
    
    sorted_kps = sorted(knowledge_point_stats.items(), key=lambda x: x[1]['error_rate'], reverse=True)
    weak_points = sorted_kps[:3]
    
    result = {
        'total_questions': total_questions,
        'correct_count': correct_count,
        'accuracy': round(accuracy, 2),
        'knowledge_point_stats': knowledge_point_stats,
        'weak_points': [{'knowledge_point': kp, **stats} for kp, stats in weak_points]
    }
    
    # Group by subject and chapter for final reports
    if group_by_subject_chapter:
        subject_chapter_stats = {}
        for record in records:
            area_id = record.get('area_id')
            if area_id:
                course_info = course_library.get(area_id)
                subject = 'Unknown Subject'
                chapter = 'Unknown Chapter'
                
                if course_info:
                    subject = course_info.get('parent_course', course_info.get('subject', 'Unknown Subject'))
                    chapter = course_info.get('chapter', 'Unknown Chapter')
                    subject_chapter_key = f"{subject} - {chapter}"
                else:
                    area = game_state['areas'].get(area_id)
                    if area and area.get('name'):
                        subject_chapter_key = area['name']
                        # Try to extract subject and chapter from area name (format: "Subject: Chapter Name")
                        if ':' in subject_chapter_key:
                            parts = subject_chapter_key.split(':', 1)
                            subject = parts[0].strip()
                            chapter = parts[1].strip()
                    else:
                        subject_chapter_key = f"Area {area_id}"
                
                if subject_chapter_key not in subject_chapter_stats:
                    subject_chapter_stats[subject_chapter_key] = {
                        'subject': subject,
                        'chapter': chapter,
                        'total': 0,
                        'correct': 0,
                        'incorrect': 0,
                        'areas': set()
                    }
                
                subject_chapter_stats[subject_chapter_key]['total'] += 1
                subject_chapter_stats[subject_chapter_key]['areas'].add(area_id)
                if record['is_correct']:
                    subject_chapter_stats[subject_chapter_key]['correct'] += 1
                else:
                    subject_chapter_stats[subject_chapter_key]['incorrect'] += 1
        
        # Convert sets to lists for JSON serialization
        for key, stats in subject_chapter_stats.items():
            stats['areas'] = list(stats['areas'])
            stats['accuracy'] = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        result['subject_chapter_stats'] = subject_chapter_stats
        
        # Debug: Print grouped statistics
        print(f"\n📊 Subject-Chapter Statistics:")
        subjects_dict = {}
        for subject_chapter, stats in subject_chapter_stats.items():
            subject = stats.get('subject', 'Unknown')
            if subject not in subjects_dict:
                subjects_dict[subject] = []
            subjects_dict[subject].append({
                'chapter': stats.get('chapter', 'Unknown'),
                'stats': stats
            })
        
        for subject, chapters in subjects_dict.items():
            print(f"  📚 {subject}:")
            for chap_info in chapters:
                chap = chap_info['chapter']
                s = chap_info['stats']
                print(f"    - {chap}: {s['accuracy']:.1f}% ({s['correct']}/{s['total']})")
    
    return result

def get_area_display_name(area_id):
    if not area_id:
        return None

    area = game_state['areas'].get(area_id)
    if area:
        area_name = area.get('name')
        if area_name:
            return area_name

    course_info = course_library.get(area_id)
    if course_info:
        subject = course_info.get('subject')
        if subject:
            return subject

    return area_id.replace('_', ' ').title()

def generate_ai_report(analysis_data, student_id, report_type='snapshot', area_name=None):
    """Generate a narrative report using an LLM, falling back to template text if needed"""
    try:
        import requests

        accuracy = analysis_data['accuracy']
        total_questions = analysis_data['total_questions']
        weak_points = analysis_data['weak_points']

        if weak_points:
            weak_points_desc = "\n".join([
                f"- {wp['knowledge_point']}: accuracy {wp['accuracy']:.1f}% ({wp['correct']}/{wp['total']} correct)"
                for wp in weak_points
            ])
        else:
            weak_points_desc = "None — every tracked knowledge point was answered correctly."

        if report_type == 'module':
            scope_line = f'This report focuses on the module "{area_name}".' if area_name else "This report focuses on this module."
            subject_section = ""
        elif report_type == 'final':
            scope_line = "This report summarizes the entire learning journey across every module."
            # Organize by subject first, then chapters within each subject
            subject_chapter_stats = analysis_data.get('subject_chapter_stats', {})
            if subject_chapter_stats:
                # Group by subject
                subjects_dict = {}
                for subject_chapter, stats in subject_chapter_stats.items():
                    subject = stats.get('subject', 'Unknown Subject')
                    chapter = stats.get('chapter', 'Unknown Chapter')
                    
                    if subject not in subjects_dict:
                        subjects_dict[subject] = []
                    subjects_dict[subject].append({
                        'chapter': chapter,
                        'accuracy': stats['accuracy'],
                        'correct': stats['correct'],
                        'total': stats['total']
                    })
                
                # Build structured breakdown by subject - more explicit formatting
                subject_section = "\n\n=== MANDATORY STRUCTURE: Report MUST be organized by SUBJECT ===\n"
                subject_section += "You MUST write separate paragraphs for EACH SUBJECT listed below.\n"
                subject_section += "Start with an opening paragraph, then one paragraph per subject, then suggestions and conclusion.\n\n"
                
                subject_section += "=== SUBJECT PERFORMANCE DATA ===\n\n"
                for subject in sorted(subjects_dict.keys()):
                    chapters = subjects_dict[subject]
                    total_q = sum(c['total'] for c in chapters)
                    total_correct = sum(c['correct'] for c in chapters)
                    subj_accuracy = (total_correct / total_q * 100) if total_q > 0 else 0
                    
                    subject_section += f"SUBJECT: {subject}\n"
                    subject_section += f"  Subject-level accuracy: {subj_accuracy:.1f}% ({total_correct} correct out of {total_q} total questions)\n"
                    subject_section += f"  Chapters in this subject:\n"
                    for chap in chapters:
                        subject_section += f"    - {chap['chapter']}: {chap['accuracy']:.1f}% accuracy ({chap['correct']} correct out of {chap['total']} questions)\n"
                    subject_section += "\n"
            else:
                subject_section = ""
        else:
            scope_line = "This report is a snapshot of recent learning performance."
            subject_section = ""

        if report_type == 'final':
            prompt = f"""You are the chief mentor of the Magic Academy. Write a celebratory completion report that congratulates the student on finishing the entire course, while providing a comprehensive summary in English only.

{scope_line}

{subject_section}
Overall Achievement:
- Total questions completed: {total_questions}
- Overall mastery accuracy: {accuracy:.1f}%
- Areas that showed challenge:
{weak_points_desc}

MANDATORY REPORT STRUCTURE (You MUST follow this exactly):

1. CONGRATULATORY OPENING (2-3 sentences):
   - Start with enthusiastic congratulations on completing the entire course
   - Celebrate the student's dedication and perseverance
   - Acknowledge the total questions answered and overall accuracy as an achievement
   - Use warm, proud, and congratulatory tone

2. COURSE SUMMARY PARAGRAPHS (One paragraph per subject):
   You MUST write one dedicated paragraph for EACH SUBJECT listed above.
   Each paragraph should:
   - Start with celebration of that subject's completion (e.g., "In [Subject Name], you have demonstrated...", "Your journey through [Subject Name] has been...")
   - Highlight the subject's overall accuracy percentage as an achievement
   - Summarize performance across all chapters in that subject
   - Recognize strengths and acknowledge areas that required extra effort
   - Frame everything in a positive, congratulatory manner
   
   Example tone for each subject:
   "You have successfully completed [Subject Name], answering [X] questions with an impressive [Y]% accuracy. 
   Throughout [Chapter 1], you achieved [Z]% accuracy, showcasing your understanding of [topic]. 
   In [Chapter 2], your [W]% accuracy reflected your growing mastery. Your solid grasp of [strength] 
   in this subject is commendable, and your willingness to tackle [challenging area] shows true dedication."

3. REFLECTION ON GROWTH (1 paragraph):
   - Reflect on the student's overall learning journey
   - Highlight key achievements and milestones
   - Acknowledge progress made, even in challenging areas

4. CONGRATULATORY CONCLUSION (2-3 sentences):
   - End with a grand, inspiring congratulations message
   - Use magical academy-themed imagery (e.g., "You have proven yourself worthy", "Your dedication has unlocked new realms of knowledge")
   - Celebrate the completion as a significant milestone
   - End on a high, inspiring note

IMPORTANT RULES:
- Write in polished, celebratory prose
- Tone should be CONGRATULATORY and PROUD throughout
- NO bullet points, NO numbered lists, NO emojis, NO markdown formatting
- NO weird numbers like "42.9 questions" - use whole numbers only
- Each subject MUST get its own paragraph
- Focus on celebration and achievement, while still providing meaningful summary
- Total length: 400-500 words (enough to celebrate and summarize thoroughly)

Now write the congratulatory completion report following the structure above exactly:"""
        else:
            prompt = f"""You are the chief mentor of the Arcane Academy. Craft a warm, encouraging learning report in English only.

{scope_line}

Overall Performance:
- Total questions answered: {total_questions}
- Overall accuracy: {accuracy:.1f}%
- Key challenges:
{weak_points_desc}

Instructions:
1. Open with positive reinforcement grounded in the data above.
2. Provide a concise analysis of strengths and opportunities.
3. Offer at least two actionable suggestions that reference the knowledge points.
4. Conclude with an inspiring message that fits a magical academy setting.
5. Limit the response to roughly 180-220 words.
6. Write in polished prose, NO bullet lists, NO emojis, NO markdown formatting.
"""

        print("🤖 Generating AI report via Ollama...")

        ai_report = call_llm_text(
            prompt=prompt,
            model='qwen2.5',
            timeout=30,
            options={'temperature': 0.7, 'top_p': 0.9}
        ).strip()
        if ai_report:
            print(f"✅ AI report generated successfully, length {len(ai_report)} characters")
            return ai_report
        return generate_fallback_report(analysis_data, report_type=report_type, area_name=area_name)

    except Exception as e:
        print(f"⚠️ AI report generation failed: {str(e)}. Using fallback text.")
        return generate_fallback_report(analysis_data, report_type=report_type, area_name=area_name)

def generate_fallback_report(analysis_data, report_type='snapshot', area_name=None):
    """Fallback text when the LLM is unavailable"""
    accuracy = analysis_data['accuracy']
    total_questions = analysis_data['total_questions']
    weak_points = analysis_data['weak_points']

    if report_type == 'module':
        scope_label = f'the "{area_name}" module' if area_name else "this module"
    elif report_type == 'final':
        scope_label = "the entire curriculum"
    else:
        scope_label = "this study period"

    if accuracy >= 90:
        opening = f"Exceptional work! Across {scope_label}, the student achieved {accuracy:.1f}% accuracy over {total_questions} questions, showcasing confident command of the material."
    elif accuracy >= 75:
        opening = f"Great progress! The student reached {accuracy:.1f}% accuracy over {total_questions} questions in {scope_label}, signalling a strong grasp with room to grow."
    elif accuracy >= 60:
        opening = f"A solid foundation has been laid. With {accuracy:.1f}% accuracy across {total_questions} questions in {scope_label}, the learner is ready to refine their technique."
    else:
        opening = f"The path forward is clear. Achieving {accuracy:.1f}% accuracy across {total_questions} questions in {scope_label} reveals the areas where renewed focus will spark improvement."

    analysis_text = (
        f"The student converted {analysis_data['correct_count']} answers into correct responses and gathered insight from the remaining challenges."
    )

    if weak_points:
        suggestion_sentences = []
        for wp in weak_points:
            suggestion_sentences.append(
                f"Revisit {wp['knowledge_point']}, where accuracy was {wp['accuracy']:.1f}% ({wp['correct']} correct out of {wp['total']}). Review the lesson notes and attempt fresh practice questions to strengthen recall."
            )
        advice_text = " ".join(suggestion_sentences)
    else:
        advice_text = "Every tracked knowledge point was mastered. Reinforce that knowledge with spaced review and explore advanced variations to stretch understanding."

    closing = "Maintain this curiosity and discipline; the Arcane Academy awaits the next breakthrough."

    return " ".join([opening, analysis_text, advice_text, closing])

def create_report_payload(student_id, records, report_type, area_id=None, metadata=None):
    # For final reports, group by subject and chapter
    group_by_subject_chapter = (report_type == 'final')
    analysis_data = analyze_battle_data(records, group_by_subject_chapter=group_by_subject_chapter)
    if not analysis_data:
        return None

    area_name = get_area_display_name(area_id) if area_id else None
    ai_summary = generate_ai_report(analysis_data, student_id, report_type=report_type, area_name=area_name)
    generated_at = datetime.now().isoformat()

    if report_type == 'module':
        title = f"{area_name or area_id} Battle Report"
        subtitle = f"Accuracy {analysis_data['accuracy']:.1f}% • {analysis_data['correct_count']} correct out of {analysis_data['total_questions']} questions"
    elif report_type == 'final':
        title = "Grand Mastery Summary"
        subtitle = f"Completed {analysis_data['total_questions']} questions across all modules with {analysis_data['accuracy']:.1f}% accuracy"
    else:
        title = "Performance Snapshot"
        subtitle = f"Accuracy {analysis_data['accuracy']:.1f}% • {analysis_data['correct_count']}/{analysis_data['total_questions']} correct"

    report = {
        'report_id': f"report_{uuid4().hex}",
        'student_id': student_id,
        'type': report_type,
        'area_id': area_id,
        'area_name': area_name,
        'title': title,
        'subtitle': subtitle,
        'generated_at': generated_at,
        'analysis': analysis_data,
        'ai_summary': ai_summary
    }

    if metadata:
        report['metadata'] = metadata

    return report

def store_report(student_id, report, replace_type=None, replace_area=None):
    reports = student_reports.setdefault(student_id, [])

    if replace_type:
        reports = [
            r for r in reports
            if not (
                r.get('type') == replace_type and
                (replace_area is None or r.get('area_id') == replace_area)
            )
        ]
        student_reports[student_id] = reports

    reports.append(report)
    reports.sort(key=lambda r: r['generated_at'], reverse=True)
    student_reports[student_id] = reports
    return report

@app.route('/api/reports/generate-area', methods=['POST'])
def generate_module_report():
    """Generate and store a module-level report after a battle"""
    try:
        data = request.get_json()
        student_id = data.get('student_id', 'default_student')
        area_id = data.get('area_id')

        if not area_id:
            return jsonify({'error': 'area_id is required'}), 400

        records = [
            record for record in battle_records.get(student_id, [])
            if record.get('area_id') == area_id
        ]

        if not records:
            return jsonify({'error': 'No battle records found for this module'}), 400

        report = create_report_payload(student_id, records, report_type='module', area_id=area_id)
        if not report:
            return jsonify({'error': 'Unable to analyze battle data'}), 500

        store_report(student_id, report, replace_type='module', replace_area=area_id)
        return jsonify(report)

    except Exception as e:
        print(f"❌ Failed to generate module report: {str(e)}")
        return jsonify({'error': f'Failed to generate module report: {str(e)}'}), 500

@app.route('/api/reports/generate-final', methods=['POST'])
def generate_final_report():
    """Generate and store the final cumulative report"""
    try:
        data = request.get_json()
        student_id = data.get('student_id', 'default_student')

        records = battle_records.get(student_id, [])
        if not records:
            return jsonify({'error': 'No battle records found for this student'}), 400

        total_modules = len([aid for aid in game_state['areas'] if aid != 'start'])
        completed_modules = sum(
            1 for aid, area in game_state['areas'].items()
            if aid != 'start' and area.get('completed')
        )

        metadata = {
            'total_modules': total_modules,
            'completed_modules': completed_modules
        }

        report = create_report_payload(
            student_id,
            records,
            report_type='final',
            area_id=None,
            metadata=metadata
        )

        if not report:
            return jsonify({'error': 'Unable to analyze battle data'}), 500

        store_report(student_id, report, replace_type='final')
        return jsonify(report)

    except Exception as e:
        print(f"❌ Failed to generate final report: {str(e)}")
        return jsonify({'error': f'Failed to generate final report: {str(e)}'}), 500

@app.route('/api/reports/generate-subject-final', methods=['POST'])
def generate_subject_final_report():
    """Generate final report for a specific subject and save to file"""
    try:
        data = request.get_json()
        student_id = data.get('student_id', 'default_student')
        area_id = data.get('area_id')
        subject = data.get('subject', 'Unknown Subject')

        if not area_id:
            return jsonify({'error': 'area_id is required'}), 400

        # Get all records for areas of this subject
        subject_areas = []
        for aid, area in game_state['areas'].items():
            if aid == 'start' or aid == area_id:
                continue  # Skip start area and the final destination area itself
            area_subject = None
            course_info = course_library.get(aid)
            if course_info:
                area_subject = course_info.get('parent_course', course_info.get('subject', ''))
            elif area.get('parent_subject'):
                area_subject = area.get('parent_subject')
            
            # Normalize subject names for comparison (handle "Subject: Chapter" format)
            if area_subject:
                # Extract subject part before colon if exists
                area_subject_clean = area_subject.split(':')[0].strip() if ':' in area_subject else area_subject.strip()
                subject_clean = subject.split(':')[0].strip() if ':' in subject else subject.strip()
                if area_subject_clean.lower() == subject_clean.lower():
                    subject_areas.append(aid)
        
        print(f"📊 Found {len(subject_areas)} areas for subject '{subject}': {subject_areas}")

        # Filter records for this subject's areas
        records = [
            record for record in battle_records.get(student_id, [])
            if record.get('area_id') in subject_areas
        ]

        if not records:
            return jsonify({'error': 'No battle records found for this subject'}), 400

        # Generate report
        analysis_data = analyze_battle_data(records, group_by_subject_chapter=True)
        if not analysis_data:
            return jsonify({'error': 'Unable to analyze battle data'}), 500

        area_name = f"{subject} - Final Report"
        ai_summary = generate_ai_report(analysis_data, student_id, report_type='final', area_name=area_name)
        generated_at = datetime.now().isoformat()

        report = {
            'report_id': f"report_{uuid4().hex}",
            'student_id': student_id,
            'type': 'subject_final',
            'area_id': area_id,
            'area_name': area_name,
            'subject': subject,
            'title': f"{subject} - Completion Summary",
            'subtitle': f"Completed {analysis_data['total_questions']} questions with {analysis_data['accuracy']:.1f}% accuracy",
            'generated_at': generated_at,
            'analysis': analysis_data,
            'ai_summary': ai_summary
        }

        # Store in memory
        store_report(student_id, report, replace_type='subject_final', replace_area=area_id)

        # Save to file for teacher access
        save_report_to_file(report)

        return jsonify(report)

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Failed to generate subject final report: {str(e)}")
        print(error_trace)
        return jsonify({'error': f'Failed to generate subject final report: {str(e)}'}), 500

def save_report_to_file(report):
    """Save report to file system for teacher access (both JSON and PDF)"""
    try:
        REPORTS_FOLDER = os.path.join(os.path.dirname(__file__), 'reports')
        if not os.path.exists(REPORTS_FOLDER):
            os.makedirs(REPORTS_FOLDER)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON version
        filename_json = f"report_{report['report_id']}_{timestamp}.json"
        filepath_json = os.path.join(REPORTS_FOLDER, filename_json)
        with open(filepath_json, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON report saved: {filepath_json}")

        # Save PDF version
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.lib.colors import HexColor
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.enums import TA_CENTER
            
            filename_pdf = f"report_{report['report_id']}_{timestamp}.pdf"
            filepath_pdf = os.path.join(REPORTS_FOLDER, filename_pdf)
            
            doc = SimpleDocTemplate(filepath_pdf, pagesize=A4,
                                   rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=72)
            
            story = []
            styles = getSampleStyleSheet()
            
            # Magic Academy themed styles
            title_style = ParagraphStyle(
                'MagicTitle',
                parent=styles['Heading1'],
                fontSize=26,
                textColor=HexColor('#2c3e50'),
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            subtitle_style = ParagraphStyle(
                'MagicSubtitle',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=HexColor('#7f8c8d'),
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Oblique'
            )
            
            heading_style = ParagraphStyle(
                'MagicHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=HexColor('#34495e'),
                spaceAfter=12,
                spaceBefore=20,
                fontName='Helvetica-Bold'
            )
            
            body_style = ParagraphStyle(
                'MagicBody',
                parent=styles['Normal'],
                fontSize=11,
                textColor=HexColor('#2c3e50'),
                spaceAfter=12,
                leading=16,
                fontName='Helvetica'
            )
            
            # Title
            title = report.get('title', 'Course Completion Certificate')
            story.append(Paragraph(title, title_style))
            
            # Subtitle
            if 'subtitle' in report:
                story.append(Paragraph(report['subtitle'], subtitle_style))
            
            # Subject and date
            story.append(Spacer(1, 0.2*inch))
            if 'subject' in report:
                story.append(Paragraph(f"<b>Subject:</b> {report['subject']}", body_style))
            
            gen_date = datetime.fromisoformat(report.get('generated_at', datetime.now().isoformat()))
            story.append(Paragraph(f"<b>Date:</b> {gen_date.strftime('%B %d, %Y at %I:%M %p')}", body_style))
            
            story.append(Spacer(1, 0.3*inch))
            
            # AI Summary (main content)
            if 'ai_summary' in report and report['ai_summary']:
                summary_paragraphs = report['ai_summary'].split('\n\n')
                for para in summary_paragraphs:
                    para = para.strip()
                    if para:
                        story.append(Paragraph(para.replace('\n', '<br/>'), body_style))
                        story.append(Spacer(1, 0.15*inch))
            
            # Performance Statistics
            if 'analysis' in report:
                analysis = report['analysis']
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("Performance Statistics", heading_style))
                if 'total_questions' in analysis:
                    story.append(Paragraph(f"<b>Total Questions Completed:</b> {analysis['total_questions']}", body_style))
                if 'accuracy' in analysis:
                    story.append(Paragraph(f"<b>Overall Mastery:</b> {analysis['accuracy']:.1f}%", body_style))
                if 'correct_count' in analysis:
                    story.append(Paragraph(f"<b>Correct Answers:</b> {analysis['correct_count']} out of {analysis.get('total_questions', 'N/A')}", body_style))
            
            doc.build(story)
            print(f"📄 PDF report saved: {filepath_pdf}")
            
        except ImportError:
            print(f"⚠️ ReportLab not installed, skipping PDF generation")
        except Exception as pdf_error:
            print(f"⚠️ PDF generation failed: {str(pdf_error)}")

        return True
    except Exception as e:
        print(f"❌ Failed to save report to file: {str(e)}")
        return False

@app.route('/api/reports/<report_id>/download-pdf', methods=['GET'])
def download_report_pdf(report_id):
    """Download a report as styled PDF"""
    import sys
    print(f"🔍 Python path: {sys.executable}")
    print(f"🔍 Python version: {sys.version}")
    
    # Check if reportlab is available
    try:
        import reportlab
        print(f"✅ ReportLab found at: {reportlab.__file__}")
    except ImportError as e:
        print(f"❌ ReportLab import failed: {str(e)}")
        print(f"🔍 Python executable: {sys.executable}")
        print(f"🔍 Python path: {sys.path[:3]}")
        return jsonify({
            'error': f'ReportLab library not installed. Python: {sys.executable}. Please activate virtual environment and install with: pip install reportlab'
        }), 500
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.lib.colors import HexColor
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_CENTER
        from flask import send_file
        from io import BytesIO
        
        # Find report in student_reports
        report = None
        for student_id, reports_list in student_reports.items():
            for r in reports_list:
                if r.get('report_id') == report_id:
                    report = r
                    break
            if report:
                break
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=72)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Magic Academy themed styles
        title_style = ParagraphStyle(
            'MagicTitle',
            parent=styles['Heading1'],
            fontSize=26,
            textColor=HexColor('#2c3e50'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'MagicSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#7f8c8d'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
        
        heading_style = ParagraphStyle(
            'MagicHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#34495e'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'MagicBody',
            parent=styles['Normal'],
            fontSize=11,
            textColor=HexColor('#2c3e50'),
            spaceAfter=12,
            leading=16,
            fontName='Helvetica'
        )
        
        # Title
        story.append(Paragraph(report.get('title', 'Course Completion Certificate'), title_style))
        if 'subtitle' in report:
            story.append(Paragraph(report['subtitle'], subtitle_style))
        
        story.append(Spacer(1, 0.2*inch))
        if 'subject' in report:
            story.append(Paragraph(f"<b>Subject:</b> {report['subject']}", body_style))
        
        gen_date = datetime.fromisoformat(report.get('generated_at', datetime.now().isoformat()))
        story.append(Paragraph(f"<b>Date:</b> {gen_date.strftime('%B %d, %Y at %I:%M %p')}", body_style))
        
        story.append(Spacer(1, 0.3*inch))
        
        # AI Summary
        if 'ai_summary' in report and report['ai_summary']:
            summary_paragraphs = report['ai_summary'].split('\n\n')
            for para in summary_paragraphs:
                para = para.strip()
                if para:
                    story.append(Paragraph(para.replace('\n', '<br/>'), body_style))
                    story.append(Spacer(1, 0.15*inch))
        
        # Performance Statistics
        if 'analysis' in report:
            analysis = report['analysis']
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("Performance Statistics", heading_style))
            if 'total_questions' in analysis:
                story.append(Paragraph(f"<b>Total Questions Completed:</b> {analysis['total_questions']}", body_style))
            if 'accuracy' in analysis:
                story.append(Paragraph(f"<b>Overall Mastery:</b> {analysis['accuracy']:.1f}%", body_style))
            if 'correct_count' in analysis:
                story.append(Paragraph(f"<b>Correct Answers:</b> {analysis['correct_count']} out of {analysis.get('total_questions', 'N/A')}", body_style))
        
        doc.build(story)
        buffer.seek(0)
        
        # Return PDF
        subject_name = report.get('subject', 'Course').replace(' ', '_')
        filename = f"{subject_name}_Final_Report_{report_id[:8]}.pdf"
        
        print(f"📄 Returning PDF: {filename}, size: {buffer.tell()} bytes")
        
        from flask import Response
        buffer.seek(0)
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/pdf'
            }
        )
        
    except ImportError as import_err:
        print(f"❌ ReportLab not installed: {str(import_err)}")
        return jsonify({'error': 'ReportLab library not installed. Please install it with: pip install reportlab'}), 500
    except Exception as e:
        print(f"❌ Failed to generate PDF: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        print(error_trace)
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

@app.route('/api/reports/<student_id>', methods=['GET'])
def list_reports(student_id):
    """Return all stored reports for the student"""
    reports = student_reports.get(student_id, [])
    return jsonify({'reports': reports})

@app.route('/api/reports/<student_id>/<report_id>', methods=['GET'])
def get_report(student_id, report_id):
    """Return a single stored report"""
    reports = student_reports.get(student_id, [])
    for report in reports:
        if report.get('report_id') == report_id:
            return jsonify(report)
    return jsonify({'error': 'Report not found'}), 404

@app.route('/api/generate-report/<student_id>', methods=['GET'])
def generate_report(student_id):
    """Generate a one-off snapshot report without storing it"""
    try:
        records = battle_records.get(student_id, [])

        if len(records) < 1:
            return jsonify({'error': 'Not enough data. Complete at least one battle before generating a report.'}), 400

        report = create_report_payload(student_id, records, report_type='snapshot')
        if not report:
            return jsonify({'error': 'Unable to analyze battle data'}), 500

        report['total_battles'] = len(records)
        return jsonify(report)

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print("\n❌ Snapshot report generation failed:")
        print(error_trace)
        return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500

@app.route('/api/check-report-eligibility/<student_id>', methods=['GET'])
def check_report_eligibility(student_id):
    """Check whether there is enough data to review reports"""
    records = battle_records.get(student_id, [])
    total_battles = len(records)

    return jsonify({
        'eligible': total_battles >= 1,
        'total_battles': total_battles,
        'required_battles': 1,
        'suggestion': 'Complete at least one battle to unlock reports.' if total_battles < 1 else 'Reports are ready to view.'
    })

@app.route('/api/teacher/reports', methods=['GET'])
def list_all_reports():
    """List all saved reports from the reports folder for teacher access"""
    try:
        REPORTS_FOLDER = os.path.join(os.path.dirname(__file__), 'reports')
        print(f"🔍 Looking for reports in: {REPORTS_FOLDER}")
        if not os.path.exists(REPORTS_FOLDER):
            print(f"⚠️ Reports folder does not exist: {REPORTS_FOLDER}")
            return jsonify({'reports': [], 'total': 0})
        print(f"✅ Reports folder exists, listing files...")
        
        reports = []
        # Read all JSON report files
        json_files = [f for f in os.listdir(REPORTS_FOLDER) if f.endswith('.json')]
        print(f"📁 Found {len(json_files)} JSON report files")
        for filename in json_files:
            filepath = os.path.join(REPORTS_FOLDER, filename)
            try:
                print(f"📄 Reading report: {filename}")
                with open(filepath, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                # Extract relevant info for teacher view
                report_info = {
                    'report_id': report_data.get('report_id'),
                    'student_id': report_data.get('student_id', 'unknown'),
                    'type': report_data.get('type', 'unknown'),
                    'subject': report_data.get('subject', 'Unknown Subject'),
                    'title': report_data.get('title', 'Untitled Report'),
                    'subtitle': report_data.get('subtitle', ''),
                    'generated_at': report_data.get('generated_at'),
                    'area_name': report_data.get('area_name', ''),
                    'accuracy': report_data.get('analysis', {}).get('accuracy', 0),
                    'total_questions': report_data.get('analysis', {}).get('total_questions', 0),
                    'filename': filename,
                    'pdf_filename': filename.replace('.json', '.pdf') if filename.endswith('.json') else None
                }
                reports.append(report_info)
            except Exception as e:
                print(f"⚠️ Failed to read report file {filename}: {str(e)}")
                continue
        
        # Sort by generated_at (newest first)
        reports.sort(key=lambda x: x.get('generated_at', ''), reverse=True)
        
        print(f"✅ Returning {len(reports)} reports to teacher portal")
        return jsonify({
            'reports': reports,
            'total': len(reports)
        })
    except Exception as e:
        print(f"❌ Failed to list reports: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'Failed to list reports: {str(e)}'}), 500

@app.route('/api/teacher/reports/<report_id>/download', methods=['GET'])
def download_teacher_report(report_id):
    """Download a report PDF for teacher"""
    try:
        REPORTS_FOLDER = os.path.join(os.path.dirname(__file__), 'reports')
        if not os.path.exists(REPORTS_FOLDER):
            return jsonify({'error': 'Reports folder not found'}), 404
        
        # Find PDF file matching report_id
        pdf_filename = None
        for filename in os.listdir(REPORTS_FOLDER):
            if filename.startswith(f'report_{report_id}') and filename.endswith('.pdf'):
                pdf_filename = filename
                break
        
        if not pdf_filename:
            return jsonify({'error': 'PDF report not found'}), 404
        
        filepath = os.path.join(REPORTS_FOLDER, pdf_filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'PDF file not found'}), 404
        
        from flask import send_file
        return send_file(filepath, mimetype='application/pdf', as_attachment=True, download_name=pdf_filename)
        
    except Exception as e:
        print(f"❌ Failed to download report: {str(e)}")
        return jsonify({'error': f'Failed to download report: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    print(f"Starting game server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug)
