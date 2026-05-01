import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import HomePage from './pages/HomePage'
import DGNLPage from './pages/DGNLPage'
import HocBaPage from './pages/HocBaPage'
import TuyenThangPage from './pages/TuyenThangPage'
import THPTPage from './pages/THPTPage'

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dgnl" element={<DGNLPage />} />
        <Route path="/hocba" element={<HocBaPage />} />
        <Route path="/tuyenthang" element={<TuyenThangPage />} />
        <Route path="/thpt" element={<THPTPage />} />
      </Routes>
    </BrowserRouter>
  )
}
