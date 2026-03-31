import Link from 'next/link'
import { ArrowRight, CheckCircle } from 'lucide-react'

export const metadata = {
  title: 'Mi Futuro Laboral | MOL',
  description: 'Descubrí tus competencias, encontrá trabajo y llevá un reporte a tu próxima entrevista.',
}

const PROMESAS = [
  'Qué trabajos encajan con lo que sabés hacer',
  'Qué competencias te faltan para llegar adonde querés',
  'Un reporte listo para llevar a la entrevista',
]

export default function MiFuturoLaboralPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">

        <span className="inline-block bg-blue-100 text-blue-700 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider mb-6">
          Gratis · Sin cuenta obligatoria
        </span>

        <h1 className="text-4xl font-bold text-gray-900 mb-4 leading-tight">
          En 5 minutos sabés<br />exactamente dónde parás
        </h1>

        <p className="text-gray-500 text-lg mb-8 max-w-lg mx-auto">
          Contanos lo que sabés hacer y el sistema te dice qué trabajos te quedan cerca,
          qué te falta y cómo cerrarlo.
        </p>

        <ul className="text-left inline-flex flex-col gap-3 mb-10">
          {PROMESAS.map((p) => (
            <li key={p} className="flex items-start gap-2 text-gray-700 text-sm">
              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
              {p}
            </li>
          ))}
        </ul>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/mi-futuro-laboral/onboarding"
            className="inline-flex items-center justify-center gap-2 bg-blue-600 text-white text-sm font-semibold px-6 py-3 rounded-xl hover:bg-blue-700 transition-colors shadow-sm"
          >
            Empezar ahora — es gratis
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/mi-futuro-laboral/dashboard"
            className="inline-flex items-center justify-center gap-2 bg-white text-gray-700 text-sm font-medium px-6 py-3 rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            Ya cargué mis competencias →
          </Link>
        </div>

        <p className="text-xs text-gray-400 mt-6">
          No necesitás crear una cuenta para empezar.
          Podés guardar tu perfil al final si querés.
        </p>
      </div>
    </div>
  )
}
