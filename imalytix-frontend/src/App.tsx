import { Navigate, Route, Routes } from "react-router-dom";
import DetailAnalysisPage from "./pages/DetailAnalysisPage";
import UploadAnalysisPage from "./pages/UploadAnalysisPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<UploadAnalysisPage />} />
      <Route path="/detail" element={<DetailAnalysisPage />} />
      <Route path="/detail/:id" element={<DetailAnalysisPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

