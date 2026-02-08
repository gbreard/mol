export const ROLE = {
  SUPER_ADMIN: "super_admin",
  ADMIN: "admin",
  ANALYST: "analyst",
  VIEWER: "viewer",
} as const;

export type Role = (typeof ROLE)[keyof typeof ROLE];

export const PLAN = {
  FREE: "free",
  PRO: "pro",
  ENTERPRISE: "enterprise",
} as const;

export type Plan = (typeof PLAN)[keyof typeof PLAN];

export interface UserProfile {
  email: string;
  displayName: string;
  role: Role;
  plan: Plan;
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

  return { email, displayName, role, plan };
}

export function isAdmin(role: Role): boolean {
  return role === ROLE.SUPER_ADMIN || role === ROLE.ADMIN;
}

export function isSubscriber(plan: Plan): boolean {
  return plan === PLAN.PRO || plan === PLAN.ENTERPRISE;
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
  };
  return badges[role] ?? badges[ROLE.VIEWER];
}

export function getPlanBadge(
  plan: Plan,
): { label: string; className: string } | null {
  if (plan === PLAN.FREE) return null;
  const badges: Record<string, { label: string; className: string }> = {
    [PLAN.PRO]: { label: "Pro", className: "bg-green-100 text-green-700" },
    [PLAN.ENTERPRISE]: {
      label: "Enterprise",
      className: "bg-amber-100 text-amber-700",
    },
  };
  return badges[plan] ?? null;
}
