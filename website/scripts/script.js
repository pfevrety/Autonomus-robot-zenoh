const mainImage = document.getElementById('main-image');
mainImage.src = 'http://localhost:8000/video_feed';

const directionButtons = document.querySelectorAll('.direction');

directionButtons.forEach(button => {
    button.addEventListener('click', (event) => {

        const buttonEl = event.target.closest('.direction');
        const directionAttr = buttonEl.id; // Utilise 'up', 'down', 'left', 'right'
        
        console.log(`Direction demandée : ${directionAttr}`);
        addLog(`Commande moteur : move_${directionAttr}`, 'info');
        
        fetch('http://localhost:8000/command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: `move_${directionAttr}` })
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Erreur:', error);
            addLog(`Échec commande : ${directionAttr}`, 'error');
        });
    });
});

const targetStyles = {
    'chair': "bg-amber-900/40 text-amber-300 border border-amber-700/60",
    'car': "bg-slate-800/80 text-slate-200 border border-slate-600/60",
    'banana': "bg-yellow-500/20 text-yellow-400 border border-yellow-500/40 shadow-yellow-500/5",
    'teddy bear': "bg-orange-950/40 text-orange-400 border border-orange-800/60",
    'bottle': "bg-cyan-950/60 text-cyan-400 border border-cyan-800/60",
    'person': "bg-purple-950/50 text-purple-300 border border-purple-800/60",

    'default': "bg-slate-800 text-slate-400 border border-slate-700"
};

const queueContainer = document.getElementById('target-queue');
const objectButtons = document.querySelectorAll('.object');


function addToQueue(targetKey, displayName) {
    const queueItem = document.createElement('div');
    
    let baseClasses = "queue-item animate-pop-in text-xs font-mono uppercase font-bold tracking-wider py-1.5 px-3 rounded-lg shadow-sm ";
    
    const specificStyle = targetStyles[targetKey.toLowerCase()] || targetStyles['default'];
    
    queueItem.className = baseClasses + specificStyle;
    queueItem.textContent = displayName; 
    
    queueContainer.appendChild(queueItem);
    addLog(`Cible ajoutée aux objectifs : ${displayName}`, 'info');
        
}



objectButtons.forEach(button => {
    button.addEventListener('click', (event) => {
        const targetObject = event.target.getAttribute('data-target');
        const targetName = event.target.innerText; 
        if (targetObject === 'klaxon') {
            addLog('Klaxon activé !', 'warning');
            fetch('http://localhost:8000/klaxon', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action: 'klaxon' })
            })
            .then(response => response.json())
            .catch(error => {
                console.error('Erreur:', error);
                addLog('Échec commande : klaxon', 'error');
            });
            return;
        }
        addToQueue(targetObject, targetName);

        fetch('http://localhost:8000/add_aimed_object', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ object_name: targetObject })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Succès:', data);
            addLog(`Backend a ajouté : ${targetName} à la liste des objets visés`, 'success');
        })
        .catch(error => {
            console.error('Erreur:', error);
            addLog(`Échec ajout cible : ${targetName}`, 'error');
        });
    });
});

const clearBtn = document.getElementById('clear-queue');
clearBtn.addEventListener('click', () => {
    queueContainer.innerHTML = ''; 
    addLog('File d\'objectifs réinitialisée', 'warning');

    fetch('http://localhost:8000/clear_aimed_objects', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Succès:', data);
    })
    .catch(error => {
        console.error('Erreur:', error);
        addLog('Échec réinitialisation liste backend', 'error');
    });     

});

const consoleInput = document.getElementById('console-input');
consoleInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault();
        
        const text = consoleInput.value.trim();
        if (!text) return; 

        const words = text.split(/\s+/); 
        
        words.forEach(word => {
            const cleanWord = word.toLowerCase();

            if (targetStyles[cleanWord]) {
                addToQueue(cleanWord, word);
            } else {
                addToQueue('default', word);
            }
        });
        consoleInput.value = '';
    }
});

function addLog(message, type = 'info') {
    const logContainer = document.getElementById('log-container');
    const logEntry = document.createElement('p');
    logEntry.className = "m-0";

    switch(type) {
        case 'success':
            logEntry.classList.add('text-emerald-400');
            break;
        case 'warning':
            logEntry.classList.add('text-amber-400');
            break;
        case 'error':
            logEntry.classList.add('text-rose-400');
            break;
        case 'info':
        default:
            logEntry.classList.add('text-slate-500');
            break;
    }

    const now = new Date();
    const timeString = now.toLocaleTimeString('fr-FR', { hour12: false });

    logEntry.innerHTML = `<span class="text-slate-600">[${timeString}]</span> ${message}`;

    logContainer.appendChild(logEntry);

    logContainer.scrollTop = logContainer.scrollHeight;
}


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
        btn.classList.add('scale-95', 'bg-blue-500'); 
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
        const btn = document.getElementById(buttonId);
        // Nettoie l'effet actif du clavier
        btn.classList.remove('scale-95', 'bg-blue-500');
    }
});

const latencySlider = document.getElementById('latency-slider');
const latencyVal = document.getElementById('latency-val');
const sensitivitySlider = document.getElementById('sensitivity-slider');
const sensitivityVal = document.getElementById('sensitivity-val');

function sendSliderValue(endpoint, valueKey, value) {
    fetch(`http://localhost:8000/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [valueKey]: value })
    })
    .catch(error => {
        console.error(`Erreur sur ${endpoint}:`, error);
    });
}

if (latencySlider) {
    latencySlider.addEventListener('input', (e) => {
        const val = parseInt(e.target.value);
        latencyVal.textContent = `${val} ms`;
        sendSliderValue('update_latency', 'latency', val);
    });
}

if (sensitivitySlider) {
    sensitivitySlider.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        sensitivityVal.textContent = val.toFixed(1); 
        sendSliderValue('update_sensitivity', 'sensitivity', val);
    });
}