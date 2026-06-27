import { useEffect, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { useFocusTrap } from '../lib/useFocusTrap';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  className?: string;
}

export default function Modal({ open, onClose, title, children, className = '' }: ModalProps) {
  const trapRef = useFocusTrap(open);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div ref={trapRef} onClick={e => e.stopPropagation()}
        className={`bg-white rounded-2xl w-full max-w-md mx-4 shadow-xl max-h-[85vh] flex flex-col ${className}`}>
        {title && (
          <div className="flex items-center justify-between p-4 border-b border-school-border shrink-0">
            <h3 className="font-bold text-sm text-school-primary">{title}</h3>
            <button onClick={onClose} className="p-1 hover:bg-school-paper rounded-lg" aria-label="Close"><X size={16} /></button>
          </div>
        )}
        <div className="overflow-y-auto p-4">{children}</div>
      </div>
    </div>,
    document.body
  );
}
