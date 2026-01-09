// Game state
let gameState = {
    sessionId: null,
    currentRoundId: null,
    currentRoundNumber: 0,
    hintUsed: false,
    trainingMode: false
};

// Initialize game on home page
document.addEventListener('DOMContentLoaded', function() {
    const startForm = document.getElementById('start-form');
    if (startForm) {
        startForm.addEventListener('submit', handleStartGame);
    }

    // If we're on the play page, initialize game play
    if (document.getElementById('game-screen')) {
        initializeGame();
    }
});

// Use base URL if defined globally, otherwise construct it
function getBaseUrl() {
    if (typeof BASE_URL !== 'undefined') {
        return BASE_URL;
    }
    return '/apps/personality-game/api/';
}

function getSummaryBaseUrl() {
    if (typeof SUMMARY_BASE_URL !== 'undefined') {
        return SUMMARY_BASE_URL;
    }
    return '/apps/personality-game/summary/';
}

// Handle start game form submission
async function handleStartGame(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const difficulty = formData.get('difficulty') || 'medium';
    const trainingMode = formData.get('training_mode') === 'on';

    try {
        const response = await fetch(getBaseUrl() + 'start/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                difficulty: difficulty,
                training_mode: trainingMode
            })
        });

        const data = await response.json();
        if (data.success) {
            window.location.href = `/apps/personality-game/play/${data.session_id}/`;
        } else {
            alert('Failed to start game. Please try again.');
        }
    } catch (error) {
        console.error('Error starting game:', error);
        alert('Failed to start game. Please try again.');
    }
}

// Initialize game play
async function initializeGame() {
    // Get session ID from URL or global variable
    const pathParts = window.location.pathname.split('/');
    const sessionIdx = pathParts.indexOf('play');
    if (sessionIdx !== -1 && pathParts.length > sessionIdx + 1) {
        gameState.sessionId = pathParts[sessionIdx + 1];
    } else if (typeof SESSION_ID !== 'undefined' && SESSION_ID) {
        gameState.sessionId = SESSION_ID;
    }

    // If session ID is not in URL, try to get from window location
    if (!gameState.sessionId) {
        const pathParts = window.location.pathname.split('/');
        const sessionIdx = pathParts.indexOf('play');
        if (sessionIdx !== -1 && pathParts.length > sessionIdx + 1 && pathParts[sessionIdx + 1]) {
            gameState.sessionId = pathParts[sessionIdx + 1];
        }
    }
    
    if (!gameState.sessionId) {
        alert('No session ID found. Redirecting to home...');
        window.location.href = '/apps/personality-game/';
        return;
    }

    // Set up event listeners
    document.getElementById('submit-btn').addEventListener('click', handleSubmitAnswer);
    document.getElementById('next-btn').addEventListener('click', loadNextScenario);
    document.getElementById('finish-btn').addEventListener('click', finishGame);
    
    const hintBtn = document.getElementById('hint-btn');
    if (hintBtn) {
        hintBtn.addEventListener('click', handleGetHint);
    }

    // Load first scenario
    await loadNextScenario();
}

// Load next scenario
async function loadNextScenario() {
    // Reset game state for new round
    gameState.hintUsed = false;
    gameState.currentRoundId = null;

    // Show loading screen
    document.getElementById('loading-screen').style.display = 'block';
    document.getElementById('game-screen').style.display = 'none';
    document.getElementById('feedback-screen').style.display = 'none';

    // Clear previous answers
    document.querySelectorAll('input[type="radio"]').forEach(input => {
        input.checked = false;
    });
    document.getElementById('hint-display').style.display = 'none';
    document.getElementById('hint-btn').style.display = 'none';

    try {
        const response = await fetch(getBaseUrl() + `session/${gameState.sessionId}/scenario/`);
        const data = await response.json();

        if (data.error) {
            alert('Error loading scenario: ' + data.error);
            return;
        }

        gameState.currentRoundId = data.round_id;
        gameState.currentRoundNumber = data.round_number;

        // Update UI
        document.getElementById('round-number').textContent = data.round_number;
        document.getElementById('scenario-title').textContent = data.scenario.title;

        // Render transcript
        const transcriptBox = document.getElementById('transcript-box');
        transcriptBox.innerHTML = '';
        data.scenario.transcript.forEach(line => {
            const p = document.createElement('p');
            p.textContent = line;
            transcriptBox.appendChild(p);
        });

        // Render response options
        const responseOptions = document.getElementById('response-options');
        responseOptions.innerHTML = '';
        Object.entries(data.scenario.response_choices).forEach(([key, value]) => {
            const label = document.createElement('label');
            label.className = 'response-option';
            
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'response-choice';
            radio.value = key;
            
            const span = document.createElement('span');
            span.className = 'option-label';
            span.textContent = `${key}: ${value}`;
            
            label.appendChild(radio);
            label.appendChild(span);
            responseOptions.appendChild(label);
        });

        // Show game screen
        document.getElementById('loading-screen').style.display = 'none';
        document.getElementById('game-screen').style.display = 'block';

        // Show hint button if in training mode (we'll need to check this from session)
        // For now, show it always
        document.getElementById('hint-btn').style.display = 'inline-block';

    } catch (error) {
        console.error('Error loading scenario:', error);
        alert('Failed to load scenario. Please try again.');
        document.getElementById('loading-screen').style.display = 'none';
    }
}

// Handle get hint
async function handleGetHint() {
    if (!gameState.currentRoundId) {
        alert('No active round. Please wait for scenario to load.');
        return;
    }

    try {
        const response = await fetch(getBaseUrl() + `session/${gameState.sessionId}/round/${gameState.currentRoundId}/hint/`);
        const data = await response.json();

        if (data.error) {
            alert('Error getting hint: ' + data.error);
            return;
        }

        // Display hint
        const hintDisplay = document.getElementById('hint-display');
        hintDisplay.textContent = `Tell Category: ${data.tell_category_display}${data.costs_point ? ' (-1 point)' : ''}`;
        hintDisplay.style.display = 'block';
        
        gameState.hintUsed = true;
        document.getElementById('hint-btn').style.display = 'none';

    } catch (error) {
        console.error('Error getting hint:', error);
        alert('Failed to get hint. Please try again.');
    }
}

// Handle submit answer
async function handleSubmitAnswer() {
    // Validate inputs
    const typeGuess = document.querySelector('input[name="personality-type"]:checked');
    const responseChoice = document.querySelector('input[name="response-choice"]:checked');
    const tellCategory = document.querySelector('input[name="tell-category"]:checked');

    if (!typeGuess || !responseChoice) {
        alert('Please answer all required questions (Personality Type and Response Choice).');
        return;
    }

    const answerData = {
        type_guess: typeGuess.value,
        response_choice: responseChoice.value,
        tell_category: tellCategory ? tellCategory.value : null,
        hint_used: gameState.hintUsed
    };

    try {
        const response = await fetch(getBaseUrl() + `session/${gameState.sessionId}/round/${gameState.currentRoundId}/answer/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(answerData)
        });

        const data = await response.json();

        if (data.error) {
            alert('Error submitting answer: ' + data.error);
            return;
        }

        // Show feedback
        showFeedback(data);

    } catch (error) {
        console.error('Error submitting answer:', error);
        alert('Failed to submit answer. Please try again.');
    }
}

// Show feedback
function showFeedback(feedback) {
    // Hide game screen, show feedback screen
    document.getElementById('game-screen').style.display = 'none';
    document.getElementById('feedback-screen').style.display = 'block';

    // Update stats
    document.getElementById('total-score').textContent = feedback.session_stats.total_score;
    document.getElementById('current-streak').textContent = feedback.session_stats.current_streak;

    // Build feedback content
    const feedbackContent = document.getElementById('feedback-content');
    feedbackContent.innerHTML = '';

    // Points earned
    const pointsDiv = document.createElement('div');
    pointsDiv.className = 'feedback-item';
    pointsDiv.innerHTML = `<h4>Points Earned: ${feedback.points_earned}</h4>`;
    feedbackContent.appendChild(pointsDiv);

    // Type feedback
    const typeDiv = document.createElement('div');
    typeDiv.className = `feedback-item ${feedback.type_correct ? 'correct' : 'incorrect'}`;
    typeDiv.innerHTML = `
        <h4>Personality Type: ${feedback.type_correct ? '✓ Correct' : '✗ Incorrect'}</h4>
        <p>Your answer: ${document.querySelector('input[name="personality-type"]:checked').parentElement.querySelector('.option-label').textContent}</p>
        <p>Correct answer: ${feedback.correct_type_display}</p>
    `;
    feedbackContent.appendChild(typeDiv);

    // Response feedback
    const responseDiv = document.createElement('div');
    responseDiv.className = `feedback-item ${feedback.response_correct ? 'correct' : 'incorrect'}`;
    responseDiv.innerHTML = `
        <h4>Response Choice: ${feedback.response_correct ? '✓ Correct' : '✗ Incorrect'}</h4>
        <p>Your answer: ${document.querySelector('input[name="response-choice"]:checked').value}</p>
        <p>Correct answer: ${feedback.correct_response}</p>
    `;
    feedbackContent.appendChild(responseDiv);

    // Tell category feedback
    if (feedback.tell_correct !== undefined) {
        const tellDiv = document.createElement('div');
        tellDiv.className = `feedback-item ${feedback.tell_correct ? 'correct' : 'incorrect'}`;
        const tellAnswer = document.querySelector('input[name="tell-category"]:checked');
        tellDiv.innerHTML = `
            <h4>Tell Category: ${feedback.tell_correct ? '✓ Correct (+1 bonus)' : '✗ Incorrect'}</h4>
            <p>Your answer: ${tellAnswer ? tellAnswer.value : 'Not answered'}</p>
            <p>Correct answer: ${feedback.correct_tell_category_display}</p>
        `;
        feedbackContent.appendChild(tellDiv);
    }

    // Explanations
    const explainDiv = document.createElement('div');
    explainDiv.className = 'feedback-item';
    explainDiv.innerHTML = `
        <h4>Explanation</h4>
        <p><strong>Tell Explanation:</strong> ${feedback.tell_explanation}</p>
        <p><strong>Response Explanation:</strong> ${feedback.response_explanation}</p>
    `;
    feedbackContent.appendChild(explainDiv);

    // Show finish button if this might be the last round (we can check total rounds)
    // For now, always show next button
    if (feedback.session_stats.total_rounds >= 10) {
        document.getElementById('finish-btn').style.display = 'inline-block';
    }
}

// Note: loadNextScenario is already defined above

// Finish game
function finishGame() {
    window.location.href = getSummaryBaseUrl() + `${gameState.sessionId}/`;
}

// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

