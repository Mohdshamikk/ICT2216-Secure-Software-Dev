import React from 'react';
import { mockClients } from '../../data/mockData';
import { Eye, ShieldX } from 'lucide-react';

const ClientList: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Client Directory</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Manage your clients and view their authorized financial data. 
          Raw account numbers are automatically masked for privacy.
        </p>
      </div>

      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '0.75rem 1rem' }}>Client Name</th>
                <th style={{ padding: '0.75rem 1rem' }}>Contact</th>
                <th style={{ padding: '0.75rem 1rem' }}>Consent Status</th>
                <th style={{ padding: '0.75rem 1rem' }}>Last Viewed</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {mockClients.map((client) => (
                <tr key={client.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '1rem', fontWeight: 500 }}>{client.name}</td>
                  <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>{client.email}</td>
                  <td style={{ padding: '1rem' }}>
                    {client.consentStatus === 'granted' ? (
                      <span className="badge badge-success">Consent Granted</span>
                    ) : (
                      <span className="badge badge-danger">Consent Revoked</span>
                    )}
                  </td>
                  <td style={{ padding: '1rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    {client.lastViewed ? new Date(client.lastViewed).toLocaleDateString() : 'Never'}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'right' }}>
                    <button 
                      className="btn"
                      disabled={client.consentStatus === 'revoked'}
                      style={{ 
                        backgroundColor: client.consentStatus === 'granted' ? 'var(--accent-light)' : 'var(--bg-tertiary)',
                        color: client.consentStatus === 'granted' ? 'var(--accent-primary)' : 'var(--text-muted)',
                        padding: '0.375rem 0.75rem',
                        fontSize: '0.875rem',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                      }}
                      title={client.consentStatus === 'revoked' ? "Access denied by client" : "View dashboard"}
                    >
                      {client.consentStatus === 'revoked' ? <ShieldX size={16} /> : <Eye size={16} />}
                      View
                    </button>
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

export default ClientList;
