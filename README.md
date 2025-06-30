# 🤖 AI投标方案生成系统

基于AI的投标方案辅助生成系统，帮助企业快速生成高质量的技术投标方案。

## ✨ 功能特性

- 📄 **智能文档解析**：支持Word、PDF格式招标文件的自动解析
- 🧠 **AI需求分析**：自动提取技术需求、功能需求、性能指标等关键信息
- 📋 **智能提纲生成**：基于需求分析自动生成方案提纲结构
- ✍️ **内容自动生成**：分章节生成专业的技术方案内容
- 🔄 **差异化处理**：自动改写内容，避免串标风险
- 📊 **工作流管理**：完整的生成流程管理和状态跟踪
- 🌐 **友好界面**：基于Gradio的直观Web界面

## 🏗️ 技术架构

### 核心技术栈
- **后端框架**：FastAPI + LangChain + LangGraph
- **AI模型**：DeepSeek Chat（可配置其他LLM）
- **文档处理**：Unstructured
- **前端界面**：Gradio
- **文档生成**：python-docx

### 系统架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面      │    │   后端API       │    │   AI服务        │
│   (Gradio)      │◄──►│   (FastAPI)     │◄──►│   (DeepSeek)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   工作流引擎    │
                       │   (LangGraph)   │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   文档处理      │
                       │ (Unstructured)  │
                       └─────────────────┘
```

## 🚀 快速开始

### 1. 环境要求
- Python 3.11+
- 8GB+ 内存
- DeepSeek API密钥（或其他LLM API密钥）

### 2. 安装依赖
```bash
# 克隆项目
git clone <repository-url>
cd ai-bidding

# 安装依赖
make install
# 或者
pip install -e .
```

### 3. 配置设置
编辑 `config.toml` 文件，配置API密钥：
```toml
[llm]
provider = "deepseek"
model_name = "deepseek-chat"
api_key = "your-api-key-here"
```

### 4. 启动系统
```bash
# 一键启动（推荐）
python run.py

# 或者分别启动
make run-backend  # 启动后端 (端口8000)
make run-frontend # 启动前端 (端口7860)
```

### 5. 访问系统
- 🌐 前端界面：http://localhost:7860
- 📊 后端API：http://localhost:8000
- 📚 API文档：http://localhost:8000/docs

## 📖 使用指南

### 基本流程
1. **创建项目**：在"项目管理"页面创建新项目
2. **上传文档**：在"文档处理"页面上传招标文件
3. **分析需求**：系统自动解析文档并提取需求
4. **生成方案**：在"方案生成"页面启动完整生成流程
5. **下载结果**：在"输出管理"页面下载生成的Word文档

### 详细步骤

#### 步骤1：项目管理
- 输入项目名称和描述
- 选择是否启用差异化处理
- 点击"创建项目"

#### 步骤2：文档上传
- 选择招标文档（支持PDF、Word格式）
- 点击"上传文档"
- 点击"分析需求"查看需求分析结果

#### 步骤3：方案生成
- 可以先点击"生成提纲"预览方案结构
- 点击"开始完整生成"启动完整流程
- 使用"检查状态"监控生成进度

#### 步骤4：结果下载
- 在"输出管理"页面查看生成的文件
- 下载Word格式的技术方案

## 🛠️ 开发指南

### 项目结构
```
ai-bidding/
├── backend/           # 后端代码
│   ├── api/          # API路由
│   ├── core/         # 核心配置
│   ├── models/       # 数据模型
│   ├── schemas/      # API模式
│   └── services/     # 业务服务
├── frontend/         # 前端代码
├── docs/            # 文档
├── tests/           # 测试
└── config.toml      # 配置文件
```

### 核心模块

#### 文档解析器 (`backend/services/document_parser.py`)
- 使用Unstructured解析各种格式文档
- 支持中英文文档
- 自动分块处理长文档

#### LLM服务 (`backend/services/llm_service.py`)
- 封装AI模型调用
- 提供需求分析、提纲生成、内容生成等功能
- 支持差异化处理

#### 工作流引擎 (`backend/services/workflow_engine.py`)
- 基于LangGraph的状态管理
- 支持流程中断和恢复
- 完整的错误处理

#### 内容生成器 (`backend/services/content_generator.py`)
- 协调整个生成流程
- Word文档生成
- 文件管理

### 扩展开发

#### 添加新的LLM提供商
1. 在 `backend/services/llm_service.py` 中添加新的LLM客户端
2. 更新 `config.toml` 配置选项
3. 测试新提供商的API调用

#### 自定义Prompt模板
在 `backend/services/llm_service.py` 中修改各个方法的system_prompt和user_prompt

#### 添加新的文档格式支持
在 `backend/services/document_parser.py` 中扩展UnstructuredLoader的配置

## 🧪 测试

```bash
# 运行所有测试
make test

# 运行测试并生成覆盖率报告
make test-cov

# 运行特定测试
python -m pytest tests/test_document_parser.py -v

# 代码质量检查
make check
```

## 🐳 Docker 部署

### 快速部署
```bash
# 一键部署
./deploy.sh

# 或者使用 make 命令
make docker-build
make docker-run
```

### 使用 Docker Compose

#### 开发环境
```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

#### 生产环境
```bash
# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d

# 启动包含监控的完整环境
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps
```

### 部署脚本使用

```bash
# 查看帮助
./deploy.sh help

# 完整部署
./deploy.sh deploy

# 只构建镜像
./deploy.sh build

# 启动服务
./deploy.sh start

# 停止服务
./deploy.sh stop

# 查看日志
./deploy.sh logs

# 清理资源
./deploy.sh clean
```

## 🔧 Makefile 使用指南

### 环境管理
```bash
make install      # 安装生产依赖
make dev-install  # 安装开发依赖
make setup        # 初始化项目环境
make clean        # 清理缓存文件
```

### 运行服务
```bash
make run          # 一键启动所有服务
make run-backend  # 只启动后端
make run-frontend # 只启动前端
```

### 测试和质量
```bash
make test         # 运行测试
make test-cov     # 测试+覆盖率报告
make lint         # 代码检查
make format       # 代码格式化
make check        # 完整质量检查
```

### Docker 操作
```bash
make docker-build           # 构建镜像
make docker-run             # 运行容器
make docker-compose-up      # 启动compose
make docker-compose-down    # 停止compose
```

### 开发工具
```bash
make dev-server   # 启动调试服务器
make logs         # 查看日志
make check-config # 检查配置
make status       # 查看项目状态
```

## 📋 TODO

- [ ] 添加数据库持久化
- [ ] 实现用户认证和权限管理
- [ ] 支持更多文档格式
- [ ] 添加模板管理功能
- [ ] 实现批量处理
- [ ] 优化生成速度
- [ ] 添加更多LLM提供商支持

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📞 支持

如有问题，请提交Issue或联系开发团队。
