let wordList = [];

function loadCurrentUser() {
    fetch('/api/me', { credentials: 'same-origin' })
        .then(function (response) {
            if (response.status === 401) {
                window.location.href = '/login';
                return null;
            }
            return response.ok ? response.json() : null;
        })
        .then(function (data) {
            if (!data) return;
            $('#user-username').text(data.username);
            $('#logout-link').show();
        })
        .catch(function (err) { console.error('Failed to load user:', err); });
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

        prefix = 'novel-gen'

        // Show the loading bar
        $('#' + prefix + '-loading-bar-container').show();
        $('#' + prefix + '-loading-bar').css('width', '0%');
        $('#' + prefix + '-loading-percent').text('0%'); // Reset the text

        let formData = gatherFormData();
        formData['title'] = $('#novel-gen-title').val().trim();
        formData["api_key"] = $("#api-key-input").val();

        $.ajax({
            type: "POST",
            url: "/novel-gen",
            contentType: "application/json",
            data: JSON.stringify(formData),
            xhr: function () {
                var xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener("progress", function (evt) {
                    if (evt.lengthComputable) {
                        var percentComplete = evt.loaded / evt.total;
                        // Update loading bar width
                        $('#' + prefix + '-loading-bar').css('width', percentComplete * 100 + '%');
                    }
                }, false);
                return xhr;
            },
            success: function (response) {
                console.log("Data submitted successfully:", response);
            },
            error: function (xhr, status, error) {
                console.error("Error in data submission:", xhr.responseText);
            },
            complete: function () {
                // Hide the loading bar when the request is complete
                updateLoadingBar(formData.title, prefix);
            }
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
        model: "gpt-4o-mini",
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

// Function to periodically fetch progress and update the loading bar
function updateLoadingBar(title, prefix) {
    $.get('/progress', function (data) {
        if (data.fail) {
            $('#' + prefix + '-loading-bar-container').hide();
            $('#novel-gen-error').text('Error occurred on the server. Unable to create novel.' + data.fail_message);
            return -1
        }
        if (data.current && data.total) {
            var progress = (data.current / data.total) * 100;
            $('#' + prefix + '-loading-bar').css('width', progress + '%');
            $('#' + prefix + '-loading-percent').text(Math.round(progress) + '%'); // Update the text
        }

        if (data.complete) {
            deliverPDF(data.chapters, title);
            $('#' + prefix + '-loading-bar-container').hide();
        }
        else {
            setTimeout(() => updateLoadingBar(title, prefix), 10000); // Update every 10 seconds
        }
    });
}

function deliverPDF(chapters, title) {
    // Prepare the data to be sent in the request
    const data = JSON.stringify({chapters: chapters, title: title});
    console.log("Sending data:", data);

    // Use the fetch API to send the POST request
    fetch('/create-pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: data
    })
    .then(response => {
        // Check if the response is ok (status in the range 200-299)
        if (!response.ok) {
            // Try to parse the error message from the response
            return response.json().then(errData => {
                console.error("Server error message:", errData);
                throw new Error(errData.message || 'Failed to create PDF');
            });
        }
        // Retrieve the filename from the Content-Disposition header
        const disposition = response.headers.get('Content-Disposition');

        let filename = 'download.pdf';
        if (disposition && disposition.indexOf('filename=') !== -1) {
            filename = disposition.split('filename=')[1].replace(/"/g, '');
        }

        return response.blob().then(blob => ({blob, filename}));
    })
    .then(({ blob, filename }) => {
        console.log("Downloading file:", filename);
        // Create a URL for the blob object
        const url = window.URL.createObjectURL(blob);
        // Create an anchor (<a>) element with the URL as the href
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    })
    .catch(error => {
        console.error('Error creating PDF:', error);
        // Display an error message to the user
        alert('An error occurred while creating the PDF: ' + error.message);
    });
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