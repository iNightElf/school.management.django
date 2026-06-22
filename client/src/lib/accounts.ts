export const ACCOUNTS = [
  { id: 'AL_RAWA_BANK', label: 'AL RAWA English School Bank', short: 'AL RAWA Bank', color: 'from-blue-500 to-blue-600', ring: 'ring-blue-200' },
  { id: 'GLOBAL_FORUM_BANK', label: 'Global Forum Bank Account', short: 'Global Forum', color: 'from-indigo-500 to-indigo-600', ring: 'ring-indigo-200' },
  { id: 'CASH_IN_HAND', label: 'Cash in Hand', short: 'Cash', color: 'from-emerald-500 to-emerald-600', ring: 'ring-emerald-200' },
] as const;

export type AccountId = (typeof ACCOUNTS)[number]['id'];
export const ACCOUNT_IDS: AccountId[] = ['AL_RAWA_BANK', 'GLOBAL_FORUM_BANK', 'CASH_IN_HAND'];

export const PRIMARY_BANK = 'AL_RAWA_BANK' as const;
export const SECONDARY_BANK = 'GLOBAL_FORUM_BANK' as const;
export const CASH_BANK = 'CASH_IN_HAND' as const;

export const ACCOUNTS_LEDGER: { id: AccountId; label: string; short: string; color: string }[] = [
  { id: 'CASH_IN_HAND', label: 'Cash in Hand', short: 'Cash', color: 'bg-emerald-500' },
  { id: 'AL_RAWA_BANK', label: 'AL RAWA Bank', short: 'Bank', color: 'bg-blue-500' },
  { id: 'GLOBAL_FORUM_BANK', label: 'Global Forum Bank', short: 'GF Bank', color: 'bg-indigo-500' },
];

export const ACCOUNT_LABELS: Record<AccountId, string> = {
  AL_RAWA_BANK: 'AL RAWA English School Bank',
  GLOBAL_FORUM_BANK: 'Global Forum Bank Account',
  CASH_IN_HAND: 'Cash in Hand',
};
