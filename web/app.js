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

document.querySelectorAll(".main-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".main-tab").forEach((item) => {
      item.classList.toggle("active", item === tab);
    });
    document.querySelectorAll(".tab-content").forEach((content) => {
      content.classList.toggle("active", content.id === `${tab.dataset.tab}-tab`);
    });
  });
});

document.querySelectorAll(".training-subtab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".training-subtab").forEach((item) => {
      item.classList.toggle("active", item === tab);
    });
    document.querySelectorAll(".subtab-content").forEach((content) => {
      content.classList.toggle(
        "active",
        content.id === `training-${tab.dataset.trainingTab}-tab`,
      );
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
  const displayBoard = boardAfterStep(trainingSteps, trainingStep);
  const depthGrid = buildDepthGrid(trainingSteps, trainingStep + 1);
  for (let row = rows - 1; row >= 0; row -= 1) {
    for (let column = 0; column < columns; column += 1) {
      const cell = document.createElement("div");
      cell.className = `cell piece-${displayBoard[row * columns + column]}`;
      if (column === step.move) {
        cell.classList.add("highlight");
      }
      const depth = depthGrid[row][column];
      if (depth !== null) {
        const depthLabel = document.createElement("span");
        depthLabel.className = "stone-depth";
        depthLabel.textContent = depth;
        depthLabel.title = `Minimax-Tiefe ${depth}`;
        cell.appendChild(depthLabel);
      }
      element.appendChild(cell);
    }
  }
  status.textContent = `Schritt ${trainingStep + 1} von ${trainingSteps.length} | ` +
    `Lehrzug: Spalte ${step.move + 1} | Spieler: ${step.player} | ` +
    `Tiefe: ${step.depth} | Partieausgang nach Abschluss: ${formatOutcome(step.result)}`;
  previous.disabled = trainingStep === 0;
  next.disabled = trainingStep === trainingSteps.length - 1;
  play.disabled = false;
  play.textContent = trainingTimer ? "Pause" : "Automatisch abspielen";
}

function boardAfterStep(steps, visibleStep) {
  const step = steps[visibleStep];
  if (visibleStep < steps.length - 1) {
    return steps[visibleStep + 1].board;
  }
  const board = [...step.board];
  const row = board.reduce(
    (occupied, value, boardIndex) =>
      occupied + (boardIndex % columns === step.move && value !== 0 ? 1 : 0),
    0,
  );
  if (row < rows) {
    board[row * columns + step.move] = step.player;
  }
  return board;
}

function formatOutcome(result) {
  if (result === 0) {
    return "Unentschieden";
  }
  return `Spieler ${result} gewinnt`;
}

function buildDepthGrid(steps, visibleStep) {
  const depthGrid = Array.from(
    { length: rows },
    () => Array(columns).fill(null),
  );
  for (let index = 0; index < visibleStep; index += 1) {
    const previousBoard = steps[index].board;
    const column = steps[index].move;
    const row = previousBoard.reduce(
      (occupied, value, boardIndex) =>
        occupied + (boardIndex % columns === column && value !== 0 ? 1 : 0),
      0,
    );
    if (row < rows) {
      depthGrid[row][column] = steps[index].depth;
    }
  }
  return depthGrid;
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
    const outcome = game.result === 0
      ? "Unentschieden"
      : `Spieler ${game.result} gewinnt`;
    option.textContent = `Spiel ${game.index + 1} · ${outcome} · ${game.step_count} Züge`;
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
    result.difficulty_distribution_by_player,
  );
  renderTrainingBoard();
}

function renderTrainingConfig(config) {
  const element = document.querySelector("#training-config");
  element.replaceChildren();
  const fields = [
    ["Name", config.name ?? "-"],
    ["Status", config.status],
    ["Schwierigkeitsmodus", config.difficulty_mode === "asymmetric" ? "Asymmetrisch" : "Symmetrisch"],
    ["Heuristik", config.heuristic || "current"],
    ["Spiele", config.game_count],
    ["Beispiele", config.example_count],
    ["Erster Zug zufällig", config.random_first_move ? "Ja" : "Nein"],
    ["Batchgröße", config.batch_size],
    ["Seed", config.seed ?? "-"],
  ];
  if (config.difficulty_mode === "asymmetric") {
    fields.push(
      ["Spieler 1 Tiefe", `${config.player_one_min_depth} bis ${config.player_one_max_depth}`],
      ["Spieler 1 Verteilung", config.player_one_distribution],
      ["Spieler -1 Tiefe", `${config.player_minus_one_min_depth} bis ${config.player_minus_one_max_depth}`],
      ["Spieler -1 Verteilung", config.player_minus_one_distribution],
    );
  } else {
    fields.splice(5, 0,
      ["Tiefenbereich", `${config.min_depth} bis ${config.max_depth}`],
      ["Verteilung", config.distribution],
    );
  }
  const table = document.createElement("table");
  table.className = "config-table";
  const caption = document.createElement("caption");
  caption.textContent = "Trainingskonfiguration";
  table.appendChild(caption);
  const body = document.createElement("tbody");
  fields.forEach(([label, value]) => {
    const row = document.createElement("tr");
    const name = document.createElement("th");
    name.scope = "row";
    name.textContent = label;
    const content = document.createElement("td");
    content.textContent = value;
    row.append(name, content);
    body.appendChild(row);
  });
  table.appendChild(body);
  element.appendChild(table);
}

function renderDifficultyDistribution(
  gameSteps,
  runDistribution,
  config,
  runDistributionByPlayer,
) {
  const element = document.querySelector("#training-distribution");
  element.replaceChildren();
  const players = config.difficulty_mode === "asymmetric" ? [1, -1] : [null];
  players.forEach((player) => {
    const chart = document.createElement("section");
    chart.className = "distribution-chart";
    const title = document.createElement("h3");
    title.textContent = player === null
      ? "Schwierigkeitsverteilung der Züge"
      : `Schwierigkeitsverteilung Spieler ${player}`;
    chart.appendChild(title);
    const playerConfig = player === 1
      ? {
          min_depth: config.player_one_min_depth,
          max_depth: config.player_one_max_depth,
        }
      : player === -1
        ? {
            min_depth: config.player_minus_one_min_depth,
            max_depth: config.player_minus_one_max_depth,
          }
        : config;
    const minimum = Number(playerConfig.min_depth);
    const maximum = Number(playerConfig.max_depth);
    const selectedSteps = player === null
      ? gameSteps
      : gameSteps.filter((step) => Number(step.player) === player);
    const playerRunDistribution = player === null
      ? runDistribution
      : (runDistributionByPlayer?.[String(player)] || {});
    appendDifficultyChart(
      chart,
      selectedSteps,
      playerRunDistribution,
      minimum,
      maximum,
      player === null ? "Schwierigkeitsverteilung der Züge" : `Spieler ${player}`,
    );
    element.appendChild(chart);
  });
}

function appendDifficultyChart(
  element,
  gameSteps,
  runDistribution,
  minimum,
  maximum,
) {
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
  const selectedTotal = Object.values(selectedCounts).reduce((sum, count) => sum + count, 0);
  const runTotal = Object.values(runCounts).reduce((sum, count) => sum + count, 0);
  const selectedShares = Object.fromEntries(
    depths.map((depth) => [
      depth,
      selectedTotal ? (selectedCounts[depth] / selectedTotal) * 100 : 0,
    ]),
  );
  const runShares = Object.fromEntries(
    depths.map((depth) => [
      depth,
      runTotal ? (runCounts[depth] / runTotal) * 100 : 0,
    ]),
  );
  const width = 700;
  const height = 360;
  const plotLeft = 72;
  const plotRight = 628;
  const plotTop = 55;
  const plotBottom = 300;
  const plotHeight = plotBottom - plotTop;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("role", "img");
  svg.setAttribute(
    "aria-label",
    "Verteilung der Minimax-Suchtiefen im gewählten Spiel und Trainingslauf",
  );
  renderDistributionBars(
    svg,
    selectedCounts,
    runCounts,
    selectedShares,
    runShares,
    depths,
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
  selectedShares,
  runShares,
  depths,
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
  const y = (share) => plotBottom - (share / 100) * plotHeight;

  for (let tick = 0; tick <= 4; tick += 1) {
    const value = tick * 25;
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
    label.setAttribute("x", String(plotLeft - 10));
    label.setAttribute("y", String(yPosition + 4));
    label.setAttribute("text-anchor", "end");
    label.setAttribute("font-size", "11");
    label.textContent = `${value} %`;
    svg.appendChild(label);

    const rightLabel = document.createElementNS(namespace, "text");
    rightLabel.setAttribute("x", String(plotRight + 10));
    rightLabel.setAttribute("y", String(yPosition + 4));
    rightLabel.setAttribute("font-size", "11");
    rightLabel.textContent = `${value} %`;
    svg.appendChild(rightLabel);
  }

  [
    ["Tiefe Spiel (%)", 20, "#eb5757"],
    ["Tiefe Training (%)", 680, "#4a90e2"],
  ].forEach(([label, xPosition, color]) => {
    const yLabel = document.createElementNS(namespace, "text");
    yLabel.setAttribute(
      "transform",
      `translate(${xPosition} ${(plotTop + plotBottom) / 2}) rotate(-90)`,
    );
    yLabel.setAttribute("text-anchor", "middle");
    yLabel.setAttribute("font-size", "12");
    yLabel.setAttribute("fill", color);
    yLabel.textContent = label;
    svg.appendChild(yLabel);
  });

  depths.forEach((depth, index) => {
    const groupLeft = plotLeft + index * xStep + (xStep - groupWidth) / 2;
    [
      [selectedShares[depth], "#eb5757", "Tiefe Spiel", selectedCounts[depth]],
      [runShares[depth], "#4a90e2", "Tiefe Training", runCounts[depth]],
    ].forEach(([share, color, label, count], seriesIndex) => {
      const bar = document.createElementNS(namespace, "rect");
      bar.setAttribute("x", String(groupLeft + seriesIndex * (barWidth + barGap)));
      bar.setAttribute("y", String(y(share)));
      bar.setAttribute("width", String(barWidth));
      bar.setAttribute("height", String(plotBottom - y(share)));
      bar.setAttribute("fill", color);
      bar.setAttribute(
        "aria-label",
        `${label}, Tiefe ${depth}: ${share.toFixed(1)} Prozent (${count} Züge)`,
      );
      svg.appendChild(bar);
      const value = document.createElementNS(namespace, "text");
      value.setAttribute(
        "x",
        String(groupLeft + seriesIndex * (barWidth + barGap) + barWidth / 2),
      );
      value.setAttribute("y", String(y(share) - 5));
      value.setAttribute("text-anchor", "middle");
      value.setAttribute("font-size", "10");
      value.textContent = `${share.toFixed(1)} %`;
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
        option.textContent = `${run.name || run.id} · ${run.id} (${run.game_count} Spiele, ${run.example_count} Beispiele)`;
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

function trainingFormValue(id) {
  return document.querySelector(`#${id}`).value;
}

async function startTrainingRun(event) {
  event.preventDefault();
  const button = document.querySelector("#training-start");
  const status = document.querySelector("#training-job-status");
  const seed = trainingFormValue("training-seed");
  const payload = {
    name: trainingFormValue("training-name").trim(),
    difficulty_mode: trainingFormValue("training-difficulty-mode"),
    game_count: Number(trainingFormValue("training-games")),
    min_depth: Number(trainingFormValue("training-min-depth")),
    max_depth: Number(trainingFormValue("training-max-depth")),
    distribution: trainingFormValue("training-distribution"),
    random_first_move: document.querySelector("#training-random-first-move").checked,
    seed: seed === "" ? null : Number(seed),
    batch_size: Number(trainingFormValue("training-batch-size")),
    heuristic: trainingFormValue("training-heuristic"),
    tree_learning: document.querySelector("#training-tree-learning").checked,
    depth_heuristic: document.querySelector("#training-depth-heuristic").checked,
    depth_penalty: Number(trainingFormValue("training-depth-penalty")),
    symmetry_augmentation: document.querySelector("#training-symmetry-augmentation").checked,
    player_one_min_depth: Number(trainingFormValue("training-player-one-min-depth")),
    player_one_max_depth: Number(trainingFormValue("training-player-one-max-depth")),
    player_one_distribution: trainingFormValue("training-player-one-distribution"),
    player_minus_one_min_depth: Number(trainingFormValue("training-player-minus-one-min-depth")),
    player_minus_one_max_depth: Number(trainingFormValue("training-player-minus-one-max-depth")),
    player_minus_one_distribution: trainingFormValue("training-player-minus-one-distribution"),
  };
  button.disabled = true;
  status.textContent = "Trainingslauf wird gestartet ...";
  try {
    const response = await fetch("/web/training/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail || `HTTP ${response.status}`);
    }
    status.textContent = "Trainingslauf läuft ...";
    await pollTrainingRun(result.id);
  } catch (error) {
    status.textContent = `Start fehlgeschlagen: ${error.message}`;
    console.error(error);
  } finally {
    button.disabled = false;
  }
}

function updateDifficultyMode() {
  const asymmetric = trainingFormValue("training-difficulty-mode") === "asymmetric";
  document.querySelector("#training-player-configs").hidden = !asymmetric;
  document.querySelector("#training-symmetric-config").hidden = asymmetric;
}

async function pollTrainingRun(runId) {
  const status = document.querySelector("#training-job-status");
  while (true) {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    const response = await fetch(
      `/web/training/runs/${encodeURIComponent(runId)}/status`,
    );
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail || `HTTP ${response.status}`);
    }
    if (result.status === "running") {
      status.textContent = "Trainingslauf läuft ...";
      continue;
    }
    if (result.status === "failed") {
      throw new Error(result.error || "Unbekannter Fehler");
    }
    status.textContent = "Trainingslauf abgeschlossen.";
    await loadTrainingRuns();
    return;
  }
}

document.querySelector("#training-run").addEventListener("change", (event) => {
  loadTrainingGames(event.target.value);
});
document.querySelector("#training-generator").addEventListener("submit", startTrainingRun);
document.querySelector("#training-difficulty-mode").addEventListener("change", updateDifficultyMode);
updateDifficultyMode();
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
