import { useState, useEffect } from 'react';

const API_BASE = `http://${window.location.hostname}:8000`;

/**
 * useScrapedComponents — fetches all components from the backend registry
 * and provides filtered access by component type.
 *
 * Returns:
 *   components: Full list of components
 *   byType(type): Function to filter components by type
 *   types: Array of distinct component types found
 *   loading: Boolean, true while fetching
 *   error: Error message or null
 */
export default function useScrapedComponents() {
  const [components, setComponents] = useState([]);
  const [types, setTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchComponents() {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/components?limit=500`);
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        const data = await res.json();
        if (cancelled) return;
        const comps = data.components || [];
        setComponents(comps);
        setTypes(data.types || []);
      } catch (err) {
        if (cancelled) return;
        setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchComponents();
    return () => { cancelled = true; };
  }, []);

  function byType(typeName) {
    return components.filter(c => c.type === typeName);
  }

  return { components, byType, types, loading, error };
}
