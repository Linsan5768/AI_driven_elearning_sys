# 🎮 伪3D游戏地图 + LLM对话系统

这是一个基于React前端和Python后端的伪3D游戏地图，集成了免费开源LLM agent的对话系统。

## ✨ 主要功能

### 🗺️ 游戏地图
- **伪3D视觉效果**：20度俯视角，2D像素风格
- **无限地图**：支持拖拽和缩放，无边界限制
- **动态路径生成**：完成区域后自动生成2-3条新路径
- **角色移动动画**：平滑的路径跟随动画

### 🤖 LLM智能学习系统
- **基于课程资料的智能出题**：LLM根据预设课程内容生成相关题目
- **多种开源模型支持**：
  - Ollama (Mistral 7B, Llama2 7B) - 本地运行
  - Hugging Face - 免费API
  - OpenAI兼容API - 开源模型
- **智能对话界面**：与AI导师进行学习交流
- **任务完成机制**：必须回答正确才能解锁下一个区域

## 🚀 快速开始

### 后端设置
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install flask flask-cors
python app.py
```

### 前端设置
```bash
cd frontend
npm install
npm run dev
```

## 🎯 游戏玩法

1. **探索地图**：点击可访问的区域按钮
2. **角色移动**：观看角色沿路径移动的动画
3. **学习交流**：与AI导师进行课程相关对话
4. **知识测试**：回答基于课程资料的智能题目
5. **解锁区域**：只有回答正确才能解锁下一个区域
6. **解锁新路径**：系统自动生成通往新区域的路径

## 🔧 技术架构

### 前端
- **React 18** + **TypeScript**
- **Emotion** - 样式组件
- **Framer Motion** - 动画效果
- **Vite** - 构建工具

### 后端
- **Python Flask** - Web框架
- **Flask-CORS** - 跨域支持
- **随机路径生成算法**

### LLM集成
- **Ollama** - 本地模型运行
- **Hugging Face** - 云端API
- **OpenAI兼容接口** - 开源模型支持
- **智能出题系统** - 基于课程资料自动生成测试题目

## 🎨 自定义配置

### 添加新的LLM模型
在 `frontend/src/components/AreaDialog.tsx` 中修改 `LLM_MODELS` 数组：

```typescript
const LLM_MODELS = [
  { id: 'your-model', name: 'Your Model Name', description: 'Description' },
  // ... 其他模型
]
```

### 修改对话完成条件
在 `AreaDialog.tsx` 中修改 `conversationCount` 的判断条件：

```typescript
{conversationCount >= 5 && ( // 改为5轮对话
  <CompleteButton onClick={handleComplete}>
    🎉 完成对话挑战
  </CompleteButton>
)}
```

## 🌟 特色亮点

- **视觉一致性**：路径和角色动画完全同步
- **响应式设计**：支持不同屏幕尺寸
- **性能优化**：使用requestAnimationFrame进行动画
- **错误处理**：完善的网络错误和异常处理
- **可扩展性**：模块化设计，易于添加新功能

## 🔮 未来计划

- [ ] 支持更多LLM模型
- [ ] 添加语音对话功能
- [ ] 实现多人协作模式
- [ ] 添加成就系统
- [ ] 支持自定义地图主题

## 📝 许可证

MIT License - 自由使用和修改

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**享受与AI的对话冒险吧！** 🚀✨
