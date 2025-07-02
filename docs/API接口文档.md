# AI投标方案生成系统 - API接口文档

## 📋 文档信息
- **API版本**：v2.0
- **基础URL**：`http://localhost:8000/api`
- **认证方式**：Bearer Token (JWT)
- **数据格式**：JSON
- **字符编码**：UTF-8

## 📋 目录
- [1. 接口概览](#1-接口概览)
- [2. 认证授权](#2-认证授权)
- [3. 项目管理API](#3-项目管理api)
- [4. 文档管理API](#4-文档管理api)
- [5. 任务管理API](#5-任务管理api)
- [6. 生成服务API](#6-生成服务api)
- [7. 错误处理](#7-错误处理)
- [8. 示例代码](#8-示例代码)

## 1. 接口概览

### 1.1 API特性
- **RESTful设计**：遵循REST架构风格
- **异步处理**：支持长时间任务异步执行
- **状态管理**：完整的任务状态跟踪
- **错误处理**：统一的错误响应格式
- **文档自动生成**：基于OpenAPI 3.0规范

### 1.2 接口分类

| 分类 | 前缀 | 描述 |
|------|------|------|
| 项目管理 | `/projects` | 项目的增删改查操作 |
| 文档管理 | `/documents` | 文档上传、下载、解析 |
| 任务管理 | `/tasks` | 异步任务的创建和管理 |
| 生成服务 | `/generation` | 内容生成相关服务 |
| 系统管理 | `/system` | 系统状态和配置 |

### 1.3 通用响应格式

#### 成功响应
```json
{
  "success": true,
  "data": {
    // 具体数据
  },
  "message": "操作成功",
  "timestamp": "2025-07-02T10:30:00Z"
}
```

#### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": "详细错误信息"
  },
  "timestamp": "2025-07-02T10:30:00Z"
}
```

## 2. 认证授权

### 2.1 获取访问令牌

**接口地址**：`POST /auth/token`

**请求参数**：
```json
{
  "username": "string",
  "password": "string"
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

### 2.2 使用访问令牌

在请求头中添加Authorization字段：
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 3. 项目管理API

### 3.1 创建项目

**接口地址**：`POST /projects/`

**请求参数**：
```json
{
  "name": "智慧城市综合管理平台项目",
  "description": "智慧城市综合管理平台建设项目投标方案",
  "enable_differentiation": true
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "id": "proj_123456789",
    "name": "智慧城市综合管理平台项目",
    "description": "智慧城市综合管理平台建设项目投标方案",
    "status": "created",
    "enable_differentiation": true,
    "created_at": "2025-07-02T10:30:00Z",
    "updated_at": "2025-07-02T10:30:00Z"
  }
}
```

### 3.2 获取项目列表

**接口地址**：`GET /projects/`

**查询参数**：
- `limit` (int, optional): 每页数量，默认20
- `offset` (int, optional): 偏移量，默认0
- `status` (string, optional): 项目状态筛选
- `search` (string, optional): 搜索关键词

**响应示例**：
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "proj_123456789",
        "name": "智慧城市综合管理平台项目",
        "status": "created",
        "created_at": "2025-07-02T10:30:00Z"
      }
    ],
    "total": 1,
    "limit": 20,
    "offset": 0
  }
}
```

### 3.3 获取项目详情

**接口地址**：`GET /projects/{project_id}`

**路径参数**：
- `project_id` (string): 项目ID

**响应示例**：
```json
{
  "success": true,
  "data": {
    "id": "proj_123456789",
    "name": "智慧城市综合管理平台项目",
    "description": "智慧城市综合管理平台建设项目投标方案",
    "status": "completed",
    "document_name": "招标文件.pdf",
    "requirements_analysis": "需求分析结果...",
    "outline": "方案提纲...",
    "sections": [
      {
        "title": "技术方案概述",
        "level": 1,
        "content": "技术方案内容...",
        "is_generated": true
      }
    ],
    "final_document_path": "/outputs/proj_123456789_proposal.docx",
    "enable_differentiation": true,
    "created_at": "2025-07-02T10:30:00Z",
    "updated_at": "2025-07-02T11:00:00Z"
  }
}
```

### 3.4 更新项目

**接口地址**：`PUT /projects/{project_id}`

**请求参数**：
```json
{
  "name": "更新后的项目名称",
  "description": "更新后的项目描述",
  "enable_differentiation": false
}
```

### 3.5 删除项目

**接口地址**：`DELETE /projects/{project_id}`

**响应示例**：
```json
{
  "success": true,
  "message": "项目删除成功"
}
```

## 4. 文档管理API

### 4.1 上传文档

**接口地址**：`POST /documents/upload`

**请求格式**：`multipart/form-data`

**请求参数**：
- `file` (file): 上传的文档文件
- `project_id` (string, optional): 关联的项目ID

**响应示例**：
```json
{
  "success": true,
  "data": {
    "file_name": "招标文件.pdf",
    "file_path": "/uploads/20250702_103000_招标文件.pdf",
    "file_size": 2048576,
    "file_type": ".pdf",
    "upload_time": "2025-07-02T10:30:00Z"
  }
}
```

### 4.2 解析文档

**接口地址**：`POST /documents/parse`

**请求参数**：
```json
{
  "file_path": "/uploads/20250702_103000_招标文件.pdf"
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "file_name": "招标文件.pdf",
    "total_pages": 25,
    "total_chunks": 12,
    "content_preview": "智慧城市综合管理平台建设项目招标文件...",
    "metadata": {
      "document_type": "招标文件",
      "language": "zh-CN",
      "structure": {
        "chapters": 5,
        "sections": 15,
        "tables": 3
      }
    }
  }
}
```

### 4.3 下载文档

**接口地址**：`GET /documents/download/{file_path}`

**路径参数**：
- `file_path` (string): 文件路径（URL编码）

**响应**：文件流下载

## 5. 任务管理API

### 5.1 创建任务

**接口地址**：`POST /tasks/`

**请求参数**：
```json
{
  "project_id": "proj_123456789",
  "task_type": "full_workflow",
  "config": {
    "document_path": "/uploads/20250702_103000_招标文件.pdf",
    "enable_differentiation": true,
    "enable_validation": true,
    "project_name": "智慧城市综合管理平台项目"
  },
  "max_retries": 3
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "id": "task_987654321",
    "project_id": "proj_123456789",
    "task_type": "full_workflow",
    "status": "pending",
    "config": {
      "document_path": "/uploads/20250702_103000_招标文件.pdf",
      "enable_differentiation": true,
      "enable_validation": true,
      "project_name": "智慧城市综合管理平台项目"
    },
    "progress": 0,
    "current_step": null,
    "total_steps": 9,
    "max_retries": 3,
    "retry_count": 0,
    "created_at": "2025-07-02T10:30:00Z"
  }
}
```

### 5.2 获取任务状态

**接口地址**：`GET /tasks/{task_id}/status`

**响应示例**：
```json
{
  "success": true,
  "data": {
    "id": "task_987654321",
    "status": "running",
    "progress": 45,
    "current_step": "generate_content",
    "total_steps": 9,
    "started_at": "2025-07-02T10:30:00Z",
    "estimated_completion": "2025-07-02T11:00:00Z"
  }
}
```

### 5.3 获取任务详情

**接口地址**：`GET /tasks/{task_id}`

**响应示例**：
```json
{
  "success": true,
  "data": {
    "id": "task_987654321",
    "project_id": "proj_123456789",
    "task_type": "full_workflow",
    "status": "success",
    "config": {
      "document_path": "/uploads/20250702_103000_招标文件.pdf",
      "enable_differentiation": true,
      "enable_validation": true
    },
    "progress": 100,
    "current_step": "finalize",
    "total_steps": 9,
    "started_at": "2025-07-02T10:30:00Z",
    "completed_at": "2025-07-02T10:55:00Z",
    "result": {
      "document_path": "/outputs/proj_123456789_proposal.docx",
      "sections_generated": 8,
      "validation_passed": true
    },
    "retry_count": 0,
    "max_retries": 3,
    "created_at": "2025-07-02T10:30:00Z",
    "updated_at": "2025-07-02T10:55:00Z"
  }
}
```

### 5.4 获取任务列表

**接口地址**：`GET /tasks/`

**查询参数**：
- `limit` (int, optional): 每页数量，默认20
- `offset` (int, optional): 偏移量，默认0
- `project_id` (string, optional): 项目ID筛选
- `status` (string, optional): 任务状态筛选
- `task_type` (string, optional): 任务类型筛选

### 5.5 重试任务

**接口地址**：`POST /tasks/{task_id}/retry`

**响应示例**：
```json
{
  "success": true,
  "message": "任务重试已启动",
  "data": {
    "task_id": "task_987654321",
    "retry_count": 1
  }
}
```

### 5.6 取消任务

**接口地址**：`POST /tasks/{task_id}/cancel`

**响应示例**：
```json
{
  "success": true,
  "message": "任务已取消"
}
```

### 5.7 获取任务检查点

**接口地址**：`GET /tasks/{task_id}/checkpoints`

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "id": "checkpoint_001",
      "task_id": "task_987654321",
      "step_name": "parse_document",
      "step_order": 1,
      "is_completed": true,
      "started_at": "2025-07-02T10:30:00Z",
      "completed_at": "2025-07-02T10:31:00Z",
      "duration_seconds": 60
    },
    {
      "id": "checkpoint_002",
      "task_id": "task_987654321",
      "step_name": "analyze_requirements",
      "step_order": 2,
      "is_completed": true,
      "started_at": "2025-07-02T10:31:00Z",
      "completed_at": "2025-07-02T10:33:00Z",
      "duration_seconds": 120
    }
  ]
}
```

## 6. 生成服务API

### 6.1 需求分析

**接口地址**：`POST /generation/analyze`

**请求参数**：
```json
{
  "file_path": "/uploads/20250702_103000_招标文件.pdf"
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "analysis": "需求分析结果...",
    "requirements": {
      "technical": ["微服务架构", "高可用性", "可扩展性"],
      "functional": ["数据采集", "数据处理", "可视化展示"],
      "performance": ["并发用户数≥1000", "处理延迟≤3秒", "可用性≥99.9%"],
      "qualification": ["软件开发资质", "项目经验要求"]
    },
    "risk_points": ["技术复杂度高", "项目周期紧张"],
    "scoring_criteria": {
      "technical_solution": 40,
      "implementation_plan": 30,
      "team_capability": 20,
      "commercial_proposal": 10
    }
  }
}
```

### 6.2 生成提纲

**接口地址**：`POST /generation/outline`

**请求参数**：
```json
{
  "requirements_analysis": "需求分析结果..."
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "outline": "技术方案提纲...",
    "sections": [
      {
        "title": "项目概述",
        "level": 1,
        "order": 1,
        "requirements": ["项目背景", "建设目标"]
      },
      {
        "title": "技术方案",
        "level": 1,
        "order": 2,
        "requirements": ["系统架构", "技术选型"]
      }
    ],
    "coverage_rate": 98.5
  }
}
```

### 6.3 生成章节内容

**接口地址**：`POST /generation/content`

**请求参数**：
```json
{
  "section_title": "技术方案",
  "requirements": "系统架构要求：采用微服务架构...",
  "context": "项目背景和需求分析结果..."
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "content": "技术方案详细内容...",
    "word_count": 1500,
    "generation_time": 120
  }
}
```

### 6.4 差异化处理

**接口地址**：`POST /generation/differentiate`

**请求参数**：
```json
{
  "original_content": "原始内容...",
  "section_title": "技术方案"
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "differentiated_content": "差异化后的内容...",
    "similarity_score": 0.25,
    "changes_made": [
      "同义词替换",
      "句式调整",
      "段落重组"
    ]
  }
}
```

### 6.5 完整方案生成

**接口地址**：`POST /generation/full`

**请求参数**：
```json
{
  "project_id": "proj_123456789",
  "document_path": "/uploads/20250702_103000_招标文件.pdf"
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "task_id": "task_987654321",
    "message": "方案生成任务已启动",
    "estimated_duration": "25-30分钟"
  }
}
```

## 7. 错误处理

### 7.1 错误代码

| 错误代码 | HTTP状态码 | 描述 |
|----------|------------|------|
| `INVALID_REQUEST` | 400 | 请求参数无效 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `FORBIDDEN` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 方法不允许 |
| `CONFLICT` | 409 | 资源冲突 |
| `VALIDATION_ERROR` | 422 | 数据验证失败 |
| `INTERNAL_ERROR` | 500 | 内部服务器错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 |

### 7.2 错误响应示例

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "field": "project_id",
      "message": "项目ID不能为空"
    }
  },
  "timestamp": "2025-07-02T10:30:00Z"
}
```

## 8. 示例代码

### 8.1 Python示例

```python
import requests
import json

# 基础配置
BASE_URL = "http://localhost:8000/api"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your_access_token"
}

# 创建项目
def create_project():
    url = f"{BASE_URL}/projects/"
    data = {
        "name": "智慧城市综合管理平台项目",
        "description": "智慧城市综合管理平台建设项目投标方案",
        "enable_differentiation": True
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# 上传文档
def upload_document(file_path):
    url = f"{BASE_URL}/documents/upload"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, headers={"Authorization": headers["Authorization"]}, files=files)
    
    return response.json()

# 启动完整工作流
def start_full_workflow(project_id, document_path):
    url = f"{BASE_URL}/tasks/"
    data = {
        "project_id": project_id,
        "task_type": "full_workflow",
        "config": {
            "document_path": document_path,
            "enable_differentiation": True,
            "enable_validation": True
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# 查询任务状态
def get_task_status(task_id):
    url = f"{BASE_URL}/tasks/{task_id}/status"
    response = requests.get(url, headers=headers)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 1. 创建项目
    project = create_project()
    project_id = project["data"]["id"]
    
    # 2. 上传文档
    upload_result = upload_document("招标文件.pdf")
    document_path = upload_result["data"]["file_path"]
    
    # 3. 启动工作流
    task = start_full_workflow(project_id, document_path)
    task_id = task["data"]["id"]
    
    # 4. 监控任务状态
    import time
    while True:
        status = get_task_status(task_id)
        print(f"任务状态: {status['data']['status']}, 进度: {status['data']['progress']}%")
        
        if status["data"]["status"] in ["success", "failed"]:
            break
        
        time.sleep(10)
```

### 8.2 JavaScript示例

```javascript
const BASE_URL = 'http://localhost:8000/api';
const ACCESS_TOKEN = 'your_access_token';

// 通用请求函数
async function apiRequest(endpoint, options = {}) {
    const url = `${BASE_URL}${endpoint}`;
    const config = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${ACCESS_TOKEN}`,
            ...options.headers
        },
        ...options
    };

    const response = await fetch(url, config);
    return response.json();
}

// 创建项目
async function createProject() {
    return apiRequest('/projects/', {
        method: 'POST',
        body: JSON.stringify({
            name: '智慧城市综合管理平台项目',
            description: '智慧城市综合管理平台建设项目投标方案',
            enable_differentiation: true
        })
    });
}

// 启动完整工作流
async function startFullWorkflow(projectId, documentPath) {
    return apiRequest('/tasks/', {
        method: 'POST',
        body: JSON.stringify({
            project_id: projectId,
            task_type: 'full_workflow',
            config: {
                document_path: documentPath,
                enable_differentiation: true,
                enable_validation: true
            }
        })
    });
}
```

### 8.3 cURL示例

```bash
# 创建项目
curl -X POST "http://localhost:8000/api/projects/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_access_token" \
  -d '{
    "name": "智慧城市综合管理平台项目",
    "description": "智慧城市综合管理平台建设项目投标方案",
    "enable_differentiation": true
  }'

# 上传文档
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer your_access_token" \
  -F "file=@招标文件.pdf"

# 启动完整工作流
curl -X POST "http://localhost:8000/api/tasks/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_access_token" \
  -d '{
    "project_id": "proj_123456789",
    "task_type": "full_workflow",
    "config": {
      "document_path": "/uploads/招标文件.pdf",
      "enable_differentiation": true,
      "enable_validation": true
    }
  }'

# 查询任务状态
curl -X GET "http://localhost:8000/api/tasks/task_987654321/status" \
  -H "Authorization: Bearer your_access_token"
```

---

**文档版本**：v2.0
**最后更新**：2025-07-02
**维护人员**：AI投标系统开发团队
**在线文档**：http://localhost:8000/docs
