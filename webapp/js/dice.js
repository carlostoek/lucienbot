/**
 * Lucien Dice WebApp - Three.js Implementation
 * Visualizacion 3D de dados con fisica simple
 */

// ============================================
// CONFIGURACION
// ============================================
const CONFIG = {
    diceSize: 0.9,
    diceSpacing: 1.6,
    floorY: -2,
    animationDuration: 2000, // ms
    gravity: 0.5,
    bounceDamping: 0.6,
    // Limites para que los dados no salgan de pantalla
    bounds: {
        minX: -3.5,
        maxX: 3.5,
        minZ: -4,
        maxZ: 4
    },
    colors: {
        dice: 0xf5f5f5,
        dots: 0x1a1a1a,
        floor: 0x2a2a2a,
        ambient: 0xffffff,
        directional: 0xffffff
    }
};

// ============================================
// ESTADO GLOBAL
// ============================================
const state = {
    isRolling: false,
    dice: [],
    diceValues: [1, 1],
    scene: null,
    camera: null,
    renderer: null,
    telegramUser: null,
    animationId: null
};

// ============================================
// INICIALIZACION DE TELEGRAM WEBAPP
// ============================================
function initTelegramWebApp() {
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;

        // Expandir a pantalla completa
        tg.expand();

        // Configurar tema
        tg.setHeaderColor('#1a1a1a');
        tg.setBackgroundColor('#121212');

        // Obtener datos del usuario
        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            state.telegramUser = tg.initDataUnsafe.user;
            console.log('Usuario Telegram:', state.telegramUser.id);
        }

        // Listo
        tg.ready();

        return tg;
    }
    return null;
}

// ============================================
// GENERACION DE TEXTURAS DE DADO
// ============================================
function createDiceFaceTexture(number) {
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');

    // Fondo blanco del dado
    ctx.fillStyle = '#f5f5f5';
    ctx.fillRect(0, 0, 128, 128);

    // Borde sutil
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 2;
    ctx.strokeRect(1, 1, 126, 126);

    // Dibujar puntos
    ctx.fillStyle = '#1a1a1a';
    const dotRadius = 10;
    const positions = {
        1: [[64, 64]],
        2: [[32, 32], [96, 96]],
        3: [[32, 32], [64, 64], [96, 96]],
        4: [[32, 32], [96, 32], [32, 96], [96, 96]],
        5: [[32, 32], [96, 32], [64, 64], [32, 96], [96, 96]],
        6: [[32, 32], [96, 32], [32, 64], [96, 64], [32, 96], [96, 96]]
    };

    const dots = positions[number] || positions[1];
    dots.forEach(([x, y]) => {
        ctx.beginPath();
        ctx.arc(x, y, dotRadius, 0, Math.PI * 2);
        ctx.fill();

        // Sombra sutil para los puntos
        ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
        ctx.shadowBlur = 2;
        ctx.shadowOffsetX = 1;
        ctx.shadowOffsetY = 1;
    });

    return new THREE.CanvasTexture(canvas);
}

// ============================================
// CREACION DEL DADO
// ============================================
function createDie(xPosition) {
    const geometry = new THREE.BoxGeometry(CONFIG.diceSize, CONFIG.diceSize, CONFIG.diceSize);

    // Crear materiales para cada cara (orden Three.js: right, left, top, bottom, front, back)
    // Mapeo: 1=front, 6=back, 2=bottom, 5=top, 3=right, 4=left
    const materials = [
        new THREE.MeshStandardMaterial({ map: createDiceFaceTexture(3) }), // right
        new THREE.MeshStandardMaterial({ map: createDiceFaceTexture(4) }), // left
        new THREE.MeshStandardMaterial({ map: createDiceFaceTexture(5) }), // top
        new THREE.MeshStandardMaterial({ map: createDiceFaceTexture(2) }), // bottom
        new THREE.MeshStandardMaterial({ map: createDiceFaceTexture(1) }), // front
        new THREE.MeshStandardMaterial({ map: createDiceFaceTexture(6) })  // back
    ];

    const die = new THREE.Mesh(geometry, materials);
    die.position.set(xPosition, 0, 0);
    die.castShadow = true;
    die.receiveShadow = true;

    // Propiedades para animacion
    die.userData = {
        velocity: new THREE.Vector3(0, 0, 0),
        angularVelocity: new THREE.Vector3(0, 0, 0),
        isSettled: true,
        targetValue: 1
    };

    return die;
}

// ============================================
// INICIALIZACION DE THREE.JS
// ============================================
function initThreeJS() {
    const container = document.getElementById('canvas-container');
    const canvas = document.getElementById('dice-canvas');

    // Escena
    state.scene = new THREE.Scene();
    state.scene.background = new THREE.Color(0x121212);

    // Camara
    const aspect = container.clientWidth / container.clientHeight;
    state.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 100);
    state.camera.position.set(0, 4, 8);
    state.camera.lookAt(0, 0, 0);

    // Renderer
    state.renderer = new THREE.WebGLRenderer({
        canvas: canvas,
        antialias: true,
        alpha: true
    });
    state.renderer.setSize(container.clientWidth, container.clientHeight);
    state.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    state.renderer.shadowMap.enabled = true;
    state.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // Iluminacion ambiental
    const ambientLight = new THREE.AmbientLight(CONFIG.colors.ambient, 0.6);
    state.scene.add(ambientLight);

    // Luz direccional principal
    const directionalLight = new THREE.DirectionalLight(CONFIG.colors.directional, 0.8);
    directionalLight.position.set(5, 10, 5);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    state.scene.add(directionalLight);

    // Luz de acento dorada
    const accentLight = new THREE.PointLight(0xd4af37, 0.4, 10);
    accentLight.position.set(-3, 3, 3);
    state.scene.add(accentLight);

    // Piso
    const floorGeometry = new THREE.PlaneGeometry(20, 20);
    const floorMaterial = new THREE.MeshStandardMaterial({
        color: CONFIG.colors.floor,
        roughness: 0.8,
        metalness: 0.2
    });
    const floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = CONFIG.floorY;
    floor.receiveShadow = true;
    state.scene.add(floor);

    // Crear dados
    const die1 = createDie(-CONFIG.diceSpacing / 2);
    const die2 = createDie(CONFIG.diceSpacing / 2);
    state.dice = [die1, die2];
    state.scene.add(die1);
    state.scene.add(die2);

    // Manejar resize
    window.addEventListener('resize', onWindowResize);

    // Iniciar loop de renderizado
    animate();
}

// ============================================
// MANEJO DE RESIZE
// ============================================
function onWindowResize() {
    const container = document.getElementById('canvas-container');
    const aspect = container.clientWidth / container.clientHeight;

    state.camera.aspect = aspect;
    state.camera.updateProjectionMatrix();
    state.renderer.setSize(container.clientWidth, container.clientHeight);
}

// ============================================
// ANIMACION PRINCIPAL
// ============================================
function animate() {
    state.animationId = requestAnimationFrame(animate);

    // Actualizar fisica de dados
    updateDicePhysics();

    // Renderizar
    state.renderer.render(state.scene, state.camera);
}

// ============================================
// FISICA DE DADOS
// ============================================
function updateDicePhysics() {
    state.dice.forEach(die => {
        if (die.userData.isSettled) return;

        // Aplicar gravedad
        die.userData.velocity.y -= CONFIG.gravity * 0.016;

        // Actualizar posicion
        die.position.add(die.userData.velocity.clone().multiplyScalar(0.1));

        // Actualizar rotacion
        die.rotation.x += die.userData.angularVelocity.x * 0.1;
        die.rotation.y += die.userData.angularVelocity.y * 0.1;
        die.rotation.z += die.userData.angularVelocity.z * 0.1;

        // Colision con el piso
        const floorLevel = CONFIG.floorY + CONFIG.diceSize / 2;
        if (die.position.y < floorLevel) {
            die.position.y = floorLevel;
            die.userData.velocity.y *= -CONFIG.bounceDamping;
            die.userData.velocity.x *= 0.9;
            die.userData.velocity.z *= 0.9;
            die.userData.angularVelocity.multiplyScalar(0.8);

            // Verificar si se detuvo
            if (Math.abs(die.userData.velocity.y) < 0.1 &&
                Math.abs(die.userData.angularVelocity.x) < 0.1) {
                die.userData.isSettled = true;
                snapToNearestFace(die);
            }
        }

        // Limitar posicion para que no salgan de pantalla
        die.position.x = Math.max(CONFIG.bounds.minX, Math.min(CONFIG.bounds.maxX, die.position.x));
        die.position.z = Math.max(CONFIG.bounds.minZ, Math.min(CONFIG.bounds.maxZ, die.position.z));

        // Reducir velocidad si se acerca a los limites
        if (Math.abs(die.position.x) > CONFIG.bounds.maxX * 0.8) {
            die.userData.velocity.x *= 0.8;
        }
        if (Math.abs(die.position.z) > CONFIG.bounds.maxZ * 0.8) {
            die.userData.velocity.z *= 0.8;
        }
    });

    // Verificar si ambos dados se detuvieron
    if (state.isRolling && state.dice.every(d => d.userData.isSettled)) {
        onRollComplete();
    }
}

// ============================================
// AJUSTAR A CARA MAS CERCANA
// ============================================
function snapToNearestFace(die) {
    // Redondear rotacion a multiplos de PI/2
    die.rotation.x = Math.round(die.rotation.x / (Math.PI / 2)) * (Math.PI / 2);
    die.rotation.y = Math.round(die.rotation.y / (Math.PI / 2)) * (Math.PI / 2);
    die.rotation.z = Math.round(die.rotation.z / (Math.PI / 2)) * (Math.PI / 2);
}

// ============================================
// CALCULAR VALOR DEL DADO BASADO EN ROTACION
// ============================================
function calculateDieValue(die) {
    // Vector "up" del dado en coordenadas mundiales
    const up = new THREE.Vector3(0, 1, 0);
    up.applyQuaternion(die.quaternion);

    // Determinar cual cara esta hacia arriba
    // Caras: +y=5, -y=2, +z=1, -z=6, +x=3, -x=4
    const faces = [
        { normal: new THREE.Vector3(0, 1, 0), value: 5 },
        { normal: new THREE.Vector3(0, -1, 0), value: 2 },
        { normal: new THREE.Vector3(0, 0, 1), value: 1 },
        { normal: new THREE.Vector3(0, 0, -1), value: 6 },
        { normal: new THREE.Vector3(1, 0, 0), value: 3 },
        { normal: new THREE.Vector3(-1, 0, 0), value: 4 }
    ];

    let maxDot = -Infinity;
    let topValue = 1;

    faces.forEach(face => {
        const dot = up.dot(face.normal);
        if (dot > maxDot) {
            maxDot = dot;
            topValue = face.value;
        }
    });

    return topValue;
}

// ============================================
// LANZAR DADOS
// ============================================
function rollDice() {
    if (state.isRolling) return;

    state.isRolling = true;
    state.diceValues = [1, 1];

    // Ocultar resultado anterior
    const resultDisplay = document.getElementById('result-display');
    resultDisplay.classList.add('hidden');

    // Deshabilitar boton
    const rollBtn = document.getElementById('roll-btn');
    rollBtn.disabled = true;

    // Mostrar loading
    const loading = document.getElementById('loading');
    loading.classList.remove('hidden');

    // Configurar cada dado
    state.dice.forEach((die, index) => {
        // Posicion inicial aleatoria pero dentro de limites
        die.position.y = 3 + Math.random() * 2;
        die.position.x = (index === 0 ? -1 : 1) * (0.8 + Math.random() * 0.4);
        die.position.z = (Math.random() - 0.5) * 1.5;

        // Velocidad inicial aleatoria (mas controlada para no salir de pantalla)
        die.userData.velocity.set(
            (Math.random() - 0.5) * 0.3,
            Math.random() * 0.3,
            (Math.random() - 0.5) * 0.3
        );

        // Velocidad angular aleatoria (menos intensa para no volar fuera)
        die.userData.angularVelocity.set(
            (Math.random() - 0.5) * 0.5,
            (Math.random() - 0.5) * 0.5,
            (Math.random() - 0.5) * 0.5
        );

        die.userData.isSettled = false;

        // Valor objetivo aleatorio (1-6)
        die.userData.targetValue = Math.floor(Math.random() * 6) + 1;
    });
}

// ============================================
// AL COMPLETAR EL LANZAMIENTO
// ============================================
function onRollComplete() {
    state.isRolling = false;

    // Calcular valores finales
    state.diceValues = state.dice.map(die => calculateDieValue(die));
    const total = state.diceValues[0] + state.diceValues[1];

    // Determinar si es victoria
    const die1 = state.diceValues[0];
    const die2 = state.diceValues[1];
    const die1Even = die1 % 2 === 0;
    const die2Even = die2 % 2 === 0;
    const isDouble = die1 === die2;
    const isWin = (die1Even && die2Even) || isDouble;

    // Mostrar modal con resultado
    showResultModal(die1, die2, total, isWin);

    // Ocultar loading
    const loading = document.getElementById('loading');
    loading.classList.add('hidden');

    // Habilitar boton
    const rollBtn = document.getElementById('roll-btn');
    rollBtn.disabled = false;

    // Enviar resultado a Telegram si esta disponible
    sendResultToBot(die1, die2, total);
}

// ============================================
// MOSTRAR MODAL DE RESULTADO
// ============================================
function showResultModal(die1, die2, total, isWin) {
    const modal = document.getElementById('result-modal');
    const modalEmoji = document.getElementById('modal-emoji');
    const modalTitle = document.getElementById('modal-title');
    const modalMessage = document.getElementById('modal-message');
    const modalReward = document.getElementById('modal-reward');

    if (isWin) {
        // Victoria
        modalEmoji.textContent = '🎉💖';
        modalTitle.textContent = '¡Ganaste!';
        modalTitle.style.color = 'var(--accent-gold)';

        // Mensaje de victoria
        if (die1 === die2) {
            modalMessage.textContent = `¡Doble ${die1}! Los dados te sonríen.`;
        } else {
            modalMessage.textContent = `${die1} + ${die2} = ${total}. Ambas son pares.`;
        }

        modalReward.textContent = '+1 besito 💋';
        modalReward.style.display = 'block';

        // Mensaje adicional para revisar el chat
        const chatNotice = document.createElement('p');
        chatNotice.className = 'modal-chat-notice';
        chatNotice.textContent = '✨ Revisa el chat para ver tu recompensa';
        chatNotice.style.cssText = 'font-size: 0.9rem; color: #d4af37; margin-top: 0.5rem; font-style: italic;';
        modalReward.appendChild(chatNotice);
    } else {
        // Derrota
        modalEmoji.textContent = '😔';
        modalTitle.textContent = 'No fue esta vez';
        modalTitle.style.color = 'var(--text-secondary)';

        if (total === 12) {
            modalMessage.textContent = '¡Doble seis! Pero no fue suficiente...';
        } else if (total === 2) {
            modalMessage.textContent = 'Snake eyes... la suerte cambiará.';
        } else {
            modalMessage.textContent = `${die1} + ${die2} = ${total}. Intenta de nuevo.`;
        }

        modalReward.style.display = 'none';
    }

    // Mostrar modal
    modal.classList.remove('hidden');

    // Configurar boton de cerrar
    const closeBtn = document.getElementById('modal-close');
    closeBtn.onclick = () => {
        modal.classList.add('hidden');
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.close();
        }
    };
}

// ============================================
// ACTUALIZAR DISPLAY DE RESULTADO
// ============================================
function updateResultDisplay(die1, die2, total) {
    const resultDisplay = document.getElementById('result-display');
    const die1Value = document.getElementById('die-1-value');
    const die2Value = document.getElementById('die-2-value');
    const totalValue = document.getElementById('total-value');
    const resultMessage = document.getElementById('result-message');

    die1Value.textContent = die1;
    die2Value.textContent = die2;
    totalValue.textContent = total;

    // Mensaje segun resultado
    let message = '';
    if (total === 12) {
        message = '¡Doble seis! La fortuna te favorece hoy.';
    } else if (total === 2) {
        message = 'Snake eyes... la suerte cambiara.';
    } else if (die1 === die2) {
        message = '¡Doble! Los dados te sonrien.';
    } else if (total >= 9) {
        message = 'Una tirada excelente.';
    } else if (total >= 6) {
        message = 'Una tirada decente.';
    } else {
        message = 'La proxima sera mejor.';
    }
    resultMessage.textContent = message;

    // Mostrar resultado
    resultDisplay.classList.remove('hidden');
}

// ============================================
// ENVIAR RESULTADO AL BOT
// ============================================
function sendResultToBot(die1, die2, total) {
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;

        // Determinar si es victoria segun reglas del juego
        // Victoria: ambos pares (2,4,6) o dobles (mismo numero)
        const die1Even = die1 % 2 === 0;
        const die2Even = die2 % 2 === 0;
        const isDouble = die1 === die2;
        const isWin = (die1Even && die2Even) || isDouble;

        const data = {
            dice1: die1,
            dice2: die2,
            sum: total,
            win: isWin,
            user_id: state.telegramUser ? state.telegramUser.id : null,
            timestamp: Date.now()
        };

        // Enviar datos al bot
        tg.sendData(JSON.stringify(data));
        console.log('Resultado enviado al bot:', data);

        // NO cerrar WebApp automaticamente - permitir que el usuario vea
        // la notificacion del bot en el chat antes de cerrar manualmente
    }
}

// ============================================
// INICIALIZACION PRINCIPAL
// ============================================
function init() {
    // Inicializar Telegram WebApp
    initTelegramWebApp();

    // Inicializar Three.js
    initThreeJS();

    // Configurar boton
    const rollBtn = document.getElementById('roll-btn');
    rollBtn.addEventListener('click', rollDice);

    console.log('Lucien Dice WebApp inicializado');
}

// Iniciar cuando el DOM este listo
document.addEventListener('DOMContentLoaded', init);
