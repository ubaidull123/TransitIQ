# TransitIQ — V3 Instructions

## V3 Goal

TransitIQ V3 should evolve from a one-shot shipment exception analyzer into a **persistent logistics exception management system**.

The system should not only analyze a shipment issue once. It should maintain the case over time, preserve previous analyses, convert AI recommendations into trackable operational actions, accept new information later, re-analyze the case when context changes, and allow external AI clients such as Claude to interact with TransitIQ through MCP.

---

# 1. Persistent Cases

## Objective

Every shipment exception should exist as a persistent case in the database instead of being treated as a temporary request.

A case represents one ongoing shipment problem.

Example:

```text
Case ID: 42
Shipment ID: SHP-1004
Origin: Karachi
Destination: Dubai
Carrier: ABC Logistics
Status: action_required
Created At: ...
```

## Case Lifecycle

Use a simple lifecycle:

```text
NEW
 ↓
ANALYZED
 ↓
ACTION_REQUIRED
 ↓
IN_PROGRESS
 ↓
RESOLVED
 ↓
CLOSED
```

Suggested statuses:

```python
new
analyzed
action_required
in_progress
resolved
closed
```

## Database Table

Create or extend the main exception table:

```text
exceptions

id
shipment_id
origin
destination
carrier
issue_description
status
created_at
updated_at
```

## API Endpoints

```http
POST /exceptions
GET /exceptions
GET /exceptions/{id}
PATCH /exceptions/{id}
PATCH /exceptions/{id}/status
```

## Requirements

* Every exception must have a unique internal ID.
* Every exception must have a status.
* Cases must remain available after server restart.
* Updating a case should update `updated_at`.
* Analysis should not delete or replace the original issue description.

---

# 2. Saved Analysis History

## Objective

Do not overwrite previous AI analyses.

Each time TransitIQ analyzes or re-analyzes a case, create a new analysis record.

Example:

```text
Exception #42
│
├── Analysis #1
├── Analysis #2
└── Analysis #3
```

This allows the system to show how the case changed over time.

## Database Table

```text
analysis_runs

id
exception_id
exception_type
severity
missing_information
recommended_actions
model_name
created_at
```

Optional fields:

```text
reason_for_reanalysis
prompt_version
```

## Relationship

```text
exceptions
    │
    │ 1
    │
    │ *
    ▼
analysis_runs
```

One exception may have many analysis records.

## API Endpoints

```http
POST /exceptions/{id}/analyze
GET /exceptions/{id}/analyses
GET /analyses/{analysis_id}
```

## Behavior

When:

```http
POST /exceptions/42/analyze
```

is called:

```text
Load case
 ↓
Load latest context
 ↓
Run TransitIQ agent
 ↓
Create NEW analysis record
 ↓
Do not overwrite old analysis
 ↓
Return latest analysis
```

## Requirements

* Every analysis must be linked to one exception.
* Old analyses must remain unchanged.
* The latest analysis should be identifiable.
* Re-analysis should always create a new analysis record.

---

# 3. Action Tracking

## Objective

Recommended actions should become actual trackable operational tasks instead of remaining plain text.

Instead of:

```json
{
  "recommended_actions": [
    "Contact carrier",
    "Verify invoice",
    "Send corrected document"
  ]
}
```

TransitIQ should create:

```text
#101 Contact carrier             pending
#102 Verify invoice              pending
#103 Send corrected document     pending
```

## Database Table

```text
actions

id
exception_id
analysis_id
description
status
created_at
updated_at
completed_at
```

Suggested statuses:

```text
pending
in_progress
completed
cancelled
```

## Relationship

```text
Exception
   │
   ├── Analysis
   │
   └── Actions
```

Optionally connect each action to the analysis that created it.

## API Endpoints

```http
GET /exceptions/{id}/actions
POST /exceptions/{id}/actions

PATCH /actions/{action_id}
PATCH /actions/{action_id}/status
DELETE /actions/{action_id}
```

## Agent Integration

After analysis:

```text
Agent returns recommended actions
        ↓
FastAPI / service layer
        ↓
Create action records
        ↓
Return analysis + actions
```

Example response:

```json
{
  "exception_type": "missing_document",
  "severity": "high",
  "actions": [
    {
      "id": 101,
      "description": "Verify commercial invoice",
      "status": "pending"
    },
    {
      "id": 102,
      "description": "Contact customs broker",
      "status": "pending"
    }
  ]
}
```

## Requirements

* Actions must be stored separately from analysis text.
* Actions must have their own status.
* Users must be able to update action status manually.
* Completing an action should not modify previous analysis records.

---

# 4. Additional Context + Re-analysis

## Objective

A shipment case evolves over time.

TransitIQ should allow new information to be attached to an existing case and use that information during future analysis.

Example initial issue:

```text
Shipment held at customs because a document is missing.
```

Initial analysis:

```text
Missing information:
- Which document?
- Customs reference?
```

Later information:

```text
The missing document is the Commercial Invoice.
Customs reference is DXB-93222.
```

TransitIQ should add this information to the existing case.

## Database Table

Create:

```text
case_context

id
exception_id
content
source
created_at
```

Suggested `source` values:

```text
user
operations_staff
carrier
customer
mcp
system
```

Example:

```text
id: 8
exception_id: 42
content: Missing document is the Commercial Invoice.
source: user
```

## API Endpoint

```http
POST /exceptions/{id}/context
GET /exceptions/{id}/context
```

Request:

```json
{
  "content": "Customs reference is DXB-93222 and the missing document is the commercial invoice.",
  "source": "operations_staff"
}
```

## Re-analysis Flow

```text
Original exception
       +
Previous context
       +
New context
       ↓
TransitIQ Agent
       ↓
New analysis
       ↓
New actions if required
```

Re-analysis should call:

```http
POST /exceptions/{id}/analyze
```

again.

## Important Rule

Do not rewrite old context.

Store context as separate chronological entries:

```text
Case #42

Context #1
Shipment held at customs.

Context #2
Commercial invoice missing.

Context #3
Customs reference received.

Context #4
Corrected invoice submitted.
```

## Requirements

* Context must persist.
* Context should remain chronological.
* The agent should receive relevant existing context during re-analysis.
* Every re-analysis should create a new analysis record.
* Previous analyses must remain available.

---

# 5. MCP Access

## Objective

Allow external AI clients such as Claude to interact with TransitIQ without manually using the web interface.

MCP should act as an additional interface to the same TransitIQ business logic.

Architecture:

```text
Web App
   ↓
FastAPI
   │
   └──────────────┐
                  ↓
           Service Layer
                  ↑
   ┌──────────────┘
   │
MCP Server
   ↑
Claude / Other AI Client
```

Do not duplicate application logic inside the MCP server.

Both FastAPI and MCP should call the same internal services.

---

## Shared Service Layer

Create services such as:

```python
ExceptionService
AnalysisService
ActionService
ContextService
```

Example:

```python
class ExceptionService:

    async def create_exception(self, data):
        ...

    async def get_exception(self, exception_id):
        ...

    async def analyze_exception(self, exception_id):
        ...

    async def add_context(self, exception_id, content):
        ...
```

FastAPI uses:

```python
await exception_service.analyze_exception(id)
```

MCP uses:

```python
await exception_service.analyze_exception(id)
```

Same logic.

---

## Recommended MCP Tools

Expose simple tools.

### Create Exception

```text
create_exception
```

Inputs:

```text
shipment_id
origin
destination
carrier
issue_description
```

---

### Get Exception

```text
get_exception
```

Input:

```text
exception_id
```

---

### List Exceptions

```text
list_exceptions
```

Optional filters:

```text
status
severity
carrier
```

---

### Analyze Exception

```text
analyze_exception
```

Input:

```text
exception_id
```

Behavior:

```text
Load case
 ↓
Run TransitIQ agent
 ↓
Store analysis
 ↓
Create actions
 ↓
Return result
```

---

### Add Context

```text
add_exception_context
```

Inputs:

```text
exception_id
content
source
```

---

### Get Analysis History

```text
get_analysis_history
```

Input:

```text
exception_id
```

---

### Get Actions

```text
get_actions
```

Input:

```text
exception_id
```

---

### Update Action

```text
update_action_status
```

Inputs:

```text
action_id
status
```

---

## Example Claude Workflow

User tells Claude:

```text
Shipment SHP-2001 from Karachi to Dubai is stuck at customs
because the commercial invoice is missing.
Add it to TransitIQ and analyze it.
```

Claude calls:

```text
create_exception(...)
```

TransitIQ returns:

```text
Exception ID: 72
```

Claude then calls:

```text
analyze_exception(72)
```

TransitIQ returns:

```text
Exception Type:
missing_document

Severity:
high

Missing Information:
customs reference

Recommended Actions:
1. Verify commercial invoice
2. Contact customs broker
3. Submit corrected invoice
```

Later:

```text
Customs reference is DXB-92912.
Add that information to the case.
```

Claude calls:

```text
add_exception_context(
    exception_id=72,
    content="Customs reference is DXB-92912."
)
```

Then optionally:

```text
analyze_exception(72)
```

again.

---

# V3 Database Overview

By the end of V3, the core database should look approximately like:

```text
exceptions
│
├── id
├── shipment_id
├── issue_description
├── status
└── timestamps


analysis_runs
│
├── id
├── exception_id
├── exception_type
├── severity
├── missing_information
├── recommended_actions
└── created_at


actions
│
├── id
├── exception_id
├── analysis_id
├── description
├── status
└── timestamps


case_context
│
├── id
├── exception_id
├── content
├── source
└── created_at
```

Relationships:

```text
Exception
   │
   ├── Analysis Run #1
   ├── Analysis Run #2
   ├── Analysis Run #3
   │
   ├── Action #1
   ├── Action #2
   │
   ├── Context #1
   ├── Context #2
   └── Context #3
```

---

# V3 Recommended Development Order

## Step 1

Implement persistent case status.

```text
new
analyzed
action_required
in_progress
resolved
closed
```

---

## Step 2

Change analysis storage from:

```text
one analysis per exception
```

to:

```text
many analysis runs per exception
```

---

## Step 3

Convert AI recommendations into `actions` database records.

Add:

```text
pending
in_progress
completed
cancelled
```

---

## Step 4

Add `case_context`.

Allow additional information to be attached to an existing case.

---

## Step 5

Update the TransitIQ agent so its input includes:

```text
original exception
+
latest context
+
previous relevant analysis
```

---

## Step 6

Implement re-analysis.

Verify:

```text
Analysis #1
 ↓
new context
 ↓
Analysis #2
```

without deleting Analysis #1.

---

## Step 7

Create a shared service layer.

Move business logic out of FastAPI route handlers.

Example:

```text
API router
    ↓
ExceptionService
    ↓
Database / Agent
```

---

## Step 8

Add the MCP server.

Initially expose only:

```text
create_exception
get_exception
analyze_exception
add_exception_context
get_actions
update_action_status
```

Add more tools later only when needed.

---

# V3 Non-Goals

Do not add these yet:

```text
Carrier APIs
Live shipment tracking
Document parsing
OCR
Invoice extraction
Bill of lading parsing
Email monitoring
Slack notifications
Automatic external escalation
RAG
Vector database
Multi-agent architecture
Kafka
Celery
Kubernetes
Automatic carrier communication
```

These belong in later versions.

---

# V3 Completion Criteria

TransitIQ V3 is complete when this entire workflow works:

```text
1. Create shipment exception

2. Store it as a persistent case

3. Run TransitIQ analysis

4. Save Analysis #1

5. Convert recommendations into actions

6. Update action statuses

7. Add new information to the case

8. Re-run analysis

9. Save Analysis #2 without deleting Analysis #1

10. Retrieve full case history

11. Connect Claude through MCP

12. Create/read/analyze/update TransitIQ cases through MCP
```

The final architecture should support:

```text
             Web App
                │
              FastAPI
                │
                ▼
         ┌───────────────┐
         │ Service Layer │
         └───────┬───────┘
                 │
      ┌──────────┼──────────┐
      ↓          ↓          ↓
  Database    Agent      Actions
      ↑
      │
 MCP Server
      ↑
 Claude
```

## V3 Core Principle

TransitIQ V3 should no longer behave like:

```text
Input → AI → Output
```

It should behave like:

```text
Create Case
    ↓
Analyze
    ↓
Store History
    ↓
Create Actions
    ↓
Receive New Information
    ↓
Re-analyze
    ↓
Track Resolution
```

That is the main architectural upgrade for V3.
