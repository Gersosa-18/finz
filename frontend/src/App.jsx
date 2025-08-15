import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useContext } from 'react';
import { AuthProvider, AuthContext } from './context/AuthContext.jsx';

import Header from './components/Header.jsx';
import Sidebar from './components/Sidebar.jsx';
import Dashboard from './components/Dashboard.jsx';
import Alertas from './components/Alertas.jsx';
import AnalisisSentimiento from './components/AnalisisSentimiento.jsx';
import Login from './pages/Login.jsx';
import './App.css';

function PrivateLayout({ children}) {
  return (
    <div className='app'>
      <div className='app-body'>
        <Sidebar />
        <div className='main-area'>
          <Header />
          <main className='main-content'>{children}</main>
        </div>
      </div>
    </div>
  )
}

function ProtectedRoute({ children}){
  const { isAuthenticated } = useContext(AuthContext);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function AppRoutes() {
  return (
  <Routes>
    <Route path="/login" element={<Login />} />
    <Route
      path='/*'
      element={
        <ProtectedRoute>
          <PrivateLayout>
            <Routes>
              <Route path='/' element={<Dashboard />} />
              <Route path='/dashboard' element={<Dashboard />} />
              <Route path='/alertas' element={<Alertas />} />
              <Route path='/analisis' element={<AnalisisSentimiento />} />
            </Routes>
          </PrivateLayout>
        </ProtectedRoute>
      }
    />
  </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;