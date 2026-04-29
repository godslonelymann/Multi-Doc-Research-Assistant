import { useEffect, useState } from "react";

import { getHealth } from "../services/healthService.js";

export function useHealthCheck() {
  const [status, setStatus] = useState("unknown");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadHealth() {
      try {
        const data = await getHealth();
        if (isMounted) {
          setStatus(data.status);
        }
      } catch {
        if (isMounted) {
          setStatus("unavailable");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadHealth();

    return () => {
      isMounted = false;
    };
  }, []);

  return { status, loading };
}
