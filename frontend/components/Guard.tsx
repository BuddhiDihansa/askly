"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { ApiError, api, clearToken } from "../lib/api";

/**
 * Wrap any page's content in <Guard> to require login.
 * On mount, it asks the backend "who am I?" (/api/auth/me) - if the
 * stored token is missing, expired, or invalid, that call fails and we
 * redirect to /login. This double-checks with the server rather than
 * just checking "is there a token in localStorage", since a token could
 * exist but no longer be valid.
 */
export default function Guard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    api("/api/auth/me")
      .then((user) => {
        if (!user.onboarding_completed && pathname !== "/onboarding") {
          router.replace("/onboarding");
        }
        if (user.onboarding_completed && pathname === "/onboarding") {
          router.replace("/dashboard");
        }
      })
      .catch((error) => {
        // Only send the user to /login when the server says the token is
        // missing/invalid/expired (401). A network outage or a temporary
        // 429/500 must NOT log a valid user out.
        if (error instanceof ApiError && error.status === 401) {
          clearToken();
          router.replace("/login");
        }
      });
  }, [pathname, router]);

  return <>{children}</>;
}