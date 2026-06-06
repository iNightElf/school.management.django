export interface Student {
  id: string;
  classId?: string | null;
  class: string;
  studentId: string;
  roll: string | null;
  session: string | null;
  name: string;
  fatherName: string | null;
  motherName: string | null;
  contact: string | null;
  hasPhoto: boolean;
  hasGraduated: boolean;
  photoUrl?: string | null;
  createdAt: string;
}

export interface Teacher {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  role: string | null;
  hasPhoto: boolean;
  photoUrl?: string | null;
  createdAt: string;
}

export interface Staff {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  designation: string | null;
  hasPhoto: boolean;
  photoUrl?: string | null;
  createdAt: string;
}

export interface SchoolClass {
  id: string;
  name: string;
  section?: string | null;
  order?: number;
  createdAt?: string;
  studentCount?: number;
  bookCount?: number;
  subjectCount?: number;
}

export interface Subject {
  id: string;
  name: string;
  fullMarks: number;
  classId: string;
  order: number;
}

export interface Result {
  id: string;
  studentId: string;
  session: string;
  term: string;
  marks: Record<string, number>;
  attendance: { days: number; present: number } | null;
  comment: string | null;
}

export interface FeeSchedule {
  id: string;
  academicYearId: string;
  classId: string | null;
  category: string;
  amount: number;
  frequency: string;
  applicability: string;
  classRel?: { name: string } | null;
}

export interface Transaction {
  id: string;
  date: string;
  transactionType: 'INCOME' | 'EXPENSE' | 'INTERNAL_TRANSFER';
  description: string;
  category: string | null;
  amount: number;
  sourceAccount: string | null;
  destinationAccount: string | null;
  studentId: string | null;
  student?: { name: string } | null;
  className?: string | null;
  feeMonth: string | null;
  feeScheduleId: string | null;
  affectsIncomeLedger?: boolean;
  affectsExpenseLedger?: boolean;
  isCancelled?: boolean;
  reversalOfId: string | null;
  createdAt: string;
}

export interface Balance {
  account: string;
  balance: number;
}

export interface AcademicYear {
  id: string;
  name: string;
  isActive: boolean;
}

export interface OpeningBalance {
  id: string;
  fiscalYear: number;
  account: string;
  amount: number;
}

export interface OpeningBalanceHistory {
  id: string;
  fiscalYear: number;
  account: string;
  oldAmount: number;
  newAmount: number;
  changedBy: string;
  changedAt: string;
}

export interface Book {
  id: string;
  title: string;
  author: string | null;
  schoolClassId: string | null;
  className?: string | null;
}

export interface SchoolSettings {
  school_name: string;
  address: string;
  phone: string;
  email: string;
  website: string;
}
