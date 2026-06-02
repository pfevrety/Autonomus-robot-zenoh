const mainImage = document.getElementById('main-image');
mainImage.src = 'http://localhost:8000/video_feed';

const directionButtons = document.querySelectorAll('.direction');

directionButtons.forEach(button => {
    button.addEventListener('click', (event) => {
        const direction = event.target.innerText;
        console.log(direction);
        
        fetch('http://localhost:8000/command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: `move_${direction.toLowerCase()}` })
        })
        .then(response => response.json())
        .then(data => console.log('Succès:', data))
        .catch(error => console.error('Erreur:', error));
    });
});

// cibles et file d'attente
const queueContainer = document.getElementById('target-queue');
const objectButtons = document.querySelectorAll('.object');

const validTargets = {
    'tasse': 'Tasse',
    'voiture': 'Voiture',
    'banane': 'Banane',
    'teddy': 'Teddy Bear',
    'brosse': 'Brosse à dent',
    'personne': 'Personne'
};

function addToQueue(targetKey, displayName) {
    const queueItem = document.createElement('div');
    queueItem.classList.add('queue-item');
    queueItem.textContent = displayName; 
    queueContainer.appendChild(queueItem);
}

objectButtons.forEach(button => {
    button.addEventListener('click', (event) => {
        const targetObject = event.target.getAttribute('data-target');
        const targetName = event.target.innerText; 
        addToQueue(targetObject, targetName);
    });
});

const clearBtn = document.getElementById('clear-queue');
clearBtn.addEventListener('click', () => {
    queueContainer.innerHTML = ''; 
});

// console textuelle
const consoleInput = document.getElementById('console-input');
consoleInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault();
        
        const text = consoleInput.value.trim().toLowerCase();
        if (!text) return; 

        const words = text.split(/\s+/); 
        
        words.forEach(word => {
            addToQueue(word, word);
            
        });
        consoleInput.value = '';
    }
});



function addLog(message, type = 'info') {
    const logContainer = document.getElementById('log-container');

    const logEntry = document.createElement('div');
    logEntry.classList.add('log-entry', `log-${type}`);

    const now = new Date();
    const timeString = now.toLocaleTimeString('fr-FR', { hour12: false });

    logEntry.textContent = `[${timeString}] ${message}`;

    logContainer.appendChild(logEntry);

    logContainer.scrollTop = logContainer.scrollHeight;
}

// Gestion des contrôles au clavier
document.addEventListener('keydown', (event) => {
    let buttonId = null;

    switch(event.key) {
        case 'ArrowUp': buttonId = 'up'; break;
        case 'ArrowDown': buttonId = 'down'; break;
        case 'ArrowLeft': buttonId = 'left'; break;
        case 'ArrowRight': buttonId = 'right'; break;
    }

    if (buttonId) {
        event.preventDefault(); 
        
        const btn = document.getElementById(buttonId);
        btn.classList.add('keyboard-active'); 
        btn.click(); 
    }
});

document.addEventListener('keyup', (event) => {
    let buttonId = null;

    switch(event.key) {
        case 'ArrowUp': buttonId = 'up'; break;
        case 'ArrowDown': buttonId = 'down'; break;
        case 'ArrowLeft': buttonId = 'left'; break;
        case 'ArrowRight': buttonId = 'right'; break;
    }

    if (buttonId) {
        document.getElementById(buttonId).classList.remove('keyboard-active');
    }
});