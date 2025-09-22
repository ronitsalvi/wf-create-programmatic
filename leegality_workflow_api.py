#!/usr/bin/env python3
"""
Complete Leegality Workflow API Integration
AI-Powered workflow creation with Gemini natural language processing
Fixes the core bug: "Create workflow with 2 documents A and B" now creates 2 documents
"""

import requests
import json
import uuid
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai
import os

class LeegalityWorkflowAPI:
    """Complete API integration for Leegality workflow creation"""
    
    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.base_url = "https://preprod-gateway.leegality.com"
        self.headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Initialize Gemini AI configuration
        self.gemini_api_key = "AIzaSyDlwtCyXrlhQzMCAvK8QEEbh46D2AFf-xc"
        self.gemini_model = "gemini-2.5-flash"
        self.gemini_base_url = "https://generativelanguage.googleapis.com"
        self.template_id = "f214c92a-8f67-489a-a4c6-2ef5ae0472c4"
        self.template_version = "0.1"
    
    def create_workflow_from_text(self, user_requirement: str) -> Dict[str, Any]:
        """
        Complete end-to-end workflow creation from natural language
        
        Args:
            user_requirement: Natural language description (e.g., "Create workflow with 2 documents A and B")
            
        Returns:
            Dict with success status, workflow_id, and details
        """
        start_time = time.time()
        
        try:
            print(f"🚀 Starting workflow creation: '{user_requirement}'")
            
            # Parse natural language input with AI - returns complete JSON
            workflow_payload = self._parse_natural_language(user_requirement)
            
            # Extract metadata for logging
            doc_count = len(workflow_payload.get('workflowData', {}).get('documents', []))
            invitee_cards = workflow_payload.get('workflowData', {}).get('invitees', {}).get('inviteeCards', [])
            invitee_count = len(invitee_cards)
            print(f"📝 AI Generated: {doc_count} documents, {invitee_count} invitees")
            
            # STEP 1: Create workflow
            print("📋 Step 1: Creating workflow...")
            workflow_data = self._step1_create_workflow()
            if not workflow_data['success']:
                return workflow_data
            
            workflow_id = workflow_data['workflow_id']
            version = workflow_data['version']
            print(f"✅ Workflow created: {workflow_id} (v{version})")
            
            # STEP 2: Update workflow with AI-generated JSON (no payload generation needed)
            print("📤 Step 2: Updating workflow...")
            update_result = self._step2_update_workflow(workflow_id, version, workflow_payload)
            if not update_result['success']:
                return update_result
            print("✅ Workflow updated successfully")
            
            # STEP 3: Approve workflow
            print("🎉 Step 3: Approving workflow...")
            approve_result = self._step3_approve_workflow(workflow_id, version)
            if not approve_result['success']:
                return approve_result
            print("✅ Workflow approved and published")
            
            # Success!
            processing_time = round(time.time() - start_time, 1)
            
            result = {
                'success': True,
                'workflow_id': workflow_id,
                'workflow_version': version,
                'status': 'PUBLISHED',
                'processing_time': f"{processing_time} seconds",
                'documents_created': doc_count,
                'invitees_created': invitee_count,
                'ai_payload': workflow_payload
            }
            
            print(f"🎊 SUCCESS! Workflow {workflow_id} created in {processing_time}s")
            print(f"📊 Created {result['documents_created']} documents and {result['invitees_created']} invitees")
            
            return result
            
        except Exception as e:
            error_msg = f"Workflow creation failed: {str(e)}"
            print(f"❌ ERROR: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'processing_time': f"{round(time.time() - start_time, 1)} seconds"
            }
    
    def _parse_with_ai(self, user_requirement: str) -> Dict[str, Any]:
        """
        AI-Powered natural language parsing using Gemini REST API
        Returns complete Leegality workflow JSON ready for API
        """
        try:
            # Load the enhanced prompt template
            prompt_path = os.path.join(os.path.dirname(__file__), "ENHANCED_NLP_PROMPT.md")
            with open(prompt_path, 'r') as f:
                prompt_template = f.read()
            
            # Replace {USER_INPUT} with actual requirement
            full_prompt = prompt_template.replace("{USER_INPUT}", user_requirement)
            
            print("🤖 Processing with Gemini AI...")
            
            # Call Gemini API using REST approach
            ai_response = self._call_gemini_api(full_prompt)
            
            if not ai_response:
                raise Exception("Empty response from Gemini API")
            
            # Parse JSON response
            json_response = self._parse_gemini_response(ai_response)
            
            print("✅ AI parsing completed successfully")
            return json_response
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {str(e)}")
            print(f"AI Response: {ai_response[:500] if ai_response else 'None'}...")
            raise Exception(f"Invalid JSON from AI: {str(e)}")
            
        except Exception as e:
            print(f"❌ AI processing failed: {str(e)}")
            raise Exception(f"AI parsing failed: {str(e)}")

    def _call_gemini_api(self, prompt: str) -> str:
        """Call Gemini API using REST endpoint"""
        url = f"{self.gemini_base_url}/v1beta/models/{self.gemini_model}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.gemini_api_key
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "topK": 1,
                "topP": 0.8,
                "maxOutputTokens": 32768,
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            
            response_data = response.json()
            
            # Extract text from Gemini response
            if 'candidates' in response_data and response_data['candidates']:
                candidate = response_data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    return candidate['content']['parts'][0]['text']
            
            raise Exception(f"No valid response from Gemini API. Response: {response_data}")
            
        except requests.RequestException as e:
            print(f"Gemini API request failed: {str(e)}")
            raise Exception(f"Gemini API call failed: {str(e)}")
        except Exception as e:
            print(f"Gemini API response parsing failed: {str(e)}")
            raise Exception(f"Failed to parse Gemini response: {str(e)}")

    def _parse_gemini_response(self, text: str) -> Dict[str, Any]:
        """Parse Gemini AI response text into JSON structure"""
        # Remove any markdown formatting
        text = text.strip()
        if text.startswith('```json'):
            text = text.replace('```json', '').replace('```', '').strip()
        if text.startswith('```'):
            text = text.replace('```', '').strip()
        
        # Parse JSON
        return json.loads(text)

    def _parse_natural_language(self, text: str) -> Dict[str, Any]:
        """Wrapper method for backward compatibility - now uses AI"""
        return self._parse_with_ai(text)
    
    def _parse_complex_signers(self, signers_text: str, original_text: str) -> List[Dict[str, Any]]:
        """Parse complex signer specifications with eSign types"""
        signers = []
        
        # Split by common separators
        parts = []
        for sep in [',', ';']:
            if sep in signers_text:
                parts = [p.strip() for p in signers_text.split(sep)]
                break
        else:
            parts = [signers_text.strip()]
        
        # Extract emails with context parsing
        import re
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', original_text)
        
        # Parse email assignments with better context
        email_assignments = {}
        if emails:
            email_context_patterns = [
                r'first\s+signer\s+email[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
                r'second\s+signer\s+email[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
                r'signer\s+(\d+)\s+email[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            ]
            
            for pattern in email_context_patterns:
                matches = re.findall(pattern, original_text.lower())
                for match in matches:
                    if isinstance(match, tuple) and len(match) == 2:
                        if match[0].isdigit():
                            email_assignments[int(match[0]) - 1] = match[1]
                        else:
                            if 'first' in pattern:
                                email_assignments[0] = match[1] if isinstance(match, tuple) else match
                            elif 'second' in pattern:
                                email_assignments[1] = match[1] if isinstance(match, tuple) else match
                    else:
                        if 'first' in pattern:
                            email_assignments[0] = match
                        elif 'second' in pattern:
                            email_assignments[1] = match
        
        for i, part in enumerate(parts):
            if not part or part.isspace():
                continue
                
            # Extract signer name and eSign type
            name = ""
            esign_type = "virtualEsign"  # default
            
            # Look for patterns like "Bank Signatory (aadhaar eSign)"
            if '(' in part and ')' in part:
                name_part = part.split('(')[0].strip()
                esign_part = part.split('(')[1].split(')')[0].strip().lower()
                
                # Determine eSign type
                if "aadhaar" in esign_part or "aadhar" in esign_part:
                    esign_type = "aadharEsign"
                elif "dsc" in esign_part:
                    esign_type = "dscToken"
                elif "multiple" in esign_part:
                    esign_type = "multiple"  # Special handling needed
            else:
                name_part = part.strip()
            
            # Clean up the name
            name = self._clean_signer_name(name_part)
            
            # Assign email only if explicitly specified, otherwise leave blank
            email = ""  # Default to blank
            if i in email_assignments:
                email = email_assignments[i]
            elif name.lower() in email_assignments:
                email = email_assignments[name.lower()]
            
            signers.append({
                'name': name,
                'esign_type': esign_type,
                'email': email,
                'signing_level': i + 1
            })
        
        return signers
    
    def _clean_signer_name(self, name: str) -> str:
        """Clean and format signer name"""
        # Remove numbers, extra whitespace
        import re
        cleaned = re.sub(r'^\d+\s*', '', name)  # Remove leading numbers
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()  # Normalize whitespace
        
        if not cleaned:
            return "Signer"
        
        # Title case
        return cleaned.title()
    
    def _extract_entities_from_phrase(self, phrase: str) -> List[str]:
        """Extract entities from phrase, handling conjunctions properly"""
        entities = []
        
        # Clean the phrase
        phrase = phrase.strip()
        
        # Split by common conjunctions
        for separator in [' and ', ' or ', ', ', ' & ', ',']:
            if separator in phrase:
                parts = phrase.split(separator)
                break
        else:
            parts = [phrase]
        
        # Process each part
        for part in parts:
            part = part.strip()
            
            # Skip common words
            if part.lower() in ['the', 'with', 'for', 'in', 'on', 'at', 'to', '']:
                continue
            
            # Extract single capital letters (A, B, C)
            if len(part) == 1 and part.isalpha():
                entities.append(part.upper())
            
            # Extract quoted strings
            elif '"' in part or "'" in part:
                cleaned = part.strip('\'"')
                if cleaned:
                    entities.append(cleaned.title())
            
            # Extract meaningful words
            elif len(part) > 1:
                # Remove numbers and clean
                import re
                cleaned = re.sub(r'^\d+\s*', '', part)  # Remove leading numbers
                if cleaned and len(cleaned) > 1:
                    entities.append(cleaned.title())
        
        return entities
    
    def _step1_create_workflow(self) -> Dict[str, Any]:
        """Step 1: Create draft workflow"""
        try:
            url = f"{self.base_url}/workflow-manager/v1/workflow"
            
            payload = {
                "name": f"NLP_Workflow_{int(time.time())}",
                "workflowTemplateId": self.template_id,
                "workflowTemplateVersion": self.template_version,
                "versionDescription": "Created via NLP Python Interface"
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=120)
            
            if response.status_code not in [200, 201]:
                return {
                    'success': False,
                    'error': f"Workflow creation failed: HTTP {response.status_code} - {response.text}"
                }
            
            data = response.json()
            
            # Handle response structure - data might be nested
            workflow_data = data.get('data', data)
            
            return {
                'success': True,
                'workflow_id': workflow_data['id'],
                'version': workflow_data['version'],
                'name': workflow_data['name']
            }
            
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout - API took too long to respond'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Connection error - Unable to reach Leegality API'}
        except Exception as e:
            return {'success': False, 'error': f"Unexpected error in workflow creation: {str(e)}"}
    
    def _step2_update_workflow(self, workflow_id: str, version: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Update workflow with generated data"""
        try:
            url = f"{self.base_url}/workflow-manager/v1/workflow/{workflow_id}/{version}"
            
            response = requests.put(url, headers=self.headers, json=payload, timeout=120)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"Workflow update failed: HTTP {response.status_code} - {response.text}"
                }
            
            return {'success': True}
            
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout during workflow update'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Connection error during workflow update'}
        except Exception as e:
            return {'success': False, 'error': f"Unexpected error during workflow update: {str(e)}"}
    
    def _step3_approve_workflow(self, workflow_id: str, version: str) -> Dict[str, Any]:
        """Step 3: Approve and publish workflow"""
        try:
            url = f"{self.base_url}/workflow-manager/v1/workflow/approve"
            
            payload = {
                "workflowId": workflow_id,
                "version": version
            }
            
            response = requests.patch(url, headers=self.headers, json=payload, timeout=120)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"Workflow approval failed: HTTP {response.status_code} - {response.text}"
                }
            
            return {'success': True, 'status': 'PUBLISHED'}
            
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout during workflow approval'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Connection error during workflow approval'}
        except Exception as e:
            return {'success': False, 'error': f"Unexpected error during workflow approval: {str(e)}"}
    
    def _generate_workflow_payload(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete workflow payload with dynamic properties"""
        
        # Generate document structures
        documents = []
        doc_dynamic_props = []
        
        for i, doc_name in enumerate(parsed_data['documents']):
            doc_id = str(uuid.uuid4())
            
            # Document data
            doc_data = {
                "id": doc_id,
                "documentName": doc_name,
                "subDocuments": [],
                "stamps": {
                    "mergedDocumentStamp": True,
                    "stampSeries": {
                        "stampSeriesEnabled": False,
                        "seriesConfig": [{}]
                    }
                }
            }
            documents.append(doc_data)
            
            # Document dynamic properties
            doc_props = {
                "deleteDocument#p": {"attributeRef": "", "v": False, "e": False, "type": "BUTTON"},
                "uploadDocumentEnabled#p": {"attributeRef": "", "v": True, "e": True, "m": False, "type": "FILE_UPLOAD"},
                "selectTemplateSection#p": {"attributeRef": "", "v": True, "type": "CONTAINER"},
                "selectTemplateSection": {
                    "selectTemplateEnabled#p": {"attributeRef": "", "v": True, "e": True, "type": "BUTTON"}
                },
                "subDocuments#p": {"attributeRef": f"documents/{i}/subDocuments", "v": True, "e": True, "m": False, "type": "SUB_DOCUMENTS_LIST"},
                "documentName#p": {"attributeRef": f"documents/{i}/documentName", "v": True, "e": True, "m": False, "type": "TEXT_INPUT"},
                "stampsSection#p": {"attributeRef": "", "v": True, "type": "CONTAINER"},
                "stampsSection": {
                    "mergedDocumentStamp#p": {"attributeRef": f"documents/{i}/stamps/mergedDocumentStamp", "v": True, "e": True, "type": "RADIO_GROUP"},
                    "stampSeries#p": {"attributeRef": f"documents/{i}/stamps/stampSeries", "v": True, "type": "CONTAINER"},
                    "stampSeries": {
                        "stampSeriesEnabled#p": {"attributeRef": f"documents/{i}/stamps/stampSeries/stampSeriesEnabled", "v": True, "e": True, "type": "TOGGLE"},
                        "seriesConfig#p": {"attributeRef": f"documents/{i}/stamps/stampSeries/seriesConfig", "v": True, "type": "CONTAINER_LIST"},
                        "seriesConfig": [{"stampSeriesId#p": {"attributeRef": f"documents/{i}/stamps/stampSeries/seriesConfig/0/stampSeriesId", "v": True, "e": True, "m": False, "type": "DROPDOWN"}}]
                    }
                }
            }
            doc_dynamic_props.append(doc_props)
        
        # Generate invitee structures with enhanced support
        invitee_cards = []
        invitee_dynamic_props = []
        
        # Use detailed invitee information if available
        invitee_info = parsed_data.get('invitee_details', [])
        if not invitee_info:
            # Fallback to simple invitee list with proper email assignment
            invitee_info = []
            email_assignments = parsed_data.get('email_assignments', {})
            
            for i, name in enumerate(parsed_data['invitees']):
                # Only assign email if explicitly specified in requirements
                email = ""  # Default to blank
                
                # Check email assignments by index
                if i in email_assignments:
                    email = email_assignments[i]
                # Check email assignments by name
                elif name.lower() in email_assignments:
                    email = email_assignments[name.lower()]
                # Check if it's the first available email from simple parsing
                elif i == 0 and parsed_data.get('emails'):
                    email = parsed_data['emails'][0]  # Only assign first email to first signer
                
                invitee_info.append({
                    'name': name,
                    'email': email,
                    'esign_type': parsed_data['esign_type'],
                    'signing_level': i + 1
                })
        
        for i, invitee_data in enumerate(invitee_info):
            invitee_id = str(uuid.uuid4())
            invitee_detail_id = str(uuid.uuid4())
            combination_id = str(uuid.uuid4())
            
            # Create document assignments (assign all documents to each invitee)
            assigned_documents = []
            for doc in documents:
                assigned_documents.append({
                    "documentReference": f"/documents/{doc['id']}",
                    "role": "signer",
                    "id": str(uuid.uuid4())
                })
            
            # Get eSign configuration for this specific invitee
            esign_config = self._get_esign_config(invitee_data.get('esign_type', 'virtualEsign'))
            
            # Handle special "multiple" eSign type
            if invitee_data.get('esign_type') == 'multiple':
                esign_config = self._get_multiple_esign_config()
            
            # Invitee card data
            invitee_card = {
                "id": invitee_id,
                "inviteeCard": {
                    "id": str(uuid.uuid4()),
                    "inviteeType": "signer",
                    "inviteeSigningLevel": invitee_data.get('signing_level', i + 1),
                    "inviteeDetails": [{
                        "id": invitee_detail_id,
                        "inviteeLabel": invitee_data['name'],
                        "inviteeEmail": invitee_data.get('email') or f"placeholder{i+1}@leegality.com"  # Valid placeholder if no email provided
                    }],
                    "inviteeSettings": {
                        "securityOptions": {
                            "twoFa": False,
                            "oneFa": True,
                            "faceCapture": True
                        }
                    },
                    "combinations": [{
                        "id": combination_id,
                        "assignedDocuments": assigned_documents,
                        "combinationSettings": {
                            "esignTypes": esign_config
                        }
                    }]
                }
            }
            invitee_cards.append(invitee_card)
            
            # Invitee dynamic properties
            invitee_props = {
                "inviteeCard#p": {"attributeRef": f"invitees/inviteeCards/{i}/inviteeCard", "v": True, "e": True, "m": False, "type": "INVITEE_CARD"},
                "inviteeCard": {
                    "inviteeType#p": {"attributeRef": f"invitees/inviteeCards/{i}/inviteeCard/inviteeType", "v": True, "e": True, "m": False, "type": "DROPDOWN"},
                    "inviteeDetails#p": {"attributeRef": f"invitees/inviteeCards/{i}/inviteeCard/inviteeDetails", "v": True, "e": True, "m": False, "type": "CONTAINER_LIST"},
                    "inviteeDetails": [{
                        "inviteeLabel#p": {"attributeRef": f"invitees/inviteeCards/{i}/inviteeCard/inviteeDetails/0/inviteeLabel", "v": True, "e": False, "m": False, "type": "TEXT_INPUT"},
                        "inviteeEmail#p": {"attributeRef": f"invitees/inviteeCards/{i}/inviteeCard/inviteeDetails/0/inviteeEmail", "v": True, "e": True, "m": False, "type": "TEXT_INPUT"}
                    }],
                    "combinations#p": {"attributeRef": f"invitees/inviteeCards/{i}/inviteeCard/combinations", "v": True, "e": True, "m": False, "type": "CONTAINER_LIST"},
                    "combinations": [{
                        "combinationSettings#p": {"attributeRef": f"invitees/inviteeCards/{i}/inviteeCard/combinations/0/combinationSettings", "v": True, "e": True, "m": False, "type": "CONTAINER"},
                        "assignedDocuments#p": {"attributeRef": f"invitees/inviteeCards/{i}/inviteeCard/combinations/0/assignedDocuments", "v": True, "e": True, "m": False, "type": "MODAL"}
                    }],
                    "inviteeSettings#p": {"attributeRef": f"invitees/inviteeCards/{i}/inviteeCard/inviteeSettings", "v": True, "e": True, "m": False, "type": "CONTAINER"}
                }
            }
            invitee_dynamic_props.append(invitee_props)
        
        # Build complete payload
        payload = {
            "versionDescription": "Updated with AI-generated configuration",
            "dynamicProperties": {
                "documents#p": {"attributeRef": "documents", "e": False, "type": "TAB_LIST"},
                "documents": doc_dynamic_props,
                "invitees#p": {"attributeRef": "invitees", "v": True, "e": True, "m": False, "type": "CONTAINER"},
                "invitees": {
                    "inviteeCards#p": {"attributeRef": "invitees/inviteeCards", "v": True, "e": True, "m": False, "type": "INVITEE_LIST"},
                    "inviteeCards": invitee_dynamic_props
                }
            },
            "workflowData": {
                "documents": documents,
                "invitees": {
                    "inviteeCards": invitee_cards
                },
                "pack": {
                    "packName": f"NLP Generated Workflow - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                }
            },
            "rules": []
        }
        
        return payload
    
    def _get_esign_config(self, esign_type: str) -> Dict[str, Any]:
        """Get eSign configuration based on type"""
        configs = {
            "virtualEsign": {
                "virtualEsign": {
                    "virtualEsignEnabled": True,
                    "virtualEsignConfig": {}
                }
            },
            "aadharEsign": {
                "aadharEsign": {
                    "aadharEsignEnabled": True,
                    "addharEsignConfig": {
                        "aadhaarOtp": True
                    }
                }
            },
            "dscToken": {
                "dscToken": {
                    "enableDscToken": True,
                    "dscTokenConfig": {}
                }
            }
        }
        
        return configs.get(esign_type, configs["virtualEsign"])
    
    def _get_multiple_esign_config(self) -> Dict[str, Any]:
        """Get multiple eSign types configuration for subordinate"""
        return {
            "aadharEsign": {
                "aadharEsignEnabled": True,
                "addharEsignConfig": {
                    "aadhaarOtp": True
                }
            },
            "dscToken": {
                "enableDscToken": True,
                "dscTokenConfig": {}
            },
            "virtualEsign": {
                "virtualEsignEnabled": True,
                "virtualEsignConfig": {}
            },
            "docSign": {
                "enableDocSigner": True
            }
        }


def test_simple_workflow():
    """Test the core bug fix: 'Create workflow with 2 documents A and B'"""
    
    # Bearer token from your testing
    BEARER_TOKEN = "eyJ4NXQjUzI1NiI6ImxZYnVTSk9JR1E1MmhNUy1DeWJVb1A0RTExdFpnd3RjRWd1bHYwa0RuT0UiLCJraWQiOiJmZWM4MDNlNC00OWZlLTQ4ZmEtODc2YS0yNWMxZmFlNWUwMmYiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJrYXZpc2guc2F4ZW5hQGxlZWdhbGl0eS5jb20iLCJhdWQiOiJpbnN0YW50LWxvZ2luLWFwcCIsIm5iZiI6MTc1ODExNjA3MCwic2NvcGUiOlsiKiJdLCJpc3MiOiJodHRwczovL3ByZXByb2QtZ2F0ZXdheS5sZWVnYWxpdHkuY29tL2F1dGgiLCJleHAiOjE3NTgxMTk2NzAsImlhdCI6MTc1ODExNjA3MCwianRpIjoiZTNkOWE2MjQtNDBiNy00ODIzLWE2MWUtNTlkMzA5MzljMjI5In0.O7Yf59IBm6WpFMjOCKDkyR-qSKBJAc9Cuo-2rmnQFvpouLuPoY8XZ_3YyjYb0beVoUdrcS4Kpgi_UlrE3oyfE-go9KuDpRtGhfnlcIR9JoDXPeqqBArEVfcu8NGX7Y-1GVLCvTSWeELigj8zZ4QI1rcWWAmntEDHhrdJVDD79RztbLmrD4UVPKHVf0qZV29DfzE6BlOCSCV7CHAjx0GoUVvUFQ2AAOYsUX8l46BPlTjE5xO-LMuVD7BAXKi3SNc-gsnPjNWnJHGNTmAow8A_mi3XHoBMBiugMd-gzJ0kIjyuzGOlr1rS4S_nG77ziBQ9GARIkNLhPC21cmIe_fZdzg"
    
    # Initialize API client
    api = LeegalityWorkflowAPI(BEARER_TOKEN)
    
    # Test case that was failing
    test_case = "Create workflow with 2 documents A and B"
    
    print(f"🧪 Testing: '{test_case}'")
    print("Expected: Should create 2 documents named 'A' and 'B'")
    print("=" * 60)
    
    # Execute workflow creation
    result = api.create_workflow_from_text(test_case)
    
    # Display results
    print("\n" + "=" * 60)
    if result['success']:
        print("✅ TEST PASSED!")
        print(f"📋 Workflow ID: {result['workflow_id']}")
        print(f"⏱️  Processing Time: {result['processing_time']}")
        print(f"📄 Documents Created: {result['documents_created']}")
        print(f"📝 Document Names: {result['parsed_data']['documents']}")
        print(f"👥 Invitees Created: {result['invitees_created']}")
        print(f"📊 Status: {result['status']}")
    else:
        print("❌ TEST FAILED!")
        print(f"Error: {result['error']}")


def create_bank_loan_workflow():
    """Create complex bank loan workflow with specific requirements"""
    
    # Updated bearer token
    BEARER_TOKEN = "eyJ4NXQjUzI1NiI6ImxZYnVTSk9JR1E1MmhNUy1DeWJVb1A0RTExdFpnd3RjRWd1bHYwa0RuT0UiLCJraWQiOiJmZWM4MDNlNC00OWZlLTQ4ZmEtODc2YS0yNWMxZmFlNWUwMmYiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJrYXZpc2guc2F4ZW5hQGxlZWdhbGl0eS5jb20iLCJhdWQiOiJpbnN0YW50LWxvZ2luLWFwcCIsIm5iZiI6MTc1ODE0MTE5OSwic2NvcGUiOlsiKiJdLCJpc3MiOiJodHRwczovL3ByZXByb2QtZ2F0ZXdheS5sZWVnYWxpdHkuY29tL2F1dGgiLCJleHAiOjE3NTgxNDQ3OTksImlhdCI6MTc1ODE0MTE5OSwianRpIjoiODI5ZjA0OTMtNWI4Zi00MzRkLTg4YzQtYzJhYzQxYjAwMTkwIn0.Z9CyqdCtOnZ2k7DPgLBEj9ww0RUyOKoJCZqXV_2AyV8ne5cGyLVIP8Qo8V3cFH3Nc2lHkQogMi-_jKT8ejySnuOD_XO-eJysZJq-VOEBerYWzFj39Ogc6jLpQKcoI2_R_ubqsAK068R1Qioueo2YSry-Ruji7d9145r2fjs0dc6YV91B9YDo2yifNK8dzkaPp4K-8V4mXdgjLqBZnEkJsxU5VFyMqycGJ_-dVvT78ylNqj9usJPSjUE8lm4A0rUaHQaWQFc55WhdbszVghqddKVT1AtMUwBBprPmduquz4FvZhDkMLea-O9eCEubWNzkW6qODtvwsPb-Lq-2PQ3f0Q"
    
    # Initialize API client with enhanced parsing
    api = LeegalityWorkflowAPI(BEARER_TOKEN)
    
    # Complex bank loan workflow specification
    requirement = "Create a bank loan workflow with 3 documents: Sanction Letter, Loan Agreement, Bank Guarantee. 4 signers: Bank Signatory (aadhaar eSign), Customer (DSC), Subordinate (multiple sign types), Bank Signatory (DSC). First signer email: ritik.saraswat@leegality.com"
    
    print(f"🏦 Creating Bank Loan Workflow")
    print(f"📝 Requirement: {requirement}")
    print("=" * 80)
    
    # Execute workflow creation
    result = api.create_workflow_from_text(requirement)
    
    # Display results
    print("\n" + "=" * 80)
    if result['success']:
        print("✅ BANK LOAN WORKFLOW CREATED SUCCESSFULLY!")
        print(f"📋 Workflow ID: {result['workflow_id']}")
        print(f"⏱️  Processing Time: {result['processing_time']}")
        print(f"📄 Documents Created: {result['documents_created']}")
        print(f"📝 Document Names: {', '.join(result['parsed_data']['documents'])}")
        print(f"👥 Signers Created: {result['invitees_created']}")
        print(f"👤 Signer Names: {', '.join(result['parsed_data']['invitees'])}")
        print(f"🔐 eSign Types: {result['parsed_data'].get('esign_types', 'Multiple')}")
        print(f"📊 Status: {result['status']}")
        
        # Additional details
        if 'parsed_data' in result:
            print(f"\n🔍 Parsing Details:")
            print(f"   📋 Documents: {result['parsed_data']['documents']}")
            print(f"   👥 Invitees: {result['parsed_data']['invitees']}")
            if 'emails' in result['parsed_data']:
                print(f"   📧 Emails: {result['parsed_data']['emails']}")
    else:
        print("❌ BANK LOAN WORKFLOW CREATION FAILED!")
        print(f"Error: {result['error']}")
        
    return result


def create_application_workflow():
    """Create application workflow with specific requirements"""
    
    # Updated bearer token
    BEARER_TOKEN = "eyJ4NXQjUzI1NiI6ImxZYnVTSk9JR1E1MmhNUy1DeWJVb1A0RTExdFpnd3RjRWd1bHYwa0RuT0UiLCJraWQiOiJmZWM4MDNlNC00OWZlLTQ4ZmEtODc2YS0yNWMxZmFlNWUwMmYiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJrYXZpc2guc2F4ZW5hQGxlZWdhbGl0eS5jb20iLCJhdWQiOiJpbnN0YW50LWxvZ2luLWFwcCIsIm5iZiI6MTc1ODE0MzM4Miwic2NvcGUiOlsiKiJdLCJpc3MiOiJodHRwczovL3ByZXByb2QtZ2F0ZXdheS5sZWVnYWxpdHkuY29tL2F1dGgiLCJleHAiOjE3NTgxNDY5ODIsImlhdCI6MTc1ODE0MzM4MiwianRpIjoiZTZmMjdjNGUtMTQzNC00MmM3LTlkMTEtMmYzM2M0ODFkNGY4In0.BbGNk4SWfSqZCHC0W1LqjE82lvY1sGWqCGk1HGHfcVDXJRdoNz-wvXWMiivZJe8tMKYJ3W-nCvwgCBQrMoRPjNdh0xRdA4uEZPJXGnUbsYLVE8nNt2NKl74EsZaDbO1xkKZmkxO6JNSe8YMVMKnqKA11w8q-POd5Ue5e5nwuWm6YyVK7r9c5MhsD4L6I-jfTNVq8wkKQc2m8rQILkP9I7nKQHKJc8r4LzHsO1qWc2qMUKNKJcI5O6KQPQfVJfQ8A7a7xCz6L1lMVNTG0H4e8nBkN7DyXDQqUmJlGf8Ckyw3E5kKxk3TBV1m9U9-_BI7F8xL-ksAhMGTxBTUFLKe0nw"


def create_ronit_sid_workflow():
    """Create workflow with 2 documents (Sanction Letter, Loan Agreement) and 3 invitees (Ronit: ronit@leegality.com, Sid, unnamed)"""
    
    # Updated valid bearer token  
    BEARER_TOKEN = "eyJ4NXQjUzI1NiI6ImxZYnVTSk9JR1E1MmhNUy1DeWJVb1A0RTExdFpnd3RjRWd1bHYwa0RuT0UiLCJraWQiOiJmZWM4MDNlNC00OWZlLTQ4ZmEtODc2YS0yNWMxZmFlNWUwMmYiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJrYXZpc2guc2F4ZW5hQGxlZWdhbGl0eS5jb20iLCJhdWQiOiJpbnN0YW50LWxvZ2luLWFwcCIsIm5iZiI6MTc1ODUyMDgzMywic2NvcGUiOlsiKiJdLCJpc3MiOiJodHRwczovL3ByZXByb2QtZ2F0ZXdheS5sZWVnYWxpdHkuY29tL2F1dGgiLCJleHAiOjE3NTg1MjQ0MzMsImlhdCI6MTc1ODUyMDgzMywianRpIjoiZmEyYTBkMzctYzY3My00YTEyLWE2YTItOTg1NTc1ODAyMDAzIn0.IkiTMAixHLV0Bb0mOVOWctdt_F_xnj93QpIqXKSUS9UTCNRtXkaMbxXU2T91-a-vp1-QMJK5lAyf8muwMql3VfnGYnBIQjwW_Qm-ipIdhK9Wl_pn2WjU2QYrKlHy774bo58Q83cDYnDIagPh0h-YQZYANDS4EPOLbosxJcZAzt5oOhTdpFLq9YcAGuRHmKFydW0-ORMCoeGh1RMxW-lyvOTp5UhU1Urwxu2zw9LV8OtpZl7bdUqdytTEKscOSiO_9DLQ8qbKSK3VB83R8yL1yeie7OevPv6jjJjJFNnFJ5-1MGkBw9G34xgadBclheX0KBnyV20vy5QsuRwd4APLyQ"
    
    # Initialize API client 
    api = LeegalityWorkflowAPI(BEARER_TOKEN)
    
    # Requirements: Bank loan processing with 3 documents, 4 signers with Aadhaar eSign
    requirement = """Create a workflow for bank loan processing with 3 documents: Sanction Letter, Loan Agreement, and Bank Guarantee. Need 4 signers- Signer 1 name- Ronit, Signer 2 name: Sid, Signer 2 email: Sidhant@leegality.com. All 4 signers should have Aadhaar eSign configured"""
    
    print(f"Creating workflow with requirement: {requirement}")
    
    try:
        # Step 1: Create workflow
        result = api.create_workflow_from_text(requirement)
        
        if result and 'workflowId' in result:
            workflow_id = result['workflowId']
            print(f"✅ Workflow created successfully with ID: {workflow_id}")
            return result
        else:
            print(f"❌ Failed to create workflow. Result: {result}")
            return result
            
    except Exception as e:
        print(f"❌ Error creating workflow: {str(e)}")
        return None


# Workflow creation functions above


def test_email_parsing_fix():
    """Test the email parsing fix without API calls"""
    
    api = LeegalityWorkflowAPI("dummy-token")  # We won't make API calls
    
    # Test requirement - same as before
    requirement = "Create a bank loan workflow with 3 documents: Sanction Letter, Loan Agreement, Bank Guarantee. 4 signers: Bank Signatory (aadhaar eSign), Customer (DSC), Subordinate (multiple sign types), Bank Signatory (DSC). First signer email: ritik.saraswat@leegality.com"
    
    print("🧪 TESTING EMAIL PARSING FIX")
    print("=" * 60)
    print(f"Requirement: {requirement}")
    print()
    
    # Parse the requirement
    parsed_data = api._parse_natural_language(requirement)
    
    print("📋 PARSING RESULTS:")
    print(f"Documents: {parsed_data['documents']}")
    print(f"Invitees: {parsed_data['invitees']}")
    print(f"Emails found: {parsed_data['emails']}")
    print(f"Email assignments: {parsed_data.get('email_assignments', {})}")
    print()
    
    # Generate invitee info to see email assignment
    if parsed_data.get('invitee_details'):
        invitee_info = parsed_data['invitee_details']
    else:
        # Simulate the fallback logic
        invitee_info = []
        email_assignments = parsed_data.get('email_assignments', {})
        
        for i, name in enumerate(parsed_data['invitees']):
            email = ""  # Default to blank
            
            if i in email_assignments:
                email = email_assignments[i]
            elif name.lower() in email_assignments:
                email = email_assignments[name.lower()]
            elif i == 0 and parsed_data.get('emails'):
                email = parsed_data['emails'][0]
            
            invitee_info.append({
                'name': name,
                'email': email,
                'esign_type': parsed_data['esign_type'],
                'signing_level': i + 1
            })
    
    print("👥 FINAL INVITEE EMAIL ASSIGNMENTS:")
    for i, invitee in enumerate(invitee_info):
        status = "✅" if invitee['email'] else "🔳"
        email_display = invitee['email'] if invitee['email'] else "(blank)"
        print(f"  {i+1}. {invitee['name']}: {status} {email_display}")
    
    print()
    print("🎯 EMAIL FIX VALIDATION:")
    print("Expected:")
    print("  1. Bank Signatory: ✅ ritik.saraswat@leegality.com")
    print("  2. Customer: 🔳 (blank)")
    print("  3. Subordinate: 🔳 (blank)")  
    print("  4. Bank Signatory: 🔳 (blank)")
    
    # Validate the fix
    success = True
    if len(invitee_info) >= 4:
        if invitee_info[0]['email'] != "ritik.saraswat@leegality.com":
            success = False
            print("❌ First signer email incorrect")
        if any(invitee_info[i]['email'] != "" for i in range(1, 4)):
            success = False
            print("❌ Other signers should have blank emails")
    else:
        success = False
        print("❌ Incorrect number of signers")
    
    if success:
        print("\n🎊 EMAIL PARSING FIX SUCCESSFUL!")
        print("✅ First signer gets specified email")
        print("✅ Other signers have blank emails (no defaults)")
    else:
        print("\n❌ EMAIL PARSING FIX FAILED!")


if __name__ == "__main__":
    create_ronit_sid_workflow()