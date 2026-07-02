import Layout from "./components/Layout";
import Impressum from "./pages/Impressum";
import Info from "./pages/Info";
import Chat from "./pages/Chat";
import { Routes, Route } from "react-router-dom";

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/impressum" element={<Impressum />} />
        <Route path="/" element={<Chat />} />
        <Route path="/info" element={<Info />} />
      </Routes>
    </Layout>
  );
}

export default App;
