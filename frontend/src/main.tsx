import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./i18n";
import "./styles/global.css";
import "./styles/components.css";
import "./styles/layout.css";
import "./styles/features.css";
import { applyTheme, getInitialTheme } from "./lib/theme";

// Apply the persisted / system theme before React mounts so the page
// doesn't flash the wrong palette on first paint.
applyTheme(getInitialTheme());

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
