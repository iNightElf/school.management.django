import { useEffect } from 'react';
import { api } from '../store';

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  return new Uint8Array(rawData.split('').map((c) => c.charCodeAt(0)));
}

export function usePushSubscription() {
  useEffect(() => {
    if (!('Notification' in window) || !('serviceWorker' in navigator)) return;
    if (Notification.permission === 'denied') return;

    const init = async () => {
      try {
        const permission = Notification.permission === 'default'
          ? await Notification.requestPermission()
          : Notification.permission;
        if (permission !== 'granted') return;

        const reg = await navigator.serviceWorker.ready;

        const vapidRes = await api.get('/parents/push/vapid-key/');
        const vapidKey = vapidRes.data.publicKey;
        if (!vapidKey) return;

        const sub = await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(vapidKey) as unknown as BufferSource,
        });

        await api.post('/parents/push/subscribe/', sub.toJSON());
      } catch {}
    };

    init();
  }, []);
}
