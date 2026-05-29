import { Link, NavLink, Route, Routes } from "react-router-dom";
import Overview from "./pages/Overview";
import Search from "./pages/Search";
import Trends from "./pages/Trends";
import Topics from "./pages/Topics";
import Sources from "./pages/Sources";

const navItem =
  "px-3 py-2 rounded-md text-sm font-medium hover:bg-brand-50 hover:text-brand-700";
const active = "bg-brand-50 text-brand-700";

export default function App() {
  return (
    <div className="min-h-full flex flex-col">
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-6">
          <Link to="/" className="text-lg font-semibold text-brand-700">
            AI Trend Intelligence
          </Link>
          <nav className="flex gap-1">
            <NavLink to="/" end className={({ isActive }) => `${navItem} ${isActive ? active : ""}`}>Overview</NavLink>
            <NavLink to="/search" className={({ isActive }) => `${navItem} ${isActive ? active : ""}`}>Search</NavLink>
            <NavLink to="/trends" className={({ isActive }) => `${navItem} ${isActive ? active : ""}`}>Trends</NavLink>
            <NavLink to="/topics" className={({ isActive }) => `${navItem} ${isActive ? active : ""}`}>Topics</NavLink>
            <NavLink to="/sources" className={({ isActive }) => `${navItem} ${isActive ? active : ""}`}>Sources</NavLink>
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/search" element={<Search />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/topics" element={<Topics />} />
          <Route path="/sources" element={<Sources />} />
        </Routes>
      </main>
      <footer className="text-center text-xs text-slate-500 py-4">
        Local • Free • Open-source • Ollama + ChromaDB + FastAPI
      </footer>
    </div>
  );
}
