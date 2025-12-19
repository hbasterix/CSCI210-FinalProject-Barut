console.log("script.js loaded ✅");

async function refreshLeaderboards() {
  const byName = await fetch("/api/leaderboard?sort=name").then(r => r.json());
  const byScore = await fetch("/api/leaderboard?sort=score").then(r => r.json());

  document.getElementById("lbName").textContent = JSON.stringify(byName, null, 2);
  document.getElementById("lbScore").textContent = JSON.stringify(byScore, null, 2);
}

async function startMatch() {
  const p1 = document.getElementById("p1").value.trim();
  const p2 = document.getElementById("p2").value.trim();

  if (!p1 || !p2) {
    document.getElementById("status").textContent = "❌ Enter BOTH Player 1 and Player 2 names.";
    return;
  }

  const res = await fetch("/api/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ p1, p2 })
  });

  const data = await res.json();
  document.getElementById("status").textContent = data.message;

  // If backend says Player1 is locked, make it readonly
  document.getElementById("p1").readOnly = data.p1_locked;

  // Enable play button only after start
  document.getElementById("playBtn").disabled = false;

  await refreshLeaderboards();
}

async function play10Rounds() {
  const res = await fetch("/api/play", { method: "POST" });
  const data = await res.json();

  document.getElementById("gameResult").textContent = JSON.stringify(data, null, 2);

  // Winner retention: set Player 1 to winner, lock it; clear Player 2 for new opponent
  document.getElementById("p1").value = data.next_player1;
  document.getElementById("p1").readOnly = true;
  document.getElementById("p2").value = "";
  document.getElementById("playBtn").disabled = true; // must enter new P2 and Start again
  document.getElementById("status").textContent =
    `✅ Game finished. Winner retained as Player 1: ${data.next_player1}. Enter a NEW Player 2 and click Start Match.`;

  await refreshLeaderboards();
}

document.getElementById("startBtn").addEventListener("click", startMatch);
document.getElementById("playBtn").addEventListener("click", play10Rounds);
