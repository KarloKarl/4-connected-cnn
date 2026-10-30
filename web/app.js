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
    trainingSteps,
    result.game_difficulty_distribution,
    result.config,
  );
  renderTrainingBoard();
}

function renderDifficultyDistribution(gameSteps, runDistribution, config) {
  const element = document.querySelector("#training-distribution");
  element.replaceChildren();
  const minimum = Number(config.min_depth);
  const maximum = Number(config.max_depth);
  const depths = Array.from(
    { length: maximum - minimum + 1 },
    (_, index) => minimum + index,
  );
  if (!depths.length) {
    element.textContent = "Keine Schwierigkeitsdaten vorhanden.";
    return;
  }
  const selectedCounts = Object.fromEntries(depths.map((depth) => [depth, 0]));
  gameSteps.forEach((step) => {
    selectedCounts[step.depth] = (selectedCounts[step.depth] || 0) + 1;
  });
  const runCounts = Object.fromEntries(
    depths.map((depth) => [depth, Number(runDistribution[String(depth)] || 0)]),
  );
  const maxCount = Math.max(
    1,
    ...depths.map((depth) => Math.max(selectedCounts[depth], runCounts[depth])),
  );
  const width = 640;
  const height = 300;
  const plotLeft = 52;
  const plotRight = 620;
  const plotWidth = plotRight - plotLeft;
  const plotHeight = 82;
  const x = (index) => plotLeft + (index * plotWidth) / Math.max(1, depths.length - 1);
  const y = (count, top) => top + plotHeight - (count / maxCount) * plotHeight;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("role", "img");
  svg.setAttribute(
    "aria-label",
    "Verteilung der Minimax-Suchtiefen im gewählten Spiel und Trainingslauf",
  );
  const title = document.createElementNS(svg.namespaceURI, "text");
  title.setAttribute("x", "52");
  title.setAttribute("y", "20");
  title.setAttribute("font-weight", "600");
  title.textContent = "Schwierigkeitsverteilung";
  svg.appendChild(title);
  renderDistributionPlot(
    svg, "Gewähltes Spiel", "Schritte", selectedCounts, depths, x, y, 35, "#eb5757",
  );
  renderDistributionPlot(
    svg, "Gesamter Trainingslauf", "Partien", runCounts, depths, x, y, 160, "#4a90e2",
  );
  element.appendChild(svg);
}

function renderDistributionPlot(svg, label, unit, counts, depths, x, y, top, color) {
  const namespace = svg.namespaceURI;
  const baseline = document.createElementNS(namespace, "line");
  baseline.setAttribute("x1", "52");
  baseline.setAttribute("x2", "620");
  baseline.setAttribute("y1", String(top + 102));
  baseline.setAttribute("y2", String(top + 102));
  baseline.setAttribute("stroke", "#9aa7b8");
  svg.appendChild(baseline);
  const heading = document.createElementNS(namespace, "text");
  heading.setAttribute("x", "52");
  heading.setAttribute("y", String(top + 14));
  heading.setAttribute("font-size", "13");
  heading.textContent = `${label} (Anzahl ${unit})`;
  svg.appendChild(heading);
  const points = depths.map((depth, index) => `${x(index)},${y(counts[depth], top + 20)}`).join(" ");
  const line = document.createElementNS(namespace, "polyline");
  line.setAttribute("points", points);
  line.setAttribute("fill", "none");
  line.setAttribute("stroke", color);
  line.setAttribute("stroke-width", "3");
  line.setAttribute("stroke-linejoin", "round");
  svg.appendChild(line);
  depths.forEach((depth, index) => {
    const point = document.createElementNS(namespace, "circle");
    point.setAttribute("cx", String(x(index)));
    point.setAttribute("cy", String(y(counts[depth], top + 20)));
    point.setAttribute("r", "5");
    point.setAttribute("fill", color);
    point.setAttribute("aria-label", `Tiefe ${depth}: ${counts[depth]}`);
    svg.appendChild(point);
    const axisLabel = document.createElementNS(namespace, "text");
    axisLabel.setAttribute("x", String(x(index)));
    axisLabel.setAttribute("y", String(top + 120));
    axisLabel.setAttribute("text-anchor", "middle");
    axisLabel.setAttribute("font-size", "12");
    axisLabel.textContent = depth;
    svg.appendChild(axisLabel);
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
