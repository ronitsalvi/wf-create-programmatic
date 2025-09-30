// Visual Workflow Builder JavaScript
class WorkflowBuilder {
    constructor() {
        this.state = {
            nodes: new Map(),
            connections: new Map(),
            selectedNode: null,
            draggedNode: null,
            zoom: 1,
            pan: { x: 0, y: 0 },
            nextNodeId: 1,
            history: [],
            historyIndex: -1,
            pendingClarification: null
        };

        this.svg = null;
        this.nodesGroup = null;
        this.connectionsGroup = null;
        
        this.init();
    }

    init() {
        this.setupSVG();
        this.setupEventListeners();
        this.showBootstrapOverlay();
    }

    setupSVG() {
        this.svg = document.getElementById('graph-svg');
        this.nodesGroup = document.getElementById('nodes');
        this.connectionsGroup = document.getElementById('connections');
        
        // Setup zoom and pan
        this.svg.addEventListener('wheel', this.handleZoom.bind(this));
        this.svg.addEventListener('mousedown', this.handleCanvasMouseDown.bind(this));
        this.svg.addEventListener('mousemove', this.handleCanvasMouseMove.bind(this));
        this.svg.addEventListener('mouseup', this.handleCanvasMouseUp.bind(this));
    }

    setupEventListeners() {
        // Bootstrap overlay events
        this.setupBootstrapEvents();
        
        // Header events
        document.getElementById('restart-btn').addEventListener('click', () => this.restart());
        document.getElementById('undo-btn').addEventListener('click', () => this.undo());
        document.getElementById('redo-btn').addEventListener('click', () => this.redo());
        document.getElementById('publish-btn').addEventListener('click', () => this.publish());
        
        // Graph control events
        document.getElementById('zoom-in').addEventListener('click', () => this.zoomIn());
        document.getElementById('zoom-out').addEventListener('click', () => this.zoomOut());
        document.getElementById('fit-to-screen').addEventListener('click', () => this.fitToScreen());
        document.getElementById('toggle-palette').addEventListener('click', () => this.togglePalette());
        
        // Natural language events
        document.getElementById('process-nl').addEventListener('click', () => this.processNaturalLanguage());
        document.getElementById('nl-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                this.processNaturalLanguage();
            }
        });
        
        // Quick command events
        document.querySelectorAll('.command-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const command = e.target.dataset.command;
                document.getElementById('nl-input').value = command;
                this.processNaturalLanguage();
            });
        });
        
        // Palette events
        this.setupPaletteEvents();
        
        // Clarification events
        this.setupClarificationEvents();
        
        // Example events
        document.getElementById('show-examples').addEventListener('click', () => this.showExamples());
        this.setupExampleEvents();
        
        // Modal events
        this.setupModalEvents();
    }

    setupBootstrapEvents() {
        const overlay = document.getElementById('bootstrap-overlay');
        const closeOverlay = document.getElementById('close-overlay');
        const needStamping = document.getElementById('need-stamping');
        const stampingDetails = document.getElementById('stamping-details');
        const nextToStep2 = document.getElementById('next-to-step-2');
        const backToStep1 = document.getElementById('back-to-step-1');
        const createWorkflow = document.getElementById('create-workflow');

        closeOverlay.addEventListener('click', () => this.hideBootstrapOverlay());

        needStamping.addEventListener('change', (e) => {
            stampingDetails.style.display = e.target.checked ? 'block' : 'none';
        });

        nextToStep2.addEventListener('click', () => {
            document.getElementById('step-1').classList.remove('active');
            document.getElementById('step-2').classList.add('active');
        });

        backToStep1.addEventListener('click', () => {
            document.getElementById('step-2').classList.remove('active');
            document.getElementById('step-1').classList.add('active');
        });

        createWorkflow.addEventListener('click', () => this.processBootstrapData());
    }

    setupPaletteEvents() {
        const paletteItems = document.querySelectorAll('.palette-item');
        paletteItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', item.dataset.type);
            });
            item.addEventListener('click', () => {
                this.createNodeFromPalette(item.dataset.type);
            });
        });
    }

    setupClarificationEvents() {
        document.getElementById('skip-clarification').addEventListener('click', () => {
            this.skipClarification();
        });
        
        document.getElementById('cancel-clarification').addEventListener('click', () => {
            this.cancelClarification();
        });
        
        document.getElementById('apply-clarification').addEventListener('click', () => {
            this.applyClarification();
        });
    }

    setupExampleEvents() {
        document.querySelectorAll('.example-card').forEach(card => {
            card.addEventListener('click', () => {
                this.loadExample(card.dataset.example);
                this.hideModal('examples-modal');
            });
        });
    }

    setupModalEvents() {
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                this.hideModal(modal.id);
            });
        });

        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideModal(modal.id);
                }
            });
        });
    }

    // Bootstrap Overlay Methods
    showBootstrapOverlay() {
        document.getElementById('bootstrap-overlay').classList.add('active');
    }

    hideBootstrapOverlay() {
        document.getElementById('bootstrap-overlay').classList.remove('active');
        document.getElementById('graph-empty-state').style.display = 'block';
    }

    processBootstrapData() {
        const docCount = parseInt(document.getElementById('doc-count').value);
        const docNames = document.getElementById('doc-names').value;
        const needStamping = document.getElementById('need-stamping').checked;
        const peopleCount = parseInt(document.getElementById('people-count').value);
        const peopleDetails = document.getElementById('people-details').value;

        // Create documents
        const documents = this.parseDocumentNames(docNames, docCount);
        documents.forEach((doc, index) => {
            this.createNode('document', {
                name: doc,
                x: 200 + (index * 180),
                y: 200,
                configured: doc !== 'Document ' + (index + 1)
            });
        });

        // Create stamps if needed
        if (needStamping) {
            const jurisdiction = document.getElementById('stamp-jurisdiction').value;
            const denomination = document.getElementById('stamp-denomination').value;
            const placement = document.querySelector('input[name="stamp-placement"]:checked').value;

            const stampId = this.createNode('stamp', {
                name: `${this.capitalizeFirst(jurisdiction)} ₹${denomination}`,
                jurisdiction: jurisdiction,
                denomination: denomination,
                placement: placement,
                x: 100,
                y: 100,
                configured: true
            });

            // Connect stamp to first document if documents exist
            if (documents.length > 0) {
                const firstDocId = Array.from(this.state.nodes.keys())[0];
                this.createConnection(stampId, firstDocId);
            }
        }

        // Create people
        const people = this.parsePeopleDetails(peopleDetails, peopleCount);
        people.forEach((person, index) => {
            this.createNode('invitee', {
                name: person.name || `Person ${index + 1}`,
                role: person.role || 'signer',
                email: person.email || '',
                esign: person.esign || 'aadhaar',
                x: 600 + (index * 150),
                y: 200,
                configured: person.name !== undefined
            });
        });

        this.hideBootstrapOverlay();
        this.updateEmptyState();
        this.updateNaturalLanguageSummary();
        this.addToHistory('Bootstrap workflow created');
        this.addToDiff('Created workflow from bootstrap', 'added');
    }

    parseDocumentNames(docNames, count) {
        if (!docNames.trim()) {
            return Array.from({length: count}, (_, i) => `Document ${i + 1}`);
        }
        
        const names = docNames.split(',').map(name => name.trim()).filter(name => name);
        while (names.length < count) {
            names.push(`Document ${names.length + 1}`);
        }
        return names.slice(0, count);
    }

    parsePeopleDetails(peopleDetails, count) {
        const people = [];
        
        if (!peopleDetails.trim()) {
            return Array.from({length: count}, () => ({}));
        }

        const entries = peopleDetails.split(',').map(entry => entry.trim());
        
        entries.forEach(entry => {
            const person = {};
            
            // Extract name (everything before first parenthesis)
            const nameMatch = entry.match(/^([^(]+)/);
            if (nameMatch) {
                person.name = nameMatch[1].trim();
            }
            
            // Extract role
            const roleMatch = entry.match(/\((signer|reviewer|cc|group signer)/i);
            if (roleMatch) {
                person.role = roleMatch[1].toLowerCase().replace(' ', '');
            }
            
            // Extract email
            const emailMatch = entry.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
            if (emailMatch) {
                person.email = emailMatch[1];
            }
            
            // Extract eSign type
            const esignMatch = entry.match(/(aadhaar|dsc|virtual)/i);
            if (esignMatch) {
                person.esign = esignMatch[1].toLowerCase();
            }
            
            people.push(person);
        });

        while (people.length < count) {
            people.push({});
        }
        
        return people.slice(0, count);
    }

    // Node Management
    createNode(type, config = {}) {
        const nodeId = `node-${this.state.nextNodeId++}`;
        const node = {
            id: nodeId,
            type: type,
            x: config.x || this.getRandomPosition().x,
            y: config.y || this.getRandomPosition().y,
            name: config.name || this.getDefaultName(type),
            configured: config.configured !== false,
            ...config
        };

        this.state.nodes.set(nodeId, node);
        this.renderNode(node);
        this.updateEmptyState();
        
        return nodeId;
    }

    renderNode(node) {
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('class', `workflow-node ${node.type}-node`);
        group.setAttribute('data-node-id', node.id);
        group.setAttribute('transform', `translate(${node.x}, ${node.y})`);

        const shape = this.createNodeShape(node);
        const text = this.createNodeText(node);
        const badge = this.createNodeBadge(node);

        group.appendChild(shape);
        group.appendChild(text);
        if (badge) {
            group.appendChild(badge);
        }

        // Add event listeners
        group.addEventListener('mousedown', (e) => this.handleNodeMouseDown(e, node.id));
        group.addEventListener('click', (e) => this.handleNodeClick(e, node.id));
        group.addEventListener('dblclick', (e) => this.handleNodeDoubleClick(e, node.id));

        this.nodesGroup.appendChild(group);
    }

    createNodeShape(node) {
        const shape = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        
        let width = 120;
        let height = 60;
        
        if (node.type === 'invitee') {
            shape.setAttribute('rx', '25');
            shape.setAttribute('ry', '25');
            width = 140;
            height = 50;
        } else {
            shape.setAttribute('rx', '8');
            shape.setAttribute('ry', '8');
        }

        shape.setAttribute('width', width);
        shape.setAttribute('height', height);
        shape.setAttribute('x', -width/2);
        shape.setAttribute('y', -height/2);

        // Apply styling based on node type and configuration
        const classList = [node.type + '-node'];
        if (node.configured) {
            classList.push('configured');
        } else {
            classList.push('runtime-config');
        }
        
        if (node.type === 'invitee' && node.role) {
            classList.push(node.role);
        }

        shape.setAttribute('class', classList.join(' '));
        
        return shape;
    }

    createNodeText(node) {
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('class', 'node-text');
        text.setAttribute('y', '0');
        
        // Truncate long names
        let displayName = node.name;
        if (displayName.length > 15) {
            displayName = displayName.substring(0, 12) + '...';
        }
        
        text.textContent = displayName;
        return text;
    }

    createNodeBadge(node) {
        if (!this.shouldShowBadge(node)) return null;

        const badgeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        badgeGroup.setAttribute('transform', 'translate(45, -20)');

        const badgeRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        badgeRect.setAttribute('class', 'node-badge');
        badgeRect.setAttribute('width', '60');
        badgeRect.setAttribute('height', '16');
        badgeRect.setAttribute('rx', '8');
        badgeRect.setAttribute('x', '-30');
        badgeRect.setAttribute('y', '-8');

        const badgeText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        badgeText.setAttribute('class', 'badge-text');
        badgeText.textContent = this.getBadgeText(node);

        badgeGroup.appendChild(badgeRect);
        badgeGroup.appendChild(badgeText);

        return badgeGroup;
    }

    shouldShowBadge(node) {
        return node.type === 'invitee' && node.esign && node.esign !== 'none';
    }

    getBadgeText(node) {
        const esignMap = {
            'aadhaar': 'Aadhaar',
            'dsc': 'DSC',
            'virtual': 'Virtual'
        };
        return esignMap[node.esign] || node.esign;
    }

    getDefaultName(type) {
        const defaults = {
            document: 'Document',
            stamp: 'Stamp',
            invitee: 'Person',
            stage: 'Stage'
        };
        return defaults[type] || 'Node';
    }

    getRandomPosition() {
        const bounds = this.svg.getBoundingClientRect();
        return {
            x: Math.random() * (bounds.width - 200) + 100,
            y: Math.random() * (bounds.height - 200) + 100
        };
    }

    // Natural Language Processing
    processNaturalLanguage() {
        const input = document.getElementById('nl-input').value.trim();
        if (!input) return;

        this.setNLStatus('processing');
        
        // Simulate processing delay
        setTimeout(() => {
            const commands = this.parseNaturalLanguage(input);
            
            if (commands.length === 0) {
                this.setNLStatus('ready');
                this.showNotification('Could not understand the command. Try being more specific.', 'warning');
                return;
            }

            this.executeCommands(commands);
            this.setNLStatus('ready');
            
            // Clear input after successful processing
            document.getElementById('nl-input').value = '';
        }, 1000);
    }

    parseNaturalLanguage(text) {
        const commands = [];
        const lowerText = text.toLowerCase();

        // Document commands
        const docMatch = text.match(/add\s+(\d+)\s+documents?:?\s*([^.]*)/i);
        if (docMatch) {
            const count = parseInt(docMatch[1]);
            const names = docMatch[2] ? docMatch[2].split(',').map(n => n.trim()).filter(n => n) : [];
            commands.push({
                type: 'add_documents',
                count: count,
                names: names,
                needsClarification: false
            });
        }

        // Stamp commands
        const stampMatch = text.match(/add\s+(delhi|maharashtra|karnataka)?\s*₹?(\d+)\s*stamp/i);
        if (stampMatch) {
            const jurisdiction = stampMatch[1];
            const denomination = stampMatch[2];
            commands.push({
                type: 'add_stamp',
                jurisdiction: jurisdiction,
                denomination: denomination,
                needsClarification: !jurisdiction,
                targetDocument: null
            });
        }

        // Invitee/Signer commands
        const signerMatch = text.match(/add\s+signer\s+(\w+)(?:\s+with\s+(aadhaar|dsc|virtual))?/i);
        if (signerMatch) {
            commands.push({
                type: 'add_invitee',
                role: 'signer',
                name: signerMatch[1],
                esign: signerMatch[2] || null,
                needsClarification: !signerMatch[2]
            });
        }

        const reviewerMatch = text.match(/add\s+reviewer\s+(\w+)/i);
        if (reviewerMatch) {
            commands.push({
                type: 'add_invitee',
                role: 'reviewer',
                name: reviewerMatch[1],
                needsClarification: false
            });
        }

        // Stage commands
        const stageMatch = text.match(/create\s+stage\s+(\d+)/i);
        if (stageMatch) {
            commands.push({
                type: 'create_stage',
                stageNumber: parseInt(stageMatch[1]),
                needsClarification: false
            });
        }

        // Connection commands
        const linkMatch = text.match(/link\s+(\w+)\s+to\s+([\w\s,]+)/i);
        if (linkMatch) {
            const sourceName = linkMatch[1];
            const targets = linkMatch[2].split(',').map(t => t.trim());
            commands.push({
                type: 'create_connections',
                source: sourceName,
                targets: targets,
                needsClarification: false
            });
        }

        return commands;
    }

    executeCommands(commands) {
        for (const command of commands) {
            if (command.needsClarification) {
                this.showClarificationPanel(command);
                return; // Stop execution until clarification is provided
            } else {
                this.executeCommand(command);
            }
        }
        
        this.updateNaturalLanguageSummary();
        this.addToHistory(`Executed: ${commands.map(c => c.type).join(', ')}`);
    }

    executeCommand(command) {
        switch (command.type) {
            case 'add_documents':
                this.executeAddDocuments(command);
                break;
            case 'add_stamp':
                this.executeAddStamp(command);
                break;
            case 'add_invitee':
                this.executeAddInvitee(command);
                break;
            case 'create_stage':
                this.executeCreateStage(command);
                break;
            case 'create_connections':
                this.executeCreateConnections(command);
                break;
        }
    }

    executeAddDocuments(command) {
        const startX = 200;
        const startY = 200;
        const spacing = 180;

        for (let i = 0; i < command.count; i++) {
            const name = command.names[i] || `Document ${i + 1}`;
            const nodeId = this.createNode('document', {
                name: name,
                x: startX + (i * spacing),
                y: startY,
                configured: command.names[i] !== undefined
            });
            
            this.addToDiff(`Added document: ${name}`, 'added');
        }
    }

    executeAddStamp(command) {
        const name = command.jurisdiction ? 
            `${this.capitalizeFirst(command.jurisdiction)} ₹${command.denomination}` :
            `₹${command.denomination} Stamp`;

        const nodeId = this.createNode('stamp', {
            name: name,
            jurisdiction: command.jurisdiction,
            denomination: command.denomination,
            configured: command.jurisdiction !== undefined
        });

        this.addToDiff(`Added stamp: ${name}`, 'added');
    }

    executeAddInvitee(command) {
        const nodeId = this.createNode('invitee', {
            name: command.name,
            role: command.role,
            esign: command.esign,
            configured: command.name !== undefined && command.esign !== undefined
        });

        this.addToDiff(`Added ${command.role}: ${command.name}`, 'added');
    }

    executeCreateStage(command) {
        const nodeId = this.createNode('stage', {
            name: `Stage ${command.stageNumber}`,
            stageNumber: command.stageNumber
        });

        this.addToDiff(`Created Stage ${command.stageNumber}`, 'added');
    }

    executeCreateConnections(command) {
        const sourceNode = this.findNodeByName(command.source);
        if (!sourceNode) return;

        command.targets.forEach(targetName => {
            const targetNode = this.findNodeByName(targetName);
            if (targetNode) {
                this.createConnection(sourceNode.id, targetNode.id);
                this.addToDiff(`Linked ${command.source} to ${targetName}`, 'added');
            }
        });
    }

    // Clarification System
    showClarificationPanel(command) {
        this.state.pendingClarification = command;
        const panel = document.getElementById('clarification-panel');
        const content = document.getElementById('clarification-content');
        
        content.innerHTML = this.generateClarificationContent(command);
        panel.style.display = 'block';
        
        // Scroll to clarification panel
        panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    generateClarificationContent(command) {
        switch (command.type) {
            case 'add_stamp':
                return `
                    <div class="form-group">
                        <label>Which state's stamp paper?</label>
                        <select id="clarify-jurisdiction" class="select-input">
                            <option value="delhi">Delhi</option>
                            <option value="maharashtra">Maharashtra</option>
                            <option value="karnataka">Karnataka</option>
                            <option value="tamil-nadu">Tamil Nadu</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Which document should this stamp be attached to?</label>
                        <select id="clarify-target-doc" class="select-input">
                            <option value="">Configure at runtime</option>
                            ${this.getDocumentOptions()}
                        </select>
                    </div>
                `;
            case 'add_invitee':
                return `
                    <div class="form-group">
                        <label>eSign type for ${command.name}:</label>
                        <select id="clarify-esign" class="select-input">
                            <option value="aadhaar">Aadhaar eSign</option>
                            <option value="dsc">DSC (Digital Certificate)</option>
                            <option value="virtual">Virtual eSign</option>
                            <option value="">Configure at runtime</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Email (optional):</label>
                        <input type="email" id="clarify-email" class="form-input" placeholder="Leave empty for runtime">
                    </div>
                `;
            default:
                return '<p>Additional configuration needed.</p>';
        }
    }

    getDocumentOptions() {
        const documentNodes = Array.from(this.state.nodes.values()).filter(node => node.type === 'document');
        return documentNodes.map(node => `<option value="${node.id}">${node.name}</option>`).join('');
    }

    applyClarification() {
        if (!this.state.pendingClarification) return;

        const command = this.state.pendingClarification;
        
        // Update command with clarification data
        switch (command.type) {
            case 'add_stamp':
                command.jurisdiction = document.getElementById('clarify-jurisdiction').value;
                const targetDocId = document.getElementById('clarify-target-doc').value;
                command.targetDocument = targetDocId || null;
                break;
            case 'add_invitee':
                command.esign = document.getElementById('clarify-esign').value || null;
                command.email = document.getElementById('clarify-email').value || null;
                break;
        }

        // Execute the clarified command
        this.executeCommand(command);
        
        // Create connection if target document was specified
        if (command.type === 'add_stamp' && command.targetDocument) {
            const stampNodes = Array.from(this.state.nodes.values()).filter(node => node.type === 'stamp');
            const latestStamp = stampNodes[stampNodes.length - 1];
            if (latestStamp) {
                this.createConnection(latestStamp.id, command.targetDocument);
            }
        }

        this.hideClarificationPanel();
        this.updateNaturalLanguageSummary();
        this.addToHistory('Applied clarification');
    }

    skipClarification() {
        if (!this.state.pendingClarification) return;

        const command = this.state.pendingClarification;
        
        // Execute command with runtime configuration
        this.executeCommand(command);
        this.hideClarificationPanel();
        this.updateNaturalLanguageSummary();
        this.addToHistory('Skipped clarification - runtime config');
    }

    cancelClarification() {
        this.hideClarificationPanel();
    }

    hideClarificationPanel() {
        document.getElementById('clarification-panel').style.display = 'none';
        this.state.pendingClarification = null;
    }

    // Connection Management
    createConnection(sourceId, targetId) {
        const connectionId = `${sourceId}-${targetId}`;
        if (this.state.connections.has(connectionId)) return;

        const connection = {
            id: connectionId,
            source: sourceId,
            target: targetId
        };

        this.state.connections.set(connectionId, connection);
        this.renderConnection(connection);
    }

    renderConnection(connection) {
        const sourceNode = this.state.nodes.get(connection.source);
        const targetNode = this.state.nodes.get(connection.target);
        
        if (!sourceNode || !targetNode) return;

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('class', 'connection-line');
        line.setAttribute('data-connection-id', connection.id);
        line.setAttribute('x1', sourceNode.x);
        line.setAttribute('y1', sourceNode.y);
        line.setAttribute('x2', targetNode.x);
        line.setAttribute('y2', targetNode.y);

        this.connectionsGroup.appendChild(line);
    }

    updateConnections() {
        // Update all connection positions
        this.state.connections.forEach(connection => {
            const sourceNode = this.state.nodes.get(connection.source);
            const targetNode = this.state.nodes.get(connection.target);
            const line = document.querySelector(`[data-connection-id="${connection.id}"]`);
            
            if (sourceNode && targetNode && line) {
                line.setAttribute('x1', sourceNode.x);
                line.setAttribute('y1', sourceNode.y);
                line.setAttribute('x2', targetNode.x);
                line.setAttribute('y2', targetNode.y);
            }
        });
    }

    // Natural Language Summary
    updateNaturalLanguageSummary() {
        const summary = this.generateNaturalLanguageSummary();
        const summaryElement = document.getElementById('nl-summary');
        
        if (summary.trim()) {
            summaryElement.innerHTML = `<div class="summary-content">${summary}</div>`;
        } else {
            summaryElement.innerHTML = `
                <div class="summary-placeholder">
                    <i class="fas fa-file-alt"></i>
                    <p>Your workflow summary will appear here as you add elements</p>
                </div>
            `;
        }
    }

    generateNaturalLanguageSummary() {
        if (this.state.nodes.size === 0) return '';

        const documents = Array.from(this.state.nodes.values()).filter(node => node.type === 'document');
        const stamps = Array.from(this.state.nodes.values()).filter(node => node.type === 'stamp');
        const invitees = Array.from(this.state.nodes.values()).filter(node => node.type === 'invitee');
        const stages = Array.from(this.state.nodes.values()).filter(node => node.type === 'stage');

        let summary = '<h5>Workflow Summary</h5>';

        // Documents
        if (documents.length > 0) {
            summary += `<p><strong>Documents (${documents.length}):</strong></p><ul>`;
            documents.forEach(doc => {
                const configStatus = doc.configured ? 'pre-configured' : 'runtime configurable';
                summary += `<li>${doc.name} (${configStatus})</li>`;
            });
            summary += '</ul>';
        }

        // Stamps
        if (stamps.length > 0) {
            summary += `<p><strong>Stamps (${stamps.length}):</strong></p><ul>`;
            stamps.forEach(stamp => {
                const configStatus = stamp.configured ? 'pre-configured' : 'runtime configurable';
                summary += `<li>${stamp.name} (${configStatus})</li>`;
            });
            summary += '</ul>';
        }

        // Invitees
        if (invitees.length > 0) {
            summary += `<p><strong>People (${invitees.length}):</strong></p><ul>`;
            invitees.forEach(invitee => {
                let description = `${invitee.name || 'Unnamed'} (${this.capitalizeFirst(invitee.role || 'signer')})`;
                if (invitee.esign) {
                    description += ` with ${this.capitalizeFirst(invitee.esign)} eSign`;
                }
                const configStatus = invitee.configured ? 'pre-configured' : 'runtime configurable';
                summary += `<li>${description} (${configStatus})</li>`;
            });
            summary += '</ul>';
        }

        // Connections
        if (this.state.connections.size > 0) {
            summary += `<p><strong>Connections:</strong></p><ul>`;
            this.state.connections.forEach(connection => {
                const sourceNode = this.state.nodes.get(connection.source);
                const targetNode = this.state.nodes.get(connection.target);
                if (sourceNode && targetNode) {
                    summary += `<li>${sourceNode.name} → ${targetNode.name}</li>`;
                }
            });
            summary += '</ul>';
        }

        return summary;
    }

    // Utility Methods
    findNodeByName(name) {
        return Array.from(this.state.nodes.values()).find(node => 
            node.name.toLowerCase().includes(name.toLowerCase())
        );
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    setNLStatus(status) {
        const statusElement = document.getElementById('nl-status');
        const indicator = statusElement.querySelector('.status-indicator');
        const text = statusElement.querySelector('span:last-child');

        indicator.className = `status-indicator ${status}`;
        
        const statusTexts = {
            ready: 'Ready',
            processing: 'Processing...',
            error: 'Error'
        };
        
        text.textContent = statusTexts[status] || status;
    }

    showNotification(message, type = 'info') {
        // Create a simple notification (you can enhance this)
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#10b981'};
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            z-index: 10000;
            animation: slideInRight 0.3s ease-out;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    updateEmptyState() {
        const emptyState = document.getElementById('graph-empty-state');
        if (this.state.nodes.size === 0) {
            emptyState.style.display = 'block';
        } else {
            emptyState.style.display = 'none';
        }
    }

    // Event Handlers
    handleNodeMouseDown(e, nodeId) {
        e.stopPropagation();
        this.state.draggedNode = nodeId;
        this.state.selectedNode = nodeId;
        
        // Update visual selection
        document.querySelectorAll('.workflow-node').forEach(node => {
            node.classList.remove('selected');
        });
        document.querySelector(`[data-node-id="${nodeId}"]`).classList.add('selected');
    }

    handleNodeClick(e, nodeId) {
        e.stopPropagation();
        // Node click handled by mousedown
    }

    handleNodeDoubleClick(e, nodeId) {
        e.stopPropagation();
        this.showNodeProperties(nodeId);
    }

    handleCanvasMouseDown(e) {
        if (e.target === this.svg || e.target.tagName === 'rect' && e.target.getAttribute('fill') === 'url(#grid)') {
            this.state.selectedNode = null;
            document.querySelectorAll('.workflow-node').forEach(node => {
                node.classList.remove('selected');
            });
        }
    }

    handleCanvasMouseMove(e) {
        if (this.state.draggedNode) {
            const rect = this.svg.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const node = this.state.nodes.get(this.state.draggedNode);
            if (node) {
                node.x = x;
                node.y = y;
                
                const nodeElement = document.querySelector(`[data-node-id="${this.state.draggedNode}"]`);
                nodeElement.setAttribute('transform', `translate(${x}, ${y})`);
                
                this.updateConnections();
            }
        }
    }

    handleCanvasMouseUp(e) {
        this.state.draggedNode = null;
    }

    handleZoom(e) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        this.zoom(delta);
    }

    // Graph Control Methods
    zoom(factor) {
        this.state.zoom *= factor;
        this.state.zoom = Math.max(0.1, Math.min(3, this.state.zoom));
        this.updateZoomDisplay();
    }

    zoomIn() {
        this.zoom(1.2);
    }

    zoomOut() {
        this.zoom(0.8);
    }

    fitToScreen() {
        this.state.zoom = 1;
        this.updateZoomDisplay();
    }

    updateZoomDisplay() {
        document.getElementById('zoom-level').textContent = Math.round(this.state.zoom * 100) + '%';
        // Apply zoom transform (simplified - you'd want proper zoom with pan)
    }

    togglePalette() {
        const palette = document.getElementById('node-palette');
        const toggleBtn = document.getElementById('toggle-palette');
        
        palette.classList.toggle('hidden');
        toggleBtn.classList.toggle('active');
    }

    // Example Workflows
    showExamples() {
        this.showModal('examples-modal');
    }

    loadExample(exampleType) {
        this.clearWorkflow();
        
        switch (exampleType) {
            case 'bank-loan':
                this.loadBankLoanExample();
                break;
            case 'simple-contract':
                this.loadSimpleContractExample();
                break;
            case 'employee-onboarding':
                this.loadEmployeeOnboardingExample();
                break;
        }
        
        this.updateNaturalLanguageSummary();
        this.addToHistory(`Loaded example: ${exampleType}`);
    }

    loadBankLoanExample() {
        // Documents
        const loanAgreement = this.createNode('document', { name: 'Loan Agreement', x: 200, y: 200 });
        const sanctionLetter = this.createNode('document', { name: 'Sanction Letter', x: 200, y: 300 });
        const bankGuarantee = this.createNode('document', { name: 'Bank Guarantee', x: 200, y: 400 });
        
        // Stamp
        const stamp = this.createNode('stamp', { name: 'Delhi ₹50', x: 50, y: 200 });
        
        // Invitees
        const ronit = this.createNode('invitee', { 
            name: 'Ronit', 
            role: 'signer', 
            esign: 'aadhaar',
            x: 500, y: 250 
        });
        const reviewer = this.createNode('invitee', { 
            name: 'Bank Reviewer', 
            role: 'reviewer',
            x: 500, y: 350 
        });
        
        // Connections
        this.createConnection(stamp, loanAgreement);
        this.createConnection(ronit, loanAgreement);
        this.createConnection(ronit, sanctionLetter);
        this.createConnection(reviewer, bankGuarantee);
    }

    loadSimpleContractExample() {
        const contract = this.createNode('document', { name: 'Service Contract', x: 200, y: 250 });
        const client = this.createNode('invitee', { name: 'Client', role: 'signer', esign: 'aadhaar', x: 400, y: 200 });
        const vendor = this.createNode('invitee', { name: 'Vendor', role: 'signer', esign: 'dsc', x: 400, y: 300 });
        
        this.createConnection(client, contract);
        this.createConnection(vendor, contract);
    }

    loadEmployeeOnboardingExample() {
        const offerLetter = this.createNode('document', { name: 'Offer Letter', x: 150, y: 150 });
        const nda = this.createNode('document', { name: 'NDA', x: 150, y: 230 });
        const handbook = this.createNode('document', { name: 'Employee Handbook', x: 150, y: 310 });
        const taxForm = this.createNode('document', { name: 'Tax Form', x: 150, y: 390 });
        
        const employee = this.createNode('invitee', { name: 'New Employee', role: 'signer', esign: 'aadhaar', x: 450, y: 200 });
        const hr = this.createNode('invitee', { name: 'HR Manager', role: 'reviewer', x: 450, y: 300 });
        const manager = this.createNode('invitee', { name: 'Direct Manager', role: 'signer', esign: 'virtual', x: 450, y: 400 });
        
        this.createConnection(employee, offerLetter);
        this.createConnection(employee, nda);
        this.createConnection(hr, handbook);
        this.createConnection(manager, taxForm);
    }

    // History and Diff Management
    addToHistory(action) {
        this.state.history.push({
            action: action,
            timestamp: new Date(),
            state: this.cloneState()
        });
        this.state.historyIndex = this.state.history.length - 1;
        this.updateHistoryButtons();
    }

    addToDiff(change, type) {
        const diffContent = document.getElementById('diff-content');
        const diffPlaceholder = diffContent.querySelector('.diff-placeholder');
        
        if (diffPlaceholder) {
            diffPlaceholder.remove();
        }
        
        const diffEntry = document.createElement('div');
        diffEntry.className = `diff-entry ${type}`;
        diffEntry.innerHTML = `
            <div class="diff-timestamp">${new Date().toLocaleTimeString()}</div>
            <div class="diff-text">${change}</div>
        `;
        
        diffContent.appendChild(diffEntry);
        diffContent.scrollTop = diffContent.scrollHeight;
    }

    cloneState() {
        return {
            nodes: new Map(this.state.nodes),
            connections: new Map(this.state.connections)
        };
    }

    undo() {
        if (this.state.historyIndex > 0) {
            this.state.historyIndex--;
            this.restoreState(this.state.history[this.state.historyIndex].state);
            this.updateHistoryButtons();
        }
    }

    redo() {
        if (this.state.historyIndex < this.state.history.length - 1) {
            this.state.historyIndex++;
            this.restoreState(this.state.history[this.state.historyIndex].state);
            this.updateHistoryButtons();
        }
    }

    restoreState(state) {
        this.clearCanvas();
        this.state.nodes = new Map(state.nodes);
        this.state.connections = new Map(state.connections);
        
        // Re-render everything
        this.state.nodes.forEach(node => this.renderNode(node));
        this.state.connections.forEach(connection => this.renderConnection(connection));
        
        this.updateNaturalLanguageSummary();
        this.updateEmptyState();
    }

    updateHistoryButtons() {
        document.getElementById('undo-btn').disabled = this.state.historyIndex <= 0;
        document.getElementById('redo-btn').disabled = this.state.historyIndex >= this.state.history.length - 1;
    }

    // Workflow Management
    restart() {
        if (confirm('Are you sure you want to start over? All changes will be lost.')) {
            this.clearWorkflow();
            this.showBootstrapOverlay();
        }
    }

    clearWorkflow() {
        this.clearCanvas();
        this.state.nodes.clear();
        this.state.connections.clear();
        this.state.history = [];
        this.state.historyIndex = -1;
        this.updateHistoryButtons();
        this.updateNaturalLanguageSummary();
        this.updateEmptyState();
        this.clearDiff();
    }

    clearCanvas() {
        this.nodesGroup.innerHTML = '';
        this.connectionsGroup.innerHTML = '';
    }

    clearDiff() {
        const diffContent = document.getElementById('diff-content');
        diffContent.innerHTML = `
            <div class="diff-placeholder">
                <i class="fas fa-clock"></i>
                <p>Changes will be tracked here</p>
            </div>
        `;
    }

    publish() {
        if (this.state.nodes.size === 0) {
            this.showNotification('Nothing to publish. Create a workflow first.', 'warning');
            return;
        }

        const workflowData = this.generateWorkflowJSON();
        
        // Simulate API call
        this.setNLStatus('processing');
        setTimeout(() => {
            this.showNotification('Workflow published successfully!', 'success');
            this.setNLStatus('ready');
            console.log('Published workflow:', workflowData);
        }, 2000);
    }

    generateWorkflowJSON() {
        const documents = Array.from(this.state.nodes.values()).filter(node => node.type === 'document');
        const invitees = Array.from(this.state.nodes.values()).filter(node => node.type === 'invitee');
        const stamps = Array.from(this.state.nodes.values()).filter(node => node.type === 'stamp');

        return {
            documents: documents.map(doc => ({
                name: doc.name,
                configured: doc.configured
            })),
            invitees: invitees.map(inv => ({
                name: inv.name,
                role: inv.role,
                esign: inv.esign,
                configured: inv.configured
            })),
            stamps: stamps.map(stamp => ({
                name: stamp.name,
                jurisdiction: stamp.jurisdiction,
                denomination: stamp.denomination,
                configured: stamp.configured
            })),
            connections: Array.from(this.state.connections.values())
        };
    }

    // Modal Management
    showModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    }

    hideModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
    }

    // Node Properties
    showNodeProperties(nodeId) {
        const node = this.state.nodes.get(nodeId);
        if (!node) return;

        // Implement properties modal (placeholder)
        console.log('Show properties for:', node);
    }

    // Palette Methods
    createNodeFromPalette(type) {
        const commands = [{
            type: type === 'invitee' ? 'add_invitee' : `add_${type}s`,
            count: 1,
            needsClarification: type === 'stamp' || type === 'invitee'
        }];

        if (commands[0].needsClarification) {
            this.showClarificationPanel(commands[0]);
        } else {
            this.executeCommand(commands[0]);
            this.updateNaturalLanguageSummary();
        }
    }
}

// Initialize the workflow builder when the page loads
document.addEventListener('DOMContentLoaded', function() {
    window.workflowBuilder = new WorkflowBuilder();
});