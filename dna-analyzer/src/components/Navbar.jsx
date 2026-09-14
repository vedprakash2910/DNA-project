function Navbar() {
  return (
    <header className="navbar">

      <div className="logo">
        🧬 DNA Analyzer
      </div>

      <nav>
        <a href="#home">Home</a>
        <a href="#upload">Upload DNA</a>
        <a href="#results">Results</a>
        <a href="#history">History</a>
      </nav>

    </header>
  );
}

export default Navbar;