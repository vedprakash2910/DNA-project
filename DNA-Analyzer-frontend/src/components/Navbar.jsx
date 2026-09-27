import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { path: "/", label: "Home" },
  { path: "/upload", label: "Upload DNA" },
  { path: "/results", label: "Results" },
  { path: "/history", label: "History" },
];

function Navbar() {
  return (
    <header className="navbar">
      <div className="logo">🧬 DNA Analyzer</div>

      <div className="navbar-right">
        <nav>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Decorative for now — no auth system wired up yet */}
        <button type="button" className="login-btn">
          Login
        </button>
      </div>
    </header>
  );
}

export default Navbar;
