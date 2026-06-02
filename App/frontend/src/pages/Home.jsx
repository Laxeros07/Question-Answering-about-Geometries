import PageTitle from "../components/PageTitle";

export default function Home() {
  return (
    <>
      <PageTitle title="Home" />

      {/* Heading Row */}
      <div className="row gy-4 gx-lg-5 align-items-center mt-5">
        <div className="col-lg-4">
          <img
            className="img-fluid rounded mb-4 mb-lg-0"
            src="/images/map_nrw.jpg"
            alt="NRW Map"
          />
        </div>

        <div className="col-lg-8">
          <h1 className="fw-light">Chat with NRW</h1>

          <p>
            Chat with NRW is an application to get precise information about the
            geometries of cities, districts and counties in North
            Rhine-Westphalia and their relations to each other. The chatbot can
            be asked questions about this, to which it responds textually and
            graphically. This great application goes back to the course “Spatial
            Information Search” from WiSe2024/25 and is maintained by Eva, Anne
            and Felix.
          </p>
        </div>
      </div>

      {/* Call to Action */}
      <div
        className="card text-white bg-success my-5 py-4 text-center"
        style={{ opacity: 0.75 }}
      >
        <div className="card-body">
          <p className="blockquote m-0">
            “Even planks in front of your head ideally leave room for a clear
            view!”
          </p>
        </div>
      </div>

      {/* Second Row */}
      <div className="row gy-4 gx-lg-5 align-items-center mt-5">
        <div className="col-lg-5">
          <div className="card-body">
            <img
              className="img-fluid rounded mb-4 mb-lg-0"
              src="/images/Hierachy_Diagram.png"
              alt="Hierarchy Diagram"
            />
          </div>
        </div>

        <div className="col-lg-4">
          <h3 className="fw-light">
            The Hierarchy of the federal government system of NRW
          </h3>

          <p>
            NRW has four administrative levels: Federal State, administrative
            District, District and the City. A City in NRW for example Siegburg
            lies in a District (Rhein-Sieg-Kreis) which lies in an
            administrative District (Köln).
          </p>
        </div>
      </div>
    </>
  );
}
