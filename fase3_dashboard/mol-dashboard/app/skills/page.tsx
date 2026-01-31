'use client';

import { useEffect, useState } from 'react';
import SkillsSunburst from '@/components/SkillsSunburst';

interface Stats {
  total: number;
  skills: number;
  knowledge: number;
  categoriesS: number;
  categoriesT: number;
}

export default function SkillsPage() {
  const [stats, setStats] = useState<Stats>({
    total: 0,
    skills: 0,
    knowledge: 0,
    categoriesS: 0,
    categoriesT: 0
  });

  useEffect(() => {
    // Cargar estadisticas del JSON
    fetch('/data/esco_skills_hierarchy.json')
      .then(res => res.json())
      .then(data => {
        let skills = 0;
        let knowledge = 0;
        let categoriesS = 0;
        let categoriesT = 0;

        const countByType = (node: any): void => {
          if (node.type === 'skill' && node.value) {
            skills += 1;
          } else if (node.type === 'knowledge' && node.value) {
            knowledge += 1;
          }
          if (node.children) {
            node.children.forEach(countByType);
          }
        };

        if (data.children) {
          data.children.forEach((cat: any) => {
            if (cat.name.startsWith('S')) {
              categoriesS += 1;
            } else if (cat.name.startsWith('T')) {
              categoriesT += 1;
            }
            countByType(cat);
          });
        }

        const total = skills + knowledge;
        setStats({ total, skills, knowledge, categoriesS, categoriesT });
      })
      .catch(console.error);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Taxonomia de Competencias ESCO
          </h1>
          <p className="mt-2 text-gray-600">
            Visualizacion interactiva de la jerarquia de competencias del framework ESCO
            (European Skills, Competences, Qualifications and Occupations)
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="text-3xl font-bold text-gray-900">
              {stats.total.toLocaleString()}
            </div>
            <div className="text-sm text-gray-500 mt-1">Total competencias</div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-indigo-600">
                  {stats.skills.toLocaleString()}
                </div>
                <div className="text-sm text-gray-500 mt-1">Skills (hacer)</div>
              </div>
              <div className="text-lg font-semibold text-indigo-400">
                {stats.total > 0 ? ((stats.skills / stats.total) * 100).toFixed(0) : 0}%
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-amber-600">
                  {stats.knowledge.toLocaleString()}
                </div>
                <div className="text-sm text-gray-500 mt-1">Conocimientos (saber)</div>
              </div>
              <div className="text-lg font-semibold text-amber-400">
                {stats.total > 0 ? ((stats.knowledge / stats.total) * 100).toFixed(0) : 0}%
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {stats.categoriesS}
                </div>
                <div className="text-sm text-gray-500 mt-1">Cat. Tecnicas (S)</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {stats.categoriesT}
                </div>
                <div className="text-sm text-gray-500 mt-1">Cat. Transversales (T)</div>
              </div>
            </div>
          </div>
        </div>

        {/* Sunburst */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Distribucion Jerarquica de Competencias
          </h2>
          <p className="text-sm text-gray-600 mb-6">
            <strong>Click en cualquier segmento</strong> para ver la lista completa de competencias en esa categoria.
            Se abrira un panel lateral con todas las skills y conocimientos.
          </p>

          <SkillsSunburst width={700} height={700} />
        </div>

        {/* Explicacion de la estructura */}
        <div className="mt-8 bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Estructura de la taxonomia ESCO
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Categorias */}
            <div>
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                <span className="w-3 h-3 rounded-full bg-green-500"></span>
                Categorias (anillos interiores)
              </h3>

              <div className="space-y-4">
                <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
                  <div className="font-medium text-blue-900 mb-2">S - Competencias Tecnicas</div>
                  <p className="text-sm text-blue-800 mb-2">
                    Habilidades especificas de un campo profesional.
                  </p>
                  <div className="text-xs text-blue-700 grid grid-cols-2 gap-1">
                    <span>S1: Comunicacion</span>
                    <span>S2: Informacion</span>
                    <span>S3: Asistencia</span>
                    <span>S4: Gestion</span>
                    <span>S5: Ordenadores</span>
                    <span>S6: Manipulacion</span>
                    <span>S7: Construccion</span>
                    <span>S8: Maquinaria</span>
                  </div>
                </div>

                <div className="bg-green-50 rounded-lg p-4 border border-green-100">
                  <div className="font-medium text-green-900 mb-2">T - Competencias Transversales</div>
                  <p className="text-sm text-green-800 mb-2">
                    Capacidades aplicables a cualquier ocupacion.
                  </p>
                  <div className="text-xs text-green-700 grid grid-cols-2 gap-1">
                    <span>T1: Capacidades basicas</span>
                    <span>T2: Razonamiento</span>
                    <span>T3: Autogestion</span>
                    <span>T4: Sociales</span>
                    <span>T5: Fisicas</span>
                    <span>T6: Para la vida</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Tipos */}
            <div>
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-indigo-500"></span>
                <span className="w-3 h-3 rounded-full bg-amber-500"></span>
                Tipos de Competencia
              </h3>

              <div className="space-y-4">
                <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-100">
                  <div className="font-medium text-indigo-900 mb-2">Skills (Saber Hacer)</div>
                  <p className="text-sm text-indigo-800 mb-2">
                    Capacidad para ejecutar tareas y resolver problemas.
                  </p>
                  <div className="text-xs text-indigo-700">
                    <p><strong>Ejemplos:</strong></p>
                    <ul className="list-disc list-inside mt-1">
                      <li>Programar en Python</li>
                      <li>Disenar bases de datos</li>
                      <li>Negociar contratos</li>
                      <li>Operar maquinaria CNC</li>
                    </ul>
                  </div>
                </div>

                <div className="bg-amber-50 rounded-lg p-4 border border-amber-100">
                  <div className="font-medium text-amber-900 mb-2">Conocimientos (Saber)</div>
                  <p className="text-sm text-amber-800 mb-2">
                    Informacion, teorias y conceptos adquiridos.
                  </p>
                  <div className="text-xs text-amber-700">
                    <p><strong>Ejemplos:</strong></p>
                    <ul className="list-disc list-inside mt-1">
                      <li>Lenguaje Python</li>
                      <li>Teoria de bases de datos SQL</li>
                      <li>Legislacion laboral</li>
                      <li>Principios de mecanica</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Como usar */}
        <div className="mt-8 bg-blue-50 rounded-xl p-6 border border-blue-100">
          <h2 className="text-lg font-semibold text-blue-900 mb-3">
            Como explorar la taxonomia
          </h2>
          <ol className="list-decimal list-inside space-y-2 text-sm text-blue-800">
            <li><strong>Vista general:</strong> Los anillos muestran la jerarquia desde categorias (interior) hasta subcategorias (exterior)</li>
            <li><strong>Ver detalle:</strong> Click en cualquier segmento para abrir el panel lateral con la lista completa</li>
            <li><strong>Buscar:</strong> En el panel podes filtrar por nombre y por tipo (Skill o Conocimiento)</li>
            <li><strong>Tooltip:</strong> Pasa el mouse sobre cualquier segmento para ver el nombre completo y estadisticas</li>
            <li><strong>Cerrar:</strong> Click en la X del panel o fuera del mismo para cerrar</li>
          </ol>
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
