#!/usr/bin/env python3
"""
FastMCP Server for Leegality Workflow Builder
Provides 4 MCP tools for workflow creation using existing LeegalityWorkflowAPI
"""

from fastmcp import FastMCP
from leegality_workflow_api import LeegalityWorkflowAPI
import json
import time
from typing import Dict, List, Any, Optional

# Initialize FastMCP server
mcp = FastMCP("Leegality Workflow Builder")

@mcp.tool()
def create_workflow(workflow_json: dict, bearer_token: str) -> dict:
    """
    CREATE → UPDATE → APPROVE (full new workflow creation)
    
    Args:
        workflow_json: Complete workflow JSON with dynamicProperties and workflowData
        bearer_token: Bearer token for Leegality API authentication
        
    Returns:
        Dict with success status, workflow_id, and details
    """
    start_time = time.time()
    
    try:
        print(f"🚀 Starting full workflow creation (CREATE → UPDATE → APPROVE)")
        
        # Initialize API client
        api = LeegalityWorkflowAPI(bearer_token)
        
        # STEP 1: Create workflow
        print("📋 Step 1: Creating workflow...")
        workflow_data = api._step1_create_workflow()
        if not workflow_data['success']:
            return {
                'success': False,
                'error': workflow_data['error'],
                'step_failed': 'CREATE'
            }
        
        workflow_id = workflow_data['workflow_id']
        version = workflow_data['version']
        print(f"✅ Workflow created: {workflow_id} (v{version})")
        
        # STEP 2: Update workflow with JSON data
        print("🔧 Step 2: Updating workflow with JSON data...")
        update_result = api._step2_update_workflow(workflow_id, version, workflow_json)
        if not update_result['success']:
            return {
                'success': False,
                'error': update_result['error'],
                'step_failed': 'UPDATE',
                'workflow_id': workflow_id,
                'workflow_version': version
            }
        print("✅ Workflow updated successfully")
        
        # STEP 3: Approve workflow
        print("🎉 Step 3: Approving workflow...")
        approve_result = api._step3_approve_workflow(workflow_id, version)
        if not approve_result['success']:
            return {
                'success': False,
                'error': approve_result['error'],
                'step_failed': 'APPROVE',
                'workflow_id': workflow_id,
                'workflow_version': version
            }
        print("✅ Workflow approved and published")
        
        # Success!
        processing_time = round(time.time() - start_time, 1)
        
        result = {
            'success': True,
            'workflow_id': workflow_id,
            'workflow_version': version,
            'status': 'PUBLISHED',
            'processing_time': f"{processing_time} seconds",
            'flow_completed': 'CREATE → UPDATE → APPROVE'
        }
        
        print(f"🎊 SUCCESS! Workflow {workflow_id} created and published in {processing_time}s")
        return result
        
    except Exception as e:
        error_msg = f"Full workflow creation failed: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'processing_time': f"{round(time.time() - start_time, 1)} seconds"
        }

@mcp.tool()
def update_and_approve(workflow_id: str, workflow_version: str, workflow_json: dict, bearer_token: str) -> dict:
    """
    UPDATE → APPROVE (edit existing workflow)
    
    Args:
        workflow_id: Existing workflow ID
        workflow_version: Workflow version to update
        workflow_json: Complete workflow JSON with dynamicProperties and workflowData
        bearer_token: Bearer token for Leegality API authentication
        
    Returns:
        Dict with success status, workflow_id, and details
    """
    start_time = time.time()
    
    try:
        print(f"🔄 Starting workflow update and approval (UPDATE → APPROVE)")
        print(f"📋 Target: {workflow_id} (v{workflow_version})")
        
        # Initialize API client
        api = LeegalityWorkflowAPI(bearer_token)
        
        # STEP 1: Update workflow with JSON data
        print("🔧 Step 1: Updating workflow with JSON data...")
        update_result = api._step2_update_workflow(workflow_id, workflow_version, workflow_json)
        if not update_result['success']:
            return {
                'success': False,
                'error': update_result['error'],
                'step_failed': 'UPDATE',
                'workflow_id': workflow_id,
                'workflow_version': workflow_version
            }
        print("✅ Workflow updated successfully")
        
        # STEP 2: Approve workflow
        print("🎉 Step 2: Approving workflow...")
        approve_result = api._step3_approve_workflow(workflow_id, workflow_version)
        if not approve_result['success']:
            return {
                'success': False,
                'error': approve_result['error'],
                'step_failed': 'APPROVE',
                'workflow_id': workflow_id,
                'workflow_version': workflow_version
            }
        print("✅ Workflow approved and published")
        
        # Success!
        processing_time = round(time.time() - start_time, 1)
        
        result = {
            'success': True,
            'workflow_id': workflow_id,
            'workflow_version': workflow_version,
            'status': 'PUBLISHED',
            'processing_time': f"{processing_time} seconds",
            'flow_completed': 'UPDATE → APPROVE'
        }
        
        print(f"🎊 SUCCESS! Workflow {workflow_id} updated and published in {processing_time}s")
        return result
        
    except Exception as e:
        error_msg = f"Workflow update and approval failed: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'processing_time': f"{round(time.time() - start_time, 1)} seconds"
        }

@mcp.tool()
def create_workflow_from_natural_language(requirement: str, bearer_token: str) -> dict:
    """
    Pure MCP Flow: Natural Language → Gemini AI → MCP Tool (create_workflow) → Leegality APIs
    
    Args:
        requirement: Natural language workflow requirement (e.g., "Create workflow with 2 documents A and B")
        bearer_token: Bearer token for Leegality API authentication
        
    Returns:
        Dict with success status, workflow_id, and details
    """
    start_time = time.time()
    
    try:
        print(f"🧠 Starting natural language workflow creation (Pure MCP Flow)")
        print(f"📝 Requirement: {requirement}")
        
        # Initialize API client (contains Gemini API integration)
        api = LeegalityWorkflowAPI(bearer_token)
        
        # STEP 1: Natural Language → Gemini AI → JSON
        print("🤖 Step 1: Processing with Gemini AI to generate workflow JSON...")
        workflow_json = api._parse_with_ai(requirement)
        print("✅ JSON generated successfully from natural language")
        
        # STEP 2: Call MCP tool with generated JSON
        print("🔧 Step 2: Calling create_workflow MCP tool with generated JSON...")
        result = create_workflow(workflow_json, bearer_token)
        
        # Add MCP-specific metadata
        if result.get('success'):
            result['flow_completed'] = 'Natural Language → Gemini AI → MCP Tool (create_workflow) → Leegality APIs'
            result['mcp_tool'] = 'create_workflow_from_natural_language → create_workflow'
            result['ai_generated_json'] = True
        else:
            result['mcp_tool'] = 'create_workflow_from_natural_language → create_workflow'
            result['ai_generated_json'] = True
        
        return result
        
    except Exception as e:
        error_msg = f"Natural language workflow creation failed: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'processing_time': f"{round(time.time() - start_time, 1)} seconds",
            'mcp_tool': 'create_workflow_from_natural_language'
        }

@mcp.tool()
def create_and_approve(workflow_json: dict, bearer_token: str) -> dict:
    """
    CREATE → APPROVE (skip update step)
    
    Args:
        workflow_json: Complete workflow JSON with dynamicProperties and workflowData
        bearer_token: Bearer token for Leegality API authentication
        
    Returns:
        Dict with success status, workflow_id, and details
    """
    start_time = time.time()
    
    try:
        print(f"⚡ Starting express workflow creation (CREATE → APPROVE)")
        
        # Initialize API client
        api = LeegalityWorkflowAPI(bearer_token)
        
        # STEP 1: Create workflow
        print("📋 Step 1: Creating workflow...")
        workflow_data = api._step1_create_workflow()
        if not workflow_data['success']:
            return {
                'success': False,
                'error': workflow_data['error'],
                'step_failed': 'CREATE'
            }
        
        workflow_id = workflow_data['workflow_id']
        version = workflow_data['version']
        print(f"✅ Workflow created: {workflow_id} (v{version})")
        
        # STEP 2: Approve workflow (skip update)
        print("🎉 Step 2: Approving workflow (skipping update)...")
        approve_result = api._step3_approve_workflow(workflow_id, version)
        if not approve_result['success']:
            return {
                'success': False,
                'error': approve_result['error'],
                'step_failed': 'APPROVE',
                'workflow_id': workflow_id,
                'workflow_version': version
            }
        print("✅ Workflow approved and published")
        
        # Success!
        processing_time = round(time.time() - start_time, 1)
        
        result = {
            'success': True,
            'workflow_id': workflow_id,
            'workflow_version': version,
            'status': 'PUBLISHED',
            'processing_time': f"{processing_time} seconds",
            'flow_completed': 'CREATE → APPROVE (express)',
            'note': 'Update step was skipped - workflow uses template defaults'
        }
        
        print(f"⚡ SUCCESS! Express workflow {workflow_id} created in {processing_time}s")
        return result
        
    except Exception as e:
        error_msg = f"Express workflow creation failed: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'processing_time': f"{round(time.time() - start_time, 1)} seconds"
        }

if __name__ == "__main__":
    print("🚀 Starting Leegality Workflow Builder MCP Server...")
    print("📋 Available tools:")
    print("  1. create_workflow - CREATE → UPDATE → APPROVE (full workflow)")
    print("  2. update_and_approve - UPDATE → APPROVE (edit existing)")
    print("  3. create_workflow_from_natural_language - Pure MCP Flow: Natural Language → Gemini AI → MCP Tool")
    print("  4. create_and_approve - CREATE → APPROVE (express, skip update)")
    print("\n🔗 Server running - Ready for MCP client connections!")
    mcp.run()