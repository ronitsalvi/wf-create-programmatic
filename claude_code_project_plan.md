# Claude Code Project Plan - Leegality Workflow Builder

## Project Context & My Frustration

Hey Claude Code - I've been working on a Leegality workflow builder that converts natural language to e-signature workflows. The current system is **broken** - when I ask for "2 documents A and B", it only creates 1 document named "A". The NLP parsing is failing.

**I want to start fresh with YOU handling the natural language processing instead of my buggy system.**

**Important Note**: The attached FUNCTIONAL_REQUIREMENTS.md was created by another AI model, so it might be **too high-level** in some places or make assumptions that aren't quite right. The core information is mostly correct, but if something seems unclear or overly generic, please ask me for clarification rather than assuming.

**My Goal**: Validate that YOU can understand and structure the requirements correctly BEFORE I build any MCP servers or complex architecture.

**Timeline**: 1 hour total, but I want to test incrementally so I know when we're screwing up.

## Phase 1: Documentation Review & Understanding (10 min)

**Your Task**: 
1. Read the attached FUNCTIONAL_REQUIREMENTS.md carefully
2. **Note**: This .md was written by another AI model and may be too high-level or make assumptions. Ask me for clarification on anything unclear.
3. Tell me if you understand:
   - The 3 API calls needed (CREATE/UPDATE/APPROVE)
   - The JSON structure for workflows  
   - How documents and invitees should be extracted from natural language
   - What the current system is doing wrong

**Success Criteria**: You can explain back to me what the system should do vs. what it's currently doing wrong. If the documentation is too vague, ask me for specific details.

**Test Questions for You**:
- "What should happen when I say 'Create workflow with 2 documents A and B'?"
- "What JSON structure should be sent to the UPDATE API?"

## Phase 2: Natural Language Parsing Test (15 min)

**Your Task**: WITHOUT writing full code yet, show me how you would parse these inputs:

**Test Cases**:
1. `"Create workflow with 2 documents A and B"`
   - Expected: 2 documents named "A" and "B"
   - Current system creates: 1 document named "A" (WRONG)

2. `"Bank loan processing with 3 documents: Sanction Letter, Loan Agreement, Bank Guarantee"`
   - Expected: 3 documents with those exact names

3. `"4 signers: Bank Signatory (aadhaar), Customer (DSC), Subordinate (multiple), Bank Signatory (DSC)"`
   - Expected: 4 signers with correct eSign types

4. `"2 invitees Ronit and Sid with emails ronit@test.com and sid@test.com"`
   - Expected: 2 invitees with proper email assignments

**Your Output**: For each test case, show me the JSON structure you would generate. Don't code yet - just show the logic.

**Success Criteria**: Your parsing logic is clearly better than the current broken system.

## Phase 3: Code the Solution (20 min)

**Only proceed if Phase 2 looks good.**

**Your Task**: Write Python code that:

1. **Function**: `parse_natural_language(description: str) -> dict`
   - Takes natural language input
   - Returns structured JSON for Leegality API

2. **Function**: `create_leegality_workflow(parsed_data: dict, bearer_token: str) -> dict`
   - Makes the 3 API calls (CREATE/UPDATE/APPROVE)
   - Returns success/failure with workflow_id

3. **Function**: `main(description: str, token: str) -> dict`
   - Combines everything
   - End-to-end workflow creation

**Testing Strategy**:
- Start with hardcoded API responses (mock the Leegality calls)
- Test your parsing logic first
- Only add real API calls once parsing works

**Success Criteria**: 
- Code handles all 4 test cases from Phase 2 correctly
- Clear separation between parsing and API logic
- Handles errors gracefully

## Phase 4: Validation & MCP Preparation (15 min)

**Your Task**: 
1. Test the code with the 4 test cases
2. Show me the JSON that would be sent to Leegality APIs
3. Explain what's different from the broken current system
4. Prepare the code structure for MCP wrapping

**MCP Preparation**: Structure your code so it can easily become:
```python
@mcp.tool()
def create_workflow(description: str, bearer_token: str) -> dict:
    # Your code here
    pass
```

**Success Criteria**: 
- All test cases pass
- Code is ready to be wrapped in FastMCP
- You've identified what was wrong with the original system

## Key Requirements (From Documentation)

**API Endpoints** (Base: `https://preprod-gateway.leegality.com`):
1. **CREATE**: `POST /api/workflow` → get workflow_id
2. **UPDATE**: `PUT /api/workflow/{id}` → upload JSON data  
3. **APPROVE**: `POST /api/workflow/{id}/approve` → publish

**Authentication**: Bearer token in Authorization header

**Critical JSON Structure Elements**:
- Documents: Must have unique UUIDs and exact names from user input
- Invitees: Must extract names, assign emails, configure eSign types
- eSign Mappings: "aadhaar" → Aadhaar eSign, "dsc" → DSC, etc.

## My Expectations

**Be Incremental**: Don't jump to full code. Let me validate each phase.

**Be Honest**: If you don't understand something from the .md, ask me.

**Focus on the Core Problem**: The current system's NLP is broken. I need YOU to be better at parsing "2 documents A and B" than my current system.

**Test Everything**: Show me your logic before implementing.

**Ready to Start with Phase 1?** Read the documentation and tell me what you understand.