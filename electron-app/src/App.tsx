import './App.css';
import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { LoginForm } from './components/LoginForm';
import { Dashboard } from './components/Dashboard';

const App: React.FC = () => {
  const { user, loading, login } = useAuth();
  const [authError, setAuthError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleLogin = async (email: string, password: string) => {
    setSubmitting(true);
    setAuthError(null);
    try {
      await login(email, password);
    } catch (error) {
      console.error(error);
      setAuthError('Não foi possível autenticar. Verifique as credenciais.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-state">
        <span className="spinner" />
        <p>Carregando…</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="login-wrapper">
        <LoginForm onSubmit={handleLogin} busy={submitting} error={authError} />
      </div>
    );
  }

  return <Dashboard user={user} />;
};

export default App;
