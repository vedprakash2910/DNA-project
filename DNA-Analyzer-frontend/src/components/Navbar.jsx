import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { path: "/", label: "Home" },
  { path: "/upload", label: "Upload DNA" },
  { path: "/results", label: "Results" },
  { path: "/history", label: "History" },
];

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

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

        {user ? (
          <button type="button" className="login-btn" onClick={handleLogout}>
            Logout ({user.name.split(" ")[0]})
          </button>
        ) : (
          <button
            type="button"
            className="login-btn"
            onClick={() => navigate("/login")}
          >
            Login
          </button>
        )}
      </div>
    </header>
  );
}

export default Navbar;
