import { useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { Layout } from './components/layout';
import { LoadingSpinner } from './components/common';
import {
  LoginPage,
  RegisterPage,
  SignupPage,
  DashboardPage,
  ChatPage,
  DocumentsPage,
  SettingsPage,
  LandingPage,
  AdminPage,
} from './pages';

// Protected route wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, accessToken, isLoading, fetchUser } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
    if (accessToken && !isAuthenticated) {
      fetchUser();
    }
  }, [accessToken, isAuthenticated, fetchUser]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!accessToken) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

// Public route wrapper (redirect if authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, accessToken } = useAuthStore();

  if (accessToken && isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// Home redirect - landing for guests, dashboard for authenticated
const HomeRedirect: React.FC = () => {
  const { isAuthenticated, accessToken } = useAuthStore();

  if (accessToken && isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <LandingPage />;
};

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <PublicRoute>
            <SignupPage />
          </PublicRoute>
        }
      />

      {/* Protected routes */}
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Route>

      {/* Landing/Trial page for guests */}
      <Route path="/try-free" element={<LandingPage />} />

      {/* Default redirect - show landing for non-auth, dashboard for auth */}
      <Route path="/" element={<HomeRedirect />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
