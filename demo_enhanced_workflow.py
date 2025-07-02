#!/usr/bin/env python3
"""
增强工作流演示脚本
演示从招标书001.docx到投标书生成的完整流程
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_enhanced_workflow():
    """演示增强的工作流"""
    print("🚀 开始演示增强的AI投标工作流")
    print("=" * 60)
    
    try:
        # 1. 导入必要的模块
        from backend.services.enhanced_document_parser import enhanced_document_parser
        from backend.services.enhanced_output_parser import enhanced_output_parser
        from backend.models.generation import WorkflowState
        from backend.services.enhanced_workflow_engine import enhanced_workflow_engine
        
        print("✅ 模块导入成功")
        
        # 2. 解析招标文档
        print("\n📄 步骤1: 解析招标文档")
        tender_doc_path = Path("temp_docs/招标书001.docx")
        
        if not tender_doc_path.exists():
            print(f"❌ 招标文档不存在: {tender_doc_path}")
            return
        
        # 使用增强的文档解析器
        parsed_result = enhanced_document_parser.parse_tender_document(tender_doc_path)
        
        print(f"✅ 文档解析完成:")
        print(f"   - 文件名: {parsed_result['file_name']}")
        print(f"   - 总页数: {parsed_result['metadata']['total_pages']}")
        print(f"   - 强制性条款: {parsed_result['metadata']['mandatory_clauses_count']} 个")
        print(f"   - 重要参数: {parsed_result['metadata']['important_clauses_count']} 个")
        print(f"   - 评分标准: {parsed_result['metadata']['scoring_criteria_count']} 个")
        
        # 显示项目基本信息
        project_info = parsed_result['structured_data']['project_info']
        print(f"\n📋 项目基本信息:")
        print(f"   - 项目名称: {project_info.name}")
        print(f"   - 预算: {project_info.budget}")
        print(f"   - 招标人: {project_info.client}")
        
        # 显示部分强制性要求
        mandatory_clauses = parsed_result['structured_data']['mandatory_clauses']
        print(f"\n⭐ 强制性要求示例（前3个）:")
        for i, clause in enumerate(mandatory_clauses[:3]):
            print(f"   {i+1}. {clause.content[:80]}...")
        
        # 3. 创建工作流状态
        print("\n🔄 步骤2: 创建工作流状态")
        
        initial_state = WorkflowState(
            project_id=f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            current_step="start",
            document_content=parsed_result['full_content'],
            enable_differentiation=True,
            enable_validation=True,
            structured_data=parsed_result['structured_data']
        )
        
        print(f"✅ 工作流状态创建完成:")
        print(f"   - 项目ID: {initial_state.project_id}")
        print(f"   - 文档长度: {len(initial_state.document_content)} 字符")
        print(f"   - 启用差异化: {initial_state.enable_differentiation}")
        print(f"   - 启用校验: {initial_state.enable_validation}")
        
        # 4. 模拟关键需求提取（简化版）
        print("\n🔍 步骤3: 提取关键需求")
        
        # 提取强制性要求
        mandatory_requirements = [clause.content for clause in mandatory_clauses[:5]]
        important_clauses = parsed_result['structured_data']['important_clauses']
        important_requirements = [clause.content for clause in important_clauses[:5]]
        
        print(f"✅ 关键需求提取完成:")
        print(f"   - 强制性要求: {len(mandatory_requirements)} 个")
        print(f"   - 重要参数: {len(important_requirements)} 个")
        
        # 5. 模拟生成简化的投标方案
        print("\n📝 步骤4: 生成投标方案大纲")
        
        # 创建简化的章节结构
        from backend.services.enhanced_output_parser import DocumentSection
        
        demo_sections = [
            DocumentSection(
                title="项目概述",
                level=1,
                content=f"""
## 1.1 项目背景与理解

{project_info.name}是一个重要的技术升级项目，旨在提升IPTV平台的用户体验和系统性能。

## 1.2 建设目标

本项目将实现以下核心目标：
- 完成EPG前端页面改版，提升用户界面体验
- 扩展可视化编辑工具功能，支持更灵活的内容管理
- 确保系统安全性，满足等保三级要求
- 保障系统高性能，支持大规模用户并发访问

## 1.3 招标内容理解

我们深度理解招标方的核心需求：
{mandatory_requirements[0] if mandatory_requirements else '核心技术要求'}

## 1.4 投标响应承诺

我方承诺严格按照招标文件要求，提供完整的技术方案和优质的实施服务。
                """,
                section_type="normal"
            ),
            DocumentSection(
                title="总体设计思路与技术架构",
                level=1,
                content="""
## 2.1 设计原则与理念

基于"安全、稳定、高效、可扩展"的设计理念，采用先进的技术架构和成熟的解决方案。

## 2.2 总体系统架构设计

采用微服务架构，确保系统的可扩展性和可维护性：
- 前端展示层：基于Vue.js的响应式用户界面
- 业务逻辑层：Spring Boot微服务架构
- 数据存储层：MySQL + Redis的混合存储方案
- 基础设施层：Docker容器化部署

## 2.3 技术路线选型

- 前端技术：Vue.js 3.0 + Element Plus
- 后端技术：Spring Boot 2.7 + Spring Cloud
- 数据库：MySQL 8.0 + Redis 6.0
- 消息队列：RabbitMQ
- 监控运维：Prometheus + Grafana

## 2.4 关键技术方案

针对高并发访问需求，采用分布式缓存和负载均衡技术，确保系统稳定运行。
                """,
                section_type="technical"
            ),
            DocumentSection(
                title="系统安全设计",
                level=1,
                content="""
## 4.1 安全体系架构

建立多层次的安全防护体系，确保系统安全可靠。

## 4.2 安全防护措施

- 身份认证：基于JWT的统一身份认证
- 权限控制：RBAC角色权限管理
- 数据加密：敏感数据AES加密存储
- 传输安全：全站HTTPS加密传输

## 4.3 等保合规设计

严格按照等保三级要求进行安全设计：
- 访问控制：多因子身份认证
- 安全审计：完整的操作日志记录
- 数据保护：数据备份和恢复机制
- 安全管理：安全策略和应急响应

## 4.4 数据安全保障

建立完善的数据安全保障机制，确保用户数据和业务数据的安全性。
                """,
                section_type="normal"
            ),
            DocumentSection(
                title="项目实施与管理",
                level=1,
                content="""
## 6.1 项目组织架构

组建专业的项目团队，包括项目经理、技术架构师、开发工程师、测试工程师等。

## 6.2 实施计划与里程碑

项目总工期1个月，分为以下阶段：
- 第1周：需求确认和详细设计
- 第2-3周：系统开发和集成测试
- 第4周：系统部署和验收

## 6.3 质量保障措施

建立完善的质量管理体系：
- 代码审查：严格的代码质量控制
- 自动化测试：单元测试和集成测试
- 性能测试：压力测试和性能优化
- 安全测试：安全漏洞扫描和修复

## 6.4 风险管控方案

识别项目风险并制定应对措施：
- 技术风险：技术预研和备选方案
- 进度风险：合理的时间安排和资源配置
- 质量风险：严格的测试和验收标准
                """,
                section_type="normal"
            )
        ]
        
        print(f"✅ 投标方案大纲生成完成:")
        print(f"   - 章节数量: {len(demo_sections)} 个")
        for section in demo_sections:
            print(f"   - {section.title} ({section.section_type})")
        
        # 6. 生成专业Word文档
        print("\n📄 步骤5: 生成专业Word文档")
        
        metadata = {
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "项目ID": initial_state.project_id,
            "文档类型": "投标技术方案书",
            "强制性要求数量": len(mandatory_requirements),
            "重要参数数量": len(important_requirements),
            "预算": project_info.budget or "未指定"
        }
        
        project_name = "广东IPTV可视化编辑工具项目投标方案"
        document_path = enhanced_output_parser.create_professional_word_document(
            demo_sections, 
            project_name, 
            metadata
        )
        
        print(f"✅ 专业Word文档生成完成:")
        print(f"   - 文档路径: {document_path}")
        print(f"   - 文档大小: {document_path.stat().st_size / 1024:.1f} KB")
        
        # 7. 总结
        print("\n🎉 演示完成总结")
        print("=" * 60)
        print("✅ 成功完成以下功能演示:")
        print("   1. 招标文档结构化解析")
        print("   2. 关键需求自动提取")
        print("   3. 投标方案大纲生成")
        print("   4. 专业Word文档输出")
        print("\n📊 处理结果统计:")
        print(f"   - 解析文档页数: {parsed_result['metadata']['total_pages']}")
        print(f"   - 提取强制性条款: {len(mandatory_requirements)}")
        print(f"   - 生成章节数量: {len(demo_sections)}")
        print(f"   - 输出文档大小: {document_path.stat().st_size / 1024:.1f} KB")
        
        print(f"\n📁 生成的投标方案文档: {document_path}")
        print("💡 建议：可以打开生成的Word文档查看完整的投标方案格式")
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🎯 AI投标系统增强工作流演示")
    print("本演示将展示从招标书解析到投标方案生成的完整流程")
    print("-" * 60)
    
    # 运行演示
    asyncio.run(demo_enhanced_workflow())
