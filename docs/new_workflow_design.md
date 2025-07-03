# 优化后的AI投标LangGraph工作流设计

## 🎯 核心改进

基于您的需求，我们重新设计了LangGraph工作流，实现了以下核心改进：

### 1. 层次化目录遍历
- **章节树结构**: 使用`SectionNode`类构建真正的树形结构
- **叶子节点优先**: 先生成最底层的具体内容
- **父节点总结**: 基于子节点内容生成上级总结

### 2. 专业化Prompt模板
- **IPTV领域专家**: 使用您提供的专业prompt
- **紧扣招标需求**: 避免自由发挥和内容扩散
- **技术架构图**: 支持PlantUML/Mermaid代码生成

## 🔄 新工作流节点

### 节点1: 解析招标文档 (`parse_document`)
```python
输入: 招标文档内容
处理: 清理和预处理文档内容
输出: 标准化的文档内容
```

### 节点2: 生成IPTV提纲 (`generate_outline`)
```python
输入: 招标文档内容
Prompt: 您提供的IPTV专家prompt
输出: 层次化的markdown提纲
```

### 节点3: 构建章节树 (`build_section_tree`)
```python
输入: markdown提纲
处理: 解析为SectionNode树结构
输出: 层次化的章节树 + 扁平章节列表
```

### 节点4: 生成叶子节点内容 (`generate_leaf_content`)
```python
输入: 章节树 + 招标文档
处理: 
  1. 识别所有叶子节点
  2. 使用IPTV专业prompt生成内容
  3. 支持mermaid图表代码
输出: 所有叶子节点的具体内容
```

### 节点5: 生成父节点总结 (`generate_parent_summaries`)
```python
输入: 已生成内容的章节树
处理:
  1. 从最深层开始向上遍历
  2. 收集子节点内容
  3. 生成总结性、串联性文案
输出: 所有父节点的总结内容
```

### 节点6: 差异化处理 (`differentiate_content`)
```python
输入: 完整的章节树
处理: 对所有节点内容进行LLM改写
输出: 差异化后的内容（30-40%差异度）
```

## 🌳 章节树结构设计

### SectionNode类
```python
class SectionNode:
    title: str              # 章节标题
    level: int              # 层级（1,2,3,4...）
    order: int              # 顺序号
    children: List[SectionNode]  # 子节点
    parent: SectionNode     # 父节点
    content: str            # 生成的内容
    is_generated: bool      # 是否已生成
    is_leaf: bool           # 是否为叶子节点
```

### 树形结构示例
```
技术方案
├── 1. 系统架构设计
│   ├── 1.1 总体架构 (叶子)
│   ├── 1.2 技术架构
│   │   ├── 1.2.1 前端架构 (叶子)
│   │   └── 1.2.2 后端架构 (叶子)
│   └── 1.3 部署架构 (叶子)
├── 2. 功能设计
│   ├── 2.1 核心功能 (叶子)
│   └── 2.2 扩展功能 (叶子)
└── 3. 实施方案
    ├── 3.1 实施计划 (叶子)
    └── 3.2 风险控制 (叶子)
```

## 📝 优化的Prompt模板

### 生成目录Prompt
```
我的顶层目标，是编写一份投标方案的技术方案部分；
你需要扮演一位广电IPTV领域的行业专家，解决方案达人；
需要注意，后续所有的工作，都要紧密围绕上传的招标方案，尤其避免出现编写方案时自由发挥和扩散的情况。因此，你始终要记住这份方案的内容；
然后，你输出一份完整的投标技术方案的完整提纲，提纲要求完整扫描用户需求，结构化安排章节内容，提纲的各子章节不能有漏项；
由于公司有固定模板，因此提纲不要编排包含"售后"、"验收"和"质量保障"相关的章节；
输出提纲时，不要加说明性文字。

招标内容如下：{招标文档内容}
```

### 生成正文Prompt
```
我的顶层目标，是编写一份投标方案的技术方案部分；
你需要扮演一位广电IPTV领域的行业专家，解决方案达人；
需要注意，后续所有的工作，都要紧密围绕上传的招标方案，尤其避免出现编写方案时自由发挥和扩散的情况。因此，你始终要记住这份方案的内容；
编制内容时，方案应尽可能贴合招标方案中提到的需求点，围绕需求点展开设计描述，但不要直接照抄原文；
涉及到技术实现的描述，应该更加偏逻辑描述，避免提到非常具体的技术栈；
涉及到需要架构设计的内容，应用plantuml(mermaid/Graphviz)的代码输出架构设计；
涉及到需要业务流程或系统流程、时序图等内容，同样用plantuml(mermaid/Graphviz)的代码输出流程设计。

章节标题如下：{章节标题}
招标内容如下：{招标文档内容}
```

## 🔧 技术实现要点

### 1. 章节树解析算法
- 支持markdown格式标题（#, ##, ###, ####）
- 支持数字编号格式（1., 1.1, 1.1.1）
- 支持缩进格式识别
- 自动构建父子关系

### 2. 叶子节点识别
```python
def get_all_leaf_nodes(self) -> List[SectionNode]:
    if self.is_leaf:
        return [self]
    
    leaf_nodes = []
    for child in self.children:
        leaf_nodes.extend(child.get_all_leaf_nodes())
    return leaf_nodes
```

### 3. 递归内容生成
```python
async def _generate_node_summary_recursive(self, node: SectionNode, document_content: str):
    # 叶子节点直接返回
    if node.is_leaf:
        return
    
    # 先确保所有子节点都有内容
    for child in node.children:
        await self._generate_node_summary_recursive(child, document_content)
    
    # 收集子节点内容并生成父节点总结
    children_content = [f"### {child.title}\n{child.content}" for child in node.children if child.content]
    # ... 生成总结
```

## 🎯 预期效果

### 1. 内容质量提升
- **专业性**: IPTV领域专家级别的内容
- **针对性**: 紧密贴合招标需求，无冗余内容
- **逻辑性**: 层次清晰，承上启下

### 2. 生成效率优化
- **并行处理**: 叶子节点可以并行生成
- **增量生成**: 支持单独重新生成某个章节
- **状态恢复**: LangGraph支持中断恢复

### 3. 差异化保证
- **结构差异**: 不同项目的章节结构可能不同
- **内容差异**: LLM改写确保30-40%差异度
- **表述差异**: 同义词替换和句式变换

## 🚀 使用方式

### 1. 启动工作流
```python
from backend.services.workflow_engine import workflow_engine
from backend.models.generation import WorkflowState

state = WorkflowState(
    project_id="project_001",
    current_step="start",
    document_content=document_content,
    enable_differentiation=True
)

final_state = await workflow_engine.run_workflow(state)
```

### 2. 检查结果
```python
if final_state.error:
    print(f"工作流失败: {final_state.error}")
else:
    print(f"生成了{len(final_state.sections)}个章节")
    for section in final_state.sections:
        print(f"- {section['title']} ({'叶子' if section['is_leaf'] else '父节点'})")
```

## 📊 测试验证

运行测试脚本验证新工作流：
```bash
python test_new_workflow.py
```

测试内容包括：
- 章节树构建测试
- 文档解析测试  
- 完整工作流测试
- 叶子节点识别测试
- 父节点总结测试

## 🔮 后续优化方向

1. **图表生成**: 集成PlantUML/Mermaid渲染引擎
2. **模板管理**: 支持多种投标模板
3. **质量检查**: 增加内容质量评估机制
4. **并行优化**: 叶子节点并行生成
5. **缓存机制**: 避免重复生成相同内容
