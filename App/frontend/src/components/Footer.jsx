import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="bg-dark text-center text-white-50 text-lg-start mt-5 footer">
      <div className="container ms-2 me-2 px-2 mt-2 py-4 d-flex flex-column justify-content-center">
        <div className="row align-items-center">
          <div className="col-md-3 text-start">
            <h5 className="text-uppercase">Links</h5>
            <ul className="list-unstyled mb-0">
              <li>
                <Link className="text-white-50 text-decoration-none" to="/info">
                  Impressum
                </Link>
              </li>
            </ul>
          </div>

          <div className="col-md-6 text-center">
            <small>
              This work was funded by the German Research Foundation (DFG project
              no. 460036893 –{" "}
              <a
                href="https://www.nfdi4earth.de/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary text-decoration-none"
              >
                NFDI4Earth
              </a>
              ).
            </small>
          </div>

          <div className="col-md-3 d-flex align-items-center justify-content-between">
  
            <a
              href="https://www.nfdi4earth.de/"
              target="_blank"
              rel="noopener noreferrer"
            >
              <img
                src="/images/NFDI4Earth_logo.png"
                alt="NFDI4Earth"
                style={{ maxHeight: "35px" }}
              />
            </a>

            <div className="d-flex align-items-center gap-3">
              <a className="text-reset" href="https://github.com/Laxeros07/Question-Answering-about-Geometries">
                <i className="bi bi-github" />
              </a>

              <a
                className="text-reset"
                href="mailto:Apollo13.spacey@gmx.de?subject=Erreicht%20ueber%20Website&body=Sehr%20geehrtes%20Spacey%20Team,%0A%0A"
              >
                <i className="bi bi-envelope-at-fill"></i>
              </a>

              <a className="text-reset" href="tel:+4915901600951">
                <i className="bi bi-phone"></i>
              </a>
            </div>
          </div>
        </div>
      </div>

      <div
        className="text-center p-1 text-white"
        style={{ backgroundColor: "#009036" }}
      >
        © 2026 by: <i className="text-white">Shadowfax</i>
      </div>
    </footer>
  )}