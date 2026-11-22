# P1 Ontology Meta-model Design

- Version: V1.0
- Date: 2026-11-21
- Status: Engineering Baseline
- Scope: P1 MVP

## 1. Purpose

本文件定义 P1 内部元模型的对象边界、标识策略、引用约束、版本规则和扩展机制。平台元模型负责描述平台如何管理本体资产；领域本体描述业务概念；实例数据则按领域本体表达具体事实。

## 2. Three Modeling Layers

| Layer | Purpose | Example |
|---|---|---|
| Platform Meta-model | 描述和管理本体资产 | Ontology、OntologyClass、OntologyVersion |
| Domain Ontology | 描述业务概念和规则 | Customer、Order、Product |
| Instance Data | 领域本体的具体实例 | C10001、O2026001 |

## 3. Core Object Groups

### Project and Domain
- OntologyProject：项目及隔离边界。
- Domain：项目内业务知识领域。

首期 Domain 只归属一个 Project。

### Ontology Structure
- Ontology：本体资产身份。
- OntologyVersion：不可变版本快照。
- OntologyClass：类。
- DatatypeProperty：数据类型属性。
- ObjectProperty：对象属性。
- Relation：编辑器中的关系建模抽象，映射到 ObjectProperty。
- Constraint：内部、JSON Schema、SHACL 或 OWL 约束。

Relation 与 ObjectProperty 不应复制同一语义定义。Relation 通过 objectPropertyId 和端点类表达图形化关系。

### Terminology
- Term：标准术语或概念词条。
- Alias：带语言、类型和适用范围的别名。

### Data Source and Mapping
- DataSource：数据库、文档库、API、代码库等来源。
- MetadataAsset：来源中的表、字段、Schema、文档等资产。
- DataMapping：来源资产与本体元素的对应关系。

### Discovery and Evidence
- DiscoveryJob：一次发现任务。
- DiscoveryProposal：候选类、属性、关系或映射。
- Evidence：候选项的来源证据。

候选结果未经审核不得直接写入正式版本。

### Validation and Release
- ValidationRun：针对工作区或具体版本的一次验证。
- Finding：验证问题、警告或信息项。
- ChangeRecord：版本变更记录。
- Release：指向明确不可变版本的发布记录。

## 4. Identifier Strategy

| Identifier | Example | Usage |
|---|---|---|
| Internal ID | UUID | 平台内部稳定身份 |
| Semantic IRI | `https://example.org/customer#Customer` | RDF/OWL 语义标识 |
| Source-native ID | `crm.customer.customer_id` | 外部资产标识 |

内部 ID 不随重命名而变化。IRI 变化必须记录迁移关系。源系统 ID 必须在 DataSource 范围内解释，不能直接替代内部 ID。

## 5. Common Fields

项目范围对象按需包含：
- `id`
- `projectId`
- `createdAt`
- `updatedAt`
- `createdBy`
- `updatedBy`
- `extensions`

本体版本范围对象还应包含 `ontologyId`、`ontologyVersionId`、`iri` 和来源引用。

不是所有对象都必须拥有全部字段；每种对象以自己的 Schema 为准。

## 6. Snapshot and Versioning

Ontology 是持续演进的资产身份；OntologyVersion 是某个时间点的不可变快照。

草稿区可修改。正式版本不能原地修改。每个发布记录必须引用一个明确版本、验证记录和制品摘要。

快照建议包含 Schema 版本、Ontology ID、Project ID、语义对象集合、来源引用和创建信息。大文件放入 S3 兼容对象存储，数据库保存引用和 SHA-256 摘要。

## 7. Relation and ObjectProperty

ObjectProperty 承载 OWL 对象属性语义，包括 domain、range、inverse 和 property characteristics。Relation 是平台编辑与可视化层的关系实例，引用一个 ObjectProperty，并给出源类与目标类。

验证器必须检查 Relation 的源类和目标类与 ObjectProperty 的 domain/range 一致。

## 8. JSON Schema

采用 JSON Schema Draft 2020-12。公共字段放入 `common.schema.json`，对象 Schema 通过 `$ref` 引用公共定义。Schema 验证结构、类型、必填字段和枚举；引用完整性、项目隔离和本体语义由后端验证器处理。

格式校验必须显式启用。不要假设任意 JSON Schema 验证器都会将 `format` 默认作为断言。

## 9. Validation Responsibility

| Layer | Responsibility |
|---|---|
| JSON Schema / Pydantic | 对象结构和字段规则 |
| Reference Validator | 对象存在、类型、项目和版本归属 |
| Semantic Validator | IRI 唯一性、类层次、属性端点和关系一致性 |
| SHACL | RDF 图约束 |
| OWL tooling | 本体逻辑一致性与适用推理任务 |

SHACL 通过不等于 OWL 逻辑一致性已证明；OWL 未发现矛盾也不意味着业务完整性规则全部满足。

## 10. Project Isolation

默认内部引用必须属于同一 Project。跨项目复用只能通过受控共享资产机制，并引用已发布的不可变版本。未经授权的草稿引用必须被拒绝。

## 11. Extension Policy

扩展字段统一放入 `extensions`，使用反向域名或组织命名空间隔离。扩展必须有 Schema 和维护责任，不得覆盖核心字段或绕过权限检查。

## 12. Compatibility Policy

- 增加可选字段：通常兼容。
- 增加枚举值：需检查旧客户端。
- 修改字段类型、必填要求或语义：不兼容变更。
- 删除字段：不兼容变更。

不兼容变更使用新的主版本，并提供显式迁移函数。未知版本和降级迁移默认拒绝。

## 13. Persistence

MVP 使用 PostgreSQL 保存结构化对象、引用和审核记录；JSONB 保存受控扩展；S3 兼容对象存储保存源文件、版本快照和导出制品。首期不强制引入图数据库或专用 RDF 三元组库。

## 14. Acceptance Criteria

- [ ] 所有对象 Schema 均符合 Draft 2020-12。
- [ ] 合法对象通过，非法对象被拒绝。
- [ ] 内部 ID 在重命名后保持稳定。
- [ ] IRI 变更有变更记录。
- [ ] 所有内部引用可以解析且目标类型正确。
- [ ] 未授权跨项目引用被拒绝。
- [ ] 正式版本不可变，快照摘要可复算。
- [ ] Release 引用准确版本和通过的验证任务。
- [ ] 导入导出不支持的结构有警告或错误。
- [ ] Schema 变更有兼容性分类和迁移路径。

## 15. Implementation Status

本文档和配套代码是 P1 元模型工程基线，不表示生产数据库、API、标准适配器或完整生命周期功能已经部署或验收。
