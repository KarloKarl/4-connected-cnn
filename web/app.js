const rows = 6;
const columns = 7;
let board = Array.from({ length: rows }, () => Array(columns).fill(0));
let currentPlayer = -1;
let gameOver = false;
let busy = false;
let trainingGames = [];
let trainingSteps = [];
let trainingStep = 0;
let trainingTimer = null;

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => {
      item.classList.toggle("active", item === tab);
    });
    document.querySelectorAll(".tab-content").forEach((content) => {
      content.classList.toggle("active", content.id === `${tab.dataset.tab}-tab`);
    });
  });
});

const boardElement = document.querySelector("#board");
const messageElement = document.querySelector("#message");

function render() {
  boardElement.replaceChildren();
  for (let row = rows - 1; row >= 0; row -= 1) {
    for (let column = 0; column < columns; column += 1) {
      const cell = document.createElement("button");
      cell.className = `cell piece-${board[row][column]}`;
      cell.type = "button";
      cell.title = `Spalte ${column + 1}`;
      cell.disabled = gameOver || busy;
      cell.addEventListener("click", () => play(column));
      boardElement.appendChild(cell);
    }
  }
}

async function play(column) {
  if (gameOver || busy) {
    return;
  }
  busy = true;
  messageElement.textContent = "KI denkt ...";
  render();
  try {
    const response = await fetch("/web/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        board,
        current_player: currentPlayer,
        column,
        algorithm: document.querySelector("#algorithm").value,
        difficulty: Number(document.querySelector("#difficulty").value),
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      messageElement.textContent = result.detail || "Der Zug ist nicht möglich.";
      return;
    }
    board = result.board;
    currentPlayer = result.current_player;
    gameOver = result.winner !== null || result.draw;
    messageElement.textContent = result.message;
  } catch (error) {
    messageElement.textContent = "Der Server ist nicht erreichbar.";
    console.error(error);
  } finally {
    busy = false;
    render();
  }
}

document.querySelector("#reset").addEventListener("click", () => {
  board = Array.from({ length: rows }, () => Array(columns).fill(0));
  currentPlayer = -1;
  gameOver = false;
  busy = false;
  messageElement.textContent = "Du bist am Zug.";
  render();
});

function renderTrainingBoard() {
  const element = document.querySelector("#training-board");
  const status = document.querySelector("#training-status");
  const previous = document.querySelector("#training-previous");
  const next = document.querySelector("#training-next");
  const play = document.querySelector("#training-play");
  element.replaceChildren();
  if (!trainingSteps.length) {
    status.textContent = "Kein Trainingsspiel ausgewählt.";
    previous.disabled = true;
    next.disabled = true;
    play.disabled = true;
    return;
  }
  const step = trainingSteps[trainingStep];
  for (let row = rows - 1; row >= 0; row -= 1) {
    for (let column = 0; column < columns; column += 1) {
      const cell = document.createElement("div");
      cell.className = `cell piece-${step.board[row * columns + column]}`;
      if (column === step.move) {
        cell.classList.add("highlight");
      }
      element.appendChild(cell);
    }
  }
  status.textContent = `Schritt ${trainingStep + 1} von ${trainingSteps.length} | ` +
    `Lehrzug: Spalte ${step.move + 1} | Spieler: ${step.player} | ` +
    `Tiefe: ${step.depth} | Ergebnis: ${step.result}`;
  previous.disabled = trainingStep === 0;
  next.disabled = trainingStep === trainingSteps.length - 1;
  play.disabled = false;
  play.textContent = trainingTimer ? "Pause" : "Automatisch abspielen";
}

function stopTrainingPlayback() {
  if (trainingTimer) {
    clearInterval(trainingTimer);
    trainingTimer = null;
  }
}

function selectTrainingStep(index) {
  trainingStep = Math.max(0, Math.min(index, trainingSteps.length - 1));
  renderTrainingBoard();
}

async function loadTrainingGames(runId) {
  stopTrainingPlayback();
  trainingSteps = [];
  const response = await fetch(`/web/training/runs/${encodeURIComponent(runId)}/games`);
  if (!response.ok) {
    throw new Error(`Spiele-API antwortete mit HTTP ${response.status}`);
  }
  trainingGames = await response.json();
  const gameSelect = document.querySelector("#training-game");
  gameSelect.replaceChildren();
  trainingGames.forEach((game) => {
    const option = document.createElement("option");
    option.value = game.index;
    option.textContent = `Spiel ${game.index + 1} (${game.step_count} Schritte)`;
    gameSelect.appendChild(option);
  });
  gameSelect.disabled = trainingGames.length === 0;
  if (trainingGames.length) {
    await loadTrainingGame(runId, 0);
  } else {
    renderTrainingBoard();
  }
}

async function loadTrainingGame(runId, index) {
  stopTrainingPlayback();
  const response = await fetch(
    `/web/training/runs/${encodeURIComponent(runId)}/games/${index}`,
  );
  if (!response.ok) {
    throw new Error(`Spiel-API antwortete mit HTTP ${response.status}`);
  }
  const result = await response.json();
  trainingSteps = result.steps;
  trainingStep = 0;
  document.querySelector("#training-config").textContent =
    JSON.stringify(result.config, null, 2);
  renderDifficultyDistribution(
    result.game_difficulty_distribution,
    result.difficulty_distribution,
  );
  renderTrainingBoard();
}

function renderDifficultyDistribution(gameDistribution, exampleDistribution) {
  const element = document.querySelector("#training-distribution");
  element.replaceChildren();
  const gameEntries = Object.entries(gameDistribution || {});
  const exampleEntries = Object.entries(exampleDistribution || {});
  if (!gameEntries.length && !exampleEntries.length) {
    element.textContent = "Keine Schwierigkeitsdaten vorhanden.";
    return;
  }
  const heading = document.createElement("strong");
  heading.textContent = "Tatsächliche Verteilung der Schwierigkeitsstufen";
  element.appendChild(heading);
  renderDistributionRows(element, "Partien", gameEntries);
  renderDistributionRows(element, "Trainingsbeispiele", exampleEntries);
}

function renderDistributionRows(element, label, entries) {
  if (!entries.length) {
    return;
  }
  const total = entries.reduce((sum, [, count]) => sum + count, 0);
  const subheading = document.createElement("div");
  subheading.textContent = `${label} (gesamt: ${total})`;
  subheading.className = "distribution-label";
  element.appendChild(subheading);
  const maxCount = Math.max(...entries.map(([, count]) => count));
  entries.forEach(([depth, count]) => {
    const row = document.createElement("div");
    row.className = "distribution-row";
    const label = document.createElement("span");
    label.textContent = `Tiefe ${depth}`;
    const bar = document.createElement("div");
    bar.className = "distribution-bar";
    bar.style.width = `${(count / maxCount) * 100}%`;
    bar.title = `${count} von ${total} Beispielen`;
    const value = document.createElement("span");
    value.textContent = `${count} (${((count / total) * 100).toFixed(1)} %)`;
    row.append(label, bar, value);
    element.appendChild(row);
  });
}

async function loadTrainingRuns() {
  const runSelect = document.querySelector("#training-run");
  try {
    const response = await fetch("/web/training/runs");
    if (!response.ok) {
      throw new Error(`Trainings-API antwortete mit HTTP ${response.status}`);
    }
    const runs = await response.json();
    runSelect.replaceChildren();
    runs.forEach((run) => {
      const option = document.createElement("option");
      option.value = run.id;
      option.textContent = `${run.id} (${run.game_count} Spiele, ${run.example_count} Beispiele)`;
      runSelect.appendChild(option);
    });
    if (runs.length) {
      await loadTrainingGames(runs[0].id);
    } else {
      runSelect.disabled = true;
      document.querySelector("#training-status").textContent =
        "Keine Trainingsläufe gefunden.";
    }
  } catch (error) {
    document.querySelector("#training-status").textContent =
      "Trainingsläufe konnten nicht geladen werden.";
    console.error(error);
  }
}

document.querySelector("#training-run").addEventListener("change", (event) => {
  loadTrainingGames(event.target.value);
});
document.querySelector("#training-game").addEventListener("change", (event) => {
  loadTrainingGame(document.querySelector("#training-run").value, Number(event.target.value));
});
document.querySelector("#training-previous").addEventListener("click", () => {
  selectTrainingStep(trainingStep - 1);
});
document.querySelector("#training-next").addEventListener("click", () => {
  selectTrainingStep(trainingStep + 1);
});
document.querySelector("#training-play").addEventListener("click", () => {
  if (trainingTimer) {
    stopTrainingPlayback();
    renderTrainingBoard();
    return;
  }
  if (trainingStep === trainingSteps.length - 1) {
    trainingStep = 0;
  }
  trainingTimer = setInterval(() => {
    if (trainingStep >= trainingSteps.length - 1) {
      stopTrainingPlayback();
    } else {
      trainingStep += 1;
    }
    renderTrainingBoard();
  }, 900);
  renderTrainingBoard();
});

render();
renderTrainingBoard();
loadTrainingRuns();
