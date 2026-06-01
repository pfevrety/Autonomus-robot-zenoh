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