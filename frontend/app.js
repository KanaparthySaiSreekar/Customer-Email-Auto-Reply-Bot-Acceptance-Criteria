// Configuration
const API_BASE = 'http://localhost:8000/api';

// State
let currentEmailId = null;
let currentFolder = 'all';
let emails = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadEmails();
});

function initializeEventListeners() {
    // Import buttons
    document.getElementById('importBtn').addEventListener('click', () => {
        document.getElementById('csvFile').click();
    });

    document.getElementById('importBtnWelcome').addEventListener('click', () => {
        document.getElementById('csvFile').click();
    });

    document.getElementById('csvFile').addEventListener('change', handleFileImport);

    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', loadEmails);

    // Folder filters
    document.querySelectorAll('.folder-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.folder-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentFolder = e.target.dataset.folder;
            loadEmails();
        });
    });

    // Email detail actions
    document.getElementById('classifyBtn').addEventListener('click', reclassifyEmail);
    document.getElementById('generateDraftBtn').addEventListener('click', generateDraft);
    document.getElementById('deleteEmailBtn').addEventListener('click', deleteEmail);

    // Modal close
    document.querySelector('.close-modal').addEventListener('click', () => {
        document.getElementById('importModal').classList.remove('show');
    });
}

// API functions
async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Request failed');
        }

        // Handle 204 No Content
        if (response.status === 204) {
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function loadEmails() {
    try {
        const folder = currentFolder === 'all' ? '' : currentFolder;
        const params = folder ? `?folder=${folder}` : '';
        emails = await apiRequest(`/emails/${params}`);
        renderEmailList(emails);
    } catch (error) {
        showError('Failed to load emails: ' + error.message);
    }
}

async function loadEmailDetail(emailId) {
    try {
        const email = await apiRequest(`/emails/${emailId}`);
        currentEmailId = emailId;
        renderEmailDetail(email);
    } catch (error) {
        showError('Failed to load email details: ' + error.message);
    }
}

async function reclassifyEmail() {
    if (!currentEmailId) return;

    try {
        const email = await apiRequest(`/emails/${currentEmailId}/classify`, {
            method: 'POST'
        });
        await loadEmailDetail(currentEmailId);
        await loadEmails();
        showSuccess('Email reclassified successfully');
    } catch (error) {
        showError('Failed to reclassify email: ' + error.message);
    }
}

async function generateDraft() {
    if (!currentEmailId) return;

    try {
        await apiRequest(`/emails/${currentEmailId}/generate-draft`, {
            method: 'POST'
        });
        await loadEmailDetail(currentEmailId);
        showSuccess('Draft generated successfully');
    } catch (error) {
        showError('Failed to generate draft: ' + error.message);
    }
}

async function deleteEmail() {
    if (!currentEmailId) return;

    if (!confirm('Are you sure you want to delete this email?')) return;

    try {
        await apiRequest(`/emails/${currentEmailId}`, {
            method: 'DELETE'
        });
        currentEmailId = null;
        document.getElementById('emailDetail').style.display = 'none';
        document.getElementById('welcomeScreen').style.display = 'block';
        await loadEmails();
        showSuccess('Email deleted successfully');
    } catch (error) {
        showError('Failed to delete email: ' + error.message);
    }
}

async function updateDraft(draftId, updates) {
    try {
        await apiRequest(`/drafts/${draftId}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
        await loadEmailDetail(currentEmailId);
        showSuccess('Draft updated successfully');
    } catch (error) {
        showError('Failed to update draft: ' + error.message);
    }
}

async function handleFileImport(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/emails/import`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Import failed');
        }

        const result = await response.json();
        showImportResults(result);
        await loadEmails();

        // Reset file input
        e.target.value = '';
    } catch (error) {
        showError('Failed to import CSV: ' + error.message);
    }
}

// Render functions
function renderEmailList(emails) {
    const emailList = document.getElementById('emailList');

    if (emails.length === 0) {
        emailList.innerHTML = '<div class="loading">No emails found</div>';
        return;
    }

    emailList.innerHTML = emails.map(email => `
        <div class="email-item ${email.id === currentEmailId ? 'active' : ''}" data-id="${email.id}">
            <div class="email-item-header">
                <div class="email-item-sender">${escapeHtml(email.sender)}</div>
            </div>
            <div class="email-item-subject">${escapeHtml(email.subject)}</div>
            <div class="email-item-meta">
                ${email.intent ? `<span class="badge badge-${email.intent}">${email.intent}</span>` : ''}
                ${email.confidence ? `<span class="confidence">${Math.round(email.confidence * 100)}%</span>` : ''}
                ${email.needs_review ? '<span class="badge badge-warning">Review</span>' : ''}
            </div>
        </div>
    `).join('');

    // Add click handlers
    document.querySelectorAll('.email-item').forEach(item => {
        item.addEventListener('click', () => {
            const emailId = parseInt(item.dataset.id);
            loadEmailDetail(emailId);
        });
    });
}

function renderEmailDetail(email) {
    document.getElementById('welcomeScreen').style.display = 'none';
    document.getElementById('emailDetail').style.display = 'block';

    // Basic info
    document.getElementById('emailSubject').textContent = email.subject;
    document.getElementById('emailSender').textContent = email.sender;
    document.getElementById('emailCase').textContent = email.case_number;
    document.getElementById('emailContent').textContent = email.content;

    // Intent and confidence
    const intentBadge = document.getElementById('emailIntent');
    intentBadge.textContent = email.intent || 'Not classified';
    intentBadge.className = `badge ${email.intent ? 'badge-' + email.intent : ''}`;

    const confidenceEl = document.getElementById('emailConfidence');
    if (email.confidence !== null) {
        confidenceEl.textContent = `${Math.round(email.confidence * 100)}%`;
    } else {
        confidenceEl.textContent = 'N/A';
    }

    document.getElementById('emailFolder').textContent = email.folder || 'Unassigned';

    // Review warning
    const reviewWarning = document.getElementById('reviewWarning');
    reviewWarning.style.display = email.needs_review ? 'block' : 'none';

    // Render drafts
    renderDrafts(email.drafts || []);

    // Update email list active state
    document.querySelectorAll('.email-item').forEach(item => {
        item.classList.toggle('active', parseInt(item.dataset.id) === email.id);
    });
}

function renderDrafts(drafts) {
    const draftsList = document.getElementById('draftsList');

    if (drafts.length === 0) {
        draftsList.innerHTML = '<div class="loading">No drafts yet. Click "Generate Auto-Reply" to create one.</div>';
        return;
    }

    draftsList.innerHTML = drafts.map(draft => `
        <div class="draft-item ${draft.approved ? 'approved' : ''}" data-id="${draft.id}">
            <div class="draft-header">
                <div class="draft-status">
                    ${draft.approved ? '<span class="badge badge-success">Approved</span>' : '<span class="badge">Draft</span>'}
                    <span style="color: #7f8c8d; font-size: 0.85rem;">
                        ${new Date(draft.created_at).toLocaleString()}
                    </span>
                </div>
                <div class="draft-actions">
                    ${!draft.approved ? `
                        <button class="btn btn-secondary edit-draft-btn" data-id="${draft.id}">Edit</button>
                        <button class="btn btn-success approve-draft-btn" data-id="${draft.id}">Approve</button>
                    ` : `
                        <button class="btn btn-secondary unapprove-draft-btn" data-id="${draft.id}">Unapprove</button>
                    `}
                </div>
            </div>
            <div class="draft-subject">
                <strong>Subject:</strong> <span class="draft-subject-text-${draft.id}">${escapeHtml(draft.subject)}</span>
                <input type="text" class="draft-subject-input-${draft.id}" value="${escapeHtml(draft.subject)}" style="display: none;">
            </div>
            <div class="draft-content">
                <div class="draft-content-text-${draft.id}">${escapeHtml(draft.content)}</div>
                <textarea class="draft-content-input-${draft.id}" style="display: none;">${escapeHtml(draft.content)}</textarea>
            </div>
        </div>
    `).join('');

    // Add event listeners
    document.querySelectorAll('.approve-draft-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const draftId = parseInt(e.target.dataset.id);
            await updateDraft(draftId, { approved: true });
        });
    });

    document.querySelectorAll('.unapprove-draft-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const draftId = parseInt(e.target.dataset.id);
            await updateDraft(draftId, { approved: false });
        });
    });

    document.querySelectorAll('.edit-draft-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const draftId = parseInt(e.target.dataset.id);
            toggleDraftEdit(draftId, true);
            e.target.textContent = 'Save';
            e.target.classList.remove('btn-secondary');
            e.target.classList.add('btn-primary');
            e.target.classList.remove('edit-draft-btn');
            e.target.classList.add('save-draft-btn');
        });
    });

    // Save handlers are added after edit is triggered
    setTimeout(() => {
        document.querySelectorAll('.save-draft-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const draftId = parseInt(e.target.dataset.id);
                const subject = document.querySelector(`.draft-subject-input-${draftId}`).value;
                const content = document.querySelector(`.draft-content-input-${draftId}`).value;
                await updateDraft(draftId, { subject, content });
            });
        });
    }, 100);
}

function toggleDraftEdit(draftId, editMode) {
    const subjectText = document.querySelector(`.draft-subject-text-${draftId}`);
    const subjectInput = document.querySelector(`.draft-subject-input-${draftId}`);
    const contentText = document.querySelector(`.draft-content-text-${draftId}`);
    const contentInput = document.querySelector(`.draft-content-input-${draftId}`);

    if (editMode) {
        subjectText.style.display = 'none';
        subjectInput.style.display = 'block';
        contentText.style.display = 'none';
        contentInput.style.display = 'block';
    } else {
        subjectText.style.display = 'inline';
        subjectInput.style.display = 'none';
        contentText.style.display = 'block';
        contentInput.style.display = 'none';
    }
}

function showImportResults(result) {
    const modal = document.getElementById('importModal');
    const resultsDiv = document.getElementById('importResults');

    let html = `
        <div class="import-summary">
            <h4>Import Summary</h4>
            <p><strong>Success:</strong> ${result.success} emails imported</p>
            <p><strong>Failed:</strong> ${result.failed} rows</p>
        </div>
    `;

    if (result.errors.length > 0) {
        html += `
            <div class="import-errors">
                <h4>Errors:</h4>
                <ul>
                    ${result.errors.map(err => `<li>${escapeHtml(err)}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    resultsDiv.innerHTML = html;
    modal.classList.add('show');
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    console.error(message);
    // Could add a toast notification here
    alert('Error: ' + message);
}

function showSuccess(message) {
    console.log(message);
    // Could add a toast notification here
}
