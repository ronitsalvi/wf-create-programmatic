// Workflow State Management
class WorkflowState {
    constructor() {
        this.documents = [
            { id: 'loan-agreement', name: 'Loan Agreement', configured: true },
            { id: 'sanction-letter', name: 'Sanction Letter', configured: true },
            { id: 'kfs', name: 'KFS', configured: true }
        ];
        this.people = [];
        this.settings = {
            sequentialSigning: false,
            allowUpload: false
        };
        this.pendingChanges = null;
    }

    addPerson(person) {
        const newPerson = {
            id: `person-${Date.now()}`,
            ...person
        };
        this.people.push(newPerson);
        this.updateUI();
        return newPerson;
    }

    removePerson(personId) {
        this.people = this.people.filter(p => p.id !== personId);
        this.updateUI();
    }

    updateUI() {
        this.updateStatusInfo();
        this.updatePeopleList();
        this.updatePeopleCount();
    }

    updateStatusInfo() {
        const statusElement = document.getElementById('current-status');
        const peopleCount = this.people.length;
        const docsCount = this.documents.length;
        statusElement.textContent = `${docsCount} documents, ${peopleCount} people`;
    }

    updatePeopleCount() {
        const countElement = document.getElementById('people-count');
        countElement.textContent = this.people.length;
    }

    updatePeopleList() {
        const listElement = document.getElementById('people-list');
        
        if (this.people.length === 0) {
            listElement.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-user-plus"></i>
                    <p>No people added yet</p>
                    <p class="empty-description">Add signers, reviewers, or other participants</p>
                </div>
            `;
        } else {
            listElement.innerHTML = this.people.map(person => `
                <div class="item-card person-card">
                    <div class="item-info">
                        <i class="fas fa-user"></i>
                        <div>
                            <span class="item-name">${person.name || 'Runtime Configuration'}</span>
                            <div class="person-role">${this.getRoleDisplayName(person.role)}</div>
                            ${person.email || person.esign ? `<div class="person-details">${[person.email, person.esign].filter(Boolean).join(' • ')}</div>` : ''}
                        </div>
                    </div>
                    <div class="item-actions">
                        <button class="action-btn edit-btn" onclick="editPerson('${person.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn delete-btn" onclick="workflowState.removePerson('${person.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        }
    }

    getRoleDisplayName(role) {
        const roleNames = {
            signer: 'Signer',
            reviewer: 'Reviewer',
            cc: 'CC',
            groupSigner: 'Group Signer'
        };
        return roleNames[role] || role;
    }

    getESignDisplayName(esign) {
        const esignNames = {
            aadhaar: 'Aadhaar eSign',
            dsc: 'DSC',
            virtual: 'Virtual eSign',
            none: 'No eSign'
        };
        return esignNames[esign] || esign;
    }
}

// Mock Natural Language Processing
class MockNLPProcessor {
    constructor() {
        this.patterns = [
            {
                pattern: /add\s+(\d+)\s+signer[s]?/i,
                handler: (match) => {
                    const count = parseInt(match[1]);
                    return {
                        type: 'add_people',
                        action: `Add ${count} signer${count > 1 ? 's' : ''}`,
                        people: Array(count).fill(null).map((_, i) => ({
                            role: 'signer',
                            name: '',
                            email: '',
                            esign: 'aadhaar'
                        }))
                    };
                }
            },
            {
                pattern: /add\s+(\d+)\s+reviewer[s]?/i,
                handler: (match) => {
                    const count = parseInt(match[1]);
                    return {
                        type: 'add_people',
                        action: `Add ${count} reviewer${count > 1 ? 's' : ''}`,
                        people: Array(count).fill(null).map((_, i) => ({
                            role: 'reviewer',
                            name: '',
                            email: '',
                            esign: ''
                        }))
                    };
                }
            },
            {
                pattern: /aadhaar\s+esign/i,
                handler: () => ({
                    type: 'set_esign',
                    action: 'Configure Aadhaar eSign for signers',
                    esign: 'aadhaar'
                })
            },
            {
                pattern: /dsc|digital\s+signature/i,
                handler: () => ({
                    type: 'set_esign',
                    action: 'Configure DSC (Digital Signature Certificate)',
                    esign: 'dsc'
                })
            },
            {
                pattern: /sequential\s+signing|signing\s+order/i,
                handler: () => ({
                    type: 'set_sequential',
                    action: 'Enable sequential signing order',
                    sequential: true
                })
            },
            {
                pattern: /group\s+signer/i,
                handler: () => ({
                    type: 'add_people',
                    action: 'Add group signer',
                    people: [{
                        role: 'groupSigner',
                        name: '',
                        email: '',
                        esign: ''
                    }]
                })
            }
        ];
    }

    process(text) {
        const results = [];
        const lowerText = text.toLowerCase();

        // Check for specific patterns
        for (const { pattern, handler } of this.patterns) {
            const match = text.match(pattern);
            if (match) {
                results.push(handler(match));
            }
        }

        // If no specific patterns found, provide generic suggestions
        if (results.length === 0) {
            if (lowerText.includes('signer') || lowerText.includes('sign')) {
                results.push({
                    type: 'add_people',
                    action: 'Add signer to workflow',
                    people: [{
                        role: 'signer',
                        name: '',
                        email: '',
                        esign: 'aadhaar'
                    }]
                });
            }
            
            if (lowerText.includes('reviewer') || lowerText.includes('review')) {
                results.push({
                    type: 'add_people',
                    action: 'Add reviewer to workflow',
                    people: [{
                        role: 'reviewer',
                        name: '',
                        email: '',
                        esign: ''
                    }]
                });
            }
        }

        return results;
    }

    generatePreview(results) {
        if (results.length === 0) {
            return '<p style="color: #6b7280;">No specific changes detected. Try being more specific about what you want to add or configure.</p>';
        }

        let preview = '<div style="space-y: 8px;">';
        results.forEach((result, index) => {
            preview += `
                <div style="padding: 8px 12px; background-color: #f0f9ff; border-left: 3px solid #0ea5e9; border-radius: 4px; margin-bottom: 8px;">
                    <div style="font-weight: 500; color: #0c4a6e; margin-bottom: 4px;">
                        ${result.action}
                    </div>
                    ${this.getResultDetails(result)}
                </div>
            `;
        });
        preview += '</div>';
        return preview;
    }

    getResultDetails(result) {
        switch (result.type) {
            case 'add_people':
                return `<div style="font-size: 12px; color: #475569;">
                    ${result.people.map(person => `
                        • ${workflowState.getRoleDisplayName(person.role)}${person.esign ? ` with ${workflowState.getESignDisplayName(person.esign)}` : ''}
                    `).join('')}
                </div>`;
            case 'set_esign':
                return `<div style="font-size: 12px; color: #475569;">
                    Will apply ${workflowState.getESignDisplayName(result.esign)} to existing signers
                </div>`;
            case 'set_sequential':
                return `<div style="font-size: 12px; color: #475569;">
                    Participants will sign in the order they were added
                </div>`;
            default:
                return '';
        }
    }
}

// Global instances
let workflowState = new WorkflowState();
let nlpProcessor = new MockNLPProcessor();
let currentEditingPerson = null;

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    workflowState.updateUI();
});

function initializeEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            switchTab(this.dataset.tab);
        });
    });

    // Natural Language tab events
    const nlpInput = document.getElementById('nlp-input');
    const previewBtn = document.getElementById('preview-changes');
    const applyBtn = document.getElementById('apply-changes');

    if (nlpInput) {
        nlpInput.addEventListener('input', debounce(handleNLPInput, 300));
    }

    if (previewBtn) {
        previewBtn.addEventListener('click', handlePreviewChanges);
    }

    if (applyBtn) {
        applyBtn.addEventListener('click', handleApplyChanges);
    }

    // Traditional Builder tab events
    const addPersonBtn = document.getElementById('add-person-btn');
    if (addPersonBtn) {
        addPersonBtn.addEventListener('click', openPersonModal);
    }

    // Suggestion chips
    document.querySelectorAll('.suggestion-chip').forEach(chip => {
        chip.addEventListener('click', function() {
            const currentText = nlpInput.value;
            const newText = currentText ? `${currentText} ${this.textContent}` : this.textContent;
            nlpInput.value = newText;
            handleNLPInput();
        });
    });

    // Modal events
    setupModalEvents();

    // Settings toggle events
    setupSettingsEvents();
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update tab panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `${tabName}-tab`);
    });
}

function handleNLPInput() {
    const input = document.getElementById('nlp-input');
    const text = input.value.trim();
    
    // Update suggestions based on input
    updateSmartSuggestions(text);
    
    // Clear any existing preview
    hidePreview();
}

function updateSmartSuggestions(text) {
    const suggestionsSection = document.getElementById('suggestions');
    const suggestionsList = suggestionsSection.querySelector('.suggestions-list');
    
    let suggestions = [];
    const lowerText = text.toLowerCase();
    
    if (!lowerText.includes('signer')) {
        suggestions.push('Add 2 signers with Aadhaar eSign');
    }
    
    if (!lowerText.includes('reviewer')) {
        suggestions.push('Add reviewer role');
    }
    
    if (!lowerText.includes('sequential') && !lowerText.includes('order')) {
        suggestions.push('Enable sequential signing');
    }
    
    if (!lowerText.includes('group')) {
        suggestions.push('Add group signer');
    }

    if (suggestions.length === 0) {
        suggestions = ['Configure document stamping', 'Set up notifications', 'Add CC participants'];
    }

    suggestionsList.innerHTML = suggestions.map(suggestion => 
        `<button class="suggestion-chip" onclick="addSuggestionToInput('${suggestion}')">${suggestion}</button>`
    ).join('');
}

function addSuggestionToInput(suggestion) {
    const input = document.getElementById('nlp-input');
    const currentText = input.value.trim();
    const newText = currentText ? `${currentText}. ${suggestion}` : suggestion;
    input.value = newText;
    handleNLPInput();
}

function handlePreviewChanges() {
    const input = document.getElementById('nlp-input');
    const text = input.value.trim();
    
    if (!text) {
        alert('Please enter some workflow changes to preview.');
        return;
    }

    // Show loading state
    const previewBtn = document.getElementById('preview-changes');
    previewBtn.classList.add('loading');
    
    // Simulate processing delay
    setTimeout(() => {
        const results = nlpProcessor.process(text);
        const preview = nlpProcessor.generatePreview(results);
        
        showPreview(preview);
        workflowState.pendingChanges = results;
        
        previewBtn.classList.remove('loading');
    }, 800);
}

function handleApplyChanges() {
    if (!workflowState.pendingChanges || workflowState.pendingChanges.length === 0) {
        alert('Please preview changes first.');
        return;
    }

    const applyBtn = document.getElementById('apply-changes');
    applyBtn.classList.add('loading');

    // Simulate processing delay
    setTimeout(() => {
        // Apply the pending changes
        workflowState.pendingChanges.forEach(change => {
            applyChange(change);
        });

        // Clear pending changes and input
        workflowState.pendingChanges = null;
        document.getElementById('nlp-input').value = '';
        hidePreview();

        applyBtn.classList.remove('loading');

        // Show success message
        showSuccessMessage('Changes applied successfully!');

    }, 1200);
}

function applyChange(change) {
    switch (change.type) {
        case 'add_people':
            change.people.forEach(person => {
                workflowState.addPerson(person);
            });
            break;
        case 'set_sequential':
            workflowState.settings.sequentialSigning = true;
            document.getElementById('sequential-signing').checked = true;
            break;
        case 'set_esign':
            // Update existing signers with new eSign type
            workflowState.people.forEach(person => {
                if (person.role === 'signer' && !person.esign) {
                    person.esign = change.esign;
                }
            });
            workflowState.updateUI();
            break;
    }
}

function showPreview(content) {
    const previewSection = document.getElementById('preview-section');
    const previewContent = document.getElementById('preview-content');
    
    previewContent.innerHTML = content;
    previewSection.style.display = 'block';
    
    // Scroll to preview
    previewSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hidePreview() {
    const previewSection = document.getElementById('preview-section');
    previewSection.style.display = 'none';
}

function showSuccessMessage(message) {
    // Create a temporary success message
    const successDiv = document.createElement('div');
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #10b981;
        color: white;
        padding: 12px 20px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1001;
        animation: slideIn 0.3s ease-out;
    `;
    successDiv.innerHTML = `<i class="fas fa-check-circle" style="margin-right: 8px;"></i>${message}`;
    
    document.body.appendChild(successDiv);
    
    setTimeout(() => {
        successDiv.remove();
    }, 3000);
}

// Person Modal Functions
function setupModalEvents() {
    const modal = document.getElementById('person-modal');
    const closeBtn = modal.querySelector('.modal-close');
    const cancelBtn = document.getElementById('cancel-person');
    const saveBtn = document.getElementById('save-person');

    closeBtn.addEventListener('click', closePersonModal);
    cancelBtn.addEventListener('click', closePersonModal);
    saveBtn.addEventListener('click', savePersonFromModal);

    // Close on outside click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closePersonModal();
        }
    });
}

function openPersonModal(person = null) {
    const modal = document.getElementById('person-modal');
    currentEditingPerson = person;

    // Populate form if editing
    if (person) {
        document.getElementById('person-role').value = person.role || 'signer';
        document.getElementById('person-name').value = person.name || '';
        document.getElementById('person-email').value = person.email || '';
        document.getElementById('person-esign').value = person.esign || '';
        modal.querySelector('h3').textContent = 'Edit Person';
    } else {
        // Reset form for new person
        document.getElementById('person-role').value = 'signer';
        document.getElementById('person-name').value = '';
        document.getElementById('person-email').value = '';
        document.getElementById('person-esign').value = '';
        modal.querySelector('h3').textContent = 'Add Person';
    }

    modal.classList.add('active');
}

function closePersonModal() {
    const modal = document.getElementById('person-modal');
    modal.classList.remove('active');
    currentEditingPerson = null;
}

function savePersonFromModal() {
    const role = document.getElementById('person-role').value;
    const name = document.getElementById('person-name').value.trim();
    const email = document.getElementById('person-email').value.trim();
    const esign = document.getElementById('person-esign').value;

    const personData = {
        role,
        name: name || undefined,
        email: email || undefined,
        esign: esign || undefined
    };

    if (currentEditingPerson) {
        // Update existing person
        Object.assign(currentEditingPerson, personData);
        workflowState.updateUI();
    } else {
        // Add new person
        workflowState.addPerson(personData);
    }

    closePersonModal();
}

function editPerson(personId) {
    const person = workflowState.people.find(p => p.id === personId);
    if (person) {
        openPersonModal(person);
    }
}

// Settings Events
function setupSettingsEvents() {
    const sequentialToggle = document.getElementById('sequential-signing');
    const uploadToggle = document.getElementById('allow-upload');

    if (sequentialToggle) {
        sequentialToggle.addEventListener('change', function() {
            workflowState.settings.sequentialSigning = this.checked;
        });
    }

    if (uploadToggle) {
        uploadToggle.addEventListener('change', function() {
            workflowState.settings.allowUpload = this.checked;
        });
    }
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Document Tab Switching (for the main interface)
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.document-tabs .tab').forEach(tab => {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs
            document.querySelectorAll('.document-tabs .tab').forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Update document name in form
            const docName = this.textContent;
            const docNameInput = document.getElementById('document-name');
            if (docNameInput) {
                docNameInput.value = docName;
            }
        });
    });
});

// Export for global access
window.workflowState = workflowState;
window.openPersonModal = openPersonModal;
window.editPerson = editPerson;