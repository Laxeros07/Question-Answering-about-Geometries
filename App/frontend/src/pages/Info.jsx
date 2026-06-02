import PageTitle from "../components/PageTitle";

export default function Info() {
  return (
    <>
      <PageTitle title="Home" />
      {/* Heading Row */}
      <div className="container">
        <div className="row padded_row">
          {/* right side content*/}
          <div className="col-md-7">
            <h2>Legal notice</h2>
            Spacey GmbH
            <br />
            <br />
            This legal notice also applies to the Spacey social media channels:{" "}
            <br />
            <a
              className="link1 text-muted text-decoration-none"
              href="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            >
              YouTube{" "}
            </a>
            <br />
            <a
              className="link1 text-muted text-decoration-none"
              href="https://www.instagram.com/geochiller/"
            >
              Instagram{" "}
            </a>
            <br />
            <br />
            Responsible for this and the previously mentioned pages is:
            <br />
            <br />
            Spacey GmbH
            <br />
            Heisenbergstraße 2
            <br />
            48149 Münster
            <br />
            Deutschland
            <br />
            <br />
            Telefon:
            <a
              className="link1 text-muted text-decoration-none"
              href="tel:+491633422862"
            >
              +49 163 342 2862
            </a>
            <br />
            E-Mail:
            <a
              className="link1 text-muted text-decoration-none"
              href="mailto:Apollo13.spacey@gmx.de?subject=Erreicht%20ueber%20Impressum&amp;amp;body=Sehr%20geehrtes%20Spacey%20Team,%0A%0A"
            >
              Apollo13.Spacey@gmx.de
            </a>
            <br />
            (shadow)Fax: 123 187 1337
            <br />
            <br />
            Managing directors of Spacey with sole power of representation:{" "}
            <br />
            Eva Langstein, Felix Disselkamp, Anne Staskiewicz
            <br />
            <br />
            UstId-Nr.: DE 162261337
            <br />
            Handelsregister: HRB 4149, Amtsgericht Münster
          </div>
        </div>
      </div>
    </>
  );
}
