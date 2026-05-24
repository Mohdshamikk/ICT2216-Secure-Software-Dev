export type UserRole = 'user' | 'advisor' | 'admin';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: 'active' | 'inactive';
  lastLogin?: string;
}

export interface Transaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  category: string;
  type: 'expense' | 'income';
}

export interface Client {
  id: string;
  name: string;
  email: string;
  consentStatus: 'granted' | 'revoked';
  lastViewed?: string;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
}
