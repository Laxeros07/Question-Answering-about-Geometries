import PageTitle from "../components/PageTitle";

export default function Info() {
  return (
  <>
    <PageTitle title="Legal Information" />

    {/* Heading Row */}
    <div className="container">
      <div className="row padded_row">
        <div className="col-md-7">
          <div className="d-flex justify-content-between align-items-start mb-4">
            <h2 className="mb-0">Legal notice</h2>
          </div>
          The{" "}
          <a
            className="link-green"
            href="https://tu-dresden.de/impressum/"
            target="_blank"
            rel="noopener noreferrer"
          >
            Legal notice of Technische Universität Dresden
          </a>{" "}
          applies with the following restrictions:
          <br />
          <br />

          <strong>Service provider:</strong>
          <br />
          <br />

          Chair of Geoinformatics
          <br />
          Faculty of Environmental Sciences
          <br />
          Technische Universität Dresden
          <br />
          <br />

          Prof. Dr. rer. nat. Lars Bernard
          <br />
          Helmholtzstraße 10
          <br />
          01069 Dresden
          <br />
          <br />

          <strong>Technical administrator:</strong>
          <br />
          <br />

          Auriol Degbelo
          <br />
          Phone:{" "}
          <a
            className="link-green"
            href="tel:+49-351-463-33819"
          >
            (+49)-351-463-33819
          </a>
          <br />
          Email:{" "}
          <a
            className="link-green"
            href="mailto:firstname.lastname@tu-dresden.de"
          >
            firstname.lastname@tu-dresden.de
          </a>
        </div>
        <div className="col-md-4 d-flex justify-content-center align-items-start">
          <img
            src="/images/AGQA.png"
            alt="Technische Universität Dresden"
            style={{
              maxWidth: "220px",
              width: "100%",
              height: "auto",
            }}
          />
        </div>
      </div>
    </div>
  </>
  );
}
