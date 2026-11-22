# P1 系统架构与 API 开发任务清单

**文件路径：** `docs/product/architecture-and-api-development-backlog.md`  
**产品：** P1 Ontology Engineering Platform  
**版本：** V1.0  
**日期：** 2026-11-21  
**状态：** 架构与研发规划基线，待评审

---

## 1. 文档目的

本文档将 P1 产品需求转化为系统架构、API 资源设计和可执行研发任务。

主要目标：

1. 明确系统整体架构和模块边界。
2. 确定首期技术栈和部署单元。
3. 规划核心 API 资源及接口。
4. 定义异步任务和状态管理机制。
5. 建立开发 Epic 和实施顺序。
6. 明确开发完成、测试通过和产品验收的标准。

本文件描述目标设计和研发计划，不代表相关系统已经实现。

## 2. 架构设计原则

### 2.1 模块化单体优先

P1 首期采用：

**Modular Monolith + Asynchronous Worker**

即一个主要后端应用，内部按业务模块划分，耗时任务通过独立 Worker 执行。

不建议 MVP 一开始就拆分为大量微服务。

原因：

- 首期业务边界仍在验证；
- 模块之间存在较多事务和数据依赖；
- 微服务会增加部署、通信、监控和调试成本；
- 模块化单体能够保留未来拆分的空间。

### 2.2 语义核心与外部引擎解耦

本体元模型、版本和发布资产应由 P1 自身管理。

外部组件负责特定技术能力：

- RDFLib：RDF 解析和序列化；
- pySHACL：SHACL 验证；
- JSON Schema：结构校验；
- LLM Provider：AI 候选生成；
- 数据连接器：外部元数据采集；
- 图形组件：本体关系展示。

外部引擎不应成为平台唯一的数据系统或业务状态管理中心。

### 2.3 AI 结果与正式资产隔离

AI 发现引擎输出候选对象。

候选进入审核流程后，经过必要的验证和转换，才能成为正式本体对象。

模型输出不得直接绕过项目权限、审核和版本控制。

### 2.4 标准优先，内部模型稳定

平台内部采用统一的领域模型。

通过适配器处理 RDF、OWL、SHACL、JSON Schema 等外部格式。

不能让某一种文件格式直接决定所有内部业务对象的存储结构。

### 2.5 可追溯性贯穿全流程

以下操作都应保留必要记录：

- 项目创建；
- 本体创建和编辑；
- 文件导入；
- 数据源采集；
- AI 模型调用；
- 候选审核；
- 质量验证；
- 版本创建；
- 发布和导出；
- 权限变更。

---

## 3. 总体系统架构

### 3.1 架构分层

```text
┌──────────────────────────────────────────────┐
│                 用户交互层                    │
│                                              │
│  Project Portal | Ontology Editor            │
│  Validation UI  | Version UI | Admin UI      │
└──────────────────────┬───────────────────────┘
                       │
                       v
┌──────────────────────────────────────────────┐
│                  API 层                      │
│                                              │
│  REST API | Authentication | Authorization  │
│  Request Validation | Error Handling         │
└──────────────────────┬───────────────────────┘
                       │
                       v
┌──────────────────────────────────────────────┐
│                应用服务层                     │
│                                              │
│ Project Service       Ontology Service      │
│ Import/Export Service Validation Service     │
│ Version Service       Publication Service   │
│ IAM/Audit Service     Job Service            │
└──────────────────────┬───────────────────────┘
                       │
                       v
┌──────────────────────────────────────────────┐
│                 语义核心层                    │
│                                              │
│ Platform Meta-model                          │
│ Ontology Domain Model                         │
│ RDF/OWL Mapping                               │
│ SHACL / JSON Schema Validation                │
│ Version & Change Model                        │
└──────────────────────┬───────────────────────┘
                       │
                       v
┌──────────────────────────────────────────────┐
│                 基础设施层                    │
│                                              │
│ PostgreSQL | MinIO/S3 | Redis                 │
│ Celery Worker | File Processing              │
│ Logging | Metrics | Backup                    │
└──────────────────────────────────────────────┘
```

### 3.2 异步任务执行架构

以下任务不应阻塞 HTTP 请求：

- 大型本体文件导入；
- 本体导出；
- 复杂质量验证；
- 数据源元数据采集；
- AI 本体发现；
- 批量模型处理。

建议使用统一的后台任务机制。

```text
Frontend
   |
   v
API Server
   |
   v
Job Service
   |
   +----> PostgreSQL: Job Metadata
   |
   +----> Redis: Task Queue
                 |
                 v
             Celery Worker
                 |
          +------+------+
          |      |      |
          v      v      v
       Import  Validate Export
          |      |      |
          +------+------+
                 |
                 v
          PostgreSQL / MinIO
                 |
                 v
          Job Status Update
```

Redis 负责任务队列，不作为任务业务记录的唯一持久化来源。

PostgreSQL 保存任务状态和必要结果引用。Worker 应支持失败重试、幂等执行和任务超时控制。

---

## 4. 系统模块与代码边界

建议后端按以下模块组织。

| 模块编号 | 模块 | 主要职责 |
|---|---|---|
| MOD-01 | Project Management | 项目、领域和成员 |
| MOD-02 | Ontology Core | 本体元模型和对象管理 |
| MOD-03 | Ontology Editor | 编辑、导入协调 |
| MOD-04 | Connector Management | 数据源和连接器 |
| MOD-05 | Metadata Management | 元数据采集和目录 |
| MOD-06 | Discovery Engine | AI 本体发现 |
| MOD-07 | Review & Evidence | 审核、证据和冲突 |
| MOD-08 | Validation Engine | 结构和语义验证 |
| MOD-09 | Version Management | 快照、差异和变更 |
| MOD-10 | Publication & Export | 发布、导出 |
| MOD-11 | Visualization | 本体关系图数据 |
| MOD-12 | IAM & Audit | 身份、权限和审计 |
| MOD-13 | Job & Observability | 后台任务和运行观测 |

### 4.1 MVP 模块实施边界

首期重点建设：

- MOD-01；
- MOD-02；
- MOD-03；
- MOD-08；
- MOD-09；
- MOD-10；
- MOD-12；
- MOD-13。

MOD-04 至 MOD-07 可以先定义接口和扩展点，不要求在首期全部实现。

MOD-11 可以先提供简单的本体关系图查询接口，图形界面逐步完善。

### 4.2 模块依赖原则

1. MOD-02 不依赖前端 UI。
2. MOD-08 通过明确的验证输入执行检查，不直接修改本体。
3. MOD-09 管理稳定快照，不负责本体编辑。
4. MOD-10 只能发布满足发布条件的版本。
5. MOD-12 提供统一的认证、授权和审计服务。
6. MOD-13 负责后台任务生命周期，不承载具体领域业务。
7. 外部连接器不得绕过 MOD-12 的权限和访问控制。

---

## 5. 技术栈与依赖组件

### 5.1 前端

| 组件 | 技术建议 | 用途 |
|---|---|---|
| 前端框架 | React / Next.js | Web 应用 |
| 语言 | TypeScript | 类型安全 |
| UI | 选定的 React UI 组件库 | 基础交互 |
| 数据请求 | TanStack Query 或等效方案 | API 数据管理 |
| 图形可视化 | Cytoscape.js | 本体结构图 |
| 表单验证 | Zod 或等效方案 | 前端数据校验 |

### 5.2 后端

| 组件 | 技术建议 | 用途 |
|---|---|---|
| Web 框架 | FastAPI | REST API |
| 语言 | Python | 业务逻辑 |
| 数据校验 | Pydantic | 请求和响应模型 |
| ORM | SQLAlchemy | 数据访问 |
| 数据迁移 | Alembic | 数据库迁移 |
| 异步任务 | Celery | 后台任务 |
| 任务队列 | Redis | 任务分发 |

### 5.3 语义处理

| 组件 | 用途 |
|---|---|
| RDFLib | RDF 图处理、解析、序列化 |
| pySHACL | SHACL 约束验证 |
| JSON Schema | 结构校验 |
| Owlready2（可选） | OWL 处理的补充能力 |
| 外部 OWL 工具（按需） | 复杂本体推理和互操作 |

具体版本、许可证和兼容性应在技术选型评审中确认。

### 5.4 存储与运行环境

| 组件 | 用途 |
|---|---|
| PostgreSQL | 业务数据和元模型 |
| MinIO / S3 | 文件和版本快照 |
| Redis | 异步任务队列 |
| Docker | 容器化 |
| Docker Compose | MVP 部署 |
| OIDC / Keycloak（可选） | 企业身份认证 |
| Prometheus / Grafana（后续） | 指标监控 |

### 5.5 首期不强制引入的组件

- 独立图数据库；
- 独立向量数据库；
- Kubernetes；
- Kafka；
- 专用 RDF 三元组存储；
- 独立微服务注册中心。

这些组件可以在后续根据实际查询规模、集成需求和部署环境评估引入。

---

## 6. API 设计原则

### 6.1 统一接口规范

建议使用 REST API，统一采用：

- JSON 请求和响应；
- UUID 或稳定资源 ID；
- 明确的 HTTP 状态码；
- 统一错误结构；
- 分页查询；
- API 版本前缀；
- OpenAPI 文档。

建议基础路径：

`/api/v1`

### 6.2 统一响应原则

成功响应可采用：

```json
{
  "data": {
    "id": "resource-uuid",
    "type": "ontology"
  },
  "meta": {
    "request_id": "request-uuid"
  }
}
```

分页响应可采用：

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 0
  }
}
```

错误响应可采用：

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Ontology validation failed",
    "details": [],
    "request_id": "request-uuid"
  }
}
```

以上仅为结构示例，正式接口应在 OpenAPI 中定义字段类型和约束。

### 6.3 HTTP 状态码

| 状态码 | 使用场景 |
|---|---|
| 200 | 查询或操作成功 |
| 201 | 资源创建成功 |
| 202 | 异步任务已接受 |
| 204 | 删除或操作成功，无响应正文 |
| 400 | 请求格式或参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 状态冲突或资源冲突 |
| 422 | 请求结构有效但业务校验失败 |
| 429 | 请求频率超限 |
| 500 | 服务内部错误 |

### 6.4 API 资源设计

#### API-01：项目管理

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/projects` | 创建项目 |
| GET | `/projects` | 查询项目列表 |
| GET | `/projects/{project_id}` | 查询项目详情 |
| PATCH | `/projects/{project_id}` | 更新项目 |
| POST | `/projects/{project_id}/archive` | 归档项目 |

#### API-02：本体管理

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/projects/{project_id}/ontologies` | 创建本体 |
| GET | `/projects/{project_id}/ontologies` | 查询本体列表 |
| GET | `/ontologies/{ontology_id}` | 查询本体 |
| PATCH | `/ontologies/{ontology_id}` | 更新本体 |
| DELETE | `/ontologies/{ontology_id}` | 删除草稿本体 |

#### API-03：本体类管理

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/ontologies/{ontology_id}/classes` | 创建类 |
| GET | `/ontologies/{ontology_id}/classes` | 查询类 |
| GET | `/classes/{class_id}` | 查询类详情 |
| PATCH | `/classes/{class_id}` | 更新类 |
| DELETE | `/classes/{class_id}` | 删除类 |

#### API-04：属性与关系管理

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/ontologies/{ontology_id}/properties` | 创建属性 |
| GET | `/ontologies/{ontology_id}/properties` | 查询属性 |
| PATCH | `/properties/{property_id}` | 更新属性 |
| POST | `/ontologies/{ontology_id}/relations` | 创建关系 |
| GET | `/ontologies/{ontology_id}/relations` | 查询关系 |
| PATCH | `/relations/{relation_id}` | 更新关系 |

#### API-05：本体导入

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/ontologies/{ontology_id}/imports` | 提交导入任务 |
| GET | `/imports/{import_id}` | 查询导入任务 |
| GET | `/imports/{import_id}/errors` | 查询导入错误 |

#### API-06：质量验证

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/ontologies/{ontology_id}/validations` | 创建验证任务 |
| GET | `/validations/{validation_id}` | 查询验证结果 |
| GET | `/validations/{validation_id}/findings` | 查询问题明细 |

#### API-07：版本管理

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/ontologies/{ontology_id}/versions` | 创建版本快照 |
| GET | `/ontologies/{ontology_id}/versions` | 查询版本列表 |
| GET | `/versions/{version_id}` | 查询版本详情 |
| POST | `/versions/compare` | 比较两个版本 |

#### API-08：发布与导出

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/versions/{version_id}/publications` | 创建发布记录 |
| GET | `/ontologies/{ontology_id}/publications` | 查询发布记录 |
| POST | `/versions/{version_id}/exports` | 提交导出任务 |
| GET | `/exports/{export_id}` | 查询导出结果 |
| GET | `/exports/{export_id}/download` | 下载导出文件 |

#### API-09：数据源和元数据（后续）

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/projects/{project_id}/data-sources` | 创建数据源 |
| GET | `/projects/{project_id}/data-sources` | 查询数据源 |
| POST | `/data-sources/{id}/test` | 测试连接 |
| POST | `/data-sources/{id}/collections` | 提交采集任务 |
| GET | `/collections/{id}` | 查询采集任务 |
| GET | `/data-sources/{id}/metadata` | 查询采集元数据 |

#### API-10：AI 发现和审核（后续）

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/ontologies/{ontology_id}/discoveries` | 提交发现任务 |
| GET | `/discoveries/{id}` | 查询发现任务 |
| GET | `/discoveries/{id}/proposals` | 查询候选 |
| POST | `/proposals/{id}/reviews` | 提交审核结果 |
| GET | `/proposals/{id}/evidence` | 查询来源证据 |

#### API-11：权限和审计

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/projects/{project_id}/members` | 查询项目成员 |
| POST | `/projects/{project_id}/members` | 添加成员 |
| PATCH | `/projects/{project_id}/members/{user_id}` | 更新项目角色 |
| GET | `/audit-events` | 查询审计事件 |

上述接口是资源规划，不是已实现 API 清单。正式开发前应形成 OpenAPI 规范，明确请求字段、响应字段、权限、状态码和幂等要求。

---

## 7. 异步任务规范

### 7.1 统一任务对象

建议统一后台任务模型：

```json
{
  "id": "job-uuid",
  "project_id": "project-uuid",
  "job_type": "ONTOLOGY_IMPORT",
  "status": "QUEUED",
  "progress": null,
  "created_at": "2026-11-21T10:00:00Z",
  "started_at": null,
  "finished_at": null,
  "result_ref": null,
  "error": null
}
```

progress 可选。只有任务能够提供可靠进度时才返回具体数值，不应以估算进度冒充真实进度。

### 7.2 任务状态

```text
QUEUED
  |
  v
RUNNING
  |
  +----> SUCCEEDED
  |
  +----> FAILED
  |
  +----> CANCELLED
```

### 7.3 任务处理要求

- 提交任务后立即返回任务 ID；
- 任务状态持久化；
- 支持查询任务状态；
- 失败原因可追踪；
- 重试策略明确；
- 重试不能重复创建业务对象；
- 长时间任务应支持超时控制；
- 取消任务必须定义实际取消语义；
- 任务结果应关联输入对象和产物。

### 7.4 幂等性

对于导入、导出、版本创建等可能重复提交的操作，应明确幂等策略。

可通过：

- Idempotency-Key；
- 任务唯一约束；
- 业务操作唯一键；
- 事务边界；
- 结果复用策略。

防止网络重试或用户重复点击产生重复业务结果。

---

## 8. 安全与权限设计

### 8.1 认证

首期可以使用平台基础认证，后续支持 OIDC 等企业身份体系。

认证结果应能够映射到统一 User 身份。

### 8.2 授权

建议采用项目级 RBAC。

| 角色 | 权限 |
|---|---|
| Project Owner | 项目完整管理 |
| Ontology Architect | 本体建模和版本管理 |
| Domain Expert | 查看和审核业务语义 |
| Developer | 查询和导出已授权本体 |
| Platform Admin | 平台配置和运维管理 |
| Viewer | 只读访问 |

权限应在后端执行。不能仅通过前端菜单隐藏实现访问控制。

### 8.3 数据源安全

后续数据连接器应遵循：

- 默认只读；
- 凭证加密或通过密钥系统引用；
- 不向普通日志输出凭证；
- 连接器限制网络访问范围；
- 设置超时和资源限制；
- 限制文件类型和文件大小；
- 对文件解析实施隔离；
- 防止 SSRF；
- 对采集数据实施最小化原则。

### 8.4 AI 安全

- 模型输出视为不可信输入；
- 对模型输出进行结构化校验；
- 不允许模型直接执行任意 SQL；
- 不允许模型绕过权限调用数据源；
- 重要候选必须经过人工审核；
- 保存必要的模型调用和证据记录；
- 限制敏感数据发送给外部模型。

---

## 9. API 与数据模型映射

| API 资源 | 主要数据对象 | 主要模块 |
|---|---|---|
| projects | Project、Domain | MOD-01 |
| ontologies | Ontology | MOD-02 |
| classes | OntologyClass | MOD-02 |
| properties | Property | MOD-02 |
| relations | Relation | MOD-02 |
| imports | ImportJob、FileAsset | MOD-03、MOD-13 |
| validations | ValidationRun、ValidationFinding | MOD-08 |
| versions | OntologyVersion、ChangeRecord | MOD-09 |
| publications | PublicationRecord | MOD-10 |
| exports | ExportArtifact | MOD-10 |
| data-sources | DataSource、Connector | MOD-04 |
| metadata | MetadataAsset、MetadataSnapshot | MOD-05 |
| discoveries | DiscoveryJob、DiscoveryProposal | MOD-06 |
| reviews | ReviewRecord、Evidence | MOD-07 |
| members | User、Role、ProjectMembership | MOD-12 |
| audit-events | AuditEvent | MOD-12 |

## 10. 开发 Epic 规划

### EPIC-00：工程基础与开发环境

目标：建立统一、可重复的开发基础。

任务：

- 创建前端和后端工程；
- 建立代码仓库目录结构；
- 配置 Python 依赖管理；
- 配置前端依赖管理；
- 配置 PostgreSQL；
- 配置数据库迁移；
- 配置 Redis；
- 建立 Celery Worker；
- 配置 Docker Compose；
- 建立环境变量和配置管理；
- 建立 CI 基础流程；
- 建立代码格式、静态检查和单元测试。

交付物：

- 可运行的工程骨架；
- 本地开发说明；
- 环境配置模板；
- 数据库迁移入口；
- CI 检查流程。

### EPIC-01：身份认证与项目管理

目标：建立用户、项目和权限基础。

任务：

- User 和 Role 模型；
- Project 和 ProjectMembership 模型；
- 项目 CRUD API；
- 项目管理页面；
- 基础认证；
- 项目级授权；
- 审计事件基础结构；
- 权限测试。

依赖：EPIC-00。

### EPIC-02：本体元模型与核心服务

目标：建立统一的本体数据模型。

任务：

- 定义 Ontology；
- 定义 OntologyClass；
- 定义 Property；
- 定义 Relation；
- 定义 Constraint；
- 定义 Term；
- 定义对象 ID 和 IRI 规则；
- 实现对象持久化；
- 实现对象 CRUD API；
- 实现引用完整性检查；
- 编写元模型测试。

依赖：EPIC-01。

### EPIC-03：本体编辑与标准导入

目标：支持本体创建、编辑和导入。

任务：

- 本体编辑基础页面；
- 类、属性、关系编辑表单；
- 本体结构查询 API；
- RDF 解析适配器；
- OWL 导入适配器；
- 导入文件管理；
- 导入任务执行；
- 导入错误记录；
- 导入事务与回滚；
- 导入安全检查；
- 导入测试。

依赖：EPIC-02。

### EPIC-04：质量验证引擎

目标：建立本体结构和基础语义质量检查能力。

任务：

- 验证规则模型；
- 结构验证器；
- 引用完整性验证；
- 基础语义规则；
- SHACL 适配接口；
- ValidationRun 模型；
- ValidationFinding 模型；
- 验证任务 API；
- 验证报告页面；
- 规则单元测试；
- 验证集成测试。

依赖：EPIC-02。

### EPIC-05：版本和变更管理

目标：实现稳定的本体版本快照和差异比较。

任务：

- OntologyVersion 模型；
- 快照序列化；
- 快照内容摘要；
- 版本创建 API；
- 版本查询 API；
- 版本比较服务；
- 新增、修改和删除差异识别；
- 版本详情页面；
- 快照不可变性测试；
- 历史版本恢复策略设计。

依赖：EPIC-02、EPIC-04。

注意：历史版本恢复应优先通过基于历史快照创建新的工作版本实现，不应直接改写历史快照。

### EPIC-06：标准导出和发布基础

目标：让本体能够作为可复用语义资产交付。

任务：

- RDF/Turtle 导出；
- RDF/XML 导出；
- JSON 导出；
- 导出任务；
- 导出产物存储；
- 发布记录模型；
- 发布前验证；
- 发布状态管理；
- 导出下载 API；
- 导入导出往返测试。

依赖：EPIC-04、EPIC-05。

### EPIC-07：平台运行管理和交付

目标：形成可部署、可测试和可运维的 MVP。

任务：

- 后台任务管理页面；
- 结构化日志；
- API 错误监控；
- 审计查询页面；
- Docker Compose 部署完善；
- 数据库备份和恢复说明；
- API 文档；
- 安装文档；
- 使用文档；
- E2E 测试；
- 部署验证；
- MVP 验收报告。

依赖：EPIC-00 至 EPIC-06。

## 11. 推荐实施顺序

```text
EPIC-00 工程基础
      |
      v
EPIC-01 认证与项目管理
      |
      v
EPIC-02 本体元模型
      |
      +--------------------+
      |                    |
      v                    v
EPIC-03 本体编辑        EPIC-04 质量验证
      |                    |
      +---------+----------+
                |
                v
        EPIC-05 版本管理
                |
                v
        EPIC-06 导出与发布
                |
                v
        EPIC-07 交付与验收
```

推荐按依赖顺序实施，但在人员和接口明确的情况下，可以并行开发部分前端页面、验证规则和部署工作。

## 12. 建议代码目录结构

```text
p1-ontology-platform/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── features/
│   │   ├── projects/
│   │   ├── ontologies/
│   │   ├── editor/
│   │   ├── validation/
│   │   ├── versions/
│   │   └── administration/
│   ├── services/
│   └── tests/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── modules/
│   │   │   ├── projects/
│   │   │   ├── ontology/
│   │   │   ├── import_export/
│   │   │   ├── validation/
│   │   │   ├── versioning/
│   │   │   ├── publication/
│   │   │   ├── iam/
│   │   │   └── audit/
│   │   ├── adapters/
│   │   │   ├── rdf/
│   │   │   ├── owl/
│   │   │   ├── shacl/
│   │   │   └── storage/
│   │   ├── workers/
│   │   ├── models/
│   │   └── main.py
│   ├── migrations/
│   └── tests/
│
├── deployment/
│   ├── docker/
│   ├── compose/
│   └── scripts/
│
├── docs/
│   ├── product/
│   ├── architecture/
│   ├── api/
│   ├── development/
│   └── deployment/
│
├── examples/
│   ├── ontologies/
│   └── test-data/
│
├── scripts/
├── .env.example
├── docker-compose.yml
└── README.md
```

目录可以根据实际仓库规范调整，但应保持前端、后端、基础设施、文档和测试资产之间的清晰边界。

## 13. 测试策略

### 13.1 单元测试

覆盖：

- 元模型对象；
- 对象 ID 和 IRI；
- 引用完整性；
- 验证规则；
- 版本差异；
- 格式转换；
- 权限判断。

### 13.2 集成测试

覆盖：

- API 与数据库；
- RDF 导入和导出；
- Worker 与任务队列；
- 文件存储；
- 验证引擎；
- 权限和审计。

### 13.3 端到端测试

使用客户与订单示例本体，完整执行：

1. 创建项目；
2. 创建本体；
3. 编辑类和关系；
4. 执行验证；
5. 修复错误；
6. 创建版本；
7. 比较版本；
8. 导出文件；
9. 重新解析；
10. 检查审计记录。

### 13.4 安全测试

至少覆盖：

- 未授权项目访问；
- 跨项目资源访问；
- 非法文件导入；
- 文件大小限制；
- 恶意文件处理；
- 敏感凭证日志泄漏；
- API 参数校验；
- 任务重复提交；
- 导出下载权限。

## 14. 开发任务完成定义

一个开发任务只有同时满足以下要求，才可以标记为完成：

1. 需求编号明确；
2. 代码实现符合模块边界；
3. API 或用户交互符合约定；
4. 数据库迁移完整；
5. 权限检查完整；
6. 错误处理完整；
7. 自动化测试通过；
8. 文档更新；
9. 代码审查通过；
10. 没有未处理的阻断级问题。

以下状态必须区分：

- Designed：设计完成；
- Implemented：代码实现；
- Tested：测试通过；
- Accepted：产品验收通过；
- Released：正式发布。

## 15. 风险与应对

| 风险 | 可能影响 | 应对措施 |
|---|---|---|
| 元模型设计不稳定 | 数据结构反复修改 | 先确定核心对象和 ID 规则 |
| 过早微服务化 | 部署和维护成本上升 | 模块化单体优先 |
| 过度追求标准兼容 | 首期研发范围失控 | 明确格式和语法支持子集 |
| AI 能力提前进入核心流程 | 系统依赖模型输出 | 候选与正式模型隔离 |
| 图数据库提前引入 | 基础设施复杂化 | 根据实际查询需求评估 |
| 版本快照设计不合理 | 历史数据无法复现 | 明确快照内容和不可变性 |
| 权限后补 | 安全模型返工 | 从首期建立项目级权限 |
| 缺乏验收标准 | 无法判断交付质量 | 需求与测试建立追踪关系 |

## 16. 首期交付检查清单

### 工程基础

- [ ] 前端和后端能够独立启动；
- [ ] 数据库迁移能够执行；
- [ ] Redis 和 Worker 能够运行；
- [ ] Docker Compose 配置完整；
- [ ] 环境变量模板完整。

### 核心业务

- [ ] 项目创建和查询；
- [ ] 本体创建和查询；
- [ ] 类、属性和关系编辑；
- [ ] 本体导入；
- [ ] 结构验证；
- [ ] 基础语义验证；
- [ ] 版本快照；
- [ ] 版本比较；
- [ ] 标准导出。

### 安全和质量

- [ ] 项目级权限；
- [ ] 关键操作审计；
- [ ] 核心自动化测试；
- [ ] 导入导出往返测试；
- [ ] 跨项目隔离测试；
- [ ] 数据备份和恢复验证。

### 发布交付

- [ ] README；
- [ ] 安装说明；
- [ ] 使用说明；
- [ ] API 文档；
- [ ] 部署说明；
- [ ] 依赖和许可证清单；
- [ ] 测试报告；
- [ ] 已知限制说明；
- [ ] 版本发布记录。

## 17. 后续扩展方向

完成 MVP 后，建议依次评估：

1. 数据源连接器框架；
2. 数据库和文档元数据采集；
3. AI 本体发现引擎适配；
4. 候选审核和证据管理；
5. 高级可视化本体设计器；
6. 本体与实例知识图谱探索；
7. 多人协作；
8. 多环境发布；
9. 企业级身份管理；
10. 与 ODAP 其他产品的集成。

AI 发现引擎应通过统一 Discovery Provider 接口接入，避免将某个具体开源项目或模型绑定为 P1 的唯一核心引擎。

## 18. 关联文档

- `vision.md`
- `problem-statement.md`
- `personas-and-use-cases.md`
- `capability-map.md`
- `mvp-scope.md`
- `acceptance-criteria.md`
- `requirements-traceability-matrix.md`
- `requirements-to-metamodel-and-modules.md`


