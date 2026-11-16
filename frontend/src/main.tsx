import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, HashRouter } from "react-router-dom";
import { DEMO } from "./api/client";
import App from "./App";
import "./index.css";

// GitHub Pages has no server-side routing, so the demo uses hash URLs.
const Router = DEMO ? HashRouter : BrowserRouter;

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Router>
      <App />
    </Router>
  </React.StrictMode>
);
