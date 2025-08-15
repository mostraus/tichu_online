const socket = io();
const joinDiv = document.getElementById("join");
const gameDiv = document.getElementById("game");
const messages = document.getElementById("messages");

document.getElementById("join-game-btn").addEventListener("click", () => {
    console.log("Join button clicked!");
    const name = document.getElementById("player-name").value.trim();
    const team = document.getElementById("team-select").value;

    if (!name || !team) {
        alert("Please enter your name and choose a team.");
        return;
    }

    socket.emit("join", { name, team });

    // Overlay ausblenden
    document.getElementById("login-overlay").classList.add("hidden");
    document.getElementById("game").style.display = "flex";
});

function submitMove() {
    const move = document.getElementById("moveInput").value.trim();
    if (move === "") return;
    socket.emit("play_card", { move });
    document.getElementById("moveInput").value = "";
}

function logMessage(msg) {
    messages.textContent += msg + "\n";
    messages.scrollTop = messages.scrollHeight;
}

// Socket Events

socket.on("game_message", data => logMessage(data.message));
socket.on("game-message", data => logMessage(data.message));  // sometimes used interchangeably
socket.on("turn_message", data => logMessage(data.message));
socket.on("error_message", data => logMessage("⚠️ " + data.message));

let selectedCards = [];

socket.on("update_hand", data => {
    const handDiv = document.getElementById("hand");
    handDiv.innerHTML = "";
    selectedCards = [];

    data.hand.forEach(filename => {
        const img = document.createElement("img");
        img.src = "/static/cards/" + filename;
        img.className = "card";
        img.onclick = () => toggleCardSelection(filename, img);
        handDiv.appendChild(img);
    });
});

function toggleCardSelection(filename, img) {
    const index = selectedCards.indexOf(filename);
    if (index === -1) {
        selectedCards.push(filename);
        img.style.border = "2px solid blue";
    } else {
        selectedCards.splice(index, 1);
        img.style.border = "";
    }
}

function submitSelectedCards() {
    if (selectedCards.length === 0) return alert("No cards selected!");
    socket.emit("play_card", { cards: selectedCards });
    selectedCards = [];
    document.getElementById("tichu-btn").style.display = "none";
}

socket.on("last_played", data => {
    const lastPlayedDiv = document.getElementById("last-played");
    lastPlayedDiv.innerHTML = "";
    data.cards.forEach(filename => {
        const img = document.createElement("img");
        img.src = "/static/cards/" + filename;
        img.className = "card";
        lastPlayedDiv.appendChild(img);
    });
});

function passTurn() {
    socket.emit("pass");
}

socket.on("your_turn", data => {
    if (data.your_turn) {
        logMessage("🎯 It's your turn!");
    } else {
        logMessage("⏳ Waiting for other players...");
    }
});

socket.on("turn_update", data => {
    console.log("Turn Update received", data);
    const turnInfo = document.getElementById("turn-info");
    const current = data.current;
    const you = data.you;

    if (current === you) {
        turnInfo.textContent = "👉 Your Turn!";
        enableControls(true);
    } else {
        turnInfo.textContent = `Waiting for ${current}...`;
        enableControls(false);
    }
});

function enableControls(enable) {
    document.getElementById("moveInput").disabled = !enable;
    document.querySelector("button[onclick='submitMove()']").disabled = !enable;
}

const dragonOverlay = document.getElementById("dragon-overlay");
const dragonButtonsDiv = document.getElementById("dragon-buttons");

socket.on('choose_dragon_recipient', data => {
    dragonButtonsDiv.innerHTML = ""; // vorher leeren
    data.recipients.forEach(name => {
        const btn = document.createElement("button");
        btn.textContent = name;
        btn.onclick = () => {
            socket.emit('dragon_recipient_selected', { recipient: name });
            dragonOverlay.style.display = "none";
        };
        dragonButtonsDiv.appendChild(btn);
    });
    dragonOverlay.style.display = "flex";
});

socket.on("ask_wish", () => {
    const wish = prompt("Make your wish (2, 5, K, A or None):");
    if (["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A", "None"].includes(wish.toUpperCase())) {
        socket.emit("wish_card", { wish: wish.toUpperCase() });
    } else {
        alert("Invalid wish!");
    }
});

socket.on("round_over", data => {
    const scoreDiv = document.getElementById("score-display");
    scoreDiv.innerHTML = `
        <p>Team A: ${data.scores.A} Punkte</p>
        <p>Team B: ${data.scores.B} Punkte</p>
        <hr>
        <p>+${data.round_points.A} Punkte für Team A in dieser Runde</p>
        <p>+${data.round_points.B} Punkte für Team B in dieser Runde</p>
    `;
    document.getElementById("round-overlay").style.display = "flex";
});

function readyNextRound() {
    socket.emit("ready_for_next_round");
    document.getElementById("round-overlay").style.display = "none";
}

function sendGrandTichu(choice) {
    socket.emit("grand_tichu_choice", { choice: choice });
    document.getElementById("grand-tichu-overlay").style.display = "none";
}

socket.on("choose_grand_tichu", () => {
    document.getElementById("grand-tichu-overlay").style.display = "block";
});

socket.on("call_grand_tichu", () => {
    showOverlay("grand-tichu-overlay");
});

document.getElementById("sendGrandTichuYes").addEventListener('click', () => {
    socket.emit("grand_tichu_choice", {'choice': true});
    hideOverlay("grand-tichu-overlay");
});

document.getElementById("sendGrandTichuNo").addEventListener('click', () => {
    socket.emit("grand_tichu_choice", {'choice': false});
    hideOverlay("grand-tichu-overlay");
});

function callTichu() {
    socket.emit("tichu_call", { choice: true });
}

let selectedCard = null;
let passAssignments = {}; // { targetName: cardId }

socket.on("start_passing", (data) => {

    passAssignments = {};
    selectedCard = null;
    document.getElementById("confirm-pass").disabled = true;

    // Handkarten anzeigen
    const handDiv = document.getElementById("passing-hand");
    handDiv.innerHTML = "";
    data.cards.forEach(card => {
        const img = document.createElement("img");
        img.classList.add("card")
        img.src = card.image;
        img.dataset.cardId = card.id;
        img.addEventListener("click", () => {
            document.querySelectorAll("#passing-hand img").forEach(c => c.classList.remove("selected"));
            img.classList.add("selected");
            selectedCard = card.id;
        });
        handDiv.appendChild(img);
    });
    updatePassSummary()
    // Ziel-Buttons dynamisch erstellen
    const targetsDiv = document.getElementById("passing-targets");
    targetsDiv.innerHTML = "";
    data.targets.forEach(targetName => {
        const targetBtn = document.createElement("div");
        targetBtn.classList.add("target");
        targetBtn.dataset.target = targetName;
        targetBtn.textContent = targetName;

        targetBtn.addEventListener("click", () => {
            if (!selectedCard) return alert("Select a card first!");

            passAssignments[targetName] = selectedCard;

            // Falls für diesen Spieler schon eine Karte zugewiesen ist → zurück in Hand
            if (passAssignments[targetName]) {
                const oldCard = passAssignments[targetName];
                renderCardBackToHand(oldCard);
            }

            // Markiere Button als ausgewählt
            targetBtn.classList.add("selected");

            // Entferne Karte aus Anzeige
            const img = document.querySelector(`#passing-hand img[data-card-id='${selectedCard}']`);
            if (img) img.remove();

            selectedCard = null;
            updatePassSummary()
            // Prüfen ob alle Ziele belegt sind
            if (Object.keys(passAssignments).length === data.targets.length) {
                document.getElementById("confirm-pass").disabled = true; // erst erlauben, wenn komplett
                document.getElementById("confirm-pass").disabled = false;
            }
        });

        targetsDiv.appendChild(targetBtn);
    });

    // Overlay anzeigen
    document.getElementById("left-panel").classList.add("hidden");
    showOverlay("passing-overlay");
});

// Bestätigung
document.getElementById("confirm-pass").addEventListener("click", () => {
    socket.emit("pass_cards", { assignments: passAssignments });
    hideOverlay("passing-overlay");
    document.getElementById("left-panel").classList.remove("hidden");

});

function renderCardBackToHand(card) {
    const specialCards = ["dragon", "mah jong", "phoenix", "dog"];
    const handDiv = document.getElementById("passing-hand");
    let img = document.createElement("img");
    if (specialCards.includes(card.toLowerCase())) {
        img.src = `/static/cards/${card.toLowerCase()}.png`;
    } else {
        let [value, suit] = card.split("_");  // "8_spades" → ["8", "spades"]
        img.src = `/static/cards/${suit}_${value}.png`;  // "spades_8.png"
    }
    img.classList.add("card")
    img.dataset.card = card;
    img.addEventListener("click", () => {
        document.querySelectorAll("#passing-hand img").forEach(c => c.classList.remove("selected"));
        img.classList.add("selected");
        selectedCard = card;
    });
    handDiv.appendChild(img);
}

function showOverlay(id) {
    document.getElementById(id).classList.remove("hidden");
}

function hideOverlay(id) {
    document.getElementById(id).classList.add("hidden");
}

passAssignments[target] = selectedCard;
updatePassSummary();

function updatePassSummary() {
    const summary = document.getElementById("pass-summary");
    summary.innerHTML = "";
    for (let player in passAssignments) {
        if (passAssignments[player]) {
            summary.innerHTML += `<p>${passAssignments[player]} → ${player}</p>`;
        } else {
            summary.innerHTML += `<p>– → ${player}</p>`;
        }
    }
}

