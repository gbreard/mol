'use client';

import { useEffect, useState } from 'react';
import SkillsSunburst from '@/components/SkillsSunburst';

interface SkillCategory {
  name: string;
  label: string;
  count: number;
  percentage: string;
}

export default function SkillsPage() {
  const [stats, setStats] = useState<{
    total: number;
    categories: SkillCategory[];
  }>({ total: 0, categories: [] });

  useEffect(() => {
    // Cargar estadísticas del JSON
    fetch('/data/esco_skills_hierarchy.json')
      .then(res => res.json())
      .then(data => {
        const categories: SkillCategory[] = [];
        let total = 0;

        const countValue = (node: any): number => {
          if (node.value) return node.value;
          if (node.children) {
            return node.children.reduce((sum: number, child: any) => sum + countValue(child), 0);
          }
          return 0;
        };

        if (data.children) {
          data.children.forEach((cat: any) => {
            const count = countValue(cat);
            total += count;
            categories.push({
              name: cat.name,
              label: cat.label,
              count,
              percentage: '0'
            });
          });

          // Calcular porcentajes
          categories.forEach(cat => {
            cat.percentage = ((cat.count / total) * 100).toFixed(1);
          });
        }

        setStats({ total, categories });
      })
      .catch(console.error);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Taxonomía de Competencias ESCO
          </h1>
          <p className="mt-2 text-gray-600">
            Visualización interactiva de la jerarquía de skills del framework ESCO
            (European Skills, Competences, Qualifications and Occupations)
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="text-3xl font-bold text-gray-900">
              {stats.total.toLocaleString()}
            </div>
            <div className="text-sm text-gray-500 mt-1">Skills totales</div>
          </div>

          {stats.categories.map(cat => (
            <div key={cat.name} className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {cat.count.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">{cat.label}</div>
                </div>
                <div className={`text-lg font-semibold ${
                  cat.name === 'S' ? 'text-blue-600' :
                  cat.name === 'T' ? 'text-green-600' :
                  cat.name === 'K' ? 'text-amber-600' : 'text-purple-600'
                }`}>
                  {cat.percentage}%
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Sunburst */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Distribución Jerárquica de Skills
          </h2>
          <p className="text-sm text-gray-600 mb-6">
            Haz clic en cualquier segmento para ver detalles. Los colores representan
            las categorías principales: <span className="text-blue-600 font-medium">Técnicas</span>,
            <span className="text-green-600 font-medium ml-1">Transversales</span>, y
            <span className="text-amber-600 font-medium ml-1">Conocimientos</span>.
          </p>

          <SkillsSunburst width={700} height={700} />
        </div>

        {/* Descripción de categorías */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-blue-50 rounded-xl p-6 border border-blue-100">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <h3 className="font-semibold text-blue-900">Competencias Técnicas (S)</h3>
            </div>
            <p className="text-sm text-blue-800">
              Habilidades específicas de un campo profesional: comunicación, gestión de información,
              trabajo con ordenadores, maquinaria, construcción, etc.
            </p>
            <ul className="mt-3 text-xs text-blue-700 space-y-1">
              <li>• S1: Comunicación y colaboración</li>
              <li>• S2: Competencias de información</li>
              <li>• S3: Asistencia y cuidados</li>
              <li>• S4: Competencias de gestión</li>
              <li>• S5-S8: Trabajo técnico y maquinaria</li>
            </ul>
          </div>

          <div className="bg-green-50 rounded-xl p-6 border border-green-100">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <h3 className="font-semibold text-green-900">Transversales (T)</h3>
            </div>
            <p className="text-sm text-green-800">
              Capacidades aplicables a cualquier ocupación: pensamiento crítico,
              autogestión, habilidades sociales, capacidades físicas.
            </p>
            <ul className="mt-3 text-xs text-green-700 space-y-1">
              <li>• T1: Capacidades básicas</li>
              <li>• T2: Razonamiento</li>
              <li>• T3: Autogestión</li>
              <li>• T4: Sociales y comunicación</li>
              <li>• T5-T6: Físicas y para la vida</li>
            </ul>
          </div>

          <div className="bg-amber-50 rounded-xl p-6 border border-amber-100">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-3 h-3 rounded-full bg-amber-500"></div>
              <h3 className="font-semibold text-amber-900">Conocimientos (K)</h3>
            </div>
            <p className="text-sm text-amber-800">
              Saberes teóricos y prácticos adquiridos a través de la experiencia
              o educación: idiomas, matemáticas, ciencias, regulaciones, etc.
            </p>
            <ul className="mt-3 text-xs text-amber-700 space-y-1">
              <li>• Conocimientos técnicos específicos</li>
              <li>• Normativas y regulaciones</li>
              <li>• Teorías y metodologías</li>
              <li>• Herramientas y tecnologías</li>
            </ul>
          </div>
        </div>

        {/* Footer info */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>
            Fuente: <a
              href="https://esco.ec.europa.eu"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              ESCO v1.2.0
            </a> - European Commission
          </p>
        </div>
      </div>
    </div>
  );
}
