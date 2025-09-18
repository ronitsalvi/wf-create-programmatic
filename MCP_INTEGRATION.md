# MCP Integration Guide - Leegality Workflow Builder

## 🔗 Model Context Protocol (MCP) Setup

This guide covers the complete MCP server setup and integration with Claude Code for the Leegality Workflow Builder system.

## 📋 Overview

**MCP Architecture:**
```
Claude Code (Client) ←→ FastMCP Server ←→ Leegality APIs
```

**What MCP Provides:**
- Standardized tool interface for Claude Code
- Secure tool execution environment  
- Real-time API integration capabilities
- Structured data exchange

## 🛠️ MCP Server Implementation

### FastMCP Server Structure

**File**: `mcp_server.py`

```python
#!/usr/bin/env python3
from fastmcp import FastMCP
from leegality_workflow_api import LeegalityWorkflowAPI

# Initialize FastMCP server
mcp = FastMCP("Leegality Workflow Builder")

# 3 MCP Tools Implementation
@mcp.tool()
def create_workflow(workflow_json: dict, bearer_token: str) -> dict:
    """CREATE → UPDATE → APPROVE (full new workflow creation)"""

@mcp.tool() 
def update_and_approve(workflow_id: str, workflow_version: str, workflow_json: dict, bearer_token: str) -> dict:
    """UPDATE → APPROVE (edit existing workflow)"""

@mcp.tool()
def create_and_approve(workflow_json: dict, bearer_token: str) -> dict:
    """CREATE → APPROVE (skip update step)"""
```

### Tool Specifications

#### 1. create_workflow
**Purpose**: Complete workflow creation from scratch
**Flow**: CREATE → UPDATE → APPROVE
**Parameters**:
- `workflow_json: dict` - Complete workflow JSON with dynamicProperties and workflowData
- `bearer_token: str` - Leegality API authentication token

**Returns**:
```json
{
  "success": true,
  "workflow_id": "abc-123-def",
  "workflow_version": "0.1", 
  "status": "PUBLISHED",
  "processing_time": "2.3 seconds",
  "flow_completed": "CREATE → UPDATE → APPROVE"
}
```

#### 2. update_and_approve
**Purpose**: Update existing workflow and publish
**Flow**: UPDATE → APPROVE
**Parameters**:
- `workflow_id: str` - Existing workflow ID
- `workflow_version: str` - Workflow version to update
- `workflow_json: dict` - Updated workflow JSON
- `bearer_token: str` - Authentication token

**Returns**:
```json
{
  "success": true,
  "workflow_id": "abc-123-def",
  "workflow_version": "0.1",
  "status": "PUBLISHED", 
  "processing_time": "1.5 seconds",
  "flow_completed": "UPDATE → APPROVE"
}
```

#### 3. create_and_approve
**Purpose**: Express workflow creation (skip update)
**Flow**: CREATE → APPROVE
**Parameters**:
- `workflow_json: dict` - Workflow JSON (may use template defaults)
- `bearer_token: str` - Authentication token

**Returns**:
```json
{
  "success": true,
  "workflow_id": "abc-123-def",
  "workflow_version": "0.1",
  "status": "PUBLISHED",
  "processing_time": "1.1 seconds", 
  "flow_completed": "CREATE → APPROVE (express)",
  "note": "Update step was skipped - workflow uses template defaults"
}
```

### Error Handling

**Error Response Format**:
```json
{
  "success": false,
  "error": "Workflow creation failed: HTTP 401 - Unauthorized",
  "step_failed": "CREATE",
  "workflow_id": "abc-123-def",  // if available
  "processing_time": "0.5 seconds"
}
```

**Common Error Scenarios**:
- **Bearer Token Expired**: `HTTP 401 - Unauthorized`
- **Network Issues**: `Connection error - Unable to reach Leegality API`
- **Invalid JSON**: `Workflow update failed: Invalid JSON payload`
- **API Timeout**: `Request timeout - API took too long to respond`

## ⚙️ Claude Code Configuration

### Configuration File Setup

**File**: `~/.claude/settings.json`

**Required Configuration**:
```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "feedbackSurveyState": {
    "lastShownTime": 1758101937018
  },
  "mcpServers": {
    "leegality-workflow": {
      "command": "/opt/homebrew/bin/python3.11",
      "args": ["/Users/ronitsalvi/Documents/Ronit Work/Leegality/ai_play/Projects/workflow-create-prompt-2/mcp_server.py"],
      "env": {}
    }
  }
}
```

**Configuration Elements**:
- **Server Name**: `"leegality-workflow"` - Identifier for the MCP server
- **Command**: Full path to Python 3.11 executable
- **Args**: Full path to `mcp_server.py` file
- **Env**: Environment variables (empty for now)

### Path Configuration

**Critical Paths**:
- **Python Path**: `/opt/homebrew/bin/python3.11` (Homebrew Python 3.11)
- **Server Path**: `/Users/ronitsalvi/Documents/Ronit Work/Leegality/ai_play/Projects/workflow-create-prompt-2/mcp_server.py`
- **Working Directory**: Project root directory

**Path Verification**:
```bash
# Verify Python path
/opt/homebrew/bin/python3.11 --version
# Expected: Python 3.11.13

# Verify server file exists
ls -la "/Users/ronitsalvi/Documents/Ronit Work/Leegality/ai_play/Projects/workflow-create-prompt-2/mcp_server.py"
```

## 🚀 Server Startup & Testing

### Manual Server Testing

**Start Server**:
```bash
cd "/Users/ronitsalvi/Documents/Ronit Work/Leegality/ai_play/Projects/workflow-create-prompt-2"
/opt/homebrew/bin/python3.11 mcp_server.py
```

**Expected Output**:
```
╭────────────────────────────────────────────────────────────────────────────╮
│                                FastMCP  2.0                                │
│               🖥️  Server name:     Leegality Workflow Builder               │
│               📦 Transport:       STDIO                                    │
│               🏎️  FastMCP version: 2.12.3                                   │
│               🤝 MCP SDK version: 1.14.0                                   │
╰────────────────────────────────────────────────────────────────────────────╯

🚀 Starting Leegality Workflow Builder MCP Server...
📋 Available tools:
  1. create_workflow - CREATE → UPDATE → APPROVE (full workflow)
  2. update_and_approve - UPDATE → APPROVE (edit existing)
  3. create_and_approve - CREATE → APPROVE (express, skip update)

🔗 Server running - Ready for MCP client connections!
```

### Server Health Check

**Python Import Test**:
```bash
/opt/homebrew/bin/python3.11 -c "
import sys
sys.path.insert(0, '.')
from mcp_server import mcp
print('🎉 MCP Server loaded successfully!')
print('✅ Server structure is valid!')
"
```

**Dependencies Check**:
```bash
/opt/homebrew/bin/python3.11 -c "
import fastmcp
import mcp
print(f'FastMCP version: {fastmcp.__version__}')
print('✅ All dependencies available!')
"
```

## 🔄 Claude Code Integration

### Restart Procedure

1. **Save Configuration**: Ensure `~/.claude/settings.json` contains MCP server config
2. **Close Claude Code**: Completely close all Claude Code windows
3. **Restart Claude Code**: Open new Claude Code session
4. **Verify Connection**: MCP server should start automatically

### Tool Verification

**In New Claude Code Session**:
```python
# Test tool availability
# These tools should be available after restart:
create_workflow(workflow_json={...}, bearer_token="...")
update_and_approve(workflow_id="...", workflow_version="...", workflow_json={...}, bearer_token="...")
create_and_approve(workflow_json={...}, bearer_token="...")
```

**Expected Behavior**:
- Tools appear in Claude Code's available tools list
- Tools can be called with proper parameters
- Real API calls are made to Leegality platform

## 📊 Performance & Monitoring

### Server Performance

**Typical Processing Times**:
- **create_workflow**: 2-3 seconds (3 API calls)
- **update_and_approve**: 1-2 seconds (2 API calls)  
- **create_and_approve**: 1-1.5 seconds (2 API calls)

**Performance Factors**:
- Network latency to Leegality APIs
- JSON payload size  
- Bearer token validation time
- API server load

### Logging & Debugging

**Server Logs** (visible in terminal):
```
🚀 Starting full workflow creation (CREATE → UPDATE → APPROVE)
📋 Step 1: Creating workflow...
✅ Workflow created: abc-123-def (v0.1)
🔧 Step 2: Updating workflow with JSON data...
✅ Workflow updated successfully
🎉 Step 3: Approving workflow...
✅ Workflow approved and published
🎊 SUCCESS! Workflow abc-123-def created and published in 2.3s
```

**Error Logs**:
```
❌ ERROR: Workflow creation failed: HTTP 401 - Unauthorized
❌ ERROR: Connection error - Unable to reach Leegality API
```

## 🔧 Advanced Configuration

### Environment Variables

**Optional Environment Configuration**:
```json
{
  "mcpServers": {
    "leegality-workflow": {
      "command": "/opt/homebrew/bin/python3.11",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "LEEGALITY_BASE_URL": "https://preprod-gateway.leegality.com",
        "LOG_LEVEL": "INFO",
        "TIMEOUT_SECONDS": "30"
      }
    }
  }
}
```

### Custom Server Options

**Server Customization** (in `mcp_server.py`):
```python
# Custom server configuration
mcp = FastMCP(
    "Leegality Workflow Builder",
    # Additional FastMCP options can be added here
)

# Custom middleware, routes, etc. can be added
```

## 🛡️ Security Considerations

### Authentication Handling
- **Bearer tokens** are passed through MCP tools, not stored
- **Token expiration** (15 minutes) handled gracefully with clear error messages
- **No credential storage** in MCP server or configuration files

### Network Security
- **HTTPS only** for Leegality API calls
- **Timeout settings** prevent hanging connections  
- **Error isolation** prevents sensitive data leakage

### Configuration Security
- **Local configuration** only (no remote config)
- **Path validation** for server file location
- **Environment isolation** between MCP servers

## 🚨 Troubleshooting

### Common MCP Issues

#### 1. MCP Tools Not Available
**Symptoms**: `No such tool available: create_workflow`
**Causes**:
- Claude Code not restarted after configuration
- Invalid MCP server configuration  
- Python path incorrect
- Server file missing or not executable

**Solutions**:
1. Restart Claude Code completely
2. Verify `~/.claude/settings.json` configuration
3. Test server manually with command line
4. Check Python and file paths

#### 2. Server Startup Fails
**Symptoms**: MCP server doesn't start or crashes immediately
**Causes**:
- Python version incompatible (need 3.10+)
- Missing dependencies (FastMCP not installed)
- Import errors (missing `leegality_workflow_api.py`)
- Path issues

**Solutions**:
1. Verify Python version: `/opt/homebrew/bin/python3.11 --version`
2. Reinstall FastMCP: `python3.11 -m pip install fastmcp`
3. Check file paths and permissions
4. Test imports manually

#### 3. API Connection Issues
**Symptoms**: `Connection error - Unable to reach Leegality API`
**Causes**:
- Network connectivity issues
- Leegality API server down
- Incorrect API endpoints
- Firewall blocking requests

**Solutions**:
1. Test network connectivity
2. Verify Leegality API status
3. Check bearer token validity
4. Test direct API calls

### Performance Issues

#### 1. Slow Tool Execution
**Symptoms**: Tools take >5 seconds to complete
**Causes**:
- Network latency
- Large JSON payloads
- API server load
- Token validation delays

**Solutions**:
1. Optimize JSON payload size
2. Use faster network connection
3. Check Leegality API status
4. Consider request timeout adjustments

#### 2. Memory Usage
**Symptoms**: High memory usage during operation
**Causes**:
- Large JSON payloads in memory
- Multiple concurrent requests
- Memory leaks in dependencies

**Solutions**:
1. Monitor memory usage patterns
2. Optimize JSON payload structure  
3. Restart server periodically if needed
4. Update dependencies

## ✅ Validation Checklist

### Pre-Deployment Checklist
- [ ] Python 3.11 installed and accessible
- [ ] FastMCP installed with all dependencies
- [ ] MCP server starts without errors
- [ ] All 3 tools load correctly
- [ ] Claude Code configuration updated
- [ ] Server responds to test calls
- [ ] Error handling works properly
- [ ] Performance meets requirements

### Post-Restart Checklist
- [ ] Claude Code shows MCP tools available
- [ ] Tools can be called with parameters
- [ ] Real API connections work
- [ ] Bearer token authentication succeeds
- [ ] Workflow creation completes successfully
- [ ] Error responses are clear and helpful

**The MCP integration provides a robust, scalable interface for workflow creation through Claude Code with comprehensive error handling and monitoring capabilities.**