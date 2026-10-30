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
  renderTrainingConfig(result.config);
  renderDifficultyDistribution(
    trainingSteps,
    result.difficulty_distribution,
    result.config,
  );
  renderTrainingBoard();
}

function renderTrainingConfig(config) {
  const element = document.querySelector("#training-config");
  element.replaceChildren();
  const fields = [
    ["Status", config.status],
    ["Spiele", config.game_count],
    ["Beispiele", config.example_count],
    ["Tiefenbereich", `${config.min_depth} bis ${config.max_depth}`],
    ["Verteilung", config.distribution],
    ["Erster Zug zufällig", config.random_first_move ? "Ja" : "Nein"],
    ["Batchgröße", config.batch_size],
    ["Seed", config.seed ?? "-"],
  ];
  fields.forEach(([label, value]) => {
    const item = document.createElement("div");
    item.className = "config-item";
    const name = document.createElement("span");
    name.className = "config-label";
    name.textContent = label;
    const content = document.createElement("strong");
    content.textContent = value;
    item.append(name, content);
    element.appendChild(item);
  });
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
  const width = 640;
  const height = 360;
  const plotLeft = 58;
  const plotRight = 620;
  const plotTop = 55;
  const plotBottom = 300;
  const plotHeight = plotBottom - plotTop;
  const maxCount = Math.max(
    1,
    ...depths.map((depth) => Math.max(selectedCounts[depth], runCounts[depth])),
  );
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
  title.textContent = "Schwierigkeitsverteilung der Züge";
  svg.appendChild(title);
  renderDistributionBars(
    svg,
    selectedCounts,
    runCounts,
    depths,
    maxCount,
    plotLeft,
    plotRight,
    plotTop,
    plotBottom,
    plotHeight,
  );
  element.appendChild(svg);
}

function renderDistributionBars(
  svg,
  selectedCounts,
  runCounts,
  depths,
  maxCount,
  plotLeft,
  plotRight,
  plotTop,
  plotBottom,
  plotHeight,
) {
  const namespace = svg.namespaceURI;
  const xStep = (plotRight - plotLeft) / depths.length;
  const groupWidth = xStep * 0.72;
  const barGap = 3;
  const barWidth = (groupWidth - barGap) / 2;
  const y = (count) => plotBottom - (count / maxCount) * plotHeight;

  for (let tick = 0; tick <= 4; tick += 1) {
    const value = Math.round((maxCount * tick) / 4);
    const yPosition = plotBottom - (plotHeight * tick) / 4;
    const grid = document.createElementNS(namespace, "line");
    grid.setAttribute("x1", String(plotLeft));
    grid.setAttribute("x2", String(plotRight));
    grid.setAttribute("y1", String(yPosition));
    grid.setAttribute("y2", String(yPosition));
    grid.setAttribute("stroke", "#c5ccd6");
    grid.setAttribute("stroke-width", "1");
    svg.appendChild(grid);
    const label = document.createElementNS(namespace, "text");
    label.setAttribute("x", String(plotLeft - 8));
    label.setAttribute("y", String(yPosition + 4));
    label.setAttribute("text-anchor", "end");
    label.setAttribute("font-size", "11");
    label.textContent = value;
    svg.appendChild(label);
  }

  const yLabel = document.createElementNS(namespace, "text");
  yLabel.setAttribute("transform", `translate(15 ${(plotTop + plotBottom) / 2}) rotate(-90)`);
  yLabel.setAttribute("text-anchor", "middle");
  yLabel.setAttribute("font-size", "12");
  yLabel.textContent = "Anzahl Züge";
  svg.appendChild(yLabel);

  depths.forEach((depth, index) => {
    const groupLeft = plotLeft + index * xStep + (xStep - groupWidth) / 2;
    [
      [selectedCounts[depth], "#eb5757", "Tiefe Spiel"],
      [runCounts[depth], "#4a90e2", "Tiefe Training"],
    ].forEach(([count, color, label], seriesIndex) => {
      const bar = document.createElementNS(namespace, "rect");
      bar.setAttribute("x", String(groupLeft + seriesIndex * (barWidth + barGap)));
      bar.setAttribute("y", String(y(count)));
      bar.setAttribute("width", String(barWidth));
      bar.setAttribute("height", String(plotBottom - y(count)));
      bar.setAttribute("fill", color);
      bar.setAttribute("aria-label", `${label}, Tiefe ${depth}: ${count}`);
      svg.appendChild(bar);
      const value = document.createElementNS(namespace, "text");
      value.setAttribute(
        "x",
        String(groupLeft + seriesIndex * (barWidth + barGap) + barWidth / 2),
      );
      value.setAttribute("y", String(y(count) - 5));
      value.setAttribute("text-anchor", "middle");
      value.setAttribute("font-size", "10");
      value.textContent = count;
      svg.appendChild(value);
    });
    const axisLabel = document.createElementNS(namespace, "text");
    axisLabel.setAttribute("x", String(groupLeft + groupWidth / 2));
    axisLabel.setAttribute("y", String(plotBottom + 20));
    axisLabel.setAttribute("text-anchor", "middle");
    axisLabel.setAttribute("font-size", "12");
    axisLabel.textContent = `Tiefe ${depth}`;
    svg.appendChild(axisLabel);
  });

  [
    ["Tiefe Spiel", "#eb5757", plotLeft],
    ["Tiefe Training", "#4a90e2", plotLeft + 130],
  ].forEach(([label, color, xPosition]) => {
    const marker = document.createElementNS(namespace, "rect");
    marker.setAttribute("x", String(xPosition));
    marker.setAttribute("y", String(plotBottom + 42));
    marker.setAttribute("width", "12");
    marker.setAttribute("height", "12");
    marker.setAttribute("fill", color);
    svg.appendChild(marker);
    const legend = document.createElementNS(namespace, "text");
    legend.setAttribute("x", String(xPosition + 18));
    legend.setAttribute("y", String(plotBottom + 52));
    legend.setAttribute("font-size", "12");
    legend.textContent = label;
    svg.appendChild(legend);
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
