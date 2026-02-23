import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { requireRateLimit } from '@/lib/api-auth';

interface Skill {
  skill_uri: string;
  skill_label: string;
  L1: string;
  L2: string;
}

interface OccupationSkills {
  essential: Skill[];
  optional: Skill[];
}

interface OccupationSkillsData {
  occupation_skills: Record<string, OccupationSkills>;
}

interface OccupationMetadata {
  uri: string;
  label: string;
  isco_code: string;
}

// Cache en memoria (el JSON es grande, cargarlo una vez)
let skillsCache: Record<string, OccupationSkills> | null = null;
let metadataCache: OccupationMetadata[] | null = null;

function loadSkillsData(): Record<string, OccupationSkills> {
  if (skillsCache) return skillsCache;

  const filePath = path.join(
    process.cwd(),
    '../../database/embeddings/esco_occupation_skills.json'
  );

  const data = fs.readFileSync(filePath, 'utf-8');
  const parsed: OccupationSkillsData = JSON.parse(data);
  skillsCache = parsed.occupation_skills;
  return skillsCache;
}

function loadMetadata(): OccupationMetadata[] {
  if (metadataCache) return metadataCache;

  const filePath = path.join(
    process.cwd(),
    '../../database/embeddings/esco_occupations_metadata.json'
  );

  const data = fs.readFileSync(filePath, 'utf-8');
  metadataCache = JSON.parse(data);
  return metadataCache!;
}

export async function GET(request: NextRequest) {
  const limited = requireRateLimit(request);
  if (limited) return limited;

  const searchParams = request.nextUrl.searchParams;
  const uri = searchParams.get('uri');
  const id = searchParams.get('id');

  if (!uri && !id) {
    return NextResponse.json(
      { error: 'uri or id parameter required' },
      { status: 400 }
    );
  }

  try {
    const skillsData = loadSkillsData();
    const metadata = loadMetadata();

    // Construir URI completo si se pasó solo ID
    let fullUri = uri;
    if (id && !uri) {
      fullUri = `http://data.europa.eu/esco/occupation/${id}`;
    }

    // Buscar metadata de la ocupación
    const occupation = metadata.find(m => m.uri === fullUri);
    if (!occupation) {
      return NextResponse.json(
        { error: 'Occupation not found' },
        { status: 404 }
      );
    }

    // Obtener skills
    const skills = skillsData[fullUri!];
    if (!skills) {
      return NextResponse.json({
        occupation: {
          id: occupation.uri.split('/').pop(),
          uri: occupation.uri,
          label: occupation.label,
          isco_code: occupation.isco_code
        },
        essential: [],
        optional: []
      });
    }

    return NextResponse.json({
      occupation: {
        id: occupation.uri.split('/').pop(),
        uri: occupation.uri,
        label: occupation.label,
        isco_code: occupation.isco_code
      },
      essential: skills.essential || [],
      optional: skills.optional || [],
      stats: {
        essentialCount: skills.essential?.length || 0,
        optionalCount: skills.optional?.length || 0,
        totalCount: (skills.essential?.length || 0) + (skills.optional?.length || 0)
      }
    });
  } catch (error) {
    console.error('Error loading occupation skills:', error);
    return NextResponse.json(
      { error: 'Error loading occupation skills' },
      { status: 500 }
    );
  }
}
