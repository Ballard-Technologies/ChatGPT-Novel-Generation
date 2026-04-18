let wordList = [];

const STYLE_DESCRIPTIONS = {
    classic: 'Times serif, indented paragraphs, traditional book look.',
    modern: 'Helvetica sans-serif, no indent, blank line between paragraphs.',
    compact: 'Smaller font and tighter spacing to fit more on each page.',
    manuscript: 'Courier typewriter font with generous line height.'
};

const VERSION_DESCRIPTIONS = {
    v0: 'Sequential single-pass pipeline: enhances the summary, splits it into parts, expands each in order, and stitches adjacent sections. Simplest and slowest; weakest long-form continuity.',
    v1: 'Builds author, character, and theme context before writing chapters in parallel threads. Faster than v0 with stronger continuity.',
    v2: 'Extends v1 with an extra novel-framework planning step, chapter numbering, and refined prompts at lower temperature for the most consistent output. Recommended.'
};

// Tracks whether the current visitor is authenticated. Determines whether we
// install the sendBeacon cancel-on-unload path (anonymous) or stash the job
// id in localStorage for refresh-resume (logged-in).
let isAuthenticated = false;
// Currently-tracked job id (null when nothing is in flight).
let activeJobId = null;
// Handle for the setTimeout that drives the polling loop.
let pollTimer = null;

const ACTIVE_JOB_STORAGE_KEY = 'activeJob-v1';

function loadCurrentUser() {
    fetch('/api/me', { credentials: 'same-origin' })
        .then(function (response) {
            return response.ok ? response.json() : null;
        })
        .then(function (data) {
            if (data && data.username) {
                isAuthenticated = true;
                $('#user-username').text(data.username);
                $('#logout-link').show();
                $('#login-link').hide();
                $('#signup-link').hide();
                loadMyNovels();
                resumeActiveJobIfAny();
            } else {
                isAuthenticated = false;
                $('#user-username').text('');
                $('#logout-link').hide();
                $('#login-link').show();
                $('#signup-link').show();
                $('#my-novels').hide();
                // Anonymous visitors never resume after a refresh; clear any
                // stale entry (e.g. left over after logout).
                try { localStorage.removeItem(ACTIVE_JOB_STORAGE_KEY); } catch (e) {}
            }
        })
        .catch(function (err) { console.error('Failed to load user:', err); });
}

function loadMyNovels() {
    fetch('/api/my-novels', { credentials: 'same-origin' })
        .then(function (response) { return response.ok ? response.json() : []; })
        .then(function (novels) {
            var $section = $('#my-novels');
            var $list = $('#my-novels-list').empty();
            var $empty = $('#my-novels-empty');
            $section.show();
            if (!novels.length) {
                $empty.show();
                return;
            }
            $empty.hide();
            novels.forEach(function (n) {
                var created = new Date(n.created_at).toLocaleString();
                var $item = $('<li>', { 'class': 'my-novel-row' });
                var $meta = $('<div>', { 'class': 'my-novel-meta' })
                    .append($('<div>', { 'class': 'my-novel-title', text: n.title }))
                    .append($('<div>', { 'class': 'my-novel-date', text: created }));
                var $download = $('<a>', {
                    'class': 'other-button',
                    href: '/api/my-novels/' + n.id + '/pdf',
                    text: 'Download PDF',
                });
                $item.append($meta).append($download);
                $list.append($item);
            });
        })
        .catch(function (err) { console.error('Failed to load novels:', err); });
}

$(document).ready(function () {
    loadCurrentUser();
    loadUserData();

    $('#save-api-key-btn').click(function (e) {
        e.preventDefault();

        testOpenAIKey().then(result => console.log(result));

        saveUserData();
    });

    $('#addInputBtn').click(function () {
        addInputField();
        updateLevels();
    });

    $('#novel-gen-form').on('submit', function (e) {
        e.preventDefault();

        // Clear previous error messages
        $('.error').text('');

        // Validation
        let isValid = true;

        if ($('#novel-gen-title').val().trim() === '') {
            $('#novel-gen-title-Error').text('Please enter a title.');
            isValid = false;
        }

        if (!isValid) {
            return; // Stop the function if validation fails
        }

        const prefix = 'novel-gen';

        // Show the loading bar
        $('#' + prefix + '-loading-bar-container').show();
        $('#' + prefix + '-loading-bar').css('width', '0%');
        $('#' + prefix + '-loading-percent').text('0%'); // Reset the text

        let formData = gatherFormData();
        formData['title'] = $('#novel-gen-title').val().trim();
        formData["api_key"] = $("#api-key-input").val();

        // Capture the selected output style at submit time so it's used
        // by the subsequent PDF download regardless of later UI changes.
        const selectedStyle = $('#novel-gen-style').val();

        fetch('/api/jobs', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        }).then(function (response) {
            return response.json().then(function (body) {
                return { ok: response.ok, status: response.status, body: body };
            });
        }).then(function (result) {
            if (!result.ok) {
                $('#' + prefix + '-loading-bar-container').hide();
                const msg = (result.body && result.body.error) || 'Failed to start job.';
                $('#novel-gen-error').text(msg);
                return;
            }
            const jobId = result.body.job_id;
            startJobTracking(jobId, formData.title, selectedStyle, prefix);
        }).catch(function (err) {
            console.error('Error submitting job:', err);
            $('#' + prefix + '-loading-bar-container').hide();
            $('#novel-gen-error').text('Network error submitting job.');
        });
    });

    // Event listener for when the selection changes
    $('#novel-gen-prompt-type').change(function() {
        // Get the selected value
        var selectedOption = $(this).val();

        // Hide both tabs initially
        $('#novel-gen-outline-tab').hide();
        $('#novel-gen-summary-tab').hide();

        // Show the relevant tab based on the selected option
        if (selectedOption === 'Outline') {
            $('#novel-gen-outline-tab').show();
        } else if (selectedOption === 'Summary') {
            $('#novel-gen-summary-tab').show();
        }
    });

    // Trigger the change event on page load to ensure the correct tab is shown
    $('#novel-gen-prompt-type').trigger('change');

    // Update the output-style description when the selection changes.
    $('#novel-gen-style').change(function () {
        var key = $(this).val();
        $('#novel-gen-style-desc').text(STYLE_DESCRIPTIONS[key] || '');
    }).trigger('change');

    // Update the generation-version description when the selection changes.
    $('#novel-gen-version').change(function () {
        var key = $(this).val();
        $('#novel-gen-version-desc').text(VERSION_DESCRIPTIONS[key] || '');
    }).trigger('change');

    fetch('assets/word_list.csv')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok, status: ${response.status}`);
            }
            return response.text();
        })
        .then(data => {
            wordList = parseCSV(data);  // Store parsed CSV data in the global variable
        })
        .catch(error => {
            console.error("Failed to fetch CSV:", error);
        });

    // Attach the click event to the button with the die icon to generate a title
    $('#generate-title-btn').click(function (e) {
        e.preventDefault();
        $('#novel-gen-title').val(generateRandomTitle());
    });
});

function addInputField() {
    let newInput = createDepthControlInput();
    $('#inputContainer').append(newInput);
}

function createDepthControlInput() {
    let inputGroup = $('<div>', {
        'class': 'input-group mb-2',
        'data-depth': '1',
        css: { 'padding-left': '20px' }
    });

    let levelIndicator = $('<div>', {
        'class': 'level-indicator',
        css: { 'margin-right': '10px' }
    });

    let indentBtn = $('<button>', {
        type: 'button',
        'class': 'btn btn-outline-secondary',
        text: '>',
        click: function () {
            adjustDepth(inputGroup, true);
        }
    });

    let outdentBtn = $('<button>', {
        type: 'button',
        'class': 'btn btn-outline-secondary',
        text: '<',
        click: function () {
            adjustDepth(inputGroup, false);
        }
    });

    let deleteBtn = $('<button>', {
        type: 'button',
        'class': 'btn btn-outline-danger',
        text: 'X',
        click: function () { deleteInputField(inputGroup); } // Corrected event handler
    });

    let input = $('<input>', {
        type: 'text',
        'class': 'form-control',
        placeholder: 'Enter detail'
    });

    inputGroup.append(levelIndicator, outdentBtn, indentBtn, input, deleteBtn);

    return inputGroup;
}

function adjustDepth(element, isIndent) {
    let currentDepth = parseInt(element.attr('data-depth'));
    currentDepth += isIndent ? 1 : -1;
    currentDepth = Math.max(1, currentDepth); // Ensure depth is not negative
    element.attr('data-depth', currentDepth.toString());

    // Adjust padding based on depth
    let padding = (20 * currentDepth);
    element.css('padding-left', `${padding}px`);

    updateLevels();
}

function updateLevels() {
    let levelNumbers = [0]; // Initialize level numbers

    $('#inputContainer').children('.input-group').each(function () {
        let depth = parseInt($(this).attr('data-depth'));

        while (levelNumbers.length - 1 > depth) {
            levelNumbers.pop(); // Remove deeper levels
        }
        if (levelNumbers.length - 1 < depth) {
            levelNumbers.push(1); // Start a new sub-level
        } else {
            levelNumbers[depth]++; // Increment the current level
        }

        let levelString = levelNumbers.slice(1).join('.');
        $(this).find('.level-indicator').text(levelString);
    });
}

function deleteInputField(element) {
    element.remove();
    updateLevels();
}

function gatherFormData() {
    let selectedPromptType = $('#novel-gen-prompt-type').val();
    let formData = {};

    if (selectedPromptType === 'Outline') {
        let inputData = [];
        $('#inputContainer').find('.input-group').each(function () {
            let level = $(this).find('.level-indicator').text();
            let value = $(this).find('input[type="text"]').val();
            inputData.push({ value: value, level: level });
        });
        formData['outline'] = inputData;
    } else if (selectedPromptType === 'Summary') {
        formData['summary'] = $('#summaryTextarea').val().trim();
        formData['version'] = $('#novel-gen-version').val().trim();
        formData['bulk_model'] = $('#bulk-model').val().trim();
    }

    return formData;
}

function setLocalStorageItem(value) {
    localStorage.setItem('key54-32579032', value);
}

function getLocalStorageItem() {
    return localStorage.getItem('key54-32579032');
}

function saveUserData() {
    var userInput = $("#api-key-input").val();
    setLocalStorageItem(userInput);
}

function loadUserData() {
    var userData = getLocalStorageItem();

    if (userData) {
        $("#api-key-input").val(userData);
    }
}

async function testOpenAIKey() {
    var apiKey = $("#api-key-input").val();

    const url = 'https://api.openai.com/v1/chat/completions';

    const headers = {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
    };

    const body = JSON.stringify({
        model: "gpt-5.4-nano",
        messages: [
            {
                role: "system",
                content: "You are a helpful assistant."
            },
            {
                role: "user",
                content: "Hello!"
            }
        ]
    });

    try {
        const response = await fetch(url, { method: 'POST', headers: headers, body: body });
        const data = await response.json();

        if (response.ok) {
            return { valid: true, message: 'API key is valid.', data: data };
        } else {
            return { valid: false, message: 'API key is not valid.', error: data };
        }
    } catch (error) {
        return { valid: false, message: 'Failed to test API key.', error: error };
    }
}

// ---- Job tracking: polling, unload handlers, PDF delivery ----

function startJobTracking(jobId, title, style, prefix) {
    activeJobId = jobId;
    // Logged-in users can reload the tab and resume where they left off;
    // anonymous users are cancelled on unload, so there's nothing to stash.
    if (isAuthenticated) {
        try {
            localStorage.setItem(ACTIVE_JOB_STORAGE_KEY, JSON.stringify({
                job_id: jobId, title: title, style: style, prefix: prefix,
            }));
        } catch (e) { /* storage disabled; not fatal */ }
    }
    installUnloadHandlers();
    pollJob(jobId, title, style, prefix);
}

function finishJobTracking() {
    if (pollTimer) { clearTimeout(pollTimer); pollTimer = null; }
    activeJobId = null;
    try { localStorage.removeItem(ACTIVE_JOB_STORAGE_KEY); } catch (e) {}
    removeUnloadHandlers();
}

function resumeActiveJobIfAny() {
    // Only logged-in users persist job state across reloads.
    if (!isAuthenticated) { return; }
    let stashed;
    try { stashed = JSON.parse(localStorage.getItem(ACTIVE_JOB_STORAGE_KEY)); }
    catch (e) { stashed = null; }
    if (!stashed || !stashed.job_id) { return; }
    // Verify the job still exists (and belongs to us) before showing the bar.
    fetch('/api/jobs/' + encodeURIComponent(stashed.job_id), {
        credentials: 'same-origin',
    }).then(function (r) {
        if (!r.ok) { localStorage.removeItem(ACTIVE_JOB_STORAGE_KEY); return null; }
        return r.json();
    }).then(function (data) {
        if (!data) { return; }
        const prefix = stashed.prefix || 'novel-gen';
        if (data.status === 'complete' || data.status === 'failed'
            || data.status === 'cancelled') {
            // Terminal already; drop the stash silently.
            localStorage.removeItem(ACTIVE_JOB_STORAGE_KEY);
            return;
        }
        $('#' + prefix + '-loading-bar-container').show();
        startJobTracking(stashed.job_id, stashed.title, stashed.style, prefix);
    }).catch(function () { /* network blip; next reload will retry */ });
}

function pollJob(jobId, title, style, prefix) {
    fetch('/api/jobs/' + encodeURIComponent(jobId), {
        credentials: 'same-origin',
    }).then(function (response) {
        if (!response.ok) {
            throw new Error('Job lookup failed: ' + response.status);
        }
        return response.json();
    }).then(function (data) {
        if (data.current && data.total) {
            const progress = (data.current / data.total) * 100;
            $('#' + prefix + '-loading-bar').css('width', progress + '%');
            $('#' + prefix + '-loading-percent').text(Math.round(progress) + '%');
        }
        if (data.status === 'failed') {
            $('#' + prefix + '-loading-bar-container').hide();
            $('#novel-gen-error').text(
                'Error occurred on the server. Unable to create novel. '
                + (data.fail_message || ''));
            finishJobTracking();
            return;
        }
        if (data.status === 'cancelled') {
            $('#' + prefix + '-loading-bar-container').hide();
            $('#novel-gen-error').text('Job was cancelled.');
            finishJobTracking();
            return;
        }
        if (data.status === 'complete') {
            $('#' + prefix + '-loading-bar-container').hide();
            deliverPDF(jobId, style);
            finishJobTracking();
            return;
        }
        pollTimer = setTimeout(function () {
            pollJob(jobId, title, style, prefix);
        }, 10000);
    }).catch(function (err) {
        console.error('Error polling job:', err);
        // Don't finish tracking -- retry on the same schedule so a network
        // blip doesn't silently abandon the run.
        pollTimer = setTimeout(function () {
            pollJob(jobId, title, style, prefix);
        }, 10000);
    });
}

function deliverPDF(jobId, style) {
    const url = '/api/jobs/' + encodeURIComponent(jobId) + '/pdf'
        + (style ? '?style=' + encodeURIComponent(style) : '');
    fetch(url, { credentials: 'same-origin' })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errData => {
                throw new Error(errData.error || 'Failed to create PDF');
            });
        }
        const disposition = response.headers.get('Content-Disposition');
        let filename = 'download.pdf';
        if (disposition && disposition.indexOf('filename=') !== -1) {
            filename = disposition.split('filename=')[1].replace(/"/g, '');
        }
        return response.blob().then(blob => ({blob, filename}));
    })
    .then(({ blob, filename }) => {
        const objectUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = objectUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(objectUrl);
        a.remove();
        // Logged-in users now have a persisted Novel row; refresh the list.
        if ($('#my-novels').is(':visible')) {
            loadMyNovels();
        }
    })
    .catch(error => {
        console.error('Error creating PDF:', error);
        alert('An error occurred while creating the PDF: ' + error.message);
    });
}

// ---- Unload handling ----
// Anonymous users see a beforeunload warning and have their job cancelled
// via sendBeacon when they actually leave. Logged-in users' jobs survive
// a refresh, so we skip both.

function _beforeUnloadHandler(e) {
    if (!activeJobId) { return; }
    if (!isAuthenticated) {
        e.preventDefault();
        e.returnValue = '';
        return '';
    }
}

function _unloadHandler() {
    if (!activeJobId || isAuthenticated) { return; }
    try {
        const url = '/api/jobs/' + encodeURIComponent(activeJobId) + '/cancel';
        navigator.sendBeacon(url, new Blob([''], { type: 'application/json' }));
    } catch (e) { /* best-effort */ }
}

function installUnloadHandlers() {
    window.addEventListener('beforeunload', _beforeUnloadHandler);
    window.addEventListener('pagehide', _unloadHandler);
}

function removeUnloadHandlers() {
    window.removeEventListener('beforeunload', _beforeUnloadHandler);
    window.removeEventListener('pagehide', _unloadHandler);
}

// Function to parse the CSV text into an array of objects
function parseCSV(data) {
    const rows = data.split('\n');
    
    return rows.slice(1).map((row, index) => {
        const columns = row.split(',');

        // Ensure we have both word and type columns
        if (columns.length !== 2 || !columns[0] || !columns[1]) {
            return null;  // Skip invalid rows
        }

        const word = columns[0].trim();
        const type = columns[1].trim();

        // Check if word and type are not undefined or empty
        if (!word || !type) {
            return null;  // Skip invalid data
        }

        return { Word: word, Type: type };
    }).filter(row => row !== null);  // Filter out null values (invalid rows)
}

function generateRandomTitle() {
    const adjectives = wordList.filter(row => row.Type === 'adj').map(row => row.Word);
    const nouns = wordList.filter(row => row.Type === 'noun').map(row => row.Word);
    const verbs = wordList.filter(row => row.Type === 'verb').map(row => row.Word);

    const titleStructures = [
        "{adj} {noun}",
        "The {adj} {noun}",
        "{noun} of {noun}",
        "{verb} the {noun}",
        "{adj} {noun} {verb} {noun}",
        "{noun} and {noun}",
        "The {noun} of {adj} {noun}"
    ];

    const getRandomElement = arr => arr[Math.floor(Math.random() * arr.length)];

    // Choose a random structure
    const structure = getRandomElement(titleStructures);

    // Replace placeholders with random words
    let title = structure
        .replace(/{adj}/g, () => getRandomElement(adjectives))
        .replace(/{noun}/g, () => getRandomElement(nouns))
        .replace(/{verb}/g, () => getRandomElement(verbs));

    // Capitalize the title properly like a book title
    title = toTitleCase(title);

    console.log("Generated Title: ", title);

    return title;
}

// Function to capitalize title properly
function toTitleCase(title) {
    const minorWords = ['and', 'or', 'but', 'a', 'an', 'the', 'for', 'nor', 'on', 'at', 'to', 'by', 'with', 'of']; // Words that should be lowercase unless at the start or end
    const words = title.split(' ');

    return words.map((word, index) => {
        if (index === 0 || index === words.length - 1 || !minorWords.includes(word.toLowerCase())) {
            return capitalizeWord(word); // Capitalize important words or the first/last word
        } else {
            return word.toLowerCase(); // Leave minor words lowercase
        }
    }).join(' ');
}

// Helper function to capitalize a single word
function capitalizeWord(word) {
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
}