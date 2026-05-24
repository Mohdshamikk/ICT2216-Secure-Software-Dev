import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';

// Pages
import Login from './pages/Login';
import Unauthorized from './pages/Unauthorized';
import NotFound from './pages/NotFound';
import Dashboard from './pages/user/Dashboard';
import ClientList from './pages/advisor/ClientList';
import UserManagement from './pages/admin/UserManagement';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/unauthorized" element={<Unauthorized />} />
          <Route path="/404" element={<NotFound />} />
          
          {/* Protected Routes inside Layout */}
          <Route element={<Layout />}>
            
            {/* User Routes */}
            <Route element={<ProtectedRoute allowedRoles={['user']} />}>
              <Route path="/dashboard" element={<Dashboard />} />
            </Route>

            {/* Advisor Routes */}
            <Route element={<ProtectedRoute allowedRoles={['advisor']} />}>
              <Route path="/advisor/clients" element={<ClientList />} />
            </Route>

            {/* Admin Routes */}
            <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
              <Route path="/admin/users" element={<UserManagement />} />
            </Route>

            {/* Default redirect logic if root is accessed */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Route>

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
