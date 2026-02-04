import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import { ConsolidatedProfilesIndex, ConsolidatedProfile } from '@/lib/types';

const DATA_PATH = path.join(process.cwd(), 'public/data/consolidated_profiles.json');

// Initialize empty file if it doesn't exist
async function ensureDataFile(): Promise<ConsolidatedProfilesIndex> {
  try {
    const data = await fs.readFile(DATA_PATH, 'utf-8');
    return JSON.parse(data);
  } catch {
    const initial: ConsolidatedProfilesIndex = {
      version: '1.0.0',
      generated_at: new Date().toISOString(),
      profiles: {}
    };
    await fs.writeFile(DATA_PATH, JSON.stringify(initial, null, 2));
    return initial;
  }
}

export async function GET() {
  try {
    const data = await ensureDataFile();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error reading consolidated profiles:', error);
    return NextResponse.json(
      { error: 'Failed to read profiles' },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { esco_uuid, profile } = body as {
      esco_uuid: string;
      profile: ConsolidatedProfile;
    };

    if (!esco_uuid || !profile) {
      return NextResponse.json(
        { error: 'Missing esco_uuid or profile' },
        { status: 400 }
      );
    }

    // Read current data
    const data = await ensureDataFile();

    // Update profile
    data.profiles[esco_uuid] = profile;
    data.generated_at = new Date().toISOString();

    // Save
    await fs.writeFile(DATA_PATH, JSON.stringify(data, null, 2));

    return NextResponse.json(data);
  } catch (error) {
    console.error('Error saving consolidated profile:', error);
    return NextResponse.json(
      { error: 'Failed to save profile' },
      { status: 500 }
    );
  }
}
