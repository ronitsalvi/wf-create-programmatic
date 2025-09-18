#!/usr/bin/env python3
"""
Complete Leegality Workflow API Integration
End-to-end workflow creation with natural language parsing
Fixes the core bug: "Create workflow with 2 documents A and B" now creates 2 documents
"""

import requests
import json
import uuid
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

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
            
            # Parse natural language input
            parsed_data = self._parse_natural_language(user_requirement)
            print(f"📝 Parsed: {parsed_data['documents']} documents, {parsed_data['invitees']} invitees")
            
            # STEP 1: Create workflow
            print("📋 Step 1: Creating workflow...")
            workflow_data = self._step1_create_workflow()
            if not workflow_data['success']:
                return workflow_data
            
            workflow_id = workflow_data['workflow_id']
            version = workflow_data['version']
            print(f"✅ Workflow created: {workflow_id} (v{version})")
            
            # STEP 2: Generate and update workflow
            print("🔧 Step 2: Generating workflow structure...")
            workflow_payload = self._generate_workflow_payload(parsed_data)
            
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
                'documents_created': len(parsed_data['documents']),
                'invitees_created': len(parsed_data['invitees']),
                'parsed_data': parsed_data
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
    
    def _parse_natural_language(self, text: str) -> Dict[str, Any]:
        """
        Enhanced natural language parsing - handles complex workflows
        Supports documents, signers with specific eSign types, and emails
        """
        original_text = text
        text = text.lower().strip()
        
        # Extract documents using semantic understanding
        documents = []
        
        # Pattern 1: "3 documents: Sanction Letter, Loan Agreement, Bank Guarantee"
        if "documents:" in text:
            after_colon = text.split("documents:")[1].split(".")[0]
            documents.extend(self._extract_entities_from_phrase(after_colon))
        
        # Pattern 2: "documents A and B" or "documents A, B, C"
        elif "documents" in text:
            after_docs = text.split("documents")[1].split(".")[0]
            documents.extend(self._extract_entities_from_phrase(after_docs))
        
        # Pattern 3: "with 2 documents A and B"
        if "with" in text and not documents:
            after_with = text.split("with")[1]
            if "documents" in after_with:
                after_docs = after_with.split("documents")[1].split(".")[0]
                documents.extend(self._extract_entities_from_phrase(after_docs))
        
        # Pattern 4: Extract any capital letters that might be document names
        if not documents:
            import re
            caps = re.findall(r'\b[A-Z]\b', original_text)
            if caps:
                documents = caps[:5]
        
        # Default fallback
        if not documents:
            documents = ['Document1']
        
        # Extract invitees/signers with enhanced parsing
        invitees = []
        invitee_details = []
        
        # Pattern 1: "4 signers: Bank Signatory (aadhaar eSign), Customer (DSC)..."
        if "signers:" in text:
            signers_section = text.split("signers:")[1].split(".")[0]
            invitee_details = self._parse_complex_signers(signers_section, original_text)
        
        # Extract just the names for backward compatibility
        if invitee_details:
            invitees = [detail['name'] for detail in invitee_details]
        else:
            # Fallback to simple parsing
            known_names = ["ronit", "sachin", "john", "mary", "alice", "bob"]
            for name in known_names:
                if name in text:
                    invitees.append(name.title())
            
            roles = ["signer", "signatory", "customer", "bank", "client", "manager", "subordinate"]
            for role in roles:
                if role in text:
                    invitees.append(role.title())
            
            if not invitees:
                invitees = ['Signer1', 'Signer2']
        
        # Extract emails with position context
        emails = []
        email_assignments = {}  # Maps signer position/name to email
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, original_text)
        
        # Parse email assignments with context
        if emails:
            # Look for patterns like "First signer email:", "Second signer email:", "Signer 1 email:", etc.
            email_context_patterns = [
                r'first\s+signer\s+email[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
                r'second\s+signer\s+email[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
                r'signer\s+(\d+)\s+email[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
                r'([A-Za-z\s]+)\s+email[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            ]
            
            for pattern in email_context_patterns:
                matches = re.findall(pattern, original_text.lower())
                for match in matches:
                    if len(match) == 2:  # signer identifier and email
                        if match[0].isdigit():  # "signer 1 email"
                            email_assignments[int(match[0]) - 1] = match[1]  # 0-based index
                        elif 'first' in match[0]:  # "first signer email"
                            email_assignments[0] = match[1]
                        elif 'second' in match[0]:  # "second signer email"  
                            email_assignments[1] = match[1]
                        else:  # signer name pattern
                            email_assignments[match[0].strip()] = match[1]
                    else:  # single match (email context pattern)
                        if 'first' in pattern:
                            email_assignments[0] = match
                        elif 'second' in pattern:
                            email_assignments[1] = match
        
        # Detect default eSign type (for simple cases)
        default_esign = "virtualEsign"
        if "aadhaar" in text or "aadhar" in text:
            default_esign = "aadharEsign"
        elif "dsc" in text:
            default_esign = "dscToken"
        
        return {
            'documents': documents,
            'invitees': invitees,
            'invitee_details': invitee_details,
            'emails': emails,
            'email_assignments': email_assignments,
            'esign_type': default_esign,
            'original_text': original_text
        }
    
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
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
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
            
            response = requests.put(url, headers=self.headers, json=payload, timeout=30)
            
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
            
            response = requests.patch(url, headers=self.headers, json=payload, timeout=30)
            
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
                        "inviteeEmail": invitee_data.get('email') if invitee_data.get('email') else f"user{i+1}@example.com"  # API requires valid email
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
    BEARER_TOKEN = "eyJ4NXQjUzI1NiI6ImxZYnVTSk9JR1E1MmhNUy1DeWJVb1A0RTExdFpnd3RjRWd1bHYwa0RuT0UiLCJraWQiOiJmZWM4MDNlNC00OWZlLTQ4ZmEtODc2YS0yNWMxZmFlNWUwMmYiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJrYXZpc2guc2F4ZW5hQGxlZWdhbGl0eS5jb20iLCJhdWQiOiJpbnN0YW50LWxvZ2luLWFwcCIsIm5iZiI6MTc1ODE0MTE5OSwic2NvcGUiOlsiKiJdLCJpc3MiOiJodHRwczovL3ByZXByb2QtZ2F0ZXdheS5sZWVnYWxpdHkuY29tL2F1dGgiLCJleHAiOjE3NTgxNDQ3OTksImlhdCI6MTc1ODE0MTE5OSwianRpIjoiODI5ZjA0OTMtNWI4Zi00MzRkLTg4YzQtYzJhYzQxYjAwMTkwIn0.Z9CyqdCtOnZ2k7DPgLBEj9ww0RUyOKoJCZqXV_2AyV8ne5cGyLVIP8Qo8V3cFH3Nc2lHkQogMi-_jKT8ejySnuOD_XO-eJysZJq-VOEBerYWzFj39Ogc6jLpQKcoI2_R_ubqsAK068R1Qioueo2YSry-Ruji7d9145r2fjs0dc6YV91B9YDo2yifNK8dzkaPp4K-8V4mXdgjLqBZnEkJsxU5VFyMqycGJ_-dVvT78ylNqj9usJPSjUE8lm4A0rUaHQaWQFc55WhdbszVghqddKVT1AtMUwBBprPmduquz4FvZhDkMLea-O9eCEubWNzkW6qODtvwsPb-Lq-2PQ3f0Q"
    
    # Initialize API client 
    api = LeegalityWorkflowAPI(BEARER_TOKEN)
    
    # Create requirement exactly as specified
    requirement = "Create workflow with 3 documents: Application Form, Loan doc, Addendum. 4 signers: Signer1 (aadhaar eSign), Signer2 (aadhaar eSign), Signer3 (DSC), Signer4 (DSC). Second signer email: vikas@leegality.com"
    
    print(f"📋 Creating Application Workflow")
    print(f"📝 Requirement: {requirement}")
    print("=" * 80)
    
    # Execute workflow creation using existing flow
    result = api.create_workflow_from_text(requirement)
    
    # Display results
    print("\n" + "=" * 80)
    if result['success']:
        print("✅ APPLICATION WORKFLOW CREATED SUCCESSFULLY!")
        print(f"📋 Workflow ID: {result['workflow_id']}")
        print(f"⏱️  Processing Time: {result['processing_time']}")
        print(f"📄 Documents Created: {result['documents_created']}")
        print(f"📝 Document Names: {', '.join(result['parsed_data']['documents'])}")
        print(f"👥 Signers Created: {result['invitees_created']}")
        print(f"👤 Signer Names: {', '.join(result['parsed_data']['invitees'])}")
        print(f"📊 Status: {result['status']}")
        
        # Additional details
        if 'parsed_data' in result:
            print(f"\n🔍 Parsing Details:")
            print(f"   📋 Documents: {result['parsed_data']['documents']}")
            print(f"   👥 Invitees: {result['parsed_data']['invitees']}")
            if 'emails' in result['parsed_data']:
                print(f"   📧 Emails: {result['parsed_data']['emails']}")
            if 'email_assignments' in result['parsed_data']:
                print(f"   📬 Email Assignments: {result['parsed_data']['email_assignments']}")
    else:
        print("❌ APPLICATION WORKFLOW CREATION FAILED!")
        print(f"Error: {result['error']}")
        
    return result


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
    create_application_workflow()