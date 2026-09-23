const NAV_ITEMS = [
  { id: "home", label: "Home" },
  { id: "upload", label: "Upload DNA" },
  { id: "results", label: "Results" },
  { id: "history", label: "History" },
];

function Navbar({ activeSection, onNavigate }) {
  return (
    <header className="navbar">
      <div className="logo">🧬 DNA Analyzer</div>

      <div className="navbar-right">
        <nav>
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={activeSection === item.id ? "nav-link active" : "nav-link"}
              onClick={() => onNavigate(item.id)}
            >
              {item.label}
            </button>
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
