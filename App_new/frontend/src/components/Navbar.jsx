import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
      <div className="container px-5">
        
        <Link className="navbar-brand" to="/">
          <img
            className="img-fluid rounded me-1 d-inline-block align-text-top"
            src="/images/favicon.png"
            width="50"
            height="50"
            alt=""
          />
        </Link>

        <Link className="navbar-brand" to="/">
          Chat with NRW
        </Link>

        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarSupportedContent"
          aria-controls="navbarSupportedContent"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        <div
          id="navbarSupportedContent"
          className="collapse navbar-collapse"
        >
          <ul className="navbar-nav ms-auto mb-2 mb-lg-0">
            
            <li className="nav-item">
              <Link className="nav-link" to="/">
                Home
              </Link>
            </li>

            <li className="nav-item">
              <Link className="nav-link" to="/chat">
                Chat
              </Link>
            </li>

            <li className="nav-item">
              <Link className="nav-link" to="/info">
                Info
              </Link>
            </li>

          </ul>
        </div>

      </div>
    </nav>
  );
}