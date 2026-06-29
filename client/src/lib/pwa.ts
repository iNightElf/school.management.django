let _prompt: any = null;

export function setInstallPrompt(e: any) {
  _prompt = e;
}

export function getInstallPrompt() {
  return _prompt;
}

export function clearInstallPrompt() {
  _prompt = null;
}

export function isStandalone() {
  return window.matchMedia('(display-mode: standalone)').matches || !!(navigator as any).standalone;
}

export function swapManifest(href: string) {
  const el = document.querySelector<HTMLLinkElement>('link[rel="manifest"]');
  if (el) el.href = href;
}
