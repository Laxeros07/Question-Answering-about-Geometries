import Navbar from "./Navbar";
import Footer from "./Footer";

export default function Layout({ children, title}) {
  return (
    <>
      {/* NAVBAR */}
      <Navbar />

      {/* CONTENT */}
      <div className="container" style={{ marginTop: "80px" }}>
        {children}
      </div>

      {/* FOOTER */}
      <Footer />
    </>
  );
}