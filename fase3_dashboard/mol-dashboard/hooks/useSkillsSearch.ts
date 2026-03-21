"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import type { SearchableSkill, SkillsSearchableIndex } from "@/lib/types";

// Module-level cache — survives component unmounts
let cachedData: SkillsSearchableIndex | null = null;
let loadingPromise: Promise<void> | null = null;

function normalize(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

/**
 * Hook for searching ESCO skills.
 * Loads skills_searchable.json once (cached at module level).
 * Returns a search function and loading state.
 */
export function useSkillsSearch() {
  const [data, setData] = useState<SkillsSearchableIndex | null>(cachedData);
  const [isLoading, setIsLoading] = useState(!cachedData);

  useEffect(() => {
    if (cachedData) {
      setData(cachedData);
      setIsLoading(false);
      return;
    }
    if (loadingPromise) {
      loadingPromise.then(() => {
        setData(cachedData);
        setIsLoading(false);
      });
      return;
    }
    loadingPromise = fetch("/data/skills_searchable.json")
      .then((res) => res.json())
      .then((json: SkillsSearchableIndex) => {
        cachedData = json;
        setData(json);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error("Error loading skills:", err);
        setIsLoading(false);
        loadingPromise = null;
      });
  }, []);

  const search = useCallback(
    (query: string, excludeIds?: Set<string>, limit = 20): SearchableSkill[] => {
      if (!data || !query.trim()) return [];
      const normalizedQuery = normalize(query);
      return data.skills
        .filter((skill) => {
          if (excludeIds?.has(skill.id)) return false;
          return normalize(skill.label).includes(normalizedQuery);
        })
        .slice(0, limit);
    },
    [data]
  );

  const skills = useMemo(() => data?.skills ?? [], [data]);

  return { skills, search, isLoading };
}
