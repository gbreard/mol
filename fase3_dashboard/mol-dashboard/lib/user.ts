export const ROLE = {
  SUPER_ADMIN: "super_admin",
  ADMIN: "admin",
  ANALYST: "analyst",
  VIEWER: "viewer",
  OFICINA_EMPLEO: "oficina_empleo",
} as const;

export type Role = (typeof ROLE)[keyof typeof ROLE];

export const PLAN = {
  FREE: "free",
  TRIAL: "trial",
  PRO: "pro",
  ENTERPRISE: "enterprise",
} as const;

export type Plan = (typeof PLAN)[keyof typeof PLAN];

const TRIAL_DAYS = 7;

export interface UserProfile {
  email: string;
  displayName: string;
  role: Role;
  plan: Plan;
  trialStartDate?: string;
}

export function getUserProfile(user: {
  email?: string;
  user_metadata?: Record<string, unknown>;
}): UserProfile {
  const metadata = user.user_metadata ?? {};
  const email = user.email ?? "";
  const displayName =
    (metadata.display_name as string) || email.split("@")[0] || "Usuario";
  const role = (metadata.role as Role) || ROLE.VIEWER;
  const plan = (metadata.plan as Plan) || PLAN.FREE;
  const trialStartDate = (metadata.trial_start_date as string) || undefined;

  return { email, displayName, role, plan, trialStartDate };
}

export function isAdmin(role: Role): boolean {
  return role === ROLE.SUPER_ADMIN || role === ROLE.ADMIN;
}

export function isSubscriber(plan: Plan): boolean {
  return plan === PLAN.PRO || plan === PLAN.ENTERPRISE;
}

export function isTrial(plan: Plan): boolean {
  return plan === PLAN.TRIAL;
}

export function hasTrialExpired(trialStartDate?: string): boolean {
  if (!trialStartDate) return true;
  const start = new Date(trialStartDate);
  if (isNaN(start.getTime())) return true;
  const now = new Date();
  const diffMs = now.getTime() - start.getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  return diffDays >= TRIAL_DAYS;
}

export function getTrialDaysRemaining(trialStartDate?: string): number {
  if (!trialStartDate) return 0;
  const start = new Date(trialStartDate);
  if (isNaN(start.getTime())) return 0;
  const now = new Date();
  const diffMs = now.getTime() - start.getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  const remaining = Math.ceil(TRIAL_DAYS - diffDays);
  return Math.max(0, Math.min(TRIAL_DAYS, remaining));
}

export function canAccessDashboard(
  role: Role,
  plan: Plan,
  trialStartDate?: string,
): boolean {
  if (isAdmin(role)) return true;
  if (isSubscriber(plan)) return true;
  if (isTrial(plan) && !hasTrialExpired(trialStartDate)) return true;
  return false;
}

export function isOficinaEmpleo(role: Role): boolean {
  return role === ROLE.OFICINA_EMPLEO;
}

export function getRoleBadge(role: Role): { label: string; className: string } {
  const badges: Record<Role, { label: string; className: string }> = {
    [ROLE.SUPER_ADMIN]: {
      label: "Super Admin",
      className: "bg-purple-100 text-purple-700",
    },
    [ROLE.ADMIN]: {
      label: "Admin",
      className: "bg-purple-100 text-purple-700",
    },
    [ROLE.ANALYST]: {
      label: "Analista",
      className: "bg-blue-100 text-blue-700",
    },
    [ROLE.VIEWER]: {
      label: "Viewer",
      className: "bg-gray-100 text-gray-600",
    },
    [ROLE.OFICINA_EMPLEO]: {
      label: "Oficina de Empleo",
      className: "bg-teal-100 text-teal-700",
    },
  };
  return badges[role] ?? badges[ROLE.VIEWER];
}

export function getPlanBadge(
  plan: Plan,
): { label: string; className: string } | null {
  if (plan === PLAN.FREE) return null;
  const badges: Record<string, { label: string; className: string }> = {
    [PLAN.TRIAL]: {
      label: "Trial (7 dias)",
      className: "bg-orange-100 text-orange-700",
    },
    [PLAN.PRO]: { label: "Pro", className: "bg-green-100 text-green-700" },
    [PLAN.ENTERPRISE]: {
      label: "Enterprise",
      className: "bg-amber-100 text-amber-700",
    },
  };
  return badges[plan] ?? null;
}
