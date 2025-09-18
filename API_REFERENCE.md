# API Reference - Leegality Workflow Builder

## 📚 Technical Reference Documentation

Complete API reference for the Leegality Workflow Builder system, including MCP tools, API methods, and data structures with enhanced NLP parsing capabilities.

## 🛠️ MCP Tools Reference

### create_workflow

**Signature:**
```python
def create_workflow(workflow_json: dict, bearer_token: str) -> dict
```

**Description:** Complete workflow creation from scratch using the full 3-step API flow.

**Flow:** CREATE → UPDATE → APPROVE

**Parameters:**
- `workflow_json` (dict): Complete workflow JSON with dynamicProperties and workflowData
- `bearer_token` (str): Bearer token for Leegality API authentication

**Returns:**
```python
{
    "success": bool,              # True if all steps completed successfully
    "workflow_id": str,           # Generated workflow ID (UUID format)
    "workflow_version": str,      # Workflow version (usually "0.1")
    "status": str,                # "PUBLISHED" on success
    "processing_time": str,       # "X.X seconds"
    "flow_completed": str         # "CREATE → UPDATE → APPROVE"
}
```

**Error Response:**
```python
{
    "success": False,
    "error": str,                 # Detailed error message
    "step_failed": str,           # "CREATE", "UPDATE", or "APPROVE"
    "workflow_id": str,           # If available (partial success)
    "workflow_version": str,      # If available
    "processing_time": str        # Time elapsed before failure
}
```

**Example Usage:**
```python
result = create_workflow(
    workflow_json={
        "dynamicProperties": {...},
        "workflowData": {...}
    },
    bearer_token="eyJ4NXQjUzI1NiI6Im..."
)
```

### update_and_approve

**Signature:**
```python
def update_and_approve(workflow_id: str, workflow_version: str, workflow_json: dict, bearer_token: str) -> dict
```

**Description:** Update existing workflow and publish it.

**Flow:** UPDATE → APPROVE

**Parameters:**
- `workflow_id` (str): Existing workflow ID
- `workflow_version` (str): Workflow version to update (e.g., "0.1")
- `workflow_json` (dict): Updated workflow JSON data
- `bearer_token` (str): Bearer token for authentication

**Returns:** Same structure as `create_workflow` with `flow_completed`: "UPDATE → APPROVE"

**Example Usage:**
```python
result = update_and_approve(
    workflow_id="abc-123-def-456",
    workflow_version="0.1",
    workflow_json={...},
    bearer_token="eyJ4NXQjUzI1NiI6Im..."
)
```

### create_and_approve

**Signature:**
```python
def create_and_approve(workflow_json: dict, bearer_token: str) -> dict
```

**Description:** Express workflow creation that skips the update step.

**Flow:** CREATE → APPROVE (skip UPDATE)

**Parameters:**
- `workflow_json` (dict): Workflow JSON (may use template defaults)
- `bearer_token` (str): Bearer token for authentication

**Returns:** Same structure as `create_workflow` with additional note field:
```python
{
    # ... standard fields ...
    "flow_completed": "CREATE → APPROVE (express)",
    "note": "Update step was skipped - workflow uses template defaults"
}
```

**Example Usage:**
```python
result = create_and_approve(
    workflow_json={...},
    bearer_token="eyJ4NXQjUzI1NiI6Im..."
)
```

## 🔌 Leegality API Methods

### LeegalityWorkflowAPI Class

**Constructor:**
```python
def __init__(self, bearer_token: str)
```

**Properties:**
```python
self.bearer_token: str           # Authentication token
self.base_url: str              # "https://preprod-gateway.leegality.com"
self.headers: dict              # Authorization and content-type headers
self.template_id: str           # "f214c92a-8f67-489a-a4c6-2ef5ae0472c4"
self.template_version: str      # "0.1"
```

### Core API Methods

#### _step1_create_workflow()

**Purpose:** Creates a draft workflow in Leegality system.

**HTTP Request:**
```
POST /workflow-manager/v1/workflow
Content-Type: application/json
Authorization: Bearer {token}

{
    "name": "NLP_Workflow_{timestamp}",
    "workflowTemplateId": "f214c92a-8f67-489a-a4c6-2ef5ae0472c4",
    "workflowTemplateVersion": "0.1",
    "versionDescription": "Created via NLP Python Interface"
}
```

**Returns:**
```python
{
    "success": bool,
    "workflow_id": str,      # UUID of created workflow
    "version": str,          # Version number (usually "0.1")  
    "name": str             # Generated workflow name
}
```

**Error Cases:**
- HTTP 401: Bearer token invalid/expired
- HTTP 400: Invalid template ID or version
- Network timeout: Connection issues
- JSON parse error: Invalid response format

#### _step2_update_workflow(workflow_id, version, payload)

**Purpose:** Updates workflow with complete JSON data.

**Parameters:**
- `workflow_id` (str): UUID of workflow to update
- `version` (str): Workflow version
- `payload` (dict): Complete workflow JSON with dynamicProperties and workflowData

**HTTP Request:**
```
PUT /workflow-manager/v1/workflow/{workflow_id}/{version}
Content-Type: application/json
Authorization: Bearer {token}

{payload}  # Complete workflow JSON
```

**Returns:**
```python
{
    "success": bool
}
```

**Error Cases:**
- HTTP 404: Workflow not found
- HTTP 400: Invalid JSON payload
- HTTP 401: Authentication failure
- HTTP 422: Validation errors in payload

#### _step3_approve_workflow(workflow_id, version)

**Purpose:** Approves and publishes the workflow.

**Parameters:**
- `workflow_id` (str): UUID of workflow to approve
- `version` (str): Workflow version

**HTTP Request:**
```
PATCH /workflow-manager/v1/workflow/approve
Content-Type: application/json
Authorization: Bearer {token}

{
    "workflowId": "{workflow_id}",
    "version": "{version}"
}
```

**Returns:**
```python
{
    "success": bool
}
```

**Error Cases:**
- HTTP 404: Workflow not found
- HTTP 400: Already approved or invalid state
- HTTP 401: Authentication failure

## 📄 Data Structures

### Workflow JSON Structure

#### Complete Workflow JSON
```json
{
    "dynamicProperties": {
        "uploadDocumentEnabled#p": {
            "v": false,      // value
            "m": false,      // mandatory
            "e": false       // editable
        },
        "allowEdit#p": {"v": true, "m": false, "e": false},
        "documentName1#p": {"v": "Document A", "m": false, "e": false},
        "documentName2#p": {"v": "Document B", "m": false, "e": false}
    },
    "workflowData": {
        "documents": [...],
        "invitees": [...],
        "workflow": {...}
    }
}
```

#### Document Structure
```json
{
    "id": "7de55cac-812f-471a-b99f-6faaa0e386d0",  // Pre-defined UUID
    "name": "Document A",                           // Document name
    "required": true,                               // Is required for signing
    "uploadEnabled": false                          // Can users upload this doc
}
```

#### Invitee Structure
```json
{
    "id": "inv-001",                                // Unique invitee ID
    "name": "John Doe",                            // Full name
    "email": "john@example.com",                   // Email address (optional)
    "signType": "aadhaar",                         // eSign type: aadhaar, dsc, virtual, multiple
    "documentAssignments": [                       // Documents this invitee signs
        "/documents/7de55cac-812f-471a-b99f-6faaa0e386d0"
    ]
}
```

### Pre-defined UUID Mapping

**Document UUIDs (UUID v4 Compliant):**
```python
DOCUMENT_UUIDS = {
    1: "7de55cac-812f-471a-b99f-6faaa0e386d0",
    2: "8ef66dbd-923f-4582-b00f-7fbbb1f497e1",
    3: "9f077ece-034f-493c-8d1e-8eccc2e508f2",
    4: "0ae88fdf-145f-404d-9e2d-9dddd3d619f3",
    5: "1bf99aea-256f-415e-af3e-0eeee4e720f4"
}

# UUID v4 Validation Regex:
# /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$/
# Position 13: Must be "4" (version bit)
# Position 17: Must be "8", "9", "a", or "b" (variant bits)
```

**Enhanced NLP Parsing Examples:**
- "2 documents A and B" → Document A gets UUID #1, Document B gets UUID #2
- "3 invitees: John, Mary, Bob" → 3 separate invitee objects created
- "John (aadhaar), Mary (DSC)" → Individual eSign type assignments
- Document assignments: `"/documents/{uuid}"`

**Entity Separation Validation:**
- Documents and invitees parsed as separate entities
- No overlap between document names and invitee names  
- Count validation: "3 invitees" creates exactly 3 objects
- Individual eSign parsing prevents assignment errors

### eSign Types

**Available Options:**
- `"aadhaar"` - Aadhaar-based eSign
- `"dsc"` - Digital Signature Certificate
- `"virtual"` - Virtual signing (OTP-based)
- `"multiple"` - Multiple signing options available

### Dynamic Properties Reference

**Common Dynamic Properties:**
```json
{
    "uploadDocumentEnabled#p": {"v": false, "m": false, "e": false},
    "allowEdit#p": {"v": true, "m": false, "e": false},
    "documentName1#p": {"v": "Document Name", "m": false, "e": false},
    "inviteeName1#p": {"v": "Invitee Name", "m": false, "e": false}
}
```

**Property Naming Convention:**
- `{property}#p` - Property definition
- `.v` - Value
- `.m` - Mandatory flag
- `.e` - Editable flag

## 🔧 Configuration Reference

### MCP Server Configuration

**Claude Code Settings** (`~/.claude/settings.json`):
```json
{
    "mcpServers": {
        "leegality-workflow": {
            "command": "/opt/homebrew/bin/python3.11",
            "args": ["/full/path/to/mcp_server.py"],
            "env": {}
        }
    }
}
```

### Environment Variables

**Optional Environment Configuration:**
```bash
export LEEGALITY_BASE_URL="https://preprod-gateway.leegality.com"
export LOG_LEVEL="INFO"
export TIMEOUT_SECONDS="30"
```

### API Configuration

**LeegalityWorkflowAPI Configuration:**
```python
# Base configuration (hardcoded in class)
BASE_URL = "https://preprod-gateway.leegality.com"
TEMPLATE_ID = "f214c92a-8f67-489a-a4c6-2ef5ae0472c4"
TEMPLATE_VERSION = "0.1"
TIMEOUT = 30  # seconds

# Headers format
HEADERS = {
    "Authorization": f"Bearer {bearer_token}",
    "Content-Type": "application/json", 
    "Accept": "application/json"
}
```

## ❌ Error Reference

### HTTP Error Codes

**401 Unauthorized:**
```python
{
    "success": False,
    "error": "Workflow creation failed: HTTP 401 - Unauthorized",
    "step_failed": "CREATE"
}
```
**Cause:** Bearer token invalid, expired, or missing.

**400 Bad Request:**
```python
{
    "success": False,
    "error": "Workflow update failed: HTTP 400 - Invalid JSON payload",
    "step_failed": "UPDATE"
}
```
**Cause:** Invalid JSON structure or missing required fields.

**404 Not Found:**
```python
{
    "success": False,
    "error": "Workflow approval failed: HTTP 404 - Workflow not found", 
    "step_failed": "APPROVE"
}
```
**Cause:** Workflow ID doesn't exist or version mismatch.

### Network Error Codes

**Connection Timeout:**
```python
{
    "success": False,
    "error": "Request timeout - API took too long to respond",
    "step_failed": "CREATE"
}
```

**Connection Error:**
```python
{
    "success": False,
    "error": "Connection error - Unable to reach Leegality API",
    "step_failed": "UPDATE"
}
```

### Validation Errors

**JSON Schema Validation:**
```python
{
    "success": False,
    "error": "Validation failed: Missing required field 'documents'",
    "step_failed": "UPDATE"
}
```

**Email Validation:**
```python
{
    "success": False,
    "error": "Invalid email format: 'invalid-email'",
    "step_failed": "UPDATE"
}
```

## 🧪 Testing Reference

### Test JSON Examples

#### Minimal Test Case
```json
{
    "dynamicProperties": {
        "uploadDocumentEnabled#p": {"v": false, "m": false, "e": false}
    },
    "workflowData": {
        "documents": [
            {"id": "7de55cac-812f-471a-b99f-6faaa0e386d0", "name": "Test Doc"}
        ],
        "invitees": [
            {"name": "Test User", "signType": "aadhaar"}
        ]
    }
}
```

#### Core Bug Test Case
```json
{
    "dynamicProperties": {
        "documentName1#p": {"v": "Document A", "m": false, "e": false},
        "documentName2#p": {"v": "Document B", "m": false, "e": false}
    },
    "workflowData": {
        "documents": [
            {"id": "7de55cac-812f-471a-b99f-6faaa0e386d0", "name": "Document A"},
            {"id": "8ef66dbd-923g-582b-c00g-7gbbb1f497e1", "name": "Document B"}
        ],
        "invitees": [
            {"name": "John Doe", "signType": "aadhaar"},
            {"name": "Jane Smith", "signType": "dsc"}
        ]
    }
}
```

### Performance Benchmarks

**Expected Processing Times:**
- **create_workflow**: 2-3 seconds (3 API calls)
- **update_and_approve**: 1-2 seconds (2 API calls)
- **create_and_approve**: 1-1.5 seconds (2 API calls)

**Performance Factors:**
- Network latency: +0.5-1.0 seconds
- JSON size: +0.1-0.3 seconds per 100KB
- API load: +0.2-0.5 seconds during peak

## 🔍 Debugging Reference

### Server Debug Commands

**Test MCP Server Loading:**
```bash
/opt/homebrew/bin/python3.11 -c "
import sys
sys.path.insert(0, '.')
from mcp_server import mcp
print('✅ MCP Server loaded successfully!')
"
```

**Test API Class Import:**
```bash
/opt/homebrew/bin/python3.11 -c "
from leegality_workflow_api import LeegalityWorkflowAPI
print('✅ API class imported successfully!')
"
```

**Test Dependencies:**
```bash
/opt/homebrew/bin/python3.11 -c "
import fastmcp, mcp, requests, json
print('✅ All dependencies available!')
"
```

### Log Analysis

**Success Pattern:**
```
🚀 Starting full workflow creation (CREATE → UPDATE → APPROVE)
📋 Step 1: Creating workflow...
✅ Workflow created: {id} (v{version})
🔧 Step 2: Updating workflow with JSON data...
✅ Workflow updated successfully
🎉 Step 3: Approving workflow...
✅ Workflow approved and published
🎊 SUCCESS! Workflow {id} created and published in {time}s
```

**Error Pattern:**
```
🚀 Starting full workflow creation (CREATE → UPDATE → APPROVE)
📋 Step 1: Creating workflow...
❌ ERROR: Workflow creation failed: {error_details}
```

**The API reference provides complete technical documentation for integrating with the Leegality Workflow Builder system through MCP tools and direct API access.**