let recognizing = false;
let isPaused = false;
let audioConfig = null;
let recognizer = null;
let speaking = false;

const status = document.getElementById('status');
const recognizedText = document.getElementById('recognizedText');
const startStopBtn = document.getElementById('startStopBtn');
const pausePlayBtn = document.getElementById('pausePlayBtn');
const transcription = document.getElementById('transcription');
const conversationsHeading = document.getElementById('conversations-heading');
const chatbotNameInput = document.getElementById('chatbotName');

document.addEventListener("DOMContentLoaded", () => {
    if (performance.navigation.type == performance.navigation.TYPE_RELOAD) {
        resetConversation()
    }
});

startStopBtn.addEventListener('click', handleStartStop);
pausePlayBtn.addEventListener('click', handlePausePlay);

// document.getElementById('chatbotName').addEventListener('input', sendFormData);
document.getElementById('llmModel').addEventListener('change', sendFormData);
document.getElementById('topic').addEventListener('input', sendFormData);
document.getElementById('prompt').addEventListener('input', sendFormData);


function handleStartStop() {
    if (startStopBtn.textContent === "End Conversation") {
        resetConversation();
        window.location.reload();

    } else {
        startConversation();
    }
}

function handlePausePlay() {
    if (isPaused) {
        resumeConversation();
    } else {
        pauseConversation();
    }
}

function formatStartOfConversation() {
    const dateTime = getFormattedDateTime();
    return `<p align="justify"><strong>[${dateTime}]</strong> Conversation Started</p>`;
}

function startConversation() {
    const chatbotNameInput = document.getElementById('chatbotName');
    const chatbotName = chatbotNameInput.value.trim();

    if (chatbotName === "" || chatbotName.length <= 2) {
        alert("Chatbot name must be more than 2 letters.");
        return;
    }
    recognizing = true;
    startStopBtn.textContent = "End Conversation";
    pausePlayBtn.style.display = "inline-block";
    sendFormData();
    send_botName();
    chatbotNameInput.disabled = true;
    transcription.innerHTML = formatStartOfConversation(); // Add this line
    startRecognition();
}

function resetConversation() {
    startStopBtn.textContent = "Start Conversation";
    recognizedText.textContent = "";
    transcription.innerHTML = "";
    window.speechSynthesis.cancel();
    // Clear client-side cache if any
    localStorage.clear();
    sessionStorage.clear();
    clearChatHistory();
    
    
}

function reload(){
    resetConversation();
    window.location.reload();
}

function pauseConversation() {
    isPaused = true;
    pausePlayBtn.textContent = "Play Conversation";
    recognizer.stopContinuousRecognitionAsync();
    status.textContent = "Status: Paused";
}

function resumeConversation() {
    isPaused = false;
    pausePlayBtn.textContent = "Pause Conversation";
    recognizer.startContinuousRecognitionAsync();
    status.textContent = "Status: Listening...";
}

function sendFormData() {
    const formData = new FormData(document.getElementById('chatbot-form'));
    formData.delete('chatbotName');
    fetch('/start/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(Object.fromEntries(formData.entries()))
    }).then(response => response.json())
      .catch(console.error);
}

function send_botName() {
    const chatbotNameInput = document.getElementById('chatbotName');
    const chatbot_name = chatbotNameInput.value.trim();

    if (chatbot_name.length <= 2) {
        alert("Chatbot name must be more than 2 letters.");
        return;
    }
    const formData = {
        chatbot_name: chatbot_name,
    };
    fetch('/chatbot_name/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(formData)
    }).then(response => response.json())
      .catch(console.error);
}

function clearChatHistory() {
    fetch('/end/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    }).then(response => response.json())
      .catch(console.error);
}

function toggleStopChatbotButton(show) {
    const stopChatbotBtn = document.getElementById('stopChatbotBtn');
    stopChatbotBtn.style.display = show ? 'inline-block' : 'none';
}

function stopChatbot() {
    window.speechSynthesis.cancel();
    speaking = false;
    toggleStopChatbotButton(false); // Hide the button when stopped
    recognizer.startContinuousRecognitionAsync();
}

function showConversationsHeading() {
    if (transcription.innerHTML.trim()) {
        conversationsHeading.style.display = 'block';
        transcription.style.display = 'block';
    } else {
        conversationsHeading.style.display = 'none';
        transcription.style.display = 'none';
    }
}

function getCookie(name) {
    return document.cookie.split(';').reduce((cookieValue, cookie) => {
        cookie = cookie.trim();
        return cookie.startsWith(name + '=') ? decodeURIComponent(cookie.substring(name.length + 1)) : cookieValue;
    }, null);
}

async function fetchApiDetails() {
    try {
        const response = await fetch('/get-api-key/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        return await response.json();
    } catch (error) {
        console.error('Error fetching API key:', error);
        return null;
    }
}

function getFormattedDateTime() {
    const now = new Date();
    const options = { 
        year: 'numeric', 
        month: 'numeric', 
        day: 'numeric', 
        hour: 'numeric', 
        minute: 'numeric', 
        hour12: false 
    };
    return now.toLocaleString('en-US', options);
}

async function startRecognition() {
    try {
        const apiDetails = await fetchApiDetails();
        if (!apiDetails || !apiDetails.subscriptionKey || !apiDetails.serviceRegion) {
            throw new Error('API details are not available');
        }

        const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(apiDetails.subscriptionKey, apiDetails.serviceRegion);
        speechConfig.speechRecognitionLanguage = 'en-US';

        await navigator.mediaDevices.getUserMedia({ audio: true });
        status.textContent = "Status: Listening...";

        audioConfig = audioConfig || SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
        recognizer = recognizer || new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);

        recognizer.recognizing = (_, e) => {
            recognizedText.textContent = `Recognizing: ${e.result.text}`;
        };

        recognizer.recognized = (_, e) => {
            if (e.result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
                handleRecognition(e.result.text);
            }
        };

        recognizer.canceled = (_, e) => {
            status.textContent = `Status: Canceled: ${e.reason}`;
        };

        recognizer.startContinuousRecognitionAsync();
    } catch (err) {
        status.textContent = `Status: Error - ${err.message}`;
    }
}

function handleRecognition(result) {
    recognizedText.textContent = `Recognized Text: ${result}`;
    transcription.innerHTML += `<p align="justify">${result}</p>`;
    showConversationsHeading();
    transcription.scrollTop = transcription.scrollHeight;

    if (result.toLowerCase().includes("stop")) {
        stopChatbot();
    }

    fetch('/recognize/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ text: result })
    }).then(response => response.json())
      .then(data => handleResponse(data))
      .catch(console.error);
}

function handleResponse(data) {
    if (data.status === 'success') {
        recognizer.stopContinuousRecognitionAsync();

        const ttsStartTime = performance.now();
        const dateTime = getFormattedDateTime();

        const botResult = `[${dateTime}]<strong>${data.chatbot_name}</strong>: ${data.response}`;
        transcription.innerHTML += `<p align="justify">${botResult}</p>`;
        transcription.scrollTop = transcription.scrollHeight;

        const u = new SpeechSynthesisUtterance(data.response);
        u.lang = 'en-US';
        // Set the speech speed (1 is normal, lower is slower, higher is faster)
        u.rate = 0.7; // Adjust this value as needed

        // Get the list of voices and select a specific voice
        const voices = speechSynthesis.getVoices();
        u.voice = voices.find(voice => voice.name === 'Microsoft David - English (United States)'); // Replace with the desired voice name
        // voices.forEach(voice => {
        //     console.log(`Name: ${voice.name}, Language: ${voice.lang}`);
        // });
        u.onstart = () => {
            speaking = true;
            toggleStopChatbotButton(true); // Show the button when speaking starts
        };
        u.onend = () => {
            console.log(`TTS Duration: ${performance.now() - ttsStartTime} milliseconds`);
            speaking = false;
            toggleStopChatbotButton(false); // Hide the button when speaking ends
            recognizer.startContinuousRecognitionAsync();
        };
        speechSynthesis.speak(u);
    }
}

function downloadCSV() {
    fetch('/download/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    }).then(response => response.ok ? response.blob() : Promise.reject('Network response was not ok.'))
      .then(blob => {
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.style.display = 'none';
          a.href = url;
          a.download = 'conversation_history.csv';
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
      })
      .catch(console.error);
}
