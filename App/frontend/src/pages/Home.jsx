import PageTitle from "../components/PageTitle";

export default function Home() {
  return (
    <>
      <PageTitle title="Home" />

      {/* Heading Row */}
      <div className="row gy-4 gx-lg-5 align-items-center mt-5">
        <div className="col-lg-4">
          <img
            className="img-fluid rounded mb-4 mb-lg-0 hover-image png-shadow"
            src="/images/GER.png"
            alt="NRW Map"
          />
        </div>

        <div className="col-lg-8">
          <h1 className="fw-light">QuA-GG</h1>
          <p>
            <strong>...</strong> is an application that provides precise information about the location,
            relative position, and administrative hierarchy of Germany’s administrative divisions.
          </p>

          <p>
            The system is based on a question-and-answer approach, allowing users to ask questions
            related to Germany’s administrative boundaries and receive concise textual responses.
            In addition, all entities mentioned in the answer are visualized on the map displayed
            alongside the chat interface.
          </p>

          <p>
            Questions must be related to Germany’s administrative divisions. The hierarchical
            structure of these divisions is illustrated in the <a href="#hierarchy-diagram">diagram below</a> .
          </p>

          <p>
            <strong>Example questions:</strong>
          </p>

          <ul>
            <li>Where is Lippstadt located?</li>
            <li>Which cities are located in the administrative district of Münster?</li>
            <li>In which federal state is Hameln located?</li>
            <li>Which cities border Hannover?</li>
            <li>Which districts are located north of Rhein-Sieg-Kreis?</li>
            <li>Which cities are located within a 100 km radius of Bocholt?</li>
          </ul>

          <p>
            The application was originally developed as part of a university course at the
            University of Münster and was later further enhanced at the University of Dresden.
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
              className="img-fluid rounded mb-4 mb-lg-0 hover-image png-shadow"
              src="/images/Hierachy_Diagram.png"
              alt="Hierarchy Diagram"
            />
          </div>
        </div>

        <div className="col-lg-6">
          <h3 className="fw-light" id="hierarchy-diagram">
            The hierarchy of the federal government system of Germany
          </h3>

          <p>
            Germany's administrative structure consists of up to five levels: 
            <strong> Federal State</strong>, <strong>Administrative District</strong>,
            <strong> District</strong>, <strong>Administrative Community</strong> and
            <strong> City</strong>.
          </p>

          <p>
            For example, the city of <em>Siegburg</em> is located in the district 
            <em> Rhein-Sieg-Kreis</em>, which belongs to the administrative district
            <em> Köln</em>, which in turn is part of the federal state
            <em> Nordrhein-Westfalen</em>.
          </p>

          <p>
            The following federal states include an additional administrative level
            (<strong>Administrative District</strong>):
          </p>

          <ul>
            <li><em>Nordrhein-Westfalen</em></li>
            <li><em>Bayern</em></li>
            <li><em>Hessen</em></li>
            <li><em>Baden-Württemberg</em></li>
          </ul>

          <p>
            The following federal states do not have administrative communities as a
            separate administrative level:
          </p>

          <ul>
            <li><em>Nordrhein-Westfalen</em></li>
            <li><em>Hessen</em></li>
            <li><em>Saarland</em></li>
          </ul>

          <p>
            The cities <em>Berlin</em>, <em>Hamburg</em>, and <em>Bremen</em> are
            city-states and therefore do not belong to a higher-level federal state.
          </p>
        </div>
      </div>
    </>
  );
}
