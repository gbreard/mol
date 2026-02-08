"use client";

import { useRef, useEffect, useState } from "react";

interface CounterProps {
  target: number;
  suffix?: string;
  duration?: number;
}

export function Counter({ target, suffix = "", duration = 2000 }: CounterProps) {
  // Start at target so SSR shows the real number, not "0"
  const [value, setValue] = useState(target);
  const ref = useRef<HTMLSpanElement>(null);
  const animated = useRef(false);
  const hydrated = useRef(false);

  useEffect(() => {
    // After hydration, reset to 0 so the animation can play
    hydrated.current = true;
    setValue(0);

    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !animated.current) {
          animated.current = true;
          const start = performance.now();

          const tick = (now: number) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - (1 - progress) * (1 - progress);
            setValue(Math.floor(eased * target));

            if (progress < 1) {
              requestAnimationFrame(tick);
            } else {
              setValue(target);
            }
          };

          requestAnimationFrame(tick);
        }
      },
      { threshold: 0.3 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [target, duration]);

  return (
    <span ref={ref}>
      {value.toLocaleString("es-AR")}
      {suffix}
    </span>
  );
}
