# P1 需求与本体元模型、系统模块映射

**文件路径：** `docs/product/requirements-to-metamodel-and-modules.md`  
**产品：** P1 Ontology Engineering Platform  
**版本：** V1.0  
**日期：** 2026-11-21  
**状态：** 设计基线，待评审

---

## 1. 文档目的

本文件定义 P1 平台的核心数据对象、对象关系、元模型边界以及与产品模块之间的映射关系。

主要解决四个问题：

1. 平台需要定义和管理哪些核心对象？
2. 这些对象之间有什么关系？
3. 产品需求由哪些数据对象支撑？
4. 哪个系统模块负责创建、维护和使用这些对象？

本文件是后续数据库设计、领域模型设计、API 设计和本体元模型实现的依据。

## 2. 首先区分两类本体

P1 平台需要管理两种性质不同的语义模型。

### 2.1 平台元模型（Platform Meta-model）

平台元模型描述 P1 自身如何管理本体工程资产。

例如：

- 一个项目包含哪些本体；
- 一个本体包含哪些类；
- 一个类有哪些属性；
- 一个属性属于哪个类；
- 一个版本对应哪个本体；
- 一次验证产生哪些问题；
- 一条审核记录对应哪个候选；
- 一个候选来自哪些数据源和证据。

平台元模型是 P1 产品自身的基础数据结构。

### 2.2 业务领域本体（Domain Ontology）

业务领域本体描述企业实际业务中的概念。

例如客户与订单领域：

- Customer；
- Order；
- Product；
- Payment；
- OrderItem。

以及它们之间的关系：

- Customer places Order；
- Order contains OrderItem；
- OrderItem references Product；
- Order has Payment。

业务领域本体由用户创建、导入或通过 AI 辅助发现生成。

### 2.3 两者之间的关系

```text
P1 平台元模型
      |
      | 定义如何存储、描述和管理
      v
业务领域本体
      |
      | 描述真实业务概念
      v
企业数据、业务系统与 AI 应用
```

平台元模型不应该与某个特定行业绑定。

例如，P1 的 `OntologyClass` 可以描述医疗领域的 `Patient`，也可以描述软件工程领域的 `Repository`。

平台自身的元模型应该保持稳定，并通过扩展机制适应不同领域的本体表达需求。

## 3. 核心对象清单

建议将 P1 的核心对象划分为六组。

### 3.1 项目与组织对象

| 对象 | 英文名称 | 说明 |
|---|---|---|
| 项目 | Project | 本体工程的组织单元 |
| 领域 | Domain | 项目所处的业务领域或语义范围 |
| 用户 | User | 平台用户 |
| 角色 | Role | 权限角色 |
| 项目成员 | ProjectMembership | 用户在项目中的成员身份和角色 |

### 3.2 本体模型对象

| 对象 | 英文名称 | 说明 |
|---|---|---|
| 本体 | Ontology | 一个独立的语义模型资产 |
| 本体类 | OntologyClass | 本体中的类 |
| 属性 | Property | 类或对象的属性定义 |
| 关系 | Relation | 本体对象之间的语义关系 |
| 约束 | Constraint | 对本体对象或数据的约束 |
| 术语 | Term | 业务术语及其定义 |
| 命名空间 | Namespace | 本体对象的命名空间 |
| 外部映射 | ExternalMapping | 本体对象与外部概念的映射 |

### 3.3 数据源与元数据对象

| 对象 | 英文名称 | 说明 |
|---|---|---|
| 数据源 | DataSource | 企业数据或文档来源 |
| 连接器 | Connector | 连接器类型和配置定义 |
| 采集任务 | MetadataCollectionJob | 元数据采集任务 |
| 元数据资产 | MetadataAsset | 采集到的表、字段、API 或文档对象 |
| 元数据快照 | MetadataSnapshot | 某次采集形成的结果快照 |
| 数据映射 | DataMapping | 数据源字段与本体对象之间的映射 |

### 3.4 AI 发现与证据对象

| 对象 | 英文名称 | 说明 |
|---|---|---|
| 发现任务 | DiscoveryJob | AI 或规则驱动的发现任务 |
| 发现提案 | DiscoveryProposal | 待审核的本体候选 |
| 证据 | Evidence | 支持候选的来源和内容证据 |
| 审核记录 | ReviewRecord | 人工审核和处理结果 |
| 冲突记录 | ConflictRecord | 候选对象之间的冲突信息 |

### 3.5 验证与版本对象

| 对象 | 英文名称 | 说明 |
|---|---|---|
| 验证规则 | ValidationRule | 验证规则定义 |
| 验证任务 | ValidationRun | 一次验证执行 |
| 验证问题 | ValidationFinding | 验证发现的问题 |
| 本体版本 | OntologyVersion | 本体的稳定快照 |
| 变更记录 | ChangeRecord | 本体对象变更记录 |
| 发布记录 | PublicationRecord | 本体版本的发布记录 |
| 导出产物 | ExportArtifact | 导出的文件或发布包 |

### 3.6 平台运行对象

| 对象 | 英文名称 | 说明 |
|---|---|---|
| 后台任务 | BackgroundJob | 异步任务的统一执行记录 |
| 审计事件 | AuditEvent | 关键业务操作记录 |
| 文件资产 | FileAsset | 导入文件和其他平台文件 |
| 模型调用记录 | ModelInvocation | AI 模型调用的必要审计信息 |

上述对象是目标元模型的候选清单。MVP 应优先实现项目、本体模型、验证、版本、审计和导出所需对象，其他对象随对应能力建设逐步引入。

## 4. 核心对象关系

### 4.1 项目与本体

```text
Domain
  |
  | 1:N
  v
Project
  |
  | 1:N
  v
Ontology
  |
  | 1:N
  +------ OntologyClass
  |
  +------ Property
  |
  +------ Relation
  |
  +------ Constraint
  |
  +------ Term
```

一个项目可以包含多个本体。

一个本体属于一个明确的项目。

项目领域可以用于组织、搜索和约束本体的业务范围，但不应把领域标签直接等同于本体之间的继承关系。

### 4.2 本体对象之间的关系

```text
Ontology
  |
  +--- OntologyClass
  |        |
  |        +--- Property
  |        |
  |        +--- Relation
  |        |
  |        +--- Constraint
  |
  +--- Term
  |
  +--- Namespace
```

建议将 `Property` 和 `Relation` 在内部模型中区分：

- Property：属性的通用概念；
- Data Property：数据属性，例如客户姓名；
- Object Property：对象关系，例如客户拥有订单；
- Relation：平台对关系语义的管理对象或统一抽象。

具体采用独立表还是统一表加类型字段，应在技术设计阶段确定。

### 4.3 数据源和元数据

```text
Project
  |
  +--- DataSource
          |
          +--- Connector
          |
          +--- MetadataCollectionJob
          |          |
          |          +--- MetadataSnapshot
          |                     |
          |                     +--- MetadataAsset
          |
          +--- DataMapping
```

一个数据源可以产生多次采集任务。

每次采集可以形成一个元数据快照。

元数据资产应保留来源标识，以便后续追踪本体候选的来源。

### 4.4 AI 发现与审核

```text
MetadataSnapshot
       |
       v
DiscoveryJob
       |
       v
DiscoveryProposal
       |
       +--- Evidence
       |
       +--- ReviewRecord
       |
       +--- ConflictRecord
       |
       v
Ontology
```

DiscoveryProposal 与正式 Ontology 对象必须保持状态隔离。

建议的候选状态：

- Draft；
- PendingReview；
- Accepted；
- Rejected；
- Merged；
- Superseded。

只有经过明确审核并完成必要的数据转换后，候选才能成为正式本体对象。

### 4.5 验证与版本

```text
Ontology
   |
   +--- ValidationRun
   |        |
   |        +--- ValidationFinding
   |
   +--- OntologyVersion
             |
             +--- ChangeRecord
             |
             +--- PublicationRecord
                      |
                      +--- ExportArtifact
```

版本应保存确定的本体内容，而不应只保存一个指向当前可变模型的引用。

验证结果需要明确对应哪个模型状态或版本。

正式发布的版本应当能够被重复查询和导出。

## 5. 核心对象字段建议

以下为逻辑字段建议，不是最终数据库 DDL。

### 5.1 Project

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | UUID | 项目 ID |
| name | String | 项目名称 |
| description | Text | 项目描述 |
| domain_id | UUID | 所属领域 |
| status | Enum | 项目状态 |
| created_by | UUID | 创建人 |
| created_at | Timestamp | 创建时间 |
| updated_at | Timestamp | 更新时间 |

### 5.2 Ontology

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | UUID | 平台内部 ID |
| project_id | UUID | 所属项目 |
| ontology_iri | URI | 本体外部标识 |
| name | String | 本体名称 |
| description | Text | 描述 |
| namespace | URI | 默认命名空间 |
| status | Enum | Draft、Active、Archived 等 |
| created_at | Timestamp | 创建时间 |
| updated_at | Timestamp | 更新时间 |

### 5.3 OntologyClass

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | UUID | 平台内部 ID |
| ontology_id | UUID | 所属本体 |
| iri | URI | 类的稳定语义标识 |
| name | String | 类名称 |
| description | Text | 类描述 |
| parent_class_iris | JSON / Relation Table | 父类引用 |
| annotations | JSON | 标签、注释等 |

### 5.4 Property

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | UUID | 平台内部 ID |
| ontology_id | UUID | 所属本体 |
| iri | URI | 属性标识 |
| name | String | 属性名称 |
| property_kind | Enum | Data / Object |
| domain_iris | JSON / Relation Table | 定义域 |
| range_definition | JSON | 值域或数据类型 |
| cardinality | JSON | 基数约束 |
| description | Text | 描述 |

### 5.5 Relation

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | UUID | 平台内部 ID |
| ontology_id | UUID | 所属本体 |
| iri | URI | 关系标识 |
| source_class_iri | URI | 源类 |
| target_class_iri | URI | 目标类 |
| relation_type | String | 关系类型 |
| inverse_relation_iri | URI | 可选逆关系 |
| description | Text | 关系描述 |

### 5.6 OntologyVersion

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | UUID | 版本记录 ID |
| ontology_id | UUID | 所属本体 |
| version_label | String | 版本号 |
| snapshot_ref | String | 快照存储引用 |
| content_hash | String | 快照内容摘要 |
| change_summary | Text | 变更说明 |
| created_by | UUID | 创建人 |
| created_at | Timestamp | 创建时间 |
| validation_status | Enum | 验证状态 |
| publication_status | Enum | 发布状态 |

### 5.7 ValidationRun 与 ValidationFinding

ValidationRun：

- id；
- ontology_id；
- version_id 或 model_revision；
- rule_set_version；
- status；
- started_at；
- finished_at；
- summary。

ValidationFinding：

- id；
- validation_run_id；
- rule_id；
- severity；
- object_iri；
- message；
- location；
- resolution_status。

### 5.8 AuditEvent

- id；
- project_id；
- actor_id；
- action；
- resource_type；
- resource_id；
- timestamp；
- result；
- request_id；
- metadata。

审计记录应避免保存不必要的敏感信息或完整密钥。

## 6. 需求与元模型对象映射

| 需求范围 | 主要对象 | 对象关系 |
|---|---|---|
| 项目管理 | Project、Domain、ProjectMembership | Project 包含多个 Ontology |
| 本体管理 | Ontology、OntologyClass、Property、Relation | 本体拥有模型对象 |
| 数据接入 | DataSource、Connector | 数据源通过连接器访问 |
| 元数据采集 | MetadataCollectionJob、MetadataSnapshot、MetadataAsset | 任务产生快照和资产 |
| AI 发现 | DiscoveryJob、DiscoveryProposal、Evidence | 发现任务产生候选和证据 |
| 审核 | ReviewRecord、ConflictRecord | 审核记录关联候选 |
| 数据映射 | DataMapping | 关联 MetadataAsset 与本体对象 |
| 验证 | ValidationRule、ValidationRun、ValidationFinding | 规则产生验证结果 |
| 版本 | OntologyVersion、ChangeRecord | 版本保存模型快照 |
| 发布 | PublicationRecord、ExportArtifact | 发布版本产生发布记录和产物 |
| 权限 | User、Role、ProjectMembership | 用户通过角色获得项目权限 |
| 审计 | AuditEvent | 记录关键操作 |

## 7. 模块边界与责任

| 模块 | 主要对象 | 责任 |
|---|---|---|
| MOD-01 Project Management | Project、Domain、ProjectMembership | 项目和领域生命周期 |
| MOD-02 Ontology Core | Ontology、OntologyClass、Property、Relation、Constraint、Term | 本体对象和元模型 |
| MOD-03 Ontology Editor | Ontology、OntologyClass、Property、Relation | 模型编辑、导入协调 |
| MOD-04 Connector Management | Connector、DataSource | 连接器配置和执行入口 |
| MOD-05 Metadata Management | MetadataCollectionJob、MetadataSnapshot、MetadataAsset | 元数据采集和目录 |
| MOD-06 Discovery Engine | DiscoveryJob、DiscoveryProposal | 候选生成 |
| MOD-07 Review & Evidence | Evidence、ReviewRecord、ConflictRecord | 证据管理、人工审核 |
| MOD-08 Validation Engine | ValidationRule、ValidationRun、ValidationFinding | 质量检查 |
| MOD-09 Version Management | OntologyVersion、ChangeRecord | 快照、差异和变更 |
| MOD-10 Publication & Export | PublicationRecord、ExportArtifact | 发布和格式导出 |
| MOD-11 Visualization | Ontology、OntologyClass、Relation | 图形数据查询和呈现 |
| MOD-12 IAM & Audit | User、Role、AuditEvent | 认证、授权和审计 |
| MOD-13 Job & Observability | BackgroundJob、ModelInvocation | 任务状态、运行记录 |

模块可以在 MVP 阶段部署在同一个后端应用中，但应保持清晰的业务责任和代码边界。

## 8. 数据持久化建议

建议采用关系数据库作为 MVP 的主要业务持久化基础。

### 8.1 PostgreSQL

适合存储：

- 项目和用户；
- 本体元数据；
- 本体对象；
- 版本记录；
- 验证结果；
- 审核记录；
- 权限和审计；
- 后台任务元数据。

本体结构可以采用关系表、JSONB 或混合存储，但需要明确对象标识和引用完整性规则。

### 8.2 对象存储

MinIO 或兼容 S3 的存储用于保存：

- 原始导入文件；
- 本体版本快照；
- 导出文件；
- 采集文件；
- 需要留存的验证报告。

### 8.3 RDF/OWL 表示

RDFLib 等组件可以承担 RDF 图解析、转换和序列化。

不要求 MVP 将 RDF 三元组数据库作为独立基础设施。若未来出现大规模图查询、推理或多应用共享需求，再评估专用 RDF 存储。

## 9. 关键数据完整性规则

### 9.1 稳定标识

- 每个内部对象有稳定 ID。
- 本体语义对象具有稳定 IRI。
- 不应使用显示名称作为唯一标识。
- 名称修改不应导致对象身份变化。

### 9.2 项目隔离

- 本体必须归属有效项目。
- 通过项目权限限制访问。
- 跨项目引用必须显式定义和授权。
- 不允许仅凭前端隐藏资源实现隔离。

### 9.3 引用完整性

- 类引用必须指向有效类。
- 属性定义域和值域必须有效。
- 关系端点必须存在。
- 版本引用必须指向有效本体和快照。

### 9.4 版本不可变性

- 已创建快照不被普通编辑覆盖。
- 修改应创建新的模型状态或版本。
- 发布版本与当前工作区版本分离。
- 快照应保存内容摘要，以便进行完整性检查。

### 9.5 来源追踪

- AI 候选必须保留来源信息。
- 元数据资产应记录采集任务和来源对象。
- 审核记录关联候选及处理结果。
- 变更记录尽可能关联触发变更的用户操作或来源事件。

### 9.6 状态转换

关键对象状态应通过明确的状态机或业务服务管理，避免任意字符串写入造成非法状态。

## 10. 核心状态模型

### 10.1 Ontology 状态

建议：

- Draft；
- Active；
- Archived。

发布状态单独管理，不建议把本体生命周期状态和发布状态混在一个字段中。

### 10.2 DiscoveryProposal 状态

```text
Draft
  |
  v
PendingReview
  |
  +----> Accepted
  |
  +----> Rejected
  |
  +----> Merged
  |
  +----> Superseded
```

### 10.3 ValidationRun 状态

```text
Queued
  |
  v
Running
  |
  +----> Succeeded
  |
  +----> Failed
  |
  +----> Cancelled
```

验证成功并不等于所有 Finding 都是零；验证任务是否满足发布要求，应由发布策略根据错误等级和规则决定。

### 10.4 PublicationRecord 状态

建议：

- Pending；
- Published；
- Withdrawn；
- Failed。

发布记录与本体版本关联，不直接覆盖历史发布记录。

## 11. 元模型扩展原则

平台元模型需要满足：

1. 核心对象类型稳定；
2. 对象可扩展属性采用受控机制；
3. 标准语义和平台私有元数据明确区分；
4. 外部格式映射可追踪；
5. 不允许任意 JSON 字段替代所有领域模型约束；
6. 扩展不破坏历史版本解析；
7. 元模型升级应具备迁移策略。

## 12. MVP 元模型实施范围

首期优先实现：

- Project；
- User、Role、ProjectMembership；
- Ontology；
- OntologyClass；
- Property；
- Relation；
- Constraint；
- OntologyVersion；
- ChangeRecord；
- ValidationRun；
- ValidationFinding；
- ExportArtifact；
- AuditEvent。

后续再增加：

- DataSource；
- Connector；
- MetadataAsset；
- MetadataSnapshot；
- DiscoveryJob；
- DiscoveryProposal；
- Evidence；
- ReviewRecord；
- DataMapping；
- PublicationRecord；
- ConflictRecord。

## 13. 关联文档

- `vision.md`
- `problem-statement.md`
- `personas-and-use-cases.md`
- `capability-map.md`
- `mvp-scope.md`
- `acceptance-criteria.md`
- `requirements-traceability-matrix.md`
- `architecture-and-api-development-backlog.md`

