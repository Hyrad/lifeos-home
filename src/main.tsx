import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import WinePage from "./WinePage";
import { winePagePath } from "./data/wine";
import "./styles.css";
import "./wine.css";

const normalizedPath = window.location.pathname
  .replace(/index\.html$/, "")
  .replace(/\/?$/, "/");
const isWinePage = normalizedPath === winePagePath;

createRoot(document.getElementById("root")!).render(
  <StrictMode>{isWinePage ? <WinePage /> : <App />}</StrictMode>,
);
