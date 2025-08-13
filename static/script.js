const socket = io();
const joinDiv = document.getElementById("join");
const gameDiv = document.getElementById("game");
const messages = document.getElementById("messages");

function joinGame() {
    const name = document.getElementById("nameInput").value.trim();
    if (name === "") return alert("Enter a name first.");
    socket.emit("join", { name });
    joinDiv.style.display = "none";
    gameDiv.style.display = "block";
    logMessage("✅ Joined game as " + name);
}

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
    document.getElementById('grand-tichu-overlay').classList.remove('hidden');
});

document.getElementById("sendGrandTichuYes").addEventListener('click', () => {
    socket.emit("grand_tichu_choice", {'choice': true});
    document.getElementById('grand-tichu-overlay').classList.add('hidden');
});

document.getElementById("sendGrandTichuNo").addEventListener('click', () => {
    socket.emit("grand_tichu_choice", {'choice': false});
    document.getElementById('grand-tichu-overlay').classList.add('hidden');
});