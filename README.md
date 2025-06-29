## AI-BIDDING

AI 增强的投标方案辅助生成系统

### 项目结构

```
ai-bidding/
├── Makefile
├── pyproject.toml
├── config.toml
├── .gitignore
├── README.md
├── docs/
│   ├── 需求.md
│   └── 技术方案.md
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── projects.py
│   │   │   ├── documents.py
│   │   │   └── generation.py
│   │   └── deps.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── document.py
│   │   └── generation.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── document.py
│   │   └── generation.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_parser.py
│   │   ├── llm_service.py
│   │   ├── workflow_engine.py
│   │   └── content_generator.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   └── generation_tasks.py
│   └── utils/
│       ├── __init__.py
│       └── file_handler.py
├── frontend/
│   ├── __init__.py
│   ├── app.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── upload.py
│   │   ├── analysis.py
│   │   ├── generation.py
│   │   └── export.py
│   └── styles.css
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_document_parser.py
    └── test_llm_service.py
```

### 项目运行

1. 安装依赖

```bash
make install
make dev-install
```
