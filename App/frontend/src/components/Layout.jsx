import Navbar from "./Navbar";
import Footer from "./Footer";

export default function Layout({ children }) {
  return (
    <div className="layout">
      {/* NAVBAR */}
      <Navbar />

      {/* CONTENT */}
      <main className="container flex-grow-1" style={{ marginTop: "80px" }}>
        {children}
      </main>

      {/* FOOTER */}
      <Footer />
    </div>
  );
}