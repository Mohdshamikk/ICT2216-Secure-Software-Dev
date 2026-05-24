import React, { useState } from 'react';
import { mockUsers } from '../../data/mockData';
import { MoreVertical, Search, ShieldCheck } from 'lucide-react';

const UserManagement: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredUsers = mockUsers.filter(user => 
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>User Management</h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            Manage platform users, roles, and access. Financial data is inaccessible from this view.
          </p>
        </div>
        <button className="btn btn-primary" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <ShieldCheck size={18} />
          Create User
        </button>
      </div>

      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ marginBottom: '1.5rem', position: 'relative', maxWidth: '400px' }}>
          <Search size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)' }} />
          <input 
            type="text" 
            className="form-input" 
            placeholder="Search users by name or email..." 
            style={{ paddingLeft: '2.5rem' }}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '0.75rem 1rem' }}>Name</th>
                <th style={{ padding: '0.75rem 1rem' }}>Email</th>
                <th style={{ padding: '0.75rem 1rem' }}>Role</th>
                <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                <th style={{ padding: '0.75rem 1rem' }}>Last Login</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((u) => (
                <tr key={u.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '1rem', fontWeight: 500 }}>{u.name}</td>
                  <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>{u.email}</td>
                  <td style={{ padding: '1rem' }}>
                    <select 
                      className="form-input" 
                      style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem', width: 'auto' }}
                      defaultValue={u.role}
                    >
                      <option value="user">User</option>
                      <option value="advisor">Advisor</option>
                      <option value="admin">Admin</option>
                    </select>
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={{ 
                        width: '8px', 
                        height: '8px', 
                        borderRadius: '50%', 
                        backgroundColor: u.status === 'active' ? 'var(--success)' : 'var(--text-muted)' 
                      }} />
                      <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                        {u.status}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '1rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    {u.lastLogin ? new Date(u.lastLogin).toLocaleString() : 'Never'}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'right' }}>
                    <button className="btn" style={{ padding: '0.25rem', backgroundColor: 'transparent', color: 'var(--text-muted)' }}>
                      <MoreVertical size={20} />
                    </button>
                  </td>
                </tr>
              ))}
              
              {filteredUsers.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No users found matching your search.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default UserManagement;
