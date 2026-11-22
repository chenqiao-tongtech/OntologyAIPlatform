# ADR-0002: 建立统一内部语义模型与标准格式适配层

- Status: Accepted for MVP design
- Date: 2026-11-21
- Decision Owners: P1 Architecture
- Scope: Ontology Semantic Core

## 1. Context

P1 需要管理不同来源、不同表达形式的本体资产。

外部来源可能使用 RDF、OWL、SHACL、SKOS、JSON Schema 或专有结构。

如果核心业务模块直接依赖某一种外部文件格式，将造成数据模型和业务逻辑耦合，影响后续扩展。

同时，标准之间存在表达能力差异，不能默认格式转换始终无损。

## 2. Decision

建立平台内部统一的 Ontology Intermediate Representation（OIR），并通过标准适配器实现外部格式交换。

OIR 至少包括：

- Ontology
- Namespace
- Class
- Property
- Relation
- Constraint
- Term
- External Mapping
- Annotation
- Provenance Reference

每个对象具有稳定 ID、项目归属、版本和必要的元数据。

RDF、OWL、SHACL 和 JSON Schema 通过各自适配器参与数据交换和验证。

## 3. Source of Truth

平台正式语义资产以经过审核并持久化的内部语义模型为统一管理入口。

标准文件是可导入、导出的语义资产载体，导入时必须转换到 OIR，并记录转换报告。

导出时从指定版本的 OIR 生成目标文件。

不得让多个互相独立的表示副本同时成为同一语义对象的权威来源。

## 4. Validation Responsibilities

| Component | Responsibility |
|---|---|
| Pydantic | API payload validation |
| JSON Schema | Data structure validation |
| OIR validation | Platform semantic and reference validation |
| RDFLib | RDF parsing, transformation and serialization |
| pySHACL | SHACL constraint validation |
| OWL tools | Optional ontology reasoning and consistency checks |

OWL 逻辑推理和 SHACL 约束验证是不同的验证维度，不能将二者合并为同一种检查结果。

## 5. Alternatives

### Directly Use OWL as Internal Database Model

优点：
- 与标准生态保持紧密联系；
- 具有明确的形式化语义。

缺点：
- 平台业务对象、审核状态、版本和发布元数据需要额外表达；
- 前后端交互和业务验证较复杂；
- 不同格式导入时仍需处理语义差异。

### Directly Use JSON as the Only Ontology Model

优点：
- 前后端开发简单；
- 适合业务对象和 API 交互。

缺点：
- 容易弱化 RDF/OWL 的形式化语义；
- 需要额外设计稳定的标准映射；
- 不应将 JSON 数据结构校验等同于本体语义验证。

### Internal Semantic Model + Standards Adapters

优点：
- 统一管理平台业务对象；
- 允许多种标准格式交换；
- 可以独立演进内部模型和外部适配器；
- 可以为转换损失提供报告。

缺点：
- 需要维护映射规则；
- 需要建立较完整的互操作性测试集。

## 6. Interoperability Requirements

每个适配器必须定义：

- 支持的标准和版本；
- 支持的构造；
- 不支持的构造；
- 转换警告；
- 语义信息损失报告；
- 导入导出测试样例。

至少应覆盖：

- RDF/XML
- Turtle
- JSON-LD
- OWL 2
- SHACL

## 7. Validation

- [ ] OIR 对象具有稳定 ID。
- [ ] 类、属性和关系的引用完整。
- [ ] 标准导入产生结构化转换结果。
- [ ] 标准导出具有可复现性。
- [ ] 对不支持结构提供明确错误或警告。
- [ ] OWL、SHACL 和 JSON Schema 分别执行各自职责范围内的验证。
- [ ] 版本快照可重新生成对应的导出制品。

## 8. Status

Accepted for the MVP architecture design. Supported format coverage will be expanded incrementally based on interoperability tests.
