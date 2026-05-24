import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import type { User, AuthContextType } from '../types';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Mock Users for development
const MOCK_USERS: Record<string, User> = {
  'user@example.com': { id: '1', name: 'John Doe', email: 'user@example.com', role: 'user', status: 'active' },
  'advisor@example.com': { id: '2', name: 'Jane Smith', email: 'advisor@example.com', role: 'advisor', status: 'active' },
  'admin@example.com': { id: '3', name: 'Admin Boss', email: 'admin@example.com', role: 'admin', status: 'active' },
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);

  const login = async (email: string, password: string): Promise<boolean> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    // Mock authentication logic (in production, this would be an API call)
    if (MOCK_USERS[email] && password === 'password123') {
      setUser(MOCK_USERS[email]);
      return true;
    }
    return false;
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
