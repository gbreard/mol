import Link from "next/link";
import {
  BarChart3,
  Search,
  Brain,
  TrendingUp,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  Mail,
} from "lucide-react";
import { AnimatedNav } from "./_components/animated-nav";
import { HeroParticles } from "./_components/hero-particles";
import { Counter } from "./_components/counter";
import { ScrollReveal } from "./_components/scroll-reveal";
import { getLandingData, LandingData } from "@/lib/supabase";

/* ─── Hero ───────────────────────────────────────────── */

function HorizontalBars({ items, color }: { items: { label: string; value: number }[]; color: string }) {
  const max = Math.max(...items.map(i => i.value), 1)
  return (
    <div className="space-y-2.5">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-3">
          <span
            className="text-xs font-medium truncate w-40 text-right shrink-0"
            style={{ color: "var(--slate-300)" }}
            title={item.label}
          >
            {item.label}
          </span>
          <div className="flex-1 h-5 rounded-sm overflow-hidden" style={{ backgroundColor: "var(--navy-900)" }}>
            <div
              className="h-full rounded-sm"
              style={{
                width: `${Math.round((item.value / max) * 100)}%`,
                background: `linear-gradient(to right, ${color}, var(--teal-300))`,
                animation: "grow-bar 1s ease-out forwards",
              }}
            />
          </div>
          <span
            className="text-xs font-bold w-8 shrink-0"
            style={{ color: "var(--teal-300)" }}
          >
            {item.value}
          </span>
        </div>
      ))}
    </div>
  )
}

function HeroSection({ data }: { data: LandingData }) {
  const ocupacionesBars = data.topOcupaciones.map(o => ({
    label: o.ocupacion,
    value: o.cantidad,
  }))

  const skillsBars = data.topSkills.map(s => ({
    label: s.name,
    value: s.value,
  }))

  return (
    <section
      className="relative min-h-screen flex items-center px-4 sm:px-6 lg:px-8 overflow-hidden"
      style={{ backgroundColor: "var(--navy-900)" }}
    >
      <HeroParticles count={35} />

      {/* gradient overlay bottom */}
      <div
        className="absolute inset-x-0 bottom-0 h-32 pointer-events-none"
        style={{
          background:
            "linear-gradient(to top, var(--off-white), transparent)",
        }}
      />

      <div className="relative max-w-7xl mx-auto w-full grid lg:grid-cols-2 gap-12 lg:gap-16 py-32 lg:py-0">
        {/* Left — text */}
        <div className="flex flex-col justify-center">
          <p
            className="text-sm font-semibold uppercase tracking-widest mb-8"
            style={{ color: "var(--teal-300)" }}
          >
            Monitor de Ofertas Laborales
          </p>

          <h1
            className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-tight"
            style={{ color: "var(--slate-100)" }}
          >
            Inteligencia del{" "}
            <span
              className="font-[family-name:var(--font-display)] italic inline-block pr-2"
              style={{
                background:
                  "linear-gradient(135deg, var(--teal-300), var(--teal-400))",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Mercado Laboral
            </span>{" "}
            Argentino en Tiempo Real
          </h1>

          <p
            className="mt-6 text-lg sm:text-xl leading-relaxed max-w-xl"
            style={{ color: "var(--slate-300)" }}
          >
            El MOL analiza miles de avisos de empleo con inteligencia artificial
            para revelar qué busca el mercado: ocupaciones, competencias,
            requerimientos y tendencias.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row gap-4">
            <Link
              href="/precios"
              className="inline-flex items-center justify-center gap-2 text-base font-semibold text-white px-8 py-3.5 rounded-xl shadow-lg hover:shadow-xl transition-all"
              style={{
                background:
                  "linear-gradient(135deg, var(--teal-500), var(--teal-400))",
              }}
            >
              Explorar Datos
              <ArrowRight className="w-5 h-5" />
            </Link>
            <a
              href="#funcionalidades"
              className="inline-flex items-center justify-center gap-2 text-base font-semibold px-8 py-3.5 rounded-xl transition-all"
              style={{
                color: "var(--slate-200)",
                border: "1px solid var(--navy-600)",
              }}
            >
              Conocer más
            </a>
          </div>
        </div>

        {/* Right — chart card */}
        <div className="flex items-center justify-center">
          <div
            className="w-full max-w-lg rounded-2xl p-6 shadow-2xl"
            style={{
              backgroundColor: "var(--navy-800)",
              border: "1px solid var(--navy-600)",
            }}
          >
            <h3
              className="text-sm font-semibold uppercase tracking-wider mb-1"
              style={{ color: "var(--slate-300)" }}
            >
              Ofertas laborales activas entre {data.rangoSemana}
            </h3>
            <p
              className="text-xs mb-5"
              style={{ color: "var(--slate-400)" }}
            >
              Dato actualizado semanalmente
            </p>

            {/* Top 5 ocupaciones */}
            <div className="mb-5">
              <h4
                className="text-xs font-semibold uppercase tracking-wider mb-3"
                style={{ color: "var(--teal-300)" }}
              >
                Top 5 ocupaciones
              </h4>
              <HorizontalBars items={ocupacionesBars} color="var(--teal-500)" />
            </div>

            {/* Top 5 competencias */}
            <div
              className="pt-4"
              style={{ borderTop: "1px solid var(--navy-600)" }}
            >
              <h4
                className="text-xs font-semibold uppercase tracking-wider mb-3"
                style={{ color: "var(--teal-300)" }}
              >
                Top 5 competencias
              </h4>
              <HorizontalBars items={skillsBars} color="var(--navy-500)" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─── Desafío / Solución ─────────────────────────────── */

function DesafioSolucion() {
  return (
    <section
      className="py-20 px-4 sm:px-6 lg:px-8"
      style={{ backgroundColor: "var(--off-white)" }}
    >
      <div className="max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="grid md:grid-cols-2 gap-8">
            {/* Desafío */}
            <div className="bg-red-50 border border-red-100 rounded-2xl p-8">
              <div className="flex items-center gap-3 mb-6">
                <AlertTriangle className="w-6 h-6 text-red-500" />
                <h3 className="text-xl font-bold font-[family-name:var(--font-display)] text-gray-900">
                  El desafío
                </h3>
              </div>
              <ul className="space-y-4 text-gray-600">
                <li className="flex items-start gap-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-2 shrink-0" />
                  <span>
                    Los datos de demanda laboral están dispersos en múltiples
                    portales sin clasificación estándar
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-2 shrink-0" />
                  <span>
                    Sin procesamiento, es imposible identificar patrones de
                    competencias y ocupaciones demandadas
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-2 shrink-0" />
                  <span>
                    Las decisiones estratégicas carecen de evidencia actualizada
                    sobre el mercado laboral
                  </span>
                </li>
              </ul>
            </div>

            {/* Solución */}
            <div className="bg-green-50 border border-green-100 rounded-2xl p-8">
              <div className="flex items-center gap-3 mb-6">
                <Lightbulb className="w-6 h-6 text-green-500" />
                <h3 className="text-xl font-bold font-[family-name:var(--font-display)] text-gray-900">
                  La solución MOL
                </h3>
              </div>
              <ul className="space-y-4 text-gray-600">
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
                  <span>
                    Recopilación automática y clasificación con taxonomía
                    internacional ESCO
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
                  <span>
                    Extracción de competencias, requerimientos y condiciones con
                    NLP avanzado
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
                  <span>
                    Tablero interactivo con indicadores para investigadores,
                    formadores y decisores
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}

/* ─── Funcionalidades ────────────────────────────────── */

function FuncionalidadesSection() {
  const features = [
    {
      icon: Search,
      title: "Monitoreo continuo",
      description:
        "Recopilación automática de ofertas desde múltiples portales de empleo argentinos con detección de duplicados y seguimiento temporal.",
    },
    {
      icon: Brain,
      title: "Clasificación inteligente",
      description:
        "Cada oferta se clasifica según la taxonomía ESCO/ISCO con modelos de lenguaje y embeddings semánticos.",
    },
    {
      icon: BarChart3,
      title: "Tablero interactivo",
      description:
        "Visualizaciones por ocupación, territorio, competencias, requerimientos y tendencias con filtros combinables.",
    },
    {
      icon: TrendingUp,
      title: "Análisis de competencias",
      description:
        "Identificación de skills técnicas y transversales demandadas, con mapeo a la clasificación ESCO de competencias.",
    },
  ];

  return (
    <section id="funcionalidades" className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
      <div className="max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold font-[family-name:var(--font-display)] text-gray-900 mb-4">
              Funcionalidades principales
            </h2>
            <p className="text-gray-500 max-w-2xl mx-auto">
              Herramientas diseñadas para transformar datos dispersos en
              inteligencia accionable
            </p>
          </div>
        </ScrollReveal>

        <div className="grid md:grid-cols-2 gap-8">
          {features.map((feature, i) => (
            <ScrollReveal key={feature.title} delay={i * 0.1}>
              <div
                className="bg-white rounded-2xl shadow-lg p-8 hover:shadow-xl transition-shadow"
                style={{ border: "1px solid var(--slate-200)" }}
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center mb-6"
                  style={{ backgroundColor: "var(--navy-800)" }}
                >
                  <feature.icon className="w-6 h-6" style={{ color: "var(--teal-300)" }} />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-500 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── Stats Banner ───────────────────────────────────── */

function StatsBanner({ totalOfertas }: { totalOfertas: number }) {
  const stats = [
    { target: totalOfertas || 120000, suffix: "+", label: "Ofertas analizadas" },
    { target: 5, suffix: "", label: "Portales monitoreados" },
    { target: 2800, suffix: "", label: "Ocupaciones ESCO" },
    { target: 24, suffix: "/7", label: "Monitoreo activo" },
  ];

  return (
    <section
      id="datos"
      className="py-20 px-4 sm:px-6 lg:px-8"
      style={{ backgroundColor: "var(--navy-800)" }}
    >
      <div className="max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="text-center mb-12">
            <h2
              className="text-3xl font-bold font-[family-name:var(--font-display)] mb-4"
              style={{ color: "var(--slate-100)" }}
            >
              Datos que hablan
            </h2>
            <p
              className="max-w-2xl mx-auto"
              style={{ color: "var(--slate-300)" }}
            >
              Información estructurada y clasificada a partir de avisos reales
              del mercado laboral argentino
            </p>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, i) => (
            <ScrollReveal key={stat.label} delay={i * 0.1}>
              <div
                className="text-center py-6"
                style={{
                  borderLeft:
                    i > 0 ? "1px solid var(--navy-600)" : "none",
                }}
              >
                <div
                  className="text-4xl lg:text-5xl font-bold mb-2"
                  style={{ color: "var(--teal-300)" }}
                >
                  <Counter target={stat.target} suffix={stat.suffix} />
                </div>
                <div
                  className="text-sm font-medium"
                  style={{ color: "var(--slate-300)" }}
                >
                  {stat.label}
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── Acceso ─────────────────────────────────────────── */

function AccesoSection() {
  return (
    <section
      id="acceso"
      className="py-20 px-4 sm:px-6 lg:px-8"
      style={{ backgroundColor: "var(--off-white)" }}
    >
      <div className="max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold font-[family-name:var(--font-display)] text-gray-900 mb-4">
              Niveles de acceso
            </h2>
            <p className="text-gray-500 max-w-2xl mx-auto">
              Información pública y herramientas avanzadas para diferentes
              necesidades
            </p>
          </div>
        </ScrollReveal>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <ScrollReveal>
            <div
              className="bg-white rounded-2xl p-8 h-full"
              style={{ border: "1px solid var(--slate-200)" }}
            >
              <div
                className="text-sm font-semibold uppercase tracking-wide mb-2"
                style={{ color: "var(--teal-500)" }}
              >
                Gratuito
              </div>
              <h3 className="text-2xl font-bold font-[family-name:var(--font-display)] text-gray-900 mb-4">
                Registrado
              </h3>
              <p className="text-gray-500 mb-8">
                Acceso a informes públicos y resúmenes del mercado laboral.
              </p>
              <ul className="space-y-3 mb-8">
                {[
                  "Informes periódicos descargables",
                  "Resúmenes por ocupación",
                  "Datos agregados por territorio",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-3 text-gray-600">
                    <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
              <Link
                href="/registro"
                className="block w-full text-center text-sm font-semibold px-6 py-3 rounded-xl transition-all"
                style={{
                  color: "var(--teal-500)",
                  border: "1px solid var(--teal-400)",
                }}
              >
                Crear cuenta gratuita
              </Link>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={0.15}>
            <div
              className="rounded-2xl p-8 text-white relative overflow-hidden h-full"
              style={{
                background:
                  "linear-gradient(135deg, var(--navy-700), var(--teal-500))",
              }}
            >
              <div
                className="absolute top-4 right-4 text-xs font-semibold px-3 py-1 rounded-full"
                style={{
                  backgroundColor: "rgba(255,255,255,0.15)",
                  color: "white",
                }}
              >
                Completo
              </div>
              <div
                className="text-sm font-semibold uppercase tracking-wide mb-2"
                style={{ color: "var(--teal-300)" }}
              >
                Institucional
              </div>
              <h3 className="text-2xl font-bold font-[family-name:var(--font-display)] mb-4">
                Tablero interactivo
              </h3>
              <p className="mb-8" style={{ color: "var(--slate-200)" }}>
                Acceso completo al tablero de análisis con filtros avanzados y
                descarga de datos.
              </p>
              <ul className="space-y-3 mb-8">
                {[
                  "Tablero interactivo completo",
                  "Filtros por ocupación, territorio y skills",
                  "Descarga de datos procesados",
                  "Análisis de brechas de competencias",
                ].map((item) => (
                  <li
                    key={item}
                    className="flex items-center gap-3"
                    style={{ color: "var(--slate-100)" }}
                  >
                    <CheckCircle2
                      className="w-5 h-5 shrink-0"
                      style={{ color: "var(--teal-300)" }}
                    />
                    {item}
                  </li>
                ))}
              </ul>
              <Link
                href="/registro"
                className="block w-full text-center text-sm font-semibold bg-white px-6 py-3 rounded-xl transition-all"
                style={{ color: "var(--navy-700)" }}
              >
                Solicitar acceso
              </Link>
            </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
}

/* ─── Footer ─────────────────────────────────────────── */

function Footer() {
  return (
    <>
      {/* Wave divider */}
      <div style={{ backgroundColor: "var(--off-white)" }}>
        <svg
          viewBox="0 0 1440 80"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full block"
          preserveAspectRatio="none"
        >
          <path
            d="M0 40C240 80 480 0 720 40C960 80 1200 0 1440 40V80H0V40Z"
            fill="var(--navy-900)"
          />
        </svg>
      </div>

      <footer
        className="py-16 px-4 sm:px-6 lg:px-8"
        style={{ backgroundColor: "var(--navy-900)" }}
      >
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-12 mb-12">
            {/* Col 1 — Logo */}
            <div>
              <div
                className="text-xl font-bold mb-3"
                style={{ color: "var(--slate-100)" }}
              >
                MOL
              </div>
              <p
                className="text-sm leading-relaxed"
                style={{ color: "var(--slate-300)" }}
              >
                Monitor de Ofertas Laborales. Inteligencia del mercado laboral
                argentino con clasificación ESCO y análisis de competencias.
              </p>
            </div>

            {/* Col 2 — Enlaces */}
            <div>
              <h4
                className="text-sm font-semibold uppercase tracking-wider mb-4"
                style={{ color: "var(--slate-200)" }}
              >
                Enlaces
              </h4>
              <ul className="space-y-2">
                {[
                  { href: "/", label: "Inicio" },
                  { href: "#datos", label: "Datos" },
                  { href: "/informes", label: "Informes" },
                  { href: "/precios", label: "Precios" },
                ].map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm transition-colors"
                      style={{ color: "var(--slate-300)" }}
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Col 3 — Recursos */}
            <div>
              <h4
                className="text-sm font-semibold uppercase tracking-wider mb-4"
                style={{ color: "var(--slate-200)" }}
              >
                Recursos
              </h4>
              <ul className="space-y-2">
                {[
                  { label: "Taxonomía ESCO", href: "#" },
                  { label: "Clasificación ISCO", href: "#" },
                  { label: "Metodología", href: "#" },
                ].map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-sm transition-colors"
                      style={{ color: "var(--slate-300)" }}
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Col 4 — Boletín */}
            <div>
              <h4
                className="text-sm font-semibold uppercase tracking-wider mb-4"
                style={{ color: "var(--slate-200)" }}
              >
                Boletín
              </h4>
              <p
                className="text-sm mb-4"
                style={{ color: "var(--slate-300)" }}
              >
                Recibí novedades del mercado laboral en tu correo.
              </p>
              <form className="flex gap-2" action="#">
                <input
                  type="email"
                  placeholder="tu@email.com"
                  className="flex-1 text-sm px-3 py-2 rounded-lg outline-none focus:ring-1"
                  style={{
                    backgroundColor: "var(--navy-800)",
                    border: "1px solid var(--navy-600)",
                    color: "var(--slate-200)",
                  }}
                />
                <button
                  type="submit"
                  className="px-3 py-2 rounded-lg transition-colors"
                  style={{
                    backgroundColor: "var(--teal-500)",
                    color: "white",
                  }}
                >
                  <Mail className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>

          {/* Bottom bar */}
          <div
            className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4"
            style={{ borderTop: "1px solid var(--navy-700)" }}
          >
            <p className="text-sm" style={{ color: "var(--slate-300)" }}>
              &copy; 2026 MOL — Monitor de Ofertas Laborales
            </p>
            <div className="flex items-center gap-6">
              <a
                href="#"
                className="text-sm transition-colors"
                style={{ color: "var(--slate-300)" }}
              >
                Términos
              </a>
              <a
                href="#"
                className="text-sm transition-colors"
                style={{ color: "var(--slate-300)" }}
              >
                Política de datos
              </a>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}

/* ─── Page ───────────────────────────────────────────── */

export default async function LandingPage() {
  const data = await getLandingData()

  return (
    <div className="min-h-screen">
      <AnimatedNav />
      <HeroSection data={data} />
      <DesafioSolucion />
      <FuncionalidadesSection />
      <StatsBanner totalOfertas={data.totalOfertas} />
      <AccesoSection />
      <Footer />
    </div>
  );
}
