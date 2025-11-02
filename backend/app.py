from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import math
import os
from werkzeug.utils import secure_filename
import json
from datetime import datetime
from uuid import uuid4
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure file upload
UPLOAD_FOLDER = 'uploads'
COURSES_FOLDER = 'courses'  # Store generated courses
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md'}  # Support PDF, TXT, and Markdown

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(COURSES_FOLDER):
    os.makedirs(COURSES_FOLDER)

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

    # Supported headers (Chinese and English)
    meta_headers = {'# 课程元信息', '# Course Meta Information'}
    content_headers = {'# 课程内容', '# Course Content'}

    # Metadata key mapping (Chinese and English)
    key_map = {
        '课程名称': 'subject',
        'Course Name': 'subject',
        '类别': 'category',
        'Category': 'category',
        '难度': 'difficulty',
        'Difficulty': 'difficulty',
        '描述': 'description',
        'Description': 'description',
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

# Use LLM to analyze PDF content and generate course
def generate_course_from_text(text_content, file_name):
    """Use LLM to analyze PDF content and generate detailed course knowledge points"""
    
    print(f"\n{'='*60}")
    print(f"🔍 Starting file content analysis")
    print(f"📄 File name: {file_name}")
    print(f"📏 Total characters: {len(text_content)}")
    print(f"📝 Content preview:\n{text_content[:300]}")
    print(f"{'='*60}\n")
    
    # Check if it's structured TXT format (supports Chinese/English markers)
    if (
        ('# 课程元信息' in text_content and '# 课程内容' in text_content)
        or ('# Course Meta Information' in text_content and '# Course Content' in text_content)
    ):
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
            
            return {
                'subject': metadata.get('subject', 'General Course'),
                'materials': detailed_materials if detailed_materials else materials_titles,
                'difficulty': metadata.get('difficulty', 'medium'),
                'category': metadata.get('category', 'General')
            }
    
    print("📋 Using general text analysis...")
    
    # Extract first 8000 characters for analysis (increased sample size)
    text_sample = text_content[:8000] if len(text_content) > 8000 else text_content
    
    prompt = f"""You are a senior professor at the Computer Magic Academy. Carefully read and analyze this course material PDF, then generate detailed course knowledge points.

【Important】You must base your summary of knowledge points on the actual PDF content below. Do not fabricate!

【PDF File Name】: {file_name}

【Complete PDF Content】:
{text_sample}

【Task】:
1. Carefully read the PDF content above
2. Identify the course topic and core concepts
3. Extract 10-15 key knowledge points from the PDF content
4. Each knowledge point must come from the actual PDF content, summarize in your own words

【Output Requirements】:
Strictly output in JSON format, do not include any other text:

{{
  "subject": "Course name determined from PDF content",
  "materials": [
    "Knowledge Point 1: Summary based on PDF content",
    "Knowledge Point 2: Summary based on PDF content",
    "Knowledge Point 3: Summary based on PDF content",
    ...at least 10
  ],
  "difficulty": "easy/medium/hard",
  "category": "Course category"
}}

Only output JSON, no additional text!"""

    # Try calling LLM (using Ollama)
    try:
        import requests
        
        print("🤖 Attempting to call Ollama LLM...")
        
        # Try using Ollama API
        ollama_response = requests.post(
            'http://ollama:11434/api/generate',
            json={
                'model': 'qwen2.5',
                'prompt': prompt,
                'stream': False
            },
            timeout=90
        )
        
        if ollama_response.status_code == 200:
            response_text = ollama_response.json().get('response', '')
            print(f"✅ LLM response successful, length: {len(response_text)}")
            print(f"📝 LLM response preview:\n{response_text[:500]}")
            
            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                course_data = json.loads(json_match.group())
                
                # Verify required fields
                if 'subject' in course_data and 'materials' in course_data:
                    print(f"✅ LLM successfully generated course: {course_data['subject']}")
                    print(f"📚 Number of knowledge points: {len(course_data['materials'])}")
                    return course_data
            else:
                print("⚠️ No valid JSON found in LLM response")
        else:
            print(f"⚠️ LLM response status code: {ollama_response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️ Ollama service not running, using intelligent extraction algorithm")
    except Exception as e:
        print(f"⚠️ LLM call failed: {e}")
    
    # If LLM fails, use intelligent extraction based on PDF content
    print("\n🔄 Using intelligent extraction algorithm to analyze PDF content...")
    return generate_course_fallback(text_content, file_name)

def generate_course_fallback(text_content, file_name):
    """When LLM is unavailable, intelligently extract knowledge points based on PDF content"""
    
    print(f"\n{'='*60}")
    print(f"📊 Intelligent extraction algorithm starting")
    print(f"📄 Text length to analyze: {len(text_content)} characters")
    print(f"{'='*60}\n")
    
    # Simple course topic recognition
    keywords_map = {
        # Chinese keywords
        '网络': ('Computer Networks', 'easy', 'Networking'),
        '数据结构': ('Data Structures and Algorithms', 'medium', 'Algorithms'),
        '算法': ('Data Structures and Algorithms', 'medium', 'Algorithms'),
        '操作系统': ('Operating Systems', 'medium', 'Systems'),
        '数据库': ('Database Systems', 'medium', 'Data Management'),
        '机器学习': ('Machine Learning Basics', 'hard', 'AI'),
        '人工智能': ('Artificial Intelligence', 'hard', 'AI'),
        '软件工程': ('Software Engineering', 'medium', 'Software Engineering'),
        # English keywords
        'python': ('Python Programming', 'easy', 'Programming Language'),
        'java': ('Java Programming', 'medium', 'Programming Language'),
        'mathematics': ('Elementary Mathematics', 'easy', 'Basic Mathematics'),
        'math': ('Elementary Mathematics', 'easy', 'Basic Mathematics'),
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
            re.match(r'^第[一二三四五六七八九十\d]+[章节课]', line) or
            any(kw in line for kw in ['定义', '概念', '原理', '方法', '技术', '算法', '协议', '模型', '特点', '优势'])):
            if 15 < len(line) < 150:  # Appropriate length
                clean_line = re.sub(r'^[\d\.\)、•·►▪■□\s]+', '', line)  # Remove prefix
                if clean_line and not clean_line.startswith('第'):
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
                any(kw in sent for kw in ['是', '为', '指', '包括', '分为', '主要', '可以', '能够', '用于', '实现', '通过'])):
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
                if 20 < len(first_sent) < 150:
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
        if m_clean and m_clean not in seen and len(m_clean) > 10:
            seen.add(m_clean)
            unique_materials.append(m_clean)
    
    print(f"   ✓ After deduplication: {len(unique_materials)} unique knowledge points")
    
    # 5. If still insufficient, add descriptive knowledge points based on PDF content
    if len(unique_materials) < 10:
        print("🔍 Step 5: Search keyword patterns...")
        # Extract keywords to generate knowledge points
        key_terms = []
        for keyword in ['定义', '概念', '原理', '方法', '算法', '协议', '模型', '架构', '特征', '应用']:
            pattern = f'{keyword}[：:，,]?([^。！？\n]{{10,80}})'
            matches = re.findall(pattern, text_content)
            for match in matches[:2]:
                key_terms.append(f"{keyword}: {match.strip()}")
        
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
            if 30 < len(sent) < 200:
                score = sum(1 for kw in ['技术', '方法', '系统', '算法', '模型', '架构', '协议', '机制'] if kw in sent)
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
    
    return {
        'subject': subject,
        'materials': final_materials[:15],
        'difficulty': difficulty,
        'category': category
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
        
        print(f"✅ Course generation successful: {course_data.get('subject')}")
        print(f"📚 Number of knowledge points: {len(course_data.get('materials', []))}")
        
        # Add additional information
        course_data['id'] = f"course_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        course_data['fileName'] = file_name
        course_data['generatedAt'] = datetime.now().isoformat()
        course_data['knowledgePointCount'] = len(course_data.get('materials', []))
        
        # 💾 Save course to file
        save_course_to_file(course_data)
        
        return jsonify(course_data)
    
    except Exception as e:
        return jsonify({'error': f'Failed to generate course: {str(e)}'}), 500

# Store course data (should use database in production)
course_library = {}

# Store student answer records (for generating learning reports)
# Structure: { student_id: [{ area_id, question, answer, is_correct, knowledge_point, timestamp }, ...] }
battle_records = {}

# Store student learning report history
# Structure: { student_id: [ { report_id, type, area_id, area_name, generated_at, analysis, ai_summary, title, subtitle }, ... ] }
student_reports = {}

# Course persistence function
def save_course_to_file(course_data):
    """Save course to file"""
    try:
        course_id = course_data['id']
        file_path = os.path.join(COURSES_FOLDER, f"{course_id}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(course_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Course saved: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to save course: {str(e)}")
        return False

def load_all_courses():
    """Load all courses from files"""
    courses = []
    try:
        if not os.path.exists(COURSES_FOLDER):
            return courses
        
        for filename in os.listdir(COURSES_FOLDER):
            if filename.endswith('.json'):
                file_path = os.path.join(COURSES_FOLDER, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        course_data = json.load(f)
                        courses.append(course_data)
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
    """Reset game map, only keep start point"""
    global game_state, course_library
    
    print(f"\n{'='*60}")
    print(f"🔄 Resetting game map")
    print(f"{'='*60}\n")
    
    # Save old state for logging
    old_area_count = len(game_state['areas'])
    old_course_count = len(course_library)
    
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
    
    print(f"✅ Map reset successful!")
    print(f"   Deleted areas: {old_area_count - 1}")
    print(f"   Cleared courses: {old_course_count}")
    print(f"{'='*60}\n")
    
    return jsonify({
        'message': 'Game map has been reset',
        'deleted_areas': old_area_count - 1,
        'cleared_courses': old_course_count
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
        materials = course_data.get('materials', [])
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
            if '第' in material and ('章' in material or '节' in material):
                # Extract chapter name
                import re
                match = re.search(r'第[一二三四五六七八九十\d]+[章节]', material)
                if match:
                    current_chapter = match.group()
                    if current_chapter not in chapters:
                        chapters[current_chapter] = []
            
            # Add knowledge point to current chapter
            if current_chapter not in chapters:
                chapters[current_chapter] = []
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
            
            # Store course materials
            course_library[area_id] = {
                'subject': area_name,
                'materials': chapter_materials,
                'difficulty': difficulty,
                'category': category,
                'knowledgePointCount': len(chapter_materials),
                'chapter': chapter_name,
                'parent_course': subject
            }
            
            print(f"✅ Created area: {area_id} - {area_name}")
            print(f"   Position: x={position['x']}, y={position['y']}")
            print(f"   Connection: {previous_area_id} → {area_id}")
            print(f"   Knowledge points: {len(chapter_materials)}")
            
            # Update to be "previous area" for next iteration
            previous_area_id = area_id
            previous_position = position
            previous_level += 1
            chapter_index += 1
        
        # Add new areas to game state
        game_state['areas'].update(new_areas)
        game_state['max_level'] = max(area['level'] for area in game_state['areas'].values())
        
        print(f"\n✅ Successfully applied course to game map!")
        print(f"   New areas created: {len(new_areas)}")
        print(f"   Total areas: {len(game_state['areas'])}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'message': f'Successfully applied course to game map',
            'new_areas': list(new_areas.keys()),
            'chapter_count': len(chapters),
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
    if area_id in course_library:
        return jsonify(course_library[area_id])
    else:
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

def analyze_battle_data(records):
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
    
    return {
        'total_questions': total_questions,
        'correct_count': correct_count,
        'accuracy': round(accuracy, 2),
        'knowledge_point_stats': knowledge_point_stats,
        'weak_points': [{'knowledge_point': kp, **stats} for kp, stats in weak_points]
    }

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
        elif report_type == 'final':
            scope_line = "This report summarizes the entire learning journey across every module."
        else:
            scope_line = "This report is a snapshot of recent learning performance."

        prompt = f"""You are the chief mentor of the Arcane Academy. Craft a warm, encouraging learning report in English only.

{scope_line}

Student performance:
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
6. Do not use bullet lists, emojis, or markdown formatting—write in polished prose.
"""

        print("🤖 Generating AI report via Ollama...")

        ollama_response = requests.post(
            'http://ollama:11434/api/generate',
            json={
                'model': 'qwen2.5',
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'top_p': 0.9
                }
            },
            timeout=30
        )

        if ollama_response.status_code == 200:
            ai_report = ollama_response.json().get('response', '').strip()
            print(f"✅ AI report generated successfully, length {len(ai_report)} characters")
            return ai_report
        else:
            print(f"⚠️ Ollama returned status {ollama_response.status_code}, using fallback report")
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
    analysis_data = analyze_battle_data(records)
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    print(f"Starting game server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug)
