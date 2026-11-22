# P1｜Ontology Engineering Platform：正式 PRD 与技术设计基线

-   版本：v1.0-baseline
-   日期：2026-11-15
-   状态：研发评审基线（不代表代码已实现或验收）
-   产品：ODAP-P1 / Ontology Engineering Platform

## 0. 执行摘要与开源选型

**决策：不直接以 NVIDIA Auto Ontology 或 Protégé 作为 P1
产品底座。自建产品工作台、统一 Ontology
Meta-model、权限/审核/版本/发布/审计流程；以适配器方式集成 Auto Ontology
的发现能力，以 RDF/OWL 导入导出与 Protégé 做专家互操作。**

  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  项目              强项                                                                                         局限/风险                                            P1 定位
  ----------------- -------------------------------------------------------------------------------------------- ---------------------------------------------------- ---------------------------------
  NVIDIA Auto       关系型数据库元数据摄取、语义目录、术语/关系候选生成、认证流程、MCP/API；Apache-2.0；Docker   重点偏数据库语义层与 Agent 查询；模型与 P1 通用      独立 Discovery Provider，先做
  Ontology          Compose 部署                                                                                 OWL/SHACL                                            POC，不复制其数据库作为权威存储
                                                                                                                 元模型不完全一致；上游当前说明不接受外部贡献，长期   
                                                                                                                 fork 维护成本较高                                    

  Protégé Desktop   成熟 OWL 2 编辑、复杂公理、推理器和插件生态                                                  Java 桌面工具，不具备 P1                             专家工具、OWL 兼容性验收
                                                                                                                 所需连接器治理、企业项目/权限、AI 发现、发布控制台   

  WebProtégé        浏览器协作编辑、权限、讨论、修订历史、多种 RDF/OWL 格式                                      自身产品模型、权限和版本体系与 P1                    协作能力参考；MVP 不依赖
                                                                                                                 不同，深度整合会形成双体系                           
  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Auto Ontology 官方资料显示，其采用
Next.js、FastAPI、摄取服务、PostgreSQL/pgvector，支持数据库连接、MCP/API
和 Docker Compose；其流程是生成语义模型、人工认证，再供 Agent
查询。它值得作为关系型数据源发现引擎候选，但不等于通用本体工程平台。Protégé
官方支持 OWL 2；WebProtégé
支持协作、权限、讨论、修订历史和多格式导入导出，Desktop
提供推理器及插件能力。\
**架构原则：Build the product shell, integrate the engines.**
产品自己的模型、版本和权限是权威；开源工具提供可替换能力。

### 0.1 P1 核心原则

1.  行业中立；不将零售、金融、教育、医疗实体写死在核心元模型。
2.  AI 发现结果默认是候选，必须人工审核并通过机器校验才能发布。
3.  本体定义与知识图谱实例分离。
4.  对象使用稳定 ID；发布版本不可原位修改。
5.  对象、映射、候选均可追溯到数据源、扫描任务、证据、模型和提示词版本。
6.  连接器默认只读；凭据存 Secret Manager，业务库仅保存引用。
7.  MVP 不强制 Neo4j、Kafka、Kubernetes 或独立向量数据库。

------------------------------------------------------------------------

# 第一部分：产品需求规格（PRD）

## 1. 产品定位、用户与场景

### 1.1 产品定位

P1 是企业本体工程工作台，覆盖数据源接入、元数据发现、AI
辅助本体建模、人工审查、语义校验、版本管理、发布、图形浏览和 API
交付。核心资产是**可审查、可验证、可版本化、可交换、可被其他 AI
产品消费的语义模型**。

### 1.2 用户角色

  角色         职责                             权限
  ------------ -------------------------------- ----------------------
  本体工程师   定义类、属性、关系、约束和版本   编辑、校验、提交发布
  领域专家     审核定义、术语、关系和约束       评论、确认、驳回
  数据架构师   管理连接器、扫描和数据映射       连接、扫描、映射
  项目管理员   用户、角色、策略和配置           项目管理
  只读用户     浏览已发布语义资产               只读
  外部 Agent   查询已发布本体                   受限 API/MCP 读取

### 1.3 典型流程

1.  创建项目和领域；2. 配置数据库/文档/API 数据源；3.
    测试连接并扫描元数据；4. AI 生成候选类、属性、关系和映射；5.
    人工审核/编辑；6. 运行 JSON Schema、OWL/RDF 和 SHACL 校验；7.
    提交评审；8. 审批并发布不可变版本；9. 图浏览、导出和 API 消费；10.
    根据新数据或反馈创建下一版。

### 1.4 MVP 范围

**必须交付** - 项目、领域、成员、角色和基础审计。 -
PostgreSQL、MySQL、CSV/XLSX、Markdown、PDF/DOCX 基础接入。 -
连接测试、元数据扫描任务、进度、错误和重试。 - AI
发现候选：术语、类、数据属性、对象关系、来源映射、证据、解释。 -
本体编辑：类、属性、关系、枚举、术语、约束、标签、别名、定义。 -
定义级语义校验；有限实例数据校验。 -
草稿、待审、已发布、已弃用；版本差异和基于旧版创建新草稿。 -
本体图浏览、搜索、过滤、邻居展开、对象详情。 - JSON、Turtle、RDF/XML
导入导出；SHACL 导出。 - REST API、Docker Compose、安装/运维文档。

**暂不交付** - 多人实时协同编辑和复杂冲突合并。 - 完整 OWL 2 DL
推理集群和大规模推理优化。 - 自动批准/自动发布；业务系统写操作。 -
全量企业数据治理平台；通用高并发知识图谱服务。 - SaaS 计费、多 Agent
自主协商本体变更。 - Neo4j、Kafka、Kubernetes 作为 MVP 强依赖。

### 1.5 验收标准

  ID     验收标准
  ------ -----------------------------------------------------
  AC01   PostgreSQL/MySQL 可连接并枚举 schema/table/column
  AC02   CSV/XLSX/Markdown/PDF/DOCX 可创建导入/扫描任务
  AC03   扫描任务可查看进度、结果、错误和重试
  AC04   AI 生成类/属性/关系候选，附证据、来源和推断理由
  AC05   候选可接受、编辑、拒绝并记录审核人和原因
  AC06   可编辑类、数据属性、对象属性、枚举、术语和约束
  AC07   校验输出 ERROR/WARNING/INFO，并定位对象和规则
  AC08   版本可比较、评审、发布、弃用；发布快照不可变
  AC09   图浏览支持搜索、过滤、详情和邻居展开
  AC10   JSON 与 Turtle/RDF/XML 至少完成导入导出，支持 SHACL
  AC11   项目、本体、发现、校验、版本和发布 REST API 可用
  AC12   项目级 RBAC、密钥引用、关键操作审计
  AC13   Compose 启动应用、数据库、对象存储和 worker
  AC14   README、配置、部署、API、备份恢复和用户手册齐全

## 2. 状态机

``` mermaid
flowchart TD
 A[创建项目/领域] --> B[配置数据源]
 B --> C[扫描元数据]
 C --> D[AI/规则发现候选]
 D --> E[人工审查和编辑]
 E --> F[语义校验]
 F -->|有阻断错误| E
 F -->|通过| G[提交评审]
 G --> H{审批}
 H -->|驳回| E
 H -->|批准| I[发布不可变版本]
 I --> J[图浏览/API/导出]
 J --> K[反馈或新数据]
 K --> D
```

版本状态：`DRAFT → VALIDATING → IN_REVIEW → PUBLISHED → DEPRECATED`。校验失败回到
DRAFT；评审驳回回到
DRAFT。发布版本不可编辑，修改时从其派生新草稿。回滚是创建新版本，不重写历史。

------------------------------------------------------------------------

# 第二部分：页面原型

## 3. 信息架构

``` text
Workspace
├── Project Overview / Domains / Recent Activities
├── Data Sources
│   ├── Connections / Scan Jobs / Metadata Catalog
├── Ontology Discovery
│   ├── Discovery Jobs / Candidate Review / Evidence Inspector
├── Ontology Designer
│   ├── Classes / Properties / Relations / Constraints / Terms
├── Validation
│   ├── Validation Runs / Findings
├── Versions & Releases
│   ├── Version History / Diff Viewer / Approval Queue
├── Graph Explorer
│   ├── Ontology Graph / Instance Preview (limited)
└── Administration
    ├── Users & Roles / Model Providers / Audit / Settings
```

## 4. 页面低保真线框

### UI-01 项目工作台

``` text
┌─────────────────────────────────────────────────────────────────┐
│ ODAP / Project: Retail Intelligence       Search  Help  User     │
├──────────────┬──────────────────────────────────────────────────┤
│ Workspace    │ Project Overview                                 │
│ Data Sources │ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│ Discovery    │ │数据源 08 │ │对象 126  │ │待审 17   │            │
│ Designer     │ └──────────┘ └──────────┘ └──────────┘            │
│ Validation   │ Recent Activities / Task Status                  │
│ Versions     │ [Add Source] [Start Discovery] [Open Designer]    │
│ Graph        │                                                  │
│ Admin        │                                                  │
└──────────────┴──────────────────────────────────────────────────┘
```

### UI-02 数据源管理

``` text
┌─────────────────────────────────────────────────────────────────┐
│ Data Sources                                  [+ Add Connection] │
│ Filter [Type▼] [Status▼] [Search.........................]       │
│ Name         Type        Scope             Status      Last Scan  │
│ ERP-PG       PostgreSQL  sales, finance    Connected   10m ago    │
│ CRM-MySQL    MySQL       customer          Connected   yesterday  │
│ Product Docs File Store /product-docs      Ready       2h ago     │
├─────────────────────────────────────────────────────────────────┤
│ Selected: ERP-PG | masked host/db | secret reference             │
│ [Test] [Scan Metadata] [Edit] [Disable]                          │
│ Tabs: Overview | Scan Jobs | Assets | Audit                      │
└─────────────────────────────────────────────────────────────────┘
```

### UI-03 本体发现中心

``` text
┌─────────────────────────────────────────────────────────────────┐
│ Ontology Discovery                         [New Discovery Job]  │
│ Job: Retail-2026-11-15 | Source: ERP+CRM | Status: Review         │
├─────────────────────┬───────────────────────────────────────────┤
│ Candidate Queue     │ Candidate Inspector                       │
│ Customer            │ Type: Class                               │
│ CustomerSegment     │ Label: Customer                           │
│ placesOrder         │ Definition: A party that purchases...     │
│ OrderAmount         │ Evidence: crm.customer.id; erp.orders.cid │
│ hasAddress          │ Confidence: 0.87 (advisory only)           │
│                     │ Rationale / Source / Warnings              │
│                     │ [Accept] [Edit] [Reject]                   │
└─────────────────────┴───────────────────────────────────────────┘
```

### UI-04 本体设计器

``` text
┌─────────────────────────────────────────────────────────────────┐
│ Ontology: Core  Draft v0.5       [Validate] [Submit for Review]  │
├──────────────┬─────────────────────────────┬────────────────────┤
│ Object Tree  │ Graph Canvas               │ Inspector          │
│ Classes      │ Customer ─ placesOrder →Order│ Selected: Customer│
│  Customer    │     └ hasAddress → Address  │ Stable ID / IRI    │
│  Order       │                             │ Label / Definition│
│  Product     │                             │ Parents / Props    │
│ Properties   │                             │ Mappings / Evidence│
│ Relations    │                             │ Constraints        │
└──────────────┴─────────────────────────────┴────────────────────┘
```

### UI-05 语义校验中心

``` text
┌─────────────────────────────────────────────────────────────────┐
│ Validation Run VAL-00031              Status: Failed             │
│ Summary: Errors 2 | Warnings 4 | Info 9                         │
│ Severity Object          Rule              Message              │
│ ERROR    placesOrder     DOMAIN_REQUIRED   Domain missing       │
│ ERROR    Customer.id     DATATYPE           Invalid datatype     │
│ WARNING  Customer        DEFINITION         Add definition       │
│ WARNING  hasAddress      INVERSE_OPTIONAL   Consider inverse     │
├─────────────────────────────────────────────────────────────────┤
│ Finding Detail / Evidence / Suggested Fix                        │
│ [Open in Designer] [Export Report] [Run Again]                   │
└─────────────────────────────────────────────────────────────────┘
```

### UI-06 版本管理

``` text
┌─────────────────────────────────────────────────────────────────┐
│ Versions & Releases           [Create Version] [Compare]         │
│ v1.0.0 PUBLISHED 2026-11-15 Approved by Domain Owner              │
│ v0.5.2 IN_REVIEW 2026-11-14 Reviewer: Data Architect             │
│ v0.5.1 DRAFT     2026-11-13 3 changed classes / 2 relations      │
├─────────────────────────────────────────────────────────────────┤
│ Diff: Added 4 | Modified 2 | Removed 1                            │
│ [Object Diff] [RDF Diff] [Export] [Create Draft from v1.0]       │
└─────────────────────────────────────────────────────────────────┘
```

### UI-07 图谱浏览器

``` text
┌─────────────────────────────────────────────────────────────────┐
│ Graph Explorer Mode: Ontology Graph▼ Search [Customer...]        │
├─────────────────────────────────────┬───────────────────────────┤
│             Customer                │ Inspector                 │
│            /         \\              │ Type: owl:Class           │
│    placesOrder     hasAddress        │ Stable ID / IRI           │
│         |              |             │ Definition / Labels       │
│        Order         Address         │ Incoming / Outgoing       │
│         |                            │ Evidence / Version        │
│    containsItem                     │                           │
│         |                            │                           │
│       Product                        │                           │
└─────────────────────────────────────┴───────────────────────────┘
```

### UI-08 管理设置

成员与角色、模型
Provider、发现模板、连接器健康状态、审计日志、系统配置。密钥仅显示名称、掩码和轮换状态，不回显明文。

统一交互要求：列表分页/过滤/排序；任务显示状态/耗时/错误/重试；AI
候选同时展示来源证据；置信度只用于排序提示，不等于事实正确率；发布、删除连接、密钥轮换、导入覆盖需要确认并审计。

------------------------------------------------------------------------

# 第三部分：Ontology Meta-model

## 5. 元模型设计

### 5.1 核心对象

  对象                    用途                     关键字段
  ----------------------- ------------------------ ----------------------------------------
  OntologyProject         项目边界                 id, key, name, tenant_id
  Domain                  领域分区                 id, project_id, namespace
  Ontology                本体集合                 id, domain_id, ontology_iri
  OntologyVersion         不可变快照               id, ontology_id, version, hash
  OntologyEntity          本体对象抽象             id, stable_key, entity_type, iri
  Class                   类/概念                  parents, disjoint classes
  Property                属性                     kind, domain, range
  Relation                对象关系                 domain, range, inverse
  Constraint              约束                     type, expression, severity
  Term                    术语                     preferred label, aliases, language
  DataSource              数据源                   connector, config, secret_ref
  MetadataAsset           扫描元数据               type, qualified_name, schema
  DataMapping             语义对象到数据资产映射   entity, asset, expression
  DiscoveryJob            发现任务                 provider, model, prompt version
  DiscoveryProposal       候选结果                 payload, evidence, confidence, review
  Evidence                证据                     source_ref, locator, excerpt, checksum
  ValidationRun/Finding   校验与问题               ruleset, severity, object
  ChangeRecord            变更历史                 actor, operation, before/after
  Release                 发布记录                 version, approver, published_at

### 5.2 内部对象 JSON Schema 基线

正式仓库应将其落为 JSON Schema Draft 2020-12 文件。

``` json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://odap.example/schemas/ontology-entity.schema.json",
  "type": "object",
  "required": ["id", "ontology_id", "entity_type", "iri", "label"],
  "properties": {
    "id": {"type": "string"},
    "ontology_id": {"type": "string"},
    "entity_type": {"enum": ["CLASS","DATA_PROPERTY","OBJECT_PROPERTY","ANNOTATION_PROPERTY","INDIVIDUAL","ENUM","TERM","CONSTRAINT"]},
    "iri": {"type": "string", "format": "uri"},
    "label": {"type": "object", "additionalProperties": {"type": "string"}},
    "definition": {"type": "object", "additionalProperties": {"type": "string"}},
    "aliases": {"type": "array", "items": {"type": "string"}},
    "domain_ids": {"type": "array", "items": {"type": "string"}},
    "range": {"type": ["object","null"]},
    "parent_ids": {"type": "array", "items": {"type": "string"}},
    "constraints": {"type": "array", "items": {"type": "string"}},
    "source_mappings": {"type": "array", "items": {"type": "string"}},
    "evidence_ids": {"type": "array", "items": {"type": "string"}},
    "lifecycle": {"enum": ["PROPOSED","ACCEPTED","REJECTED","DEPRECATED"]},
    "extensions": {"type": "object"}
  },
  "additionalProperties": false
}
```

示例：

``` json
{
  "id": "cls_customer",
  "ontology_id": "ont_core",
  "entity_type": "CLASS",
  "iri": "https://example.org/core#Customer",
  "label": {"en": "Customer", "zh": "客户"},
  "definition": {"en": "A party that purchases products or services."},
  "aliases": ["Buyer", "Client"],
  "parent_ids": ["cls_party"],
  "evidence_ids": ["ev_1001"],
  "lifecycle": "ACCEPTED",
  "extensions": {}
}
```

### 5.3 标准映射

  -----------------------------------------------------------------------
  内部类型                            标准表达
  ----------------------------------- -----------------------------------
  Class                               `owl:Class`

  Data Property                       `owl:DatatypeProperty`

  Object Property                     `owl:ObjectProperty`

  Parent                              `rdfs:subClassOf`

  Domain/Range                        `rdfs:domain` / `rdfs:range`

  Label/Definition/Alias              `rdfs:label` / `skos:definition` /
                                      `skos:altLabel`

  Constraint                          SHACL NodeShape / PropertyShape

  Provenance                          `prov:wasDerivedFrom` + ODAP
                                      provenance

  Stable ID                           自定义 `odap:stableId`
  -----------------------------------------------------------------------

OWL 表达本体逻辑语义；SHACL 表达数据形状与约束，不能混为一谈。

### 5.4 版本规则

-   每个对象：数据库 UUID、跨版本 stable_key、语义 IRI
    三种标识各司其职。
-   发布时生成完整快照并计算 SHA-256。
-   发布版本只读；修改必须创建新草稿。
-   MAJOR：破坏兼容的语义重定义/删除；MINOR：新增兼容对象；PATCH：定义、标签和非破坏性修正。
-   回滚创建新版本，不覆盖历史。
-   外部引用必须指定 ontology IRI 和版本，不只使用 latest。

------------------------------------------------------------------------

# 第四部分：数据库 Schema

## 6. PostgreSQL DDL 基线

存储策略：PostgreSQL
保存项目、权限、连接器配置（不含明文密钥）、本体编辑对象、任务和审计；MinIO/S3
保存原始文件、扫描结果、版本快照和导出包。MVP 以 JSONB + RDF
文件存储；需要复杂 RDF 查询时再评估 Fuseki/RDF4J。Neo4j/pgvector
均非强制。

``` sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE tenants (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 name TEXT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE users (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 email TEXT NOT NULL UNIQUE,
 display_name TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'ACTIVE',
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE projects (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 tenant_id UUID NOT NULL REFERENCES tenants(id),
 project_key TEXT NOT NULL,
 name TEXT NOT NULL,
 description TEXT,
 created_by UUID REFERENCES users(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(tenant_id, project_key)
);
CREATE TABLE project_members (
 project_id UUID REFERENCES projects(id),
 user_id UUID REFERENCES users(id),
 role TEXT NOT NULL CHECK(role IN ('OWNER','ONTOLOGY_ENGINEER','DOMAIN_EXPERT','DATA_ARCHITECT','VIEWER')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY(project_id,user_id)
);
CREATE TABLE domains (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 project_id UUID NOT NULL REFERENCES projects(id),
 domain_key TEXT NOT NULL,
 name TEXT NOT NULL,
 namespace_iri TEXT NOT NULL,
 description TEXT,
 UNIQUE(project_id,domain_key)
);
CREATE TABLE data_sources (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 project_id UUID NOT NULL REFERENCES projects(id),
 name TEXT NOT NULL,
 connector_type TEXT NOT NULL,
 config JSONB NOT NULL DEFAULT '{}',
 secret_ref TEXT,
 status TEXT NOT NULL DEFAULT 'DRAFT',
 created_by UUID REFERENCES users(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE scan_jobs (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 data_source_id UUID NOT NULL REFERENCES data_sources(id),
 status TEXT NOT NULL,
 scope JSONB NOT NULL DEFAULT '{}',
 started_at TIMESTAMPTZ,
 finished_at TIMESTAMPTZ,
 result_uri TEXT,
 error JSONB,
 created_by UUID REFERENCES users(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE metadata_assets (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 project_id UUID NOT NULL REFERENCES projects(id),
 data_source_id UUID NOT NULL REFERENCES data_sources(id),
 scan_job_id UUID REFERENCES scan_jobs(id),
 asset_type TEXT NOT NULL,
 qualified_name TEXT NOT NULL,
 metadata JSONB NOT NULL DEFAULT '{}',
 fingerprint TEXT,
 discovered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_metadata_assets_source ON metadata_assets(data_source_id,qualified_name);
CREATE TABLE ontologies (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 domain_id UUID NOT NULL REFERENCES domains(id),
 ontology_iri TEXT NOT NULL UNIQUE,
 title TEXT NOT NULL,
 description TEXT,
 active_version_id UUID,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE ontology_entities (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 ontology_id UUID NOT NULL REFERENCES ontologies(id),
 stable_key TEXT NOT NULL,
 entity_type TEXT NOT NULL,
 iri TEXT NOT NULL,
 payload JSONB NOT NULL,
 lifecycle TEXT NOT NULL DEFAULT 'ACCEPTED',
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(ontology_id,stable_key),
 UNIQUE(ontology_id,iri)
);
CREATE INDEX idx_entities_type ON ontology_entities(ontology_id,entity_type);
CREATE INDEX idx_entities_payload ON ontology_entities USING GIN(payload);
CREATE TABLE data_mappings (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 entity_id UUID NOT NULL REFERENCES ontology_entities(id),
 metadata_asset_id UUID NOT NULL REFERENCES metadata_assets(id),
 mapping_type TEXT NOT NULL,
 mapping_expression JSONB NOT NULL DEFAULT '{}',
 confidence NUMERIC(5,4),
 evidence JSONB NOT NULL DEFAULT '{}',
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE discovery_jobs (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 project_id UUID NOT NULL REFERENCES projects(id),
 ontology_id UUID REFERENCES ontologies(id),
 provider_key TEXT NOT NULL,
 provider_version TEXT,
 model_name TEXT,
 template_version TEXT NOT NULL,
 input_snapshot_uri TEXT,
 status TEXT NOT NULL,
 parameters JSONB NOT NULL DEFAULT '{}',
 started_at TIMESTAMPTZ,
 finished_at TIMESTAMPTZ,
 error JSONB,
 created_by UUID REFERENCES users(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE evidence (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 project_id UUID NOT NULL REFERENCES projects(id),
 source_type TEXT NOT NULL,
 source_ref TEXT NOT NULL,
 locator JSONB NOT NULL DEFAULT '{}',
 excerpt TEXT,
 checksum TEXT,
 metadata JSONB NOT NULL DEFAULT '{}',
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE discovery_proposals (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 discovery_job_id UUID NOT NULL REFERENCES discovery_jobs(id),
 target_type TEXT NOT NULL,
 proposed_payload JSONB NOT NULL,
 confidence NUMERIC(5,4),
 rationale TEXT,
 evidence_ids UUID[] NOT NULL DEFAULT '{}',
 review_status TEXT NOT NULL DEFAULT 'PENDING',
 reviewed_by UUID REFERENCES users(id),
 reviewed_at TIMESTAMPTZ,
 review_comment TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE validation_runs (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 ontology_id UUID NOT NULL REFERENCES ontologies(id),
 target_snapshot_uri TEXT,
 validator_name TEXT NOT NULL,
 ruleset_version TEXT NOT NULL,
 status TEXT NOT NULL,
 summary JSONB NOT NULL DEFAULT '{}',
 started_at TIMESTAMPTZ,
 finished_at TIMESTAMPTZ,
 created_by UUID REFERENCES users(id)
);
CREATE TABLE validation_findings (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 validation_run_id UUID NOT NULL REFERENCES validation_runs(id),
 object_stable_key TEXT,
 rule_id TEXT NOT NULL,
 severity TEXT NOT NULL CHECK(severity IN ('ERROR','WARNING','INFO')),
 message TEXT NOT NULL,
 details JSONB NOT NULL DEFAULT '{}'
);
CREATE TABLE ontology_versions (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 ontology_id UUID NOT NULL REFERENCES ontologies(id),
 version_label TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('DRAFT','IN_REVIEW','PUBLISHED','DEPRECATED')),
 snapshot_uri TEXT NOT NULL,
 content_hash TEXT NOT NULL,
 parent_version_id UUID REFERENCES ontology_versions(id),
 changelog TEXT,
 created_by UUID REFERENCES users(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 published_at TIMESTAMPTZ,
 UNIQUE(ontology_id,version_label)
);
ALTER TABLE ontologies ADD CONSTRAINT fk_active_version
 FOREIGN KEY(active_version_id) REFERENCES ontology_versions(id);
CREATE TABLE change_records (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 ontology_id UUID NOT NULL REFERENCES ontologies(id),
 object_stable_key TEXT,
 actor_id UUID REFERENCES users(id),
 operation TEXT NOT NULL,
 before_payload JSONB,
 after_payload JSONB,
 correlation_id TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE releases (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 ontology_version_id UUID NOT NULL UNIQUE REFERENCES ontology_versions(id),
 release_status TEXT NOT NULL,
 approved_by UUID REFERENCES users(id),
 published_by UUID REFERENCES users(id),
 published_at TIMESTAMPTZ,
 release_notes TEXT
);
CREATE TABLE audit_events (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 project_id UUID REFERENCES projects(id),
 actor_id UUID REFERENCES users(id),
 action TEXT NOT NULL,
 resource_type TEXT NOT NULL,
 resource_id TEXT NOT NULL,
 outcome TEXT NOT NULL,
 details JSONB NOT NULL DEFAULT '{}',
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

实现说明： - `payload` 是 MVP 灵活承载元模型属性的
JSONB；高频字段单独列出。 - 发布快照写入对象存储，hash 校验完整性。 -
`secret_ref` 只保存 Vault/Secrets Manager 引用。 -
生产环境所有资源查询必须强制校验 project/tenant 范围；后续可增加
PostgreSQL RLS。 - 正式实现还需 Alembic
migrations、软删除策略、索引评估、备份恢复演练和审计保留策略。

------------------------------------------------------------------------

# 第五部分：REST API 基线

## 7. 通用规范

-   Base path：`/api/v1`
-   JSON；文件用 multipart 或预签名对象存储 URL。
-   认证：OIDC Session 或 Bearer API Token。
-   授权：项目级 RBAC；身份来自服务端 token/session，不信任客户端传入
    user-id header。
-   分页：`limit=50&cursor=...`；写操作支持 `Idempotency-Key`；响应带
    `X-Request-ID`。

错误结构：

``` json
{
  "error": {
    "code": "ONTOLOGY_VALIDATION_FAILED",
    "message": "Ontology contains blocking findings.",
    "details": [{"rule_id":"PROP_DOMAIN_REQUIRED","object_id":"rel_places_order"}],
    "request_id":"req_123"
  }
}
```

## 8. API 清单

  Method             Endpoint                               说明
  ------------------ -------------------------------------- ---------------------
  GET/POST           `/projects`                            项目列表/创建
  GET/PATCH          `/projects/{projectId}`                项目详情/更新
  GET/POST           `/projects/{projectId}/domains`        领域列表/创建
  GET/POST           `/projects/{projectId}/data-sources`   数据源列表/创建
  POST               `/data-sources/{id}/test`              测试连接
  POST               `/data-sources/{id}/scan-jobs`         创建扫描任务
  GET                `/scan-jobs/{id}`                      扫描任务状态
  GET                `/projects/{id}/metadata-assets`       元数据资产
  POST               `/ontologies`                          创建本体
  GET/PATCH          `/ontologies/{id}`                     本体详情/元数据更新
  GET/POST           `/ontologies/{id}/entities`            对象列表/创建
  GET/PATCH/DELETE   `/ontology-entities/{id}`              对象读取/更新/弃用
  POST               `/ontologies/{id}/discovery-jobs`      创建发现任务
  GET                `/discovery-jobs/{id}`                 发现任务详情
  GET                `/discovery-jobs/{id}/proposals`       候选列表
  POST               `/proposals/{id}/review`               接受/拒绝/修改
  POST               `/ontologies/{id}/validation-runs`     执行校验
  GET                `/validation-runs/{id}`                校验结果
  POST               `/ontologies/{id}/versions`            创建快照版本
  GET                `/ontologies/{id}/versions`            版本列表
  GET                `/versions/{id}/diff?against={id}`     版本差异
  POST               `/versions/{id}/submit-review`         提交评审
  POST               `/versions/{id}/approve`               审批
  POST               `/versions/{id}/publish`               发布
  POST               `/ontologies/{id}/imports`             导入 RDF/OWL/JSON
  GET                `/versions/{id}/exports/{format}`      导出
  GET                `/ontologies/{id}/graph`               图数据
  GET                `/projects/{id}/audit-events`          审计记录

### 8.1 请求示例：创建数据源

``` http
POST /api/v1/projects/{projectId}/data-sources
Authorization: Bearer <token>
Content-Type: application/json
```

``` json
{
  "name": "ERP PostgreSQL",
  "connector_type": "postgresql",
  "config": {"host":"db.internal","port":5432,"database":"erp","schema_allowlist":["public","sales"]},
  "credential_secret_ref": "secret://project/erp-postgres"
}
```

### 8.2 请求示例：启动发现

``` json
{
  "ontology_id": "ont-uuid",
  "source_asset_ids": ["asset-uuid-1","asset-uuid-2"],
  "provider": "nvidia_auto_ontology",
  "template": "relational-domain-discovery",
  "language": ["en","zh"],
  "options": {"include_relationship_candidates":true,"include_data_mappings":true,"sample_data":false}
}
```

### 8.3 请求示例：审核候选

``` json
{
  "decision": "ACCEPT",
  "edited_payload": {"stable_key":"cls_customer","entity_type":"CLASS","label":{"en":"Customer","zh":"客户"}},
  "comment": "Confirmed by domain owner."
}
```

API 约束：删除对象默认转为
DEPRECATED；发布必须检查校验、审批、权限、快照 hash；导入覆盖必须先展示
diff；发现结果只能成为候选，不得直接修改已发布版本；图 API
分页/按邻居展开，避免返回超大图。

------------------------------------------------------------------------

# 第六部分：架构、组件依赖与开源适配

## 9. 逻辑架构

``` mermaid
flowchart TB
 U[Ontology Engineer / Domain Expert] --> WEB[Web Workbench]
 AG[External Agent] --> API[REST API]
 WEB --> API
 API --> IAM[OIDC / RBAC / Policy]
 API --> CORE[Ontology Core]
 CORE --> DB[(PostgreSQL)]
 CORE --> OBJ[(MinIO / S3)]
 API --> CONN[Connector Manager]
 CONN --> SRC[DB / Files / REST APIs]
 CONN --> SCAN[Metadata Scanner]
 SCAN --> Q[Redis Queue / Worker]
 Q --> DISC[Discovery Orchestrator]
 DISC --> LLM[LLM Provider Adapter]
 DISC --> NAO[NVIDIA Auto Ontology Adapter]
 CORE --> VAL[Validation Service]
 VAL --> SHACL[pySHACL]
 VAL --> RDF[RDF/OWL Parser]
 CORE --> VER[Version & Release]
 VER --> OBJ
 CORE --> GRAPH[Graph API]
 GRAPH --> UI[Graph Explorer]
 API --> AUDIT[Audit / Observability]
```

MVP 使用模块化单体 + 异步 worker，不急于拆微服务。

## 10. NVIDIA Auto Ontology 适配

适合复用/借鉴：关系型 schema
ingestion、术语/关系候选、数据映射、语义目录、认证思路、MCP/API 输出。

不直接耦合的原因： - 核心聚焦数据库语义层与 Agent 查询，不覆盖所有通用
OWL/SHACL 生命周期需求。 - Terms、SQL Attributes、Relationships 与通用
Class/Property/Constraint 不完全同构。 - 其
UI、权限、数据表和版本机制是独立产品体系，直接复用会产生双主数据。 -
当前仓库说明不接受外部贡献，fork 长期维护风险需要单独评估。 - P1
还需文档、代码库、API 等连接器。

适配器接口：

``` python
from typing import Protocol, Any

class DiscoveryProvider(Protocol):
    provider_key: str
    async def inspect(self, request: dict[str, Any]) -> dict[str, Any]: ...
    async def propose(self, request: dict[str, Any]) -> list[dict[str, Any]]: ...
    async def health(self) -> dict[str, Any]: ...
```

适配输出必须标准化为 P1
Proposal：`target_type`、`proposed_payload`、`source_refs`、`evidence`、`rationale`、`provider_key/version`、`model_name`、`prompt_template_version`、`confidence`、`warnings`。

POC 必测： 1. schema/table 范围是否可控；是否只读并避免复制业务数据。 2.
能否保留字段级来源、映射、证据和推断理由。 3. 输出映射到 P1
Class/Property/Relation/DataMapping 的损失。 4. 是否可配置
OpenAI-compatible endpoint 或本地模型。 5.
自托管安全边界、RBAC、密钥管理和 API 稳定性。 6. Apache-2.0
主项目及第三方 notices、容器依赖、模型服务条款和数据传输要求。

## 11. Protégé 互操作

MVP 路径： 1. P1 维护内部 JSON Meta-model 和版本快照。 2. 导出 OWL
2/RDF/Turtle，Protégé Desktop 打开进行专家审查。 3. Protégé
保存后重新导入 P1，先生成差异预览，再进入校验流程。 4. 建立 P1 JSON →
OWL/Turtle → Protégé 保存 → P1 导入的往返测试。 5.
对无法无损往返的构造给出兼容性警告，不静默丢弃。

不建议嵌入 Protégé UI：Desktop 是 Java 桌面应用；WebProtégé
有自己的用户、权限、协作和修订体系。P1
直接嵌入会造成双账号、双版本、双审计和 UI 割裂。**Protégé
是专家互操作工具，不是 P1 主 UI。**

## 12. 组件依赖

  层              技术建议                                  重要性
  --------------- ----------------------------------------- ----------------------------
  Web             Next.js + React + TypeScript              必选
  UI              Ant Design 或 shadcn/ui                   二选一
  Graph UI        Cytoscape.js                              必选
  API             Python 3.12+ / FastAPI                    必选
  ORM/Migration   SQLAlchemy 2 + Alembic                    必选
  DB              PostgreSQL 16/17                          必选
  Object Store    MinIO / S3                                必选
  Async           Celery + Redis                            MVP 推荐
  RDF             RDFLib                                    必选
  SHACL           pySHACL                                   必选
  JSON Schema     jsonschema                                必选
  OWL 深度处理    OWLAPI Java sidecar                       POC 后决定
  LLM             NVIDIA NIM / OpenAI-compatible endpoint   可配置
  Auto Ontology   Provider Adapter                          可选
  Auth            OIDC / Keycloak                           MVP 可先本地账号，接口预留
  Secrets         Docker secrets / Vault                    生产必需
  Observability   OpenTelemetry / Prometheus                后续增强
  RDF Store       Fuseki / RDF4J                            按需
  Graph DB        Neo4j                                     非 MVP
  Vector          pgvector                                  非 MVP

Python
依赖类别：`fastapi`、`uvicorn`、`pydantic`、`sqlalchemy`、`psycopg`、`alembic`、`celery`、`redis`、`rdflib`、`pyshacl`、`jsonschema`、`httpx`、`cryptography`、`pandas`、`openpyxl`、`python-docx`、`pypdf`、`pytest`、`ruff`。实现时锁定精确版本和许可证，不在基线文档中臆造版本号。

------------------------------------------------------------------------

# 第七部分：Docker Compose 部署基线

## 13. 部署拓扑

开发/演示环境服务：web、api、worker、postgres、redis、minio、minio-init。生产环境需补齐
TLS、OIDC、密钥管理、备份、网络策略、资源限制和镜像扫描。

建议文件：`deploy/docker-compose.yml`

``` yaml
name: odap-p1
services:
  web:
    build:
      context: ../
      dockerfile: apps/web/Dockerfile
    environment:
      NEXT_PUBLIC_API_BASE_URL: ${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000}
    ports: ["3000:3000"]
    depends_on:
      api: {condition: service_healthy}
    restart: unless-stopped
    networks: [frontend, backend]

  api:
    build:
      context: ../
      dockerfile: services/api/Dockerfile
    environment:
      APP_ENV: ${APP_ENV:-development}
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      S3_ENDPOINT_URL: http://minio:9000
      S3_BUCKET: ${S3_BUCKET:-odap-artifacts}
      S3_ACCESS_KEY: ${MINIO_ROOT_USER}
      S3_SECRET_KEY: ${MINIO_ROOT_PASSWORD}
      LLM_BASE_URL: ${LLM_BASE_URL:-}
      LLM_API_KEY: ${LLM_API_KEY:-}
      LLM_MODEL: ${LLM_MODEL:-}
    ports: ["8000:8000"]
    depends_on:
      postgres: {condition: service_healthy}
      redis: {condition: service_healthy}
      minio: {condition: service_healthy}
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"]
      interval: 20s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks: [frontend, backend]

  worker:
    build:
      context: ../
      dockerfile: services/worker/Dockerfile
    command: celery -A app.celery_app worker --loglevel=INFO
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      S3_ENDPOINT_URL: http://minio:9000
      S3_BUCKET: ${S3_BUCKET:-odap-artifacts}
      S3_ACCESS_KEY: ${MINIO_ROOT_USER}
      S3_SECRET_KEY: ${MINIO_ROOT_PASSWORD}
      LLM_BASE_URL: ${LLM_BASE_URL:-}
      LLM_API_KEY: ${LLM_API_KEY:-}
      LLM_MODEL: ${LLM_MODEL:-}
    depends_on:
      postgres: {condition: service_healthy}
      redis: {condition: service_healthy}
      minio: {condition: service_healthy}
    restart: unless-stopped
    networks: [backend]

  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-odap}
      POSTGRES_USER: ${POSTGRES_USER:-odap}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD}
    volumes: [postgres_data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-odap} -d ${POSTGRES_DB:-odap}"]
      interval: 10s
      timeout: 5s
      retries: 10
    restart: unless-stopped
    networks: [backend]

  redis:
    image: redis:7-alpine
    command: ["redis-server", "--appendonly", "yes"]
    volumes: [redis_data:/data]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 10
    restart: unless-stopped
    networks: [backend]

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:?Set MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:?Set MINIO_ROOT_PASSWORD}
    volumes: [minio_data:/data]
    ports: ["9001:9001"]
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 15s
      timeout: 5s
      retries: 10
    restart: unless-stopped
    networks: [backend]

  minio-init:
    image: minio/mc:latest
    depends_on:
      minio: {condition: service_healthy}
    entrypoint: >
      /bin/sh -c "mc alias set local http://minio:9000 $$MINIO_ROOT_USER $$MINIO_ROOT_PASSWORD &&
      mc mb --ignore-existing local/$$S3_BUCKET"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
      S3_BUCKET: ${S3_BUCKET:-odap-artifacts}
    networks: [backend]
    restart: "no"

volumes:
  postgres_data:
  redis_data:
  minio_data:

networks:
  frontend:
  backend:
    internal: true
```

### 13.1 `.env.example`

``` dotenv
APP_ENV=development
POSTGRES_DB=odap
POSTGRES_USER=odap
POSTGRES_PASSWORD=replace-with-long-random-password
MINIO_ROOT_USER=odapminio
MINIO_ROOT_PASSWORD=replace-with-long-random-password
S3_BUCKET=odap-artifacts
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
AUTO_ONTOLOGY_BASE_URL=
AUTO_ONTOLOGY_API_TOKEN=
```

### 13.2 启动

``` bash
cp .env.example .env
# 修改所有密码和密钥
docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml ps
```

访问：Web `http://localhost:3000`；API 文档
`http://localhost:8000/docs`；MinIO Console `http://localhost:9001`。

**注意**：Compose 中 `latest` 仅作示例占位，正式部署需锁定
tag/digest；PostgreSQL/Redis 不映射宿主机端口；MinIO Console
仅开发环境开放；生产用 Docker secrets/Vault；LLM Key 仅后端和 worker
可见；数据库迁移由单独 release job 执行。

------------------------------------------------------------------------

# 第八部分：安全、质量与研发计划

## 14. 安全基线

1.  数据库连接默认只读；默认扫描 schema 元数据，不采集完整业务数据。
2.  Schema/table allowlist；样本采集显式开启、限制行数并脱敏。
3.  凭据放 Secret Manager，数据库只保存 `secret_ref`。
4.  项目级 RBAC 在服务端强制校验；禁止信任客户端 user-id header。
5.  文件解析在隔离 worker 执行，限制大小、页数、解压深度和时间。
6.  发送给外部 LLM 前执行数据分类/脱敏；默认只传必要元数据。
7.  AI 输出视为不可信输入，经过 JSON Schema、语义规则和人工审核。
8.  连接器出口 allowlist，防 SSRF 和云元数据地址访问。
9.  审计连接测试、扫描、导入、审批、发布和密钥轮换；日志不得记录密钥或完整连接串。

## 15. 测试策略

-   Unit：元模型、IRI、版本 diff、状态机、RBAC。
-   Contract：REST API、Provider Adapter、Connector Adapter。
-   Integration：PostgreSQL/MySQL、MinIO、Redis、worker。
-   Semantic：OWL/RDF 解析、SHACL、导入导出往返。
-   Security：越权、密钥泄露、SSRF、文件解析边界。
-   E2E：项目→连接→扫描→发现→审查→校验→发布→导出。

发布门禁：无阻断级错误；评审已批准；发布者具备权限；快照及 hash
已持久化；变更说明非空；导入兼容性错误已处理；审计记录成功写入。

## 16. 研发阶段

  阶段   目标               产物
  ------ ------------------ --------------------------------------------
  P1-0   冻结范围与元模型   PRD、Meta-model、API 合同、ADR
  P1-1   工程底座           Repo、Compose、DB migration、RBAC、基础 UI
  P1-2   数据接入           PostgreSQL/MySQL/CSV/XLSX/文档扫描
  P1-3   发现与编辑         Provider 接口、LLM 发现、候选审查、设计器
  P1-4   校验与版本         JSON Schema/SHACL、diff、审批、发布、导出
  P1-5   图浏览与验收       Graph Explorer、API、E2E、安全检查、文档

### P1-0 技术验证清单

-   [ ] 独立部署 NVIDIA Auto Ontology，记录
    API、数据结构、权限和资源依赖。
-   [ ] 用同一关系型样本库比较 Auto Ontology 输出与 P1 Meta-model
    的映射损失。
-   [ ] P1 导出的 OWL 在 Protégé 打开、保存、重新导入，验证往返兼容。
-   [ ] 验证 RDFLib + pySHACL 对 MVP 语义约束的覆盖度。
-   [ ] 仅在 RDFLib 不满足复杂 OWL 处理时引入 OWLAPI sidecar。
-   [ ] 明确本地模型/远程模型的数据边界；锁定依赖版本和许可证清单。

## 17. ADR 摘要

-   **ADR-001 模块化单体优先**：Next.js + FastAPI +
    worker；模块按接口解耦，后续按需要拆分。
-   **ADR-002 内部 Meta-model +
    RDF/OWL/SHACL**：内部模型是权威；标准格式用于语义表达和交换；SHACL
    做形状校验。
-   **ADR-003 Auto Ontology Adapter**：不复用其数据库/UI；通过 Provider
    输出候选，避免双主数据和 fork 锁定。
-   **ADR-004 Protégé Interoperability**：通过 OWL/RDF
    导入导出与往返测试兼容；不嵌入桌面 UI。

## 18. 待评审事项

1.  首个部署目标是单机私有化演示，还是客户内网多节点。
2.  第一批数据源优先级是否按 PostgreSQL、MySQL、CSV/XLSX、文档排序。
3.  MVP 身份认证先用本地账号，还是直接接 Keycloak/OIDC。
4.  Auto Ontology POC 的运行条件与 NVIDIA 模型服务策略。
5.  OWL 兼容范围是否先限定常见 OWL 2/RDF 构造，对高级表达式告警。
6.  首批样例建议一个关系型业务库 + 一套文档，避免行业特例影响通用模型。

**最终建议**：先实现自有 Meta-model、扫描、发现 Provider
接口、人工编辑、校验和版本发布闭环；Auto Ontology 与 Protégé
作为可插拔能力。此路线兼顾开源复用、产品独立性、私有化部署和后续 P2-P5
共用语义基础设施。

## 参考资料

1.  NVIDIA Auto Ontology：<https://github.com/NVIDIA/auto-ontology>
2.  NVIDIA Auto Ontology
    License：<https://github.com/NVIDIA/auto-ontology/blob/main/LICENSE>
3.  NVIDIA Auto Ontology Contribution
    Policy：<https://github.com/NVIDIA/auto-ontology/blob/main/CONTRIBUTING.md>
4.  Protégé 官方软件：<https://protege.stanford.edu/software/>
5.  WebProtégé：<https://protegewiki.stanford.edu/wiki/WebProtege>
6.  Protégé Desktop：<https://github.com/protegeproject/protege>
7.  Protégé Getting
    Started：<https://protegeproject.github.io/protege/getting-started/>
