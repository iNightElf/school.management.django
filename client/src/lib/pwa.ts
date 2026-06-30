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


