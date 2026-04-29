import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="bg-dark text-center text-muted text-lg-start mt-5">
      <div className="container ms-2 me-2 px-2 mt-2">
        <div className="row">
          
          <div className="col-2 text-start">
            <h5 className="text-uppercase">Links</h5>
            <ul className="list-unstyled mb-0">
              <li>
                <Link
                  className="text-muted text-decoration-none"
                  to="/info"
                >
                  Impressum
                </Link>
              </li>
            </ul>
          </div>

          <div className="col-3"></div>
          <div className="col-2"></div>

          <div className="col-3 text-end">
            <div>
              <a
                className="me-4 text-reset"
                href="https://github.com/Felioxx/SIS-Course"
              >
                <i className="bi bi-github" />
              </a>

              <a
                className="me-4 text-reset"
                href="mailto:Apollo13.spacey@gmx.de?subject=Erreicht%20ueber%20Website&body=Sehr%20geehrtes%20Spacey%20Team,%0A%0A"
              >
                <i className="bi bi-envelope-at-fill"></i>
              </a>

              <a
                className="me-4 text-reset"
                href="tel:+4915901600951"
              >
                <i className="bi bi-phone"></i>
              </a>
            </div>
          </div>
        </div>

        <div className="row">
          <div className="col-md-2"></div>

          <div className="col-md-8 text-center">
            <img
              className="logo sm m-2"
              src="/images/flavicon_ring.png"
              width="50"
              height="50"
              alt=""
            />
          </div>

          <div className="col-md-2"></div>
        </div>
      </div>

      <div
        className="text-center p-1 text-white"
        style={{ backgroundColor: "#009036" }}
      >
        © 2024 by:{" "}
        <i className="text-white">Shadowfax</i>

        <img
          className="img-fluid rounded me-1 d-inline-block align-text-top"
          src="/images/shadowfax.jpg"
          width="30"
          height="30"
          alt=""
        />
      </div>
    </footer>
  );
}