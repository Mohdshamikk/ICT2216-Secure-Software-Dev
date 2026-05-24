import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Wallet, TrendingUp, TrendingDown, CreditCard } from 'lucide-react';
import StatCard from '../../components/StatCard';
import { mockTransactions, mockMonthlyData } from '../../data/mockData';

const Dashboard: React.FC = () => {
  // Compute basic stats
  const totalBalance = 24500.50;
  const monthlyIncome = 5000.00;
  const monthlyExpense = mockTransactions
    .filter(t => t.type === 'expense')
    .reduce((acc, t) => acc + t.amount, 0);

  // Format currency
  const formatSGD = (amount: number) => {
    return new Intl.NumberFormat('en-SG', { style: 'currency', currency: 'SGD' }).format(amount);
  };

  // Pie chart data
  const expensesByCategory = mockTransactions
    .filter(t => t.type === 'expense')
    .reduce((acc, t) => {
      const existing = acc.find(item => item.name === t.category);
      if (existing) {
        existing.value += t.amount;
      } else {
        acc.push({ name: t.category, value: t.amount });
      }
      return acc;
    }, [] as { name: string; value: number }[]);

  const COLORS = ['#10b981', '#f59e0b', '#3b82f6', '#ef4444', '#8b5cf6'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <h1 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Dashboard Overview</h1>
      
      {/* Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem' }}>
        <StatCard title="Total Balance" value={formatSGD(totalBalance)} icon={Wallet} trend={5.2} />
        <StatCard title="Monthly Income" value={formatSGD(monthlyIncome)} icon={TrendingUp} />
        <StatCard title="Monthly Expenses" value={formatSGD(monthlyExpense)} icon={TrendingDown} trend={-2.4} />
        <StatCard title="Total Transactions" value={mockTransactions.length.toString()} icon={CreditCard} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
        {/* Trend Chart */}
        <div className="glass-panel" style={{ padding: '1.5rem', gridColumn: 'span 2' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>6-Month Cash Flow</h3>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={mockMonthlyData}>
                <defs>
                  <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--success)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="var(--success)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorExpense" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--danger)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="var(--danger)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                <XAxis dataKey="month" stroke="var(--text-secondary)" />
                <YAxis stroke="var(--text-secondary)" tickFormatter={(value) => `$${value}`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
                  itemStyle={{ color: 'var(--text-primary)' }}
                />
                <Area type="monotone" dataKey="income" stroke="var(--success)" fillOpacity={1} fill="url(#colorIncome)" name="Income" />
                <Area type="monotone" dataKey="expense" stroke="var(--danger)" fillOpacity={1} fill="url(#colorExpense)" name="Expenses" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Expense Breakdown */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>Expenses by Category</h3>
          <div style={{ height: '300px', display: 'flex', justifyContent: 'center' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={expensesByCategory}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                >
                  {expensesByCategory.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--border-color)' }}
                  formatter={(value: any) => formatSGD(Number(value))}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h3>Recent Transactions</h3>
          <button className="btn btn-primary" style={{ fontSize: '0.875rem', padding: '0.25rem 0.75rem' }}>View All</button>
        </div>
        
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '0.75rem 0' }}>Date</th>
                <th style={{ padding: '0.75rem 0' }}>Description</th>
                <th style={{ padding: '0.75rem 0' }}>Category</th>
                <th style={{ padding: '0.75rem 0', textAlign: 'right' }}>Amount</th>
              </tr>
            </thead>
            <tbody>
              {mockTransactions.map((tx) => (
                <tr key={tx.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '1rem 0', color: 'var(--text-secondary)' }}>{tx.date}</td>
                  <td style={{ padding: '1rem 0', fontWeight: 500 }}>{tx.description}</td>
                  <td style={{ padding: '1rem 0' }}>
                    <span style={{ padding: '0.25rem 0.5rem', backgroundColor: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem' }}>
                      {tx.category}
                    </span>
                  </td>
                  <td style={{ padding: '1rem 0', textAlign: 'right', fontWeight: 600, color: tx.type === 'income' ? 'var(--success)' : 'var(--text-primary)' }}>
                    {tx.type === 'income' ? '+' : '-'}{formatSGD(tx.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
