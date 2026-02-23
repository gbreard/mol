import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { requireRateLimit } from '@/lib/api-auth';

interface Occupation {
  uri: string;
  label: string;
  isco_code: string;
}

// Cache del metadata en memoria
let occupationsCache: Occupation[] | null = null;

function loadOccupations(): Occupation[] {
  if (occupationsCache) return occupationsCache;

  const filePath = path.join(
    process.cwd(),
    '../../database/embeddings/esco_occupations_metadata.json'
  );

  const data = fs.readFileSync(filePath, 'utf-8');
  occupationsCache = JSON.parse(data);
  return occupationsCache!;
}

function normalizeText(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // Quitar acentos
    .replace(/[^\w\s]/g, ''); // Quitar caracteres especiales
}

export async function GET(request: NextRequest) {
  const limited = requireRateLimit(request);
  if (limited) return limited;

  const searchParams = request.nextUrl.searchParams;
  const query = searchParams.get('q') || '';
  const limit = parseInt(searchParams.get('limit') || '20', 10);

  if (!query || query.length < 2) {
    return NextResponse.json({ results: [] });
  }

  try {
    const occupations = loadOccupations();
    const normalizedQuery = normalizeText(query);
    const queryWords = normalizedQuery.split(/\s+/).filter(w => w.length > 0);

    // Buscar ocupaciones que contengan todas las palabras
    const results = occupations
      .map(occ => {
        const normalizedLabel = normalizeText(occ.label);

        // Calcular score basado en matches
        let score = 0;
        let allWordsMatch = true;

        for (const word of queryWords) {
          if (normalizedLabel.includes(word)) {
            score += 10;
            // Bonus si empieza con la palabra
            if (normalizedLabel.startsWith(word)) {
              score += 5;
            }
          } else {
            allWordsMatch = false;
          }
        }

        // También buscar en ISCO code
        if (occ.isco_code.toLowerCase().includes(query.toLowerCase())) {
          score += 15;
          allWordsMatch = true;
        }

        return { occupation: occ, score, allWordsMatch };
      })
      .filter(item => item.score > 0 && item.allWordsMatch)
      .sort((a, b) => b.score - a.score)
      .slice(0, limit)
      .map(item => ({
        id: item.occupation.uri.split('/').pop(), // ID corto
        uri: item.occupation.uri,
        label: item.occupation.label,
        isco_code: item.occupation.isco_code
      }));

    return NextResponse.json({ results });
  } catch (error) {
    console.error('Error searching occupations:', error);
    return NextResponse.json(
      { error: 'Error searching occupations' },
      { status: 500 }
    );
  }
}
