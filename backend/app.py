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

# 配置文件上传
UPLOAD_FOLDER = 'uploads'
COURSES_FOLDER = 'courses'  # 存储生成的课程
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md'}  # 支持PDF、TXT和Markdown

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
            'completed': True,  # 起点默认已完成，允许解锁第一个区域
            'position': {'x': 200, 'y': 400},  # 横向布局：从左开始
            'connections': [],  # 初始无连接，等待教师添加课程
            'level': 0,
            'castle_type': random.randint(1, 5),  # 随机城堡类型 1-5
            'learningProgress': 100,  # 起点学习进度100%
            'learnedPoints': []  # 已学习的知识点编号列表
        }
    },
    'current_area': 'start',
    'max_level': 0
}

def calculate_new_position(current_area_id, branch_index, total_branches):
    """计算新区域的位置，横向布局从左到右"""
    current_pos = game_state['areas'][current_area_id]['position']
    current_level = game_state['areas'][current_area_id]['level']
    
    # 固定的前进距离（像素）- 横向（增加间距）
    forward_distance = 600  # 区域间的水平距离（从400增加到600）
    
    # 计算新的x坐标（向右移动）
    new_x = current_pos['x'] + forward_distance
    
    # 计算新的y坐标（在当前位置上下分布）
    if total_branches == 1:
        # 单个分支时保持在同一水平线上
        new_y = current_pos['y']
    else:
        # 多个分支时在当前位置上下分布
        spread = 150  # 区域间的垂直距离（从100增加到150）
        if total_branches == 2:
            # 两个分支时对称分布（上下）
            offset = spread * (-1 if branch_index == 0 else 1)
            new_y = current_pos['y'] + offset
        else:
            # 三个分支时，一个在中间，两个在上下
            if branch_index == 0:
                new_y = current_pos['y'] - spread
            elif branch_index == 1:
                new_y = current_pos['y']
            else:
                new_y = current_pos['y'] + spread
    
    return {'x': new_x, 'y': new_y}

def generate_new_area(current_area_id, branch_index, total_branches):
    """生成新区域"""
    area_id = f'area{len(game_state["areas"]) + 1}'
    current_level = game_state['areas'][current_area_id]['level']
    
    return {
        'completed': False,
        'position': calculate_new_position(current_area_id, branch_index, total_branches),
        'connections': [],
        'level': current_level + 1,
        'castle_type': random.randint(1, 5)  # 随机城堡类型 1-5
    }

def generate_new_paths(current_area_id):
    """生成新路径"""
    current_area = game_state['areas'][current_area_id]
    
    # 重置当前区域的连接
    current_area['connections'] = []
    
    # 决定新分支数量（2-3个）
    num_branches = random.randint(2, 3)
    
    # 生成新区域
    for i in range(num_branches):
        new_area_id = f'area{len(game_state["areas"]) + 1}'
        game_state['areas'][new_area_id] = generate_new_area(current_area_id, i, num_branches)
        current_area['connections'].append(new_area_id)
    
    # 更新最大层级
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
    """完成区域 - 线性地图模式，只解锁下一个单元"""
    if area_id in game_state['areas']:
        game_state['areas'][area_id]['completed'] = True
        game_state['current_area'] = area_id
        
        # 线性地图：不再动态生成新路径
        # 路径已经在应用课程时预先创建好了
        print(f"✅ 完成区域: {area_id}")
        
        # 检查是否有下一个区域
        next_areas = game_state['areas'][area_id].get('connections', [])
        if next_areas:
            print(f"🔓 已解锁下一个区域: {next_areas[0]}")
        else:
            print(f"🎉 恭喜！已完成所有区域！")
        
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
    """更新区域的学习进度"""
    if area_id not in game_state['areas']:
        return jsonify({"error": "Area not found"}), 404
    
    data = request.get_json()
    learned_points = data.get('learnedPoints', [])  # 已学习的知识点编号列表
    
    # 获取该区域的总知识点数量
    total_points = course_library.get(area_id, {}).get('knowledgePointCount', 5)
    
    # 计算学习进度
    learned_count = len(learned_points)
    progress = (learned_count / total_points) * 100 if total_points > 0 else 0
    
    # 更新游戏状态
    game_state['areas'][area_id]['learnedPoints'] = learned_points
    game_state['areas'][area_id]['learningProgress'] = progress
    
    print(f"📊 更新学习进度: {area_id} - {learned_count}/{total_points} ({progress:.1f}%)")
    
    return jsonify({
        "message": "Progress updated",
        "area_id": area_id,
        "learnedPoints": learned_points,
        "progress": progress,
        "game_state": game_state
    })

# 文本提取函数
def extract_text_from_file(file_path):
    """从文件中提取文本（支持PDF、TXT、MD）"""
    # 安全地获取文件扩展名
    if '.' in file_path:
        file_ext = file_path.rsplit('.', 1)[1].lower()
    else:
        return "错误: 文件没有扩展名"
    
    try:
        # TXT和MD文件直接读取
        if file_ext in ['txt', 'md']:
            print(f"📄 读取文本文件: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            print(f"✅ 文本读取成功，长度: {len(text)} 字符")
            return text
        
        # PDF文件使用PyPDF2
        elif file_ext == 'pdf':
            print(f"📄 读取PDF文件: {file_path}")
            import PyPDF2
            
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                print(f"📖 PDF共有 {num_pages} 页")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    text += page_text + "\n"
                    print(f"   第 {page_num + 1}/{num_pages} 页，提取 {len(page_text)} 字符")
            
            print(f"✅ PDF读取成功，总共 {len(text)} 字符")
            return text
        
        else:
            return f"错误: 不支持的文件格式 {file_ext}"
    
    except UnicodeDecodeError:
        # 如果UTF-8失败，尝试其他编码
        try:
            with open(file_path, 'r', encoding='gbk') as file:
                text = file.read()
            print(f"✅ 使用GBK编码读取成功")
            return text
        except:
            return "错误: 无法识别文件编码，请使用UTF-8或GBK编码"
    
    except ImportError:
        return "错误: 未安装PyPDF2库，请运行: pip install PyPDF2"
    except Exception as e:
        return f"错误: 无法提取文本 - {str(e)}"

# 解析结构化TXT文件
def parse_structured_txt(text_content):
    """解析结构化的TXT文件格式（支持中英文元信息和章节标记）"""
    metadata = {}
    materials = []

    lines = text_content.split('\n')
    in_metadata = False
    in_content = False
    current_chapter = ""

    # 支持的标题（中英文）
    meta_headers = {'# 课程元信息', '# Course Meta Information'}
    content_headers = {'# 课程内容', '# Course Content'}

    # 元信息键映射（中英文）
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

        # 检测元信息部分
        if line in meta_headers:
            in_metadata = True
            in_content = False
            continue
        elif line in content_headers:
            in_metadata = False
            in_content = True
            continue

        # 解析元信息
        if in_metadata and ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            mapped = key_map.get(key)
            if mapped:
                metadata[mapped] = value

        # 解析课程内容
        if in_content:
            # 章节标题
            if line.startswith('## '):
                current_chapter = line[3:].strip()
            # 知识点/条目
            elif line.startswith('### '):
                point_title = line[4:].strip()
                materials.append(point_title)

    return metadata, materials

# 使用LLM分析PDF内容并生成课程
def generate_course_from_text(text_content, file_name):
    """使用LLM分析PDF内容并生成详细的课程知识点"""
    
    print(f"\n{'='*60}")
    print(f"🔍 开始分析文件内容")
    print(f"📄 文件名: {file_name}")
    print(f"📏 总字符数: {len(text_content)}")
    print(f"📝 内容预览:\n{text_content[:300]}")
    print(f"{'='*60}\n")
    
    # 检查是否是结构化TXT格式（支持中英文标记）
    if (
        ('# 课程元信息' in text_content and '# 课程内容' in text_content)
        or ('# Course Meta Information' in text_content and '# Course Content' in text_content)
    ):
        print("✨ 检测到结构化TXT格式，使用专用解析器...")
        metadata, materials_titles = parse_structured_txt(text_content)
        
        if metadata and materials_titles:
            print(f"✅ 解析成功!")
            print(f"   - 课程名称: {metadata.get('subject', '未指定')}")
            print(f"   - 类别: {metadata.get('category', '未指定')}")
            print(f"   - 难度: {metadata.get('difficulty', 'medium')}")
            print(f"   - 知识点数: {len(materials_titles)}")
            
            # 提取详细内容
            detailed_materials = []
            lines = text_content.split('\n')
            current_point = None
            current_content = []
            
            for line in lines:
                line_stripped = line.strip()
                
                # 检测知识点标题
                if line_stripped.startswith('### '):
                    # 保存上一个知识点
                    if current_point and current_content:
                        detail = ' '.join(current_content).strip()
                        if len(detail) > 20:
                            detailed_materials.append(f"{current_point}: {detail}")
                        else:
                            detailed_materials.append(current_point)
                    
                    # 开始新知识点
                    current_point = line_stripped[4:].strip()
                    current_content = []
                
                # 收集知识点内容
                elif current_point and line_stripped and not line_stripped.startswith('#'):
                    current_content.append(line_stripped)
            
            # 保存最后一个知识点
            if current_point and current_content:
                detail = ' '.join(current_content).strip()
                if len(detail) > 20:
                    detailed_materials.append(f"{current_point}: {detail}")
                else:
                    detailed_materials.append(current_point)
            
            print(f"\n📚 提取的详细知识点数: {len(detailed_materials)}")
            
            return {
                'subject': metadata.get('subject', 'General Course'),
                'materials': detailed_materials if detailed_materials else materials_titles,
                'difficulty': metadata.get('difficulty', 'medium'),
                'category': metadata.get('category', 'General')
            }
    
    print("📋 使用通用文本分析...")
    
    # 截取前8000字符用于分析（增加采样量）
    text_sample = text_content[:8000] if len(text_content) > 8000 else text_content
    
    prompt = f"""你是计算机魔法学院的资深教授，需要仔细阅读并分析这份课程资料PDF，然后生成详细的课程知识点。

【重要】必须基于下面的PDF实际内容来总结知识点，不要编造！

【PDF文件名】：{file_name}

【PDF完整内容】：
{text_sample}

【任务】：
1. 仔细阅读上述PDF内容
2. 识别课程的主题和核心概念
3. 从PDF内容中提取10-15个关键知识点
4. 每个知识点必须来自PDF的实际内容，用你自己的话总结

【输出要求】：
严格按照JSON格式输出，不要有任何其他文字：

{{
  "subject": "根据PDF内容确定的课程名称",
  "materials": [
    "知识点1：基于PDF内容的总结",
    "知识点2：基于PDF内容的总结",
    "知识点3：基于PDF内容的总结",
    ...至少10个
  ],
  "difficulty": "easy/medium/hard",
  "category": "课程分类"
}}

只输出JSON，不要任何额外文字！"""

    # 尝试调用LLM（使用Ollama）
    try:
        import requests
        
        print("🤖 尝试调用Ollama LLM...")
        
        # 尝试使用Ollama API
        ollama_response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'qwen2.5',
                'prompt': prompt,
                'stream': False
            },
            timeout=90
        )
        
        if ollama_response.status_code == 200:
            response_text = ollama_response.json().get('response', '')
            print(f"✅ LLM响应成功，长度: {len(response_text)}")
            print(f"📝 LLM响应预览:\n{response_text[:500]}")
            
            # 提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                course_data = json.loads(json_match.group())
                
                # 验证必需字段
                if 'subject' in course_data and 'materials' in course_data:
                    print(f"✅ LLM成功生成课程: {course_data['subject']}")
                    print(f"📚 知识点数量: {len(course_data['materials'])}")
                    return course_data
            else:
                print("⚠️ LLM响应中未找到有效JSON")
        else:
            print(f"⚠️ LLM响应状态码: {ollama_response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️ Ollama服务未运行，使用智能提取算法")
    except Exception as e:
        print(f"⚠️ LLM调用失败: {e}")
    
    # 如果LLM失败，使用基于PDF内容的智能提取
    print("\n🔄 使用智能提取算法分析PDF内容...")
    return generate_course_fallback(text_content, file_name)

def generate_course_fallback(text_content, file_name):
    """当LLM不可用时，基于PDF内容智能提取知识点"""
    
    print(f"\n{'='*60}")
    print(f"📊 智能提取算法开始工作")
    print(f"📄 待分析文本长度: {len(text_content)} 字符")
    print(f"{'='*60}\n")
    
    # 简单的课程主题识别
    keywords_map = {
        # 中文关键词
        '网络': ('Computer Networks', 'easy', 'Networking'),
        '数据结构': ('Data Structures and Algorithms', 'medium', 'Algorithms'),
        '算法': ('Data Structures and Algorithms', 'medium', 'Algorithms'),
        '操作系统': ('Operating Systems', 'medium', 'Systems'),
        '数据库': ('Database Systems', 'medium', 'Data Management'),
        '机器学习': ('Machine Learning Basics', 'hard', 'AI'),
        '人工智能': ('Artificial Intelligence', 'hard', 'AI'),
        '软件工程': ('Software Engineering', 'medium', 'Software Engineering'),
        # 英文关键词
        'python': ('Python Programming', 'easy', 'Programming Language'),
        'java': ('Java Programming', 'medium', 'Programming Language'),
        'mathematics': ('Elementary Mathematics', 'easy', 'Basic Mathematics'),
        'math': ('Elementary Mathematics', 'easy', 'Basic Mathematics'),
    }
    
    subject = "General Course"
    difficulty = "medium"
    category = "General"
    
    # 识别课程主题
    text_lower = text_content.lower()
    for keyword, (subj, diff, cat) in keywords_map.items():
        if keyword.lower() in text_lower or keyword.lower() in file_name.lower():
            subject = subj
            difficulty = diff
            category = cat
            break
    
    # 智能提取知识点
    materials = []
    
    print("📋 步骤1: 提取标题和结构化内容...")
    
    # 1. 尝试提取标题和关键句子（以数字、bullet point或关键词开头）
    lines = text_content.split('\n')
    for line in lines:
        line = line.strip()
        # 匹配标题模式：数字开头、bullet开头、或包含关键词
        if (re.match(r'^\d+[\.\)、]', line) or 
            re.match(r'^[•·►▪■□]', line) or
            re.match(r'^第[一二三四五六七八九十\d]+[章节课]', line) or
            any(kw in line for kw in ['定义', '概念', '原理', '方法', '技术', '算法', '协议', '模型', '特点', '优势'])):
            if 15 < len(line) < 150:  # 合适的长度
                clean_line = re.sub(r'^[\d\.\)、•·►▪■□\s]+', '', line)  # 去除前缀
                if clean_line and not clean_line.startswith('第'):
                    materials.append(clean_line)
    
    print(f"   ✓ 提取了 {len(materials)} 个结构化内容")
    
    # 2. 如果提取的不够，从文本中提取有意义的句子
    if len(materials) < 10:
        print("📝 步骤2: 提取关键句子...")
        sentences = re.split(r'[。！？\n]+', text_content)
        for sent in sentences:
            sent = sent.strip()
            # 筛选包含关键术语的句子
            if (30 < len(sent) < 200 and 
                any(kw in sent for kw in ['是', '为', '指', '包括', '分为', '主要', '可以', '能够', '用于', '实现', '通过'])):
                materials.append(sent)
                if len(materials) >= 15:
                    break
        
        print(f"   ✓ 现在共有 {len(materials)} 个知识点")
    
    # 3. 如果还不够，提取段落的第一句
    if len(materials) < 10:
        print("📄 步骤3: 提取段落首句...")
        paragraphs = text_content.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if para:
                first_sent = re.split(r'[。！？]', para)[0].strip()
                if 20 < len(first_sent) < 150:
                    materials.append(first_sent)
                    if len(materials) >= 15:
                        break
        
        print(f"   ✓ 现在共有 {len(materials)} 个知识点")
    
    # 4. 去重和清理
    print("🧹 步骤4: 去重和清理...")
    seen = set()
    unique_materials = []
    for m in materials:
        # 移除特殊字符和多余空格
        m_clean = re.sub(r'\s+', ' ', m).strip()
        if m_clean and m_clean not in seen and len(m_clean) > 10:
            seen.add(m_clean)
            unique_materials.append(m_clean)
    
    print(f"   ✓ 去重后剩余 {len(unique_materials)} 个独特知识点")
    
    # 5. 如果还是不够，添加基于PDF内容的描述性知识点
    if len(unique_materials) < 10:
        print("🔍 步骤5: 搜索关键词模式...")
        # 提取关键词来生成知识点
        key_terms = []
        for keyword in ['定义', '概念', '原理', '方法', '算法', '协议', '模型', '架构', '特征', '应用']:
            pattern = f'{keyword}[：:，,]?([^。！？\n]{{10,80}})'
            matches = re.findall(pattern, text_content)
            for match in matches[:2]:
                key_terms.append(f"{keyword}: {match.strip()}")
        
        unique_materials.extend(key_terms[:10 - len(unique_materials)])
        print(f"   ✓ 添加了 {len(key_terms)} 个关键词匹配")
    
    # 6. 如果仍然不够，从PDF中提取最有价值的内容片段
    if len(unique_materials) < 10:
        print("⭐ 步骤6: 按重要性评分提取句子...")
        # 按长度和关键词密度评分，选择最有价值的句子
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
        
        print(f"   ✓ 现在共有 {len(unique_materials)} 个知识点")
    
    # 确保至少有10个知识点
    final_materials = unique_materials[:15] if len(unique_materials) >= 10 else unique_materials
    
    print(f"\n📊 提取结果统计:")
    print(f"   - 原始提取数量: {len(materials)}")
    print(f"   - 去重后数量: {len(unique_materials)}")
    print(f"   - 最终知识点数: {len(final_materials)}")
    
    if len(final_materials) < 10:
        print("⚠️ 知识点不足10个，添加补充内容...")
        # 最后兜底：生成描述性知识点
        final_materials.extend([
            f"{subject}：本课程的核心内容和学习目标",
            f"{subject}：基础概念和理论框架",
            f"{subject}：关键技术和实现方法",
            f"{subject}：实际应用场景和案例分析",
            f"{subject}：常见问题和解决方案",
            f"{subject}：最佳实践和设计原则",
            f"{subject}：性能优化和改进策略",
            f"{subject}：发展趋势和未来展望",
            f"{subject}：综合练习和实战项目",
            f"{subject}：总结与知识体系构建"
        ][:10 - len(final_materials)])
    
    print(f"\n✅ 智能提取完成!")
    print(f"   - 课程名称: {subject}")
    print(f"   - 知识点数: {len(final_materials[:15])}")
    print(f"   - 难度等级: {difficulty}")
    print(f"   - 课程分类: {category}")
    print(f"{'='*60}\n")
    
    # 打印前3个知识点作为预览
    print("📚 提取的知识点预览:")
    for i, point in enumerate(final_materials[:3], 1):
        print(f"   {i}. {point[:80]}{'...' if len(point) > 80 else ''}")
    print()
    
    return {
        'subject': subject,
        'materials': final_materials[:15],
        'difficulty': difficulty,
        'category': category
    }

# 教师端API - 上传PDF
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
        # 保存文件
        original_filename = file.filename
        print(f"📥 原始文件名: {original_filename}")
        
        # 获取文件扩展名
        if '.' in original_filename:
            file_ext = original_filename.rsplit('.', 1)[1].lower()
            base_name = original_filename.rsplit('.', 1)[0]
        else:
            return jsonify({'error': 'File has no extension'}), 400
        
        # 处理文件名（保留扩展名）
        safe_basename = secure_filename(base_name)
        
        # 如果secure_filename把所有字符都去掉了（中文文件名），使用时间戳
        if not safe_basename:
            safe_basename = "course"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{safe_basename}.{file_ext}"
        
        print(f"🔒 处理后文件名: {filename}")
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"💾 保存路径: {file_path}")
        
        file.save(file_path)
        
        print(f"\n{'='*60}")
        print(f"📤 文件上传成功: {filename}")
        print(f"{'='*60}")
        
        # 提取文本
        text_content = extract_text_from_file(file_path)
        
        if isinstance(text_content, str) and text_content.startswith('错误:'):
            print(f"❌ {text_content}")
            return jsonify({'error': text_content}), 500
        
        print(f"\n✅ 文本提取成功!")
        print(f"📄 文本长度: {len(text_content)} 字符")
        print(f"📝 前500字符预览:")
        print(f"{text_content[:500]}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'message': '文件上传成功',
            'file_path': file_path,
            'file_name': filename,
            'text_content': text_content,
            'text_length': len(text_content)
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n❌ 上传错误:")
        print(error_trace)
        return jsonify({'error': f'Upload failed: {str(e)}', 'trace': error_trace}), 500

# 教师端API - 生成课程
@app.route('/api/generate-course', methods=['POST'])
def generate_course():
    """使用LLM分析PDF内容并生成课程知识点"""
    try:
        data = request.get_json()
        text_content = data.get('text_content', '')
        file_name = data.get('file_name', 'unknown.pdf')
        
        if not text_content:
            return jsonify({'error': 'PDF text content is empty'}), 400
        
        print(f"🤖 开始生成课程，文本长度: {len(text_content)}")
        
        # 使用LLM生成课程
        course_data = generate_course_from_text(text_content, file_name)
        
        print(f"✅ 课程生成成功: {course_data.get('subject')}")
        print(f"📚 知识点数量: {len(course_data.get('materials', []))}")
        
        # 添加额外信息
        course_data['id'] = f"course_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        course_data['fileName'] = file_name
        course_data['generatedAt'] = datetime.now().isoformat()
        course_data['knowledgePointCount'] = len(course_data.get('materials', []))
        
        # 💾 保存课程到文件
        save_course_to_file(course_data)
        
        return jsonify(course_data)
    
    except Exception as e:
        return jsonify({'error': f'Failed to generate course: {str(e)}'}), 500

# 存储课程数据（在实际应用中应该使用数据库）
course_library = {}

# 存储学生答题记录（用于生成学习报告）
# 结构: { student_id: [{ area_id, question, answer, is_correct, knowledge_point, timestamp }, ...] }
battle_records = {}

# 存储学生的学习报告历史
# 结构: { student_id: [ { report_id, type, area_id, area_name, generated_at, analysis, ai_summary, title, subtitle }, ... ] }
student_reports = {}

# 课程持久化函数
def save_course_to_file(course_data):
    """将课程保存到文件"""
    try:
        course_id = course_data['id']
        file_path = os.path.join(COURSES_FOLDER, f"{course_id}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(course_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 课程已保存: {file_path}")
        return True
    except Exception as e:
        print(f"❌ 保存课程失败: {str(e)}")
        return False

def load_all_courses():
    """从文件加载所有课程"""
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
                    print(f"⚠️  加载课程文件失败: {filename}, {str(e)}")
        
        # 按生成时间倒序排列（最新的在前）
        courses.sort(key=lambda x: x.get('generatedAt', ''), reverse=True)
        print(f"📚 成功加载 {len(courses)} 个课程")
        return courses
    except Exception as e:
        print(f"❌ 加载课程列表失败: {str(e)}")
        return []

def delete_course_file(course_id):
    """删除课程文件"""
    try:
        file_path = os.path.join(COURSES_FOLDER, f"{course_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️  课程已删除: {course_id}")
            return True
        return False
    except Exception as e:
        print(f"❌ 删除课程失败: {str(e)}")
        return False

# 教师端API - 重置游戏地图（清除所有课程区域）
@app.route('/api/reset-game-map', methods=['POST'])
def reset_game_map():
    """重置游戏地图，只保留起点"""
    global game_state, course_library
    
    print(f"\n{'='*60}")
    print(f"🔄 重置游戏地图")
    print(f"{'='*60}\n")
    
    # 保存旧状态用于日志
    old_area_count = len(game_state['areas'])
    old_course_count = len(course_library)
    
    # 重置游戏状态
    game_state = {
        'areas': {
            'start': {
                'completed': True,  # 起点默认已完成
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
    
    # 清空课程库
    course_library = {}
    
    print(f"✅ 地图重置成功!")
    print(f"   删除区域数: {old_area_count - 1}")
    print(f"   清空课程数: {old_course_count}")
    print(f"{'='*60}\n")
    
    return jsonify({
        'message': '游戏地图已重置',
        'deleted_areas': old_area_count - 1,
        'cleared_courses': old_course_count
    })

# 教师端API - 将课程应用到游戏地图
# 教师端API - 获取所有课程
@app.route('/api/courses', methods=['GET'])
def get_all_courses():
    """获取所有保存的课程"""
    try:
        courses = load_all_courses()
        return jsonify({
            'courses': courses,
            'total': len(courses)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get course list: {str(e)}'}), 500

# 教师端API - 删除课程
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
        print(f"🎮 将课程应用到游戏地图")
        print(f"📚 课程: {course_data.get('subject')}")
        print(f"🔄 替换模式: {replace_existing}")
        print(f"{'='*60}\n")
        
        # 如果选择替换，先重置地图
        if replace_existing:
            print(f"⚠️  替换模式：清除现有地图...")
            reset_game_map()
            print(f"✅ 地图已清空，开始添加新课程\n")
        
        # 解析课程结构，按章节分组知识点
        materials = course_data.get('materials', [])
        subject = course_data.get('subject', '课程')
        category = course_data.get('category', 'General')
        difficulty = course_data.get('difficulty', 'medium')
        
        # 分析章节结构
        chapters = {}
        # Default chapter label in English for non-marked materials
        current_chapter = "Chapter 1"
        chapter_num = 1
        
        for material in materials:
            # 检查是否是新章节的标记
            if '第' in material and ('章' in material or '节' in material):
                # 提取章节名
                import re
                match = re.search(r'第[一二三四五六七八九十\d]+[章节]', material)
                if match:
                    current_chapter = match.group()
                    if current_chapter not in chapters:
                        chapters[current_chapter] = []
            
            # 将知识点添加到当前章节
            if current_chapter not in chapters:
                chapters[current_chapter] = []
            chapters[current_chapter].append(material)
        
        # 如果没有检测到章节，将所有知识点平均分配
        if len(chapters) == 1 and len(chapters[current_chapter]) == len(materials):
            # 重新分配：每5个知识点一个章节
            chapters = {}
            points_per_chapter = 5
            for i in range(0, len(materials), points_per_chapter):
                chapter_name = f"Chapter {i // points_per_chapter + 1}"
                chapters[chapter_name] = materials[i:i + points_per_chapter]
        
        print(f"📖 检测到 {len(chapters)} 个章节:")
        for chapter_name, points in chapters.items():
            print(f"   - {chapter_name}: {len(points)} 个知识点")
        
        # 为每个章节创建一个Area
        new_areas = {}
        area_count = len(game_state['areas'])
        
        # 找到最后一个已完成的区域
        last_completed_area = None
        for area_id, area in game_state['areas'].items():
            if area['completed'] or area_id == 'start':
                last_completed_area = area_id
        
        if not last_completed_area:
            last_completed_area = 'start'
        
        # 【线性地图】：按顺序创建区域，每个区域只连接下一个
        last_area = game_state['areas'][last_completed_area]
        last_area['connections'] = []  # 清空现有连接
        
        # 获取起始位置和level
        previous_position = last_area['position']
        previous_level = last_area['level']
        
        previous_area_id = last_completed_area
        chapter_index = 0
        
        forward_distance = 600  # 区域间的水平距离
        
        for chapter_name, chapter_materials in chapters.items():
            area_id = f"area{area_count + 1 + chapter_index}"
            area_name = f"{subject}: {chapter_name}"
            
            # 【线性布局】：直接计算位置，不依赖calculate_new_position
            # 水平向右移动，Y坐标保持不变
            position = {
                'x': previous_position['x'] + forward_distance,
                'y': previous_position['y']
            }
            
            # 创建新Area
            new_areas[area_id] = {
                'completed': False,
                'position': position,
                'connections': [],  # 初始为空，下一个循环会连接
                'level': previous_level + 1,
                # If you added more castle images (castle6.png, castle7.png, ...),
                # increase the upper bound accordingly (default supports 1..10)
                'castle_type': random.randint(1, 10),
                'name': area_name,  # 添加名称
                'learningProgress': 0,  # 学习进度初始化为0%
                'learnedPoints': []  # 已学习的知识点列表
            }
            
            # 【线性连接】：前一个区域只连接到当前区域
            if previous_area_id in game_state['areas']:
                game_state['areas'][previous_area_id]['connections'] = [area_id]
            else:
                new_areas[previous_area_id]['connections'] = [area_id]
            
            # 存储课程材料
            course_library[area_id] = {
                'subject': area_name,
                'materials': chapter_materials,
                'difficulty': difficulty,
                'category': category,
                'knowledgePointCount': len(chapter_materials),
                'chapter': chapter_name,
                'parent_course': subject
            }
            
            print(f"✅ 创建区域: {area_id} - {area_name}")
            print(f"   位置: x={position['x']}, y={position['y']}")
            print(f"   连接: {previous_area_id} → {area_id}")
            print(f"   知识点数: {len(chapter_materials)}")
            
            # 更新为下一个循环的"前一个区域"
            previous_area_id = area_id
            previous_position = position
            previous_level += 1
            chapter_index += 1
        
        # 添加新区域到游戏状态
        game_state['areas'].update(new_areas)
        game_state['max_level'] = max(area['level'] for area in game_state['areas'].values())
        
        print(f"\n✅ 成功将课程应用到游戏地图!")
        print(f"   新增区域数: {len(new_areas)}")
        print(f"   总区域数: {len(game_state['areas'])}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'message': f'成功应用课程到游戏地图',
            'new_areas': list(new_areas.keys()),
            'chapter_count': len(chapters),
            'game_state': game_state
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n❌ 应用课程失败:")
        print(error_trace)
        return jsonify({'error': f'Application failed: {str(e)}'}), 500

# API - 获取课程库（供前端获取课程材料）
@app.route('/api/course-library/<area_id>', methods=['GET'])
def get_course_library(area_id):
    """获取指定区域的课程材料"""
    if area_id in course_library:
        return jsonify(course_library[area_id])
    else:
        # 返回默认课程材料（如果没有从教师端添加）
        return jsonify({
            'subject': f'{area_id}区域',
            'materials': [
                '这是默认知识点1',
                '这是默认知识点2',
                '这是默认知识点3',
                '这是默认知识点4',
                '这是默认知识点5'
            ],
            'difficulty': 'medium',
            'category': 'General',
            'knowledgePointCount': 5
        })

# ==================== 学习报告相关API ====================

@app.route('/api/save-battle-record', methods=['POST'])
def save_battle_record():
    """保存答题记录"""
    try:
        data = request.get_json()
        student_id = data.get('student_id', 'default_student')  # 默认学生ID
        area_id = data.get('area_id')
        question = data.get('question')
        answer = data.get('answer')
        is_correct = data.get('is_correct')
        knowledge_point = data.get('knowledge_point', '')
        
        if not all([area_id, question, answer is not None, is_correct is not None]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # 初始化学生记录
        if student_id not in battle_records:
            battle_records[student_id] = []
        
        # 添加答题记录
        record = {
            'area_id': area_id,
            'question': question,
            'answer': answer,
            'is_correct': is_correct,
            'knowledge_point': knowledge_point,
            'timestamp': datetime.now().isoformat()
        }
        
        battle_records[student_id].append(record)
        
        print(f"📝 保存答题记录: {student_id} - {area_id} - {'✅' if is_correct else '❌'}")
        
        return jsonify({
            'message': 'Record saved successfully',
            'total_records': len(battle_records[student_id])
        })
    
    except Exception as e:
        print(f"❌ 保存答题记录失败: {str(e)}")
        return jsonify({'error': f'Failed to save record: {str(e)}'}), 500

@app.route('/api/get-battle-records/<student_id>', methods=['GET'])
def get_battle_records(student_id):
    """获取学生的答题记录"""
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
            'http://localhost:11434/api/generate',
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
    print("Starting game server on port 8001...")
    app.run(host='0.0.0.0', port=8001, debug=True)
