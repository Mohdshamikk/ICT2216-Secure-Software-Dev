import type { User, Transaction, Client } from '../types';

export const mockUsers: User[] = [
  { id: '1', name: 'John Doe', email: 'user@example.com', role: 'user', status: 'active', lastLogin: '2026-05-24T10:00:00Z' },
  { id: '2', name: 'Jane Smith', email: 'advisor@example.com', role: 'advisor', status: 'active', lastLogin: '2026-05-24T09:30:00Z' },
  { id: '3', name: 'Admin Boss', email: 'admin@example.com', role: 'admin', status: 'active', lastLogin: '2026-05-24T08:15:00Z' },
  { id: '4', name: 'Inactive User', email: 'olduser@example.com', role: 'user', status: 'inactive', lastLogin: '2025-12-01T10:00:00Z' },
];

export const mockTransactions: Transaction[] = [
  { id: 't1', date: '2026-05-24', description: 'Hawker Centre Lunch', amount: 8.50, category: 'Food', type: 'expense' },
  { id: 't2', date: '2026-05-23', description: 'MRT Top-up', amount: 20.00, category: 'Transport', type: 'expense' },
  { id: 't3', date: '2026-05-22', description: 'NTUC Fairprice', amount: 45.20, category: 'Groceries', type: 'expense' },
  { id: 't4', date: '2026-05-20', description: 'Salary', amount: 5000.00, category: 'Income', type: 'income' },
  { id: 't5', date: '2026-05-18', description: 'SP Services (Utilities)', amount: 120.00, category: 'Utilities', type: 'expense' },
];

export const mockClients: Client[] = [
  { id: 'c1', name: 'John Doe', email: 'user@example.com', consentStatus: 'granted', lastViewed: '2026-05-20T14:30:00Z' },
  { id: 'c2', name: 'Alice Lee', email: 'alice@example.com', consentStatus: 'revoked', lastViewed: '2026-04-15T09:00:00Z' },
  { id: 'c3', name: 'Bob Tan', email: 'bob@example.com', consentStatus: 'granted', lastViewed: '2026-05-22T11:20:00Z' },
];

export const mockMonthlyData = [
  { month: 'Jan', income: 5000, expense: 3200 },
  { month: 'Feb', income: 5000, expense: 2800 },
  { month: 'Mar', income: 5000, expense: 3500 },
  { month: 'Apr', income: 5000, expense: 3100 },
  { month: 'May', income: 5000, expense: 193.70 },
];
