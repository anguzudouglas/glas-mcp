import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import Tools from './pages/Tools'
import Playground from './pages/Playground'
import Docs from './pages/Docs'
import ApiRef from './pages/ApiRef'

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display:'flex', flexDirection:'column', minHeight:'100vh' }}>
        <Navbar />
        <main style={{ flex:1 }}>
          <Routes>
            <Route path="/"           element={<Home />} />
            <Route path="/tools"      element={<Tools />} />
            <Route path="/playground" element={<Playground />} />
            <Route path="/docs"       element={<Docs />} />
            <Route path="/api"        element={<ApiRef />} />
            <Route path="*"           element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  )
}
