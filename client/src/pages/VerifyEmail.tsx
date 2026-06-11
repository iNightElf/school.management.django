import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { api } from '../store';
import { MailCheck, AlertTriangle, Loader2 } from 'lucide-react';
import { SCHOOL_LOGO } from '../lib/logo';

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setStatus('error');
      setMessage('No verification token provided.');
      return;
    }
    api.post('/auth/verify-email/', { token })
      .then((res) => {
        setStatus('success');
        setMessage(res.data.detail || 'Email verified successfully.');
      })
      .catch((err) => {
        setStatus('error');
        setMessage(err.response?.data?.error || 'Verification failed.');
      });
  }, [searchParams]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-school-primary via-school-secondary to-school-accent2 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-school-paper rounded-3xl shadow-2xl overflow-hidden">
        <div className="bg-gradient-to-r from-school-primary to-school-secondary p-8 text-white text-center">
          <img src={SCHOOL_LOGO} alt="AL RAWA" className="w-16 h-16 rounded-full mx-auto mb-3 border-2 border-white/20 shadow-lg object-cover" />
          <h1 className="font-serif text-2xl">Email Verification</h1>
        </div>
        <div className="p-8 text-center space-y-4">
          {status === 'loading' && (
            <>
              <Loader2 size={48} className="text-school-primary animate-spin mx-auto" />
              <p className="text-sm text-school-muted">Verifying your email...</p>
            </>
          )}
          {status === 'success' && (
            <>
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                <MailCheck size={32} className="text-green-600" />
              </div>
              <h2 className="text-xl font-bold text-school-primary">Verified!</h2>
              <p className="text-sm text-school-muted">{message}</p>
              <Link to="/login" className="inline-block w-full bg-gradient-to-r from-school-primary to-school-secondary hover:from-school-secondary hover:to-school-primary text-white font-bold py-4 rounded-xl shadow-lg transition-all text-center">
                Go to Sign In
              </Link>
            </>
          )}
          {status === 'error' && (
            <>
              <div className="w-16 h-16 bg-rose-100 rounded-full flex items-center justify-center mx-auto">
                <AlertTriangle size={32} className="text-rose-600" />
              </div>
              <h2 className="text-xl font-bold text-school-primary">Verification Failed</h2>
              <p className="text-sm text-school-muted">{message}</p>
              <Link to="/login" className="inline-block w-full bg-gradient-to-r from-school-primary to-school-secondary hover:from-school-secondary hover:to-school-primary text-white font-bold py-4 rounded-xl shadow-lg transition-all text-center">
                Go to Sign In
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;
