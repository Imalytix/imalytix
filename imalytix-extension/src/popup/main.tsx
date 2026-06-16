import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "../shared/index.css";
import PopupApp from "./PopupApp";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <PopupApp />
  </StrictMode>,
);
