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
import threading
import requests

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
    """Compatibility endpoint: route frontend Gemini calls to local Ollama."""
    try:
        data = request.get_json(silent=True) or {}
        prompt = (data.get('prompt') or '').strip()
        if not prompt:
            return jsonify({'error': 'prompt is required'}), 400

        # Ignore requested cloud model and always use local model.
        text = call_ollama_text(prompt=prompt, model='qwen2.5', timeout=90)
        return jsonify({'response': text, 'provider': 'ollama', 'model': 'qwen2.5'})
    except requests.Timeout:
        return jsonify({'error': 'Local model timeout'}), 504
    except Exception as e:
        return jsonify({'error': f'Local model request failed: {str(e)}'}), 502

# Text extraction function
def extract_text_from_file(file_path):
    """Extract text from file (supports PDF, TXT, MD)"""
    # Safely get file extension
    if '.' in file_path:
        file_ext = file_path.rsplit('.', 1)[1].lower()
    else:
        return "Error: File has no extension"
    
    try:
        # TXT and MD files: read directly
        if file_ext in ['txt', 'md']:
            print(f"📄 Reading text file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            print(f"✅ Text read successfully, length: {len(text)} characters")
            return text
        
        # PDF files: use PyPDF2
        elif file_ext == 'pdf':
            print(f"📄 Reading PDF file: {file_path}")
            import PyPDF2
            
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                print(f"📖 PDF has {num_pages} pages")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    text += page_text + "\n"
                    print(f"   Page {page_num + 1}/{num_pages}, extracted {len(page_text)} characters")
            
            print(f"✅ PDF read successfully, total {len(text)} characters")
            return text
        
        else:
            return f"Error: Unsupported file format {file_ext}"
    
    except UnicodeDecodeError:
        # If UTF-8 fails, try other encodings
        try:
            with open(file_path, 'r', encoding='gbk') as file:
                text = file.read()
            print(f"✅ Successfully read using GBK encoding")
            return text
        except:
            return "Error: Unable to identify file encoding, please use UTF-8 or GBK encoding"
    
    except ImportError:
        return "Error: PyPDF2 library not installed, please run: pip install PyPDF2"
    except Exception as e:
        return f"Error: Unable to extract text - {str(e)}"

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

def extract_first_json_object(text: str):
    """Best-effort JSON extraction from LLM responses."""
    if not text:
        return None
    match = re.search(r'\{[\s\S]*\}', text)
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

    # Minimum meaningful alpha content
    alpha_words = [w for w in re.split(r'\W+', t) if len(w) >= 3 and w.isalpha()]
    if len(alpha_words) < 2:
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
    Stage 1 (single responsibility): extract concept + definition + key facts only.
    """
    prompt = f"""
You are a knowledge modeling extractor.
Process only CHUNK {chunk_idx}/{total_chunks}.

Definition of "knowledge point":
- MUST be one of: concept, definition, principle, measurable fact.
- MUST NOT be: question, slide title, discussion topic, example list.

Task:
1) Classify chunk items as concept|example|question|section.
2) Keep all extracted items in output with explicit type.
3) For examples, set belongs_to to the related concept.
4) Preserve concrete details and numbers exactly from chunk.
5) No topic classification and no concept-relationship inference.

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
        {{
          "fact": "factual statement",
          "numbers": ["exact numbers/formulas if present"],
          "source_quote": "exact supporting quote"
        }}
      ]
    }}
  ]
}}

CHUNK:
\"\"\"
{chunk_text}
\"\"\"
"""
    try:
        llm_text = call_ollama_text(prompt=prompt, model='qwen2.5', timeout=90)
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

            # Keep only concept as knowledge nodes. Examples are attached later.
            if item_type == 'concept':
                concept = str(c.get('concept', '')).strip()
                if not concept or looks_like_non_concept_label(concept):
                    continue
                key = normalize_concept_key(concept)
                if key not in concept_map:
                    concept_map[key] = {
                        'concept': concept,
                        'definition': {'text': '', 'source_quotes': []},
                        'examples': [],
                        'key_facts': [],
                        'relationships': []
                    }
                definition = str(c.get('definition', '')).strip()
                definition_quote = str(c.get('definition_quote', '')).strip()
                if len(definition) > len(concept_map[key]['definition'].get('text', '')):
                    concept_map[key]['definition']['text'] = definition
                concept_map[key]['definition']['source_quotes'] = _dedupe_str_list(
                    concept_map[key]['definition'].get('source_quotes', []) + [definition_quote]
                )

                key_facts_raw = c.get('key_facts', [])
                if isinstance(key_facts_raw, list):
                    for f in key_facts_raw:
                        if not isinstance(f, dict):
                            continue
                        fact = str(f.get('fact', '')).strip()
                        src = str(f.get('source_quote', '')).strip()
                        nums = f.get('numbers', [])
                        if not isinstance(nums, list):
                            nums = []
                        nums = _dedupe_str_list(nums)
                        if fact or src:
                            concept_map[key]['key_facts'].append({
                                'fact': fact,
                                'numbers': nums,
                                'source_quote': src
                            })
            elif item_type == 'example':
                pending_examples.append({
                    'belongs_to': str(c.get('belongs_to', '')).strip(),
                    'text': str(c.get('example_text', '')).strip(),
                    'source_quote': str(c.get('example_quote', '')).strip()
                })

        # Attach examples to concept nodes only (discard orphan examples)
        for ex in pending_examples:
            belongs_to = ex.get('belongs_to', '')
            text = ex.get('text', '')
            quote = ex.get('source_quote', '')
            if not belongs_to or (not text and not quote):
                continue
            key = normalize_concept_key(belongs_to)
            if key in concept_map:
                concept_map[key]['examples'].append({
                    'text': text,
                    'source_quote': quote
                })

        normalized = list(concept_map.values())
        return {'chunk_index': chunk_idx, 'concepts': normalized} if normalized else None
    except Exception as e:
        print(f"⚠️ Chunk {chunk_idx} extraction failed: {e}")
        return None

def deterministic_merge_concepts(chunk_summaries):
    """
    Stage 2a deterministic merge (code, not LLM): dedupe + preserve details.
    """
    merged = {}
    for summary in chunk_summaries:
        for c in summary.get('concepts', []):
            concept = str(c.get('concept', '')).strip()
            if not concept:
                continue
            key = normalize_concept_key(concept)
            if key not in merged:
                merged[key] = {
                    'id': f'concept_{uuid4().hex[:10]}',
                    'concept': concept,
                    'topic': 'General',
                    'level': 'intermediate',
                    'definition': {'text': '', 'source_quotes': []},
                    'examples': [],
                    'key_facts': [],
                    'relationships': []
                }
            item = merged[key]
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
    return list(merged.values())

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
        llm_text = call_ollama_text(prompt=prompt, model='qwen2.5', timeout=90)
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
    Stage 3 LLM for relationships only.
    """
    if not concepts:
        return []
    brief = []
    for c in concepts[:220]:
        brief.append({
            'concept': c.get('concept', ''),
            'definition': c.get('definition', {}).get('text', '')
        })
    prompt = f"""
Build relationships between concepts only.
No classification, no rewriting definitions.

Return JSON only:
{{
  "relationships": [
    {{"source_concept": "A", "type": "depends-on|part-of|uses|causes|is-a|other", "target_concept": "B", "evidence": "short evidence phrase"}}
  ]
}}

CONCEPTS:
{json.dumps(brief, ensure_ascii=False)}
"""
    try:
        llm_text = call_ollama_text(prompt=prompt, model='qwen2.5', timeout=90)
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

def _area_position(index: int):
    return {'x': 120 + index * 280, 'y': 300 + ((index % 2) * 120 - 60)}

def build_course_path_json(subject, file_name, concepts, topics):
    """
    Build teacher-agent friendly course path JSON:
    Course -> Area -> Concept Node
    """
    course_code = _infer_course_code(subject, file_name)
    topic_to_concepts = {}
    for c in concepts:
        topic = str(c.get('topic', 'General')).strip() or 'General'
        topic_to_concepts.setdefault(topic, []).append(c)

    areas = []
    concept_id_map = {}

    # Stable per-topic ordering by level then concept title
    level_rank = {'beginner': 1, 'intermediate': 2, 'advanced': 3}
    sorted_topics = sorted(topic_to_concepts.keys(), key=lambda x: x.lower())

    for i, topic in enumerate(sorted_topics, start=1):
        concept_list = topic_to_concepts[topic]
        concept_list = sorted(
            concept_list,
            key=lambda c: (level_rank.get(str(c.get('level', 'intermediate')).lower(), 2), str(c.get('concept', '')).lower())
        )
        area_id = f'area_{i}'
        difficulty = 2
        if concept_list:
            avg = sum(level_rank.get(str(c.get('level', 'intermediate')).lower(), 2) for c in concept_list) / len(concept_list)
            difficulty = 1 if avg < 1.7 else (3 if avg > 2.3 else 2)

        area_obj = {
            'id': area_id,
            'name': topic,
            'description': f'Concept cluster for {topic}',
            'difficulty': difficulty,
            'position': _area_position(i - 1),
            'concept_nodes': []
        }

        for j, c in enumerate(concept_list, start=1):
            cid = str(c.get('id', '')).strip() or f'{area_id}_concept_{j}'
            title = str(c.get('concept', '')).strip() or f'Concept {j}'
            definition = str((c.get('definition') or {}).get('text', '')).strip()
            facts = c.get('key_facts', []) if isinstance(c.get('key_facts'), list) else []
            rels = c.get('relationships', []) if isinstance(c.get('relationships'), list) else []
            keywords = _dedupe_str_list(
                [title] +
                [str(f.get('fact', '')).strip() for f in facts if isinstance(f, dict)]
            )[:8]

            importance = 3
            level = str(c.get('level', 'intermediate')).lower()
            if level == 'beginner':
                importance = 3
            elif level == 'advanced':
                importance = 5
            else:
                importance = 4
            if len(facts) >= 3:
                importance = min(5, importance + 1)

            concept_node = {
                'concept_id': cid,
                'title': title,
                'summary': definition[:240] if definition else '',
                'importance': importance,
                'prerequisites': [],
                'keywords': keywords,
                'quiz': [],
                'npc': {
                    'role': 'Tutor',
                    'style': 'Socratic and concise'
                },
                'tasks': []
            }

            # Lightweight default quiz/task templates for teacher-agent refinement.
            concept_node['quiz'].append({
                'type': 'single_choice',
                'prompt': f'Which statement best describes "{title}"?',
                'options': [],
                'answer': None
            })
            concept_node['tasks'].append({
                'type': 'explain',
                'prompt': f'Explain "{title}" with one concrete example.'
            })

            area_obj['concept_nodes'].append(concept_node)
            concept_id_map[normalize_concept_key(title)] = cid

        areas.append(area_obj)

    # Fill prerequisites from relationships if possible.
    title_to_node = {}
    for area in areas:
        for node in area.get('concept_nodes', []):
            title_to_node[normalize_concept_key(node.get('title', ''))] = node

    for c in concepts:
        src_key = normalize_concept_key(c.get('concept', ''))
        src_node = title_to_node.get(src_key)
        if not src_node:
            continue
        rels = c.get('relationships', [])
        if not isinstance(rels, list):
            continue
        prereq_ids = []
        for r in rels:
            if not isinstance(r, dict):
                continue
            rel_type = str(r.get('type', '')).strip().lower()
            target = str(r.get('target_concept', '')).strip()
            if rel_type in ['depends-on', 'part-of', 'uses', 'is-a'] and target:
                tid = concept_id_map.get(normalize_concept_key(target))
                if tid:
                    prereq_ids.append(tid)
        src_node['prerequisites'] = _dedupe_str_list(prereq_ids)

    return {
        'course': course_code,
        'areas': areas
    }

def build_course_path_schema_template():
    """Schema template for teacher-side agent output contract."""
    return {
        'course': 'INFO4444',
        'areas': [
            {
                'id': 'area_1',
                'name': 'AI Strategy',
                'description': 'How firms adopt AI',
                'difficulty': 2,
                'position': {'x': 120, 'y': 300},
                'concept_nodes': [
                    {
                        'concept_id': 'concept_12',
                        'title': 'Dominant Design',
                        'summary': 'Core idea and practical significance.',
                        'importance': 5,
                        'prerequisites': ['concept_8'],
                        'keywords': ['design', 'standard', 'adoption'],
                        'quiz': [
                            {
                                'type': 'single_choice',
                                'prompt': 'Which statement best captures Dominant Design?',
                                'options': ['A', 'B', 'C', 'D'],
                                'answer': 0
                            }
                        ],
                        'npc': {
                            'role': 'Tutor',
                            'style': 'Socratic and concise'
                        },
                        'tasks': [
                            {
                                'type': 'explain',
                                'prompt': 'Explain Dominant Design with a real case.'
                            }
                        ]
                    }
                ]
            }
        ]
    }

def build_teacher_course_path_prompt(subject, file_name):
    course_code = _infer_course_code(subject, file_name)
    return (
        "You are a teacher-side curriculum path planner.\n"
        "Generate JSON only (no markdown, no explanation) using this exact hierarchy:\n"
        "Course -> Area -> Concept Node.\n"
        "Hard constraints:\n"
        "1) Root fields: course, areas.\n"
        "2) areas must be an array of objects with: id,name,description,difficulty,position,concept_nodes.\n"
        "3) concept_nodes must include: concept_id,title,summary,importance,prerequisites,keywords,quiz,npc,tasks.\n"
        "4) prerequisites must reference existing concept_id values.\n"
        "5) difficulty in [1,2,3], importance in [1..5].\n"
        "6) Keep content concrete and course-specific; avoid placeholders.\n"
        f"Target course code: {course_code}\n"
    )

def validate_course_path_json(course_path):
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

    # Check prerequisite references after collecting all concept IDs.
    for pid in prereq_refs:
        if pid not in concept_ids:
            errors.append(f'prerequisite reference not found: {pid}')

    return len(errors) == 0, errors

def ensure_valid_course_path(candidate, subject, file_name, concepts, topics):
    fallback = build_course_path_json(subject, file_name, concepts, topics)
    ok, errs = validate_course_path_json(candidate)
    if ok:
        return candidate, []
    return fallback, errs

# Use LLM to analyze PDF content and generate course
def generate_course_from_text(text_content, file_name, progress_callback=None):
    """Use LLM to analyze PDF content and generate detailed course knowledge points"""
    thinking_trace = []

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
                        'concept': concept_name,
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
            
            structured_topics = [
                {
                    'topic': metadata.get('category', 'General'),
                    'levels': {
                        'beginner': [c['concept'] for c in structured_concepts if c.get('level') == 'beginner'],
                        'intermediate': [c['concept'] for c in structured_concepts if c.get('level') == 'intermediate'],
                        'advanced': [c['concept'] for c in structured_concepts if c.get('level') == 'advanced']
                    }
                }
            ]
            course_path_candidate = build_course_path_json(
                metadata.get('subject', 'General Course'),
                file_name,
                structured_concepts,
                structured_topics
            )
            course_path, course_path_errors = ensure_valid_course_path(
                course_path_candidate,
                metadata.get('subject', 'General Course'),
                file_name,
                structured_concepts,
                structured_topics
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
                    'pipeline': ['chunk', 'concept_extraction', 'merge', 'structuring'],
                    'concept_index': structured_concepts,
                    'topics': structured_topics
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
        chunks = split_text_into_chunks(text_content, max_chars=1000, overlap_chars=120)
        thinking_trace.append(f"Split material into {len(chunks)} chunks.")
        emit_progress(30, "Chunking content", f"Generated {len(chunks)} chunks.")
        print(f"🧩 Generated {len(chunks)} chunks for local model understanding")

        if not chunks:
            print("⚠️ No chunks generated, falling back")
            return generate_course_fallback(text_content, file_name)

        chunk_summaries = []
        total_chunks = max(len(chunks), 1)
        for idx, chunk in enumerate(chunks, start=1):
            chunk_progress = 30 + int((idx - 1) / total_chunks * 50)
            emit_progress(chunk_progress, "Extracting concepts", f"Processing chunk {idx}/{total_chunks}.")
            thinking_trace.append(f"Analyzing chunk {idx}/{len(chunks)}.")
            print(f"🔍 Summarizing chunk {idx}/{len(chunks)} (chars={len(chunk)})")
            summary = extract_atomic_concepts_from_chunk_llm(chunk, idx, len(chunks))
            if summary and summary.get('concepts'):
                chunk_summaries.append(summary)
                thinking_trace.append(
                    f"Chunk {idx}: extracted {len(summary.get('concepts', []))} atomic concepts."
                )
                print(f"✅ Chunk {idx}: extracted {len(summary.get('concepts', []))} concepts")
            else:
                thinking_trace.append(f"Chunk {idx}: no stable extraction, skipped.")
                print(f"⚠️ Chunk {idx}: no valid points extracted")
            emit_progress(
                30 + int(idx / total_chunks * 50),
                "Extracting concepts",
                f"Completed chunk {idx}/{total_chunks}."
            )

        if not chunk_summaries:
            print("⚠️ No chunk summaries extracted, falling back")
            return generate_course_fallback(text_content, file_name)

        print(f"🧠 Merging {len(chunk_summaries)} chunk summaries (deterministic)...")
        emit_progress(82, "Merging concepts", "Deterministic merge and deduplication.")
        thinking_trace.append("Merged chunk outputs with deterministic deduplication (code-based).")

        merged_concepts = deterministic_merge_concepts(chunk_summaries)
        if merged_concepts:
            thinking_trace.append(f"Deterministic merge retained {len(merged_concepts)} unique concepts.")

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
            c['relationships'] = by_source.get(normalize_concept_key(c.get('concept', '')), [])

        topics = build_topics_from_concepts(merged_concepts)
        materials = build_structured_materials(merged_concepts, max_items=200)

        if merged_concepts:
            thinking_trace.append(
                f"Structured output ready: {len(merged_concepts)} concepts, {len(topics)} topics."
            )
            print(f"✅ Structured extraction successful: {cls.get('subject', 'General Course')}")
            print(f"📚 Final concept count: {len(merged_concepts)}")
            course_path_candidate = build_course_path_json(
                cls.get('subject', 'General Course'),
                file_name,
                merged_concepts,
                topics
            )
            course_path, course_path_errors = ensure_valid_course_path(
                course_path_candidate,
                cls.get('subject', 'General Course'),
                file_name,
                merged_concepts,
                topics
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
                    'pipeline': ['chunk', 'concept_extraction', 'merge', 'structuring'],
                    'concept_index': merged_concepts,
                    'topics': topics
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
                {
                    'course': _infer_course_code("General Course", file_name),
                    'areas': []
                },
                "General Course",
                file_name,
                [],
                []
            )
            return {
                'subject': "General Course",
                'materials': [{'id': f'fallback_{i+1}', 'concept': x, 'topic': 'General', 'level': 'intermediate', 'definition': '', 'facts': []} for i, x in enumerate(flattened[:30])],
                'difficulty': 'medium',
                'category': 'General',
                'topics': [],
                'knowledge_structure': {
                    'pipeline': ['chunk', 'concept_extraction', 'merge', 'structuring'],
                    'concept_index': [],
                    'topics': []
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
            'id': f'fallback_{i}',
            'concept': point,
            'topic': category,
            'level': 'intermediate',
            'definition': {'text': '', 'source_quotes': []},
            'examples': [],
            'key_facts': [],
            'relationships': []
        })
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
            'pipeline': ['chunk', 'concept_extraction', 'merge', 'structuring'],
            'concept_index': fallback_concepts,
            'topics': fallback_topics
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
        
        # Extract text
        text_content = extract_text_from_file(file_path)
        
        if isinstance(text_content, str) and text_content.startswith('Error:'):
            print(f"❌ {text_content}")
            return jsonify({'error': text_content}), 500
        
        print(f"\n✅ Text extraction successful!")
        print(f"📄 Text length: {len(text_content)} characters")
        print(f"📝 First 500 characters preview:")
        print(f"{text_content[:500]}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'message': 'File upload successful',
            'file_path': file_path,
            'file_name': filename,
            'text_content': text_content,
            'text_length': len(text_content)
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n❌ Upload error:")
        print(error_trace)
        return jsonify({'error': f'Upload failed: {str(e)}', 'trace': error_trace}), 500

# Teacher Portal API - Generate course
@app.route('/api/generate-course', methods=['POST'])
def generate_course():
    """Use LLM to analyze PDF content and generate course knowledge points"""
    try:
        data = request.get_json()
        text_content = data.get('text_content', '')
        file_name = data.get('file_name', 'unknown.pdf')
        
        if not text_content:
            return jsonify({'error': 'PDF text content is empty'}), 400
        
        print(f"🤖 Starting course generation, text length: {len(text_content)}")
        
        # Use LLM to generate course
        course_data = generate_course_from_text(text_content, file_name)
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

def _run_generation_job(job_id, text_content, file_name):
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

        course_data = generate_course_from_text(text_content, file_name, progress_callback=progress_cb)
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

        if not text_content:
            return jsonify({'error': 'PDF text content is empty'}), 400

        job_id = f"job_{uuid4().hex}"
        _init_generation_job(job_id)

        worker = threading.Thread(
            target=_run_generation_job,
            args=(job_id, text_content, file_name),
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

        # Strict mode persistence: only keep 3-layer path in file.
        strict_payload = course_data.get('course_path')
        if not _is_strict_course_path_payload(strict_payload):
            strict_payload = {
                'course': _infer_course_code(course_data.get('subject', ''), course_data.get('fileName', '')),
                'areas': []
            }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(strict_payload, f, ensure_ascii=False, indent=2)
        
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
                        if _is_strict_course_path_payload(loaded_data) and not loaded_data.get('subject'):
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
        materials = []
        for item in raw_materials:
            # Ensure every material is a plain string so that regex
            # and chapter parsing logic below will not crash.
            if isinstance(item, str):
                materials.append(item)
            elif isinstance(item, dict):
                # Structured material object from knowledge extractor
                if 'concept' in item:
                    concept = str(item.get('concept', '')).strip()
                    definition = str(item.get('definition', '')).strip()
                    topic = str(item.get('topic', 'General')).strip() or 'General'
                    if concept and definition:
                        materials.append(f"{topic}: {concept}: {definition}")
                    elif concept:
                        materials.append(f"{topic}: {concept}")
                    else:
                        materials.append(str(item))
                # Common pattern from LLM: {"Section Title": "..."}
                elif 'Section Title' in item:
                    materials.append(str(item['Section Title']))
                else:
                    parts = []
                    for k, v in item.items():
                        parts.append(f"{k}: {v}")
                    if parts:
                        materials.append(" | ".join(parts))
            else:
                materials.append(str(item))
        subject = course_data.get('subject', 'Course')
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

        ai_report = call_ollama_text(
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
