from flask import Flask, jsonify
from flask_cors import CORS
import random
import math

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Store game state
game_state = {
    'areas': {
        'start': {
            'completed': False,
            'position': {'x': 500, 'y': 900},  # 使用像素坐标
            'connections': ['area1', 'area2'],
            'level': 0
        },
        'area1': {
            'completed': False,
            'position': {'x': 350, 'y': 700},
            'connections': [],
            'level': 1
        },
        'area2': {
            'completed': False,
            'position': {'x': 650, 'y': 700},
            'connections': [],
            'level': 1
        }
    },
    'current_area': 'start',
    'max_level': 1
}

def calculate_new_position(current_area_id, branch_index, total_branches):
    """计算新区域的位置，确保在当前区域的正上方"""
    current_pos = game_state['areas'][current_area_id]['position']
    current_level = game_state['areas'][current_area_id]['level']
    
    # 固定的前进距离（像素）
    forward_distance = 250  # 增加区域间的垂直距离
    
    # 计算新的y坐标（向上移动）
    new_y = current_pos['y'] - forward_distance
    
    # 计算新的x坐标（在当前位置左右分布）
    if total_branches == 1:
        # 单个分支时保持在同一直线上
        new_x = current_pos['x']
    else:
        # 多个分支时在当前位置两侧分布
        spread = 200  # 增加区域间的水平距离
        if total_branches == 2:
            # 两个分支时对称分布
            offset = spread * (-1 if branch_index == 0 else 1)
            new_x = current_pos['x'] + offset
        else:
            # 三个分支时，一个在中间，两个在两侧
            if branch_index == 0:
                new_x = current_pos['x'] - spread
            elif branch_index == 1:
                new_x = current_pos['x']
            else:
                new_x = current_pos['x'] + spread
    
    return {'x': new_x, 'y': new_y}

def generate_new_area(current_area_id, branch_index, total_branches):
    """生成新区域"""
    area_id = f'area{len(game_state["areas"]) + 1}'
    current_level = game_state['areas'][current_area_id]['level']
    
    return {
        'completed': False,
        'position': calculate_new_position(current_area_id, branch_index, total_branches),
        'connections': [],
        'level': current_level + 1
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
    if area_id in game_state['areas']:
        game_state['areas'][area_id]['completed'] = True
        game_state['current_area'] = area_id
        
        # 生成新路径
        generate_new_paths(area_id)
        
        return jsonify({"message": f"Area {area_id} completed", "game_state": game_state})
    else:
        return jsonify({"error": "Area not found"}), 404

if __name__ == '__main__':
    print("Starting game server on port 8001...")
    app.run(host='0.0.0.0', port=8001, debug=True)
