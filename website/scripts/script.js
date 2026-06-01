const queueContainer = document.getElementById('target-queue');
const objectButtons = document.querySelectorAll('.object');

objectButtons.forEach(button => {
    button.addEventListener('click', (event) => {
        const targetObject = event.target.getAttribute('data-target');
        const targetName = event.target.innerText; 
        
        // Création de la pastille visuelle
        const queueItem = document.createElement('div');
        queueItem.classList.add('queue-item');
        // On donne à la pastille le nom affiché sur le bouton
        queueItem.textContent = targetName; 
        
        // Ajout dans la zone HTML
        queueContainer.appendChild(queueItem);
        
        console.log(`Cible ajoutée à la séquence : ${targetObject}`);
    });
});
// Écouteurs pour la croix directionnelle
const directionButtons = document.querySelectorAll('.direction');

directionButtons.forEach(button => {
    button.addEventListener('click', (event) => {
        const direction = event.target.innerText;
        console.log(`Commande de déplacement envoyée : ${direction}`);
        // Logique d'envoi vers le robot ici
    });
});


objectButtons.forEach(button => {
    button.addEventListener('click', (event) => {
        // On récupère la valeur stockée dans data-target
        const targetObject = event.target.getAttribute('data-target');
        console.log(`Recherche activée pour la cible : ${targetObject}`);
        // Logique pour lancer le script de vision ici
    });
});

// Gestion des contrôles au clavier
document.addEventListener('keydown', (event) => {
    let buttonId = null;

    // Association des touches aux IDs des boutons
    switch(event.key) {
        case 'ArrowUp': buttonId = 'up'; break;
        case 'ArrowDown': buttonId = 'down'; break;
        case 'ArrowLeft': buttonId = 'left'; break;
        case 'ArrowRight': buttonId = 'right'; break;
    }

    if (buttonId) {
        // Empêche le défilement de la page
        event.preventDefault(); 
        
        const btn = document.getElementById(buttonId);
        // Ajoute une classe pour l'effet visuel d'enfoncement
        btn.classList.add('keyboard-active'); 
        // Simule le clic pour déclencher ton `console.log` ou ta future logique
        btn.click(); 
    }
});

// Relâchement de la touche pour annuler l'effet visuel
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