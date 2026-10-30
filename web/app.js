const rows = 6;
const columns = 7;
let board = Array.from({ length: rows }, () => Array(columns).fill(0));
let currentPlayer = -1;
let gameOver = false;
let busy = false;

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

render();
