import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AppProvider } from "./context/AppContext";
import Layout from "./components/Layout";
import DocumentsPage from "./pages/DocumentsPage";
import SearchPage from "./pages/SearchPage";
import DraftsPage from "./pages/DraftsPage";
import ImprovementsPage from "./pages/ImprovementsPage";

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Toaster position="top-right" />
        <Layout>
          <Routes>
            <Route path="/" element={<DocumentsPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/drafts" element={<DraftsPage />} />
            <Route path="/improvements" element={<ImprovementsPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </AppProvider>
  );
}
