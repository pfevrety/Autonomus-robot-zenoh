// --- CONFIGURATION DU FLUX VIDÉO ---
const mainImage = document.getElementById('main-image');
mainImage.src = 'http://localhost:8000/video_feed';

// --- CONTROLES MANUELS (FETCH / DIRECTION) ---
const directionButtons = document.querySelectorAll('.direction');

directionButtons.forEach(button => {
    button.addEventListener('click', (event) => {
        // Gestion si le clic tape sur l'icône texte interne
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
        .then(data => {
            console.log('Succès:', data);
            addLog(`Robot a pivoté vers : ${directionAttr}`, 'success');
        })
        .catch(error => {
            console.error('Erreur:', error);
            addLog(`Échec commande : ${directionAttr}`, 'error');
        });
    });
});

// --- DICTIONNAIRE DES STYLES TAILWIND POUR LES OBJECTIFS ---
// Permet d'associer des classes uniques et propres à chaque type de badge
const targetStyles = {
    'tasse': "bg-amber-900/40 text-amber-300 border border-amber-700/60",
    'voiture': "bg-slate-800/80 text-slate-200 border border-slate-600/60",
    'banane': "bg-yellow-500/20 text-yellow-400 border border-yellow-500/40 shadow-yellow-500/5",
    'teddy': "bg-orange-950/40 text-orange-400 border border-orange-800/60",
    'brosse': "bg-cyan-950/60 text-cyan-400 border border-cyan-800/60",
    'personne': "bg-purple-950/50 text-purple-300 border border-purple-800/60",
    // Style par défaut pour les mots saisis dans la console inconnus
    'default': "bg-slate-800 text-slate-400 border border-slate-700"
};

const queueContainer = document.getElementById('target-queue');
const objectButtons = document.querySelectorAll('.object');

// --- FONCTION AJOUT FIL D'ATTENTE (CORRIGÉE POUR TAILWIND) ---
function addToQueue(targetKey, displayName) {
    const queueItem = document.createElement('div');
    
    // Classes de base communes à tous les badges (Tailwind)
    let baseClasses = "queue-item animate-pop-in text-xs font-mono uppercase font-bold tracking-wider py-1.5 px-3 rounded-lg shadow-sm ";
    
    // Récupération du style spécifique ou application du style par défaut
    const specificStyle = targetStyles[targetKey.toLowerCase()] || targetStyles['default'];
    
    // Injection du style complet et du texte
    queueItem.className = baseClasses + specificStyle;
    queueItem.textContent = displayName; 
    
    queueContainer.appendChild(queueItem);
    addLog(`Cible ajoutée aux objectifs : ${displayName}`, 'info');
}

// Clic sur les boutons de cibles graphiques
objectButtons.forEach(button => {
    button.addEventListener('click', (event) => {
        const targetObject = event.target.getAttribute('data-target');
        const targetName = event.target.innerText; 
        addToQueue(targetObject, targetName);
    });
});

// Bouton Effacer la file
const clearBtn = document.getElementById('clear-queue');
clearBtn.addEventListener('click', () => {
    queueContainer.innerHTML = ''; 
    addLog('File d\'objectifs réinitialisée', 'warning');
});

// --- CONSOLE TEXTUELLE ---
const consoleInput = document.getElementById('console-input');
consoleInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault();
        
        const text = consoleInput.value.trim();
        if (!text) return; 

        // Sépare par les espaces pour gérer les séquences de mots
        const words = text.split(/\s+/); 
        
        words.forEach(word => {
            const cleanWord = word.toLowerCase();
            // Si le mot existe dans nos styles de cibles, on utilise sa clé, sinon style par défaut
            if (targetStyles[cleanWord]) {
                addToQueue(cleanWord, word);
            } else {
                addToQueue('default', word);
            }
        });
        consoleInput.value = '';
    }
});

// --- LOGS SYSTÈME (CORRIGÉS POUR TAILWIND) ---
function addLog(message, type = 'info') {
    const logContainer = document.getElementById('log-container');
    const logEntry = document.createElement('p'); // Changement en <p> pour matcher les exemples HTML
    logEntry.className = "m-0"; // Retire les marges par défaut des paragraphes

    // Association des couleurs de logs dynamiques en Tailwind
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

    // Injection de la structure avec le timestamp grisé
    logEntry.innerHTML = `<span class="text-slate-600">[${timeString}]</span> ${message}`;

    logContainer.appendChild(logEntry);

    // Auto-scroll vers le bas
    logContainer.scrollTop = logContainer.scrollHeight;
}

// --- GESTION DES CONTROLES AU CLAVIER ---
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
        // Ajoute les classes d'activation Tailwind dynamiquement au D-Pad lors de l'appui touche
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