export interface CourseMaterial {
  subject: string
  materials: string[]
  difficulty: 'easy' | 'medium' | 'hard'
  category: string
  knowledgePointCount: number
}

export interface KnowledgePoint {
  id: string
  title: string
  content: string
  difficulty: 'easy' | 'medium' | 'hard'
}

export interface Question {
  id: string
  question: string
  options: string[]
  correctAnswer: number
  explanation: string
}

export const COURSE_MATERIALS: Record<string, CourseMaterial> = {
  'area1': {
    subject: '计算机网络基础',
    materials: [
      'OSI七层模型：物理层、数据链路层、网络层、传输层、会话层、表示层、应用层',
      'TCP/IP协议栈：网络接口层、网络层、传输层、应用层',
      'IP地址分类：A类(1-126)、B类(128-191)、C类(192-223)',
      'TCP vs UDP：TCP可靠连接，UDP不可靠无连接',
      'HTTP协议特性：无状态、请求-响应模式、支持多种方法'
    ],
    difficulty: 'medium',
    category: '网络通信',
    knowledgePointCount: 5
  },
  'area2': {
    subject: '数据结构与算法',
    materials: [
      '数组与链表：数组连续存储，链表离散存储',
      '栈与队列：栈后进先出，队列先进先出',
      '二叉树：每个节点最多有两个子节点',
      '哈希表：通过哈希函数快速查找数据',
      '排序算法：冒泡排序、快速排序、归并排序等'
    ],
    difficulty: 'hard',
    category: '算法设计',
    knowledgePointCount: 5
  },
  'area3': {
    subject: '操作系统原理',
    materials: [
      '进程与线程：进程是资源分配单位，线程是执行单位',
      '死锁条件：互斥、占有等待、非抢占、循环等待',
      '虚拟内存：将物理内存和磁盘空间结合使用',
      '文件系统：组织和管理文件存储的机制',
      '调度算法：先来先服务、短作业优先、时间片轮转等'
    ],
    difficulty: 'hard',
    category: '系统软件',
    knowledgePointCount: 5
  },
  'area4': {
    subject: '数据库系统',
    materials: [
      '关系数据库：基于关系模型的数据库系统',
      'SQL语言：结构化查询语言，用于操作数据库',
      '事务ACID：原子性、一致性、隔离性、持久性',
      '索引优化：提高查询效率的数据结构',
      '数据库范式：第一范式、第二范式、第三范式等'
    ],
    difficulty: 'medium',
    category: '数据管理',
    knowledgePointCount: 5
  },
  'area5': {
    subject: '软件工程',
    materials: [
      '软件生命周期：需求分析、设计、编码、测试、维护',
      '敏捷开发：迭代开发、持续交付、团队协作',
      '设计模式：单例模式、工厂模式、观察者模式等',
      '版本控制：Git等工具管理代码版本',
      '测试方法：单元测试、集成测试、系统测试'
    ],
    difficulty: 'medium',
    category: '开发方法',
    knowledgePointCount: 5
  }
}

// Get course material for specified area
export const getCourseMaterial = (areaId: string): CourseMaterial | null => {
  return COURSE_MATERIALS[areaId] || null
}

// Get all course categories
export const getCourseCategories = (): string[] => {
  const categories = new Set<string>()
  Object.values(COURSE_MATERIALS).forEach(material => {
    categories.add(material.category)
  })
  return Array.from(categories)
}

// Get courses by difficulty level
export const getCoursesByDifficulty = (difficulty: 'easy' | 'medium' | 'hard'): CourseMaterial[] => {
  return Object.values(COURSE_MATERIALS).filter(material => material.difficulty === difficulty)
}

// Get courses by category
export const getCoursesByCategory = (category: string): CourseMaterial[] => {
  return Object.values(COURSE_MATERIALS).filter(material => material.category === category)
}
