document.addEventListener('DOMContentLoaded', () => {
    const enrichForm = document.getElementById('enrich-form');
    const urlInput = document.getElementById('company-url');
    const enrichBtn = document.getElementById('enrich-btn');
    const btnText = enrichBtn.querySelector('.btn-text');
    const enrichLoader = document.getElementById('enrich-loader');
    const statusMessage = document.getElementById('status-message');
    const singleResultContainer = document.getElementById('single-result-container');
    
    const showResultsBtn = document.getElementById('show-results-btn');
    const resultsLoader = document.getElementById('results-loader');
    const allResultsContainer = document.getElementById('all-results-container');

    // Create a card HTML string from company data
    const createCardHTML = (company) => {
        const mailsHTML = company.mail && company.mail.length > 0 
            ? company.mail.map(m => `<span class="data-tag">${m}</span>`).join('') 
            : '<span class="data-value text-muted">N/A</span>';
            
        return `
            <div class="company-card">
                <div class="card-header">
                    <h3 class="card-title">${company.website_name || 'Unknown Website'}</h3>
                    <div class="card-subtitle">${company.company_name || 'N/A'}</div>
                </div>
                <div class="card-body">
                    <div class="data-row">
                        <span class="data-label">Core Service</span>
                        <span class="data-value">${company.core_service || 'N/A'}</span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">Target Customer</span>
                        <span class="data-value">${company.target_customer || 'N/A'}</span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">Probable Pain Point</span>
                        <span class="data-value">${company.probable_pain_point || 'N/A'}</span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">Contact Emails</span>
                        <div>${mailsHTML}</div>
                    </div>
                    <div class="data-row">
                        <span class="data-label">Mobile Number</span>
                        <span class="data-value">${company.mobile_number || 'N/A'}</span>
                    </div>
                    <div class="data-row">
                        <span class="data-label">Address</span>
                        <span class="data-value">${company.address || 'N/A'}</span>
                    </div>
                    <div class="outreach-box">
                        "${company.outreach_opener || 'N/A'}"
                    </div>
                </div>
            </div>
        `;
    };

    const showStatus = (message, type) => {
        statusMessage.textContent = message;
        statusMessage.className = `status-message status-${type}`;
        statusMessage.classList.remove('hidden');
    };

    // Handle Enrich Form Submission
    enrichForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();
        if (!url) return;

        // UI Loading State
        enrichBtn.disabled = true;
        btnText.textContent = 'Enriching...';
        enrichLoader.classList.remove('hidden');
        statusMessage.classList.add('hidden');
        singleResultContainer.classList.add('hidden');

        try {
            const response = await fetch('/enrich', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to enrich company data');
            }

            showStatus('Successfully enriched data!', 'success');
            
            // Render single result
            singleResultContainer.innerHTML = createCardHTML(data);
            singleResultContainer.classList.remove('hidden');
            
            urlInput.value = ''; // clear input

        } catch (error) {
            showStatus(error.message, 'error');
        } finally {
            // Restore UI State
            enrichBtn.disabled = false;
            btnText.textContent = 'Enrich';
            enrichLoader.classList.add('hidden');
        }
    });

    // Handle Show All Results
    showResultsBtn.addEventListener('click', async () => {
        // UI Loading State
        showResultsBtn.disabled = true;
        resultsLoader.classList.remove('hidden');
        allResultsContainer.classList.add('hidden');

        try {
            const response = await fetch('/results');
            if (!response.ok) throw new Error('Failed to fetch results');
            
            const results = await response.json();
            
            if (results.length === 0) {
                allResultsContainer.innerHTML = '<div style="text-align:center; width:100%; color:var(--text-muted); grid-column: 1 / -1;">No results found yet. Enrich a URL first.</div>';
            } else {
                allResultsContainer.innerHTML = results.map(company => createCardHTML(company)).join('');
            }
            
            allResultsContainer.classList.remove('hidden');

        } catch (error) {
            alert(error.message);
        } finally {
            showResultsBtn.disabled = false;
            resultsLoader.classList.add('hidden');
        }
    });
});
