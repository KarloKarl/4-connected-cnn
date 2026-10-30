const rows = 6;
const columns = 7;
let board = Array.from({ length: rows }, () => Array(columns).fill(0));

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
      cell.addEventListener("click", () => play(column));
      boardElement.appendChild(cell);
    }
  }
}

async function play(column) {
  const response = await fetch("/web/move", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      board,
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
  messageElement.textContent = result.message;
  render();
}

document.querySelector("#reset").addEventListener("click", () => {
  board = Array.from({ length: rows }, () => Array(columns).fill(0));
  messageElement.textContent = "Du bist am Zug.";
  render();
});

render();
