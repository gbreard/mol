import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const LOWERCASE_WORDS = new Set([
  'de', 'del', 'la', 'las', 'los', 'el', 'en', 'y', 'o', 'a',
  'con', 'por', 'para', 'al', 'un', 'una',
]);

export function capitalize(text: string): string {
  if (!text) return text;
  return text
    .toLowerCase()
    .split(' ')
    .map((word, i) =>
      i === 0 || !LOWERCASE_WORDS.has(word)
        ? word.charAt(0).toUpperCase() + word.slice(1)
        : word
    )
    .join(' ');
}
