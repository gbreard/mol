import Image from "next/image";
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
  Database,
  Cpu,
  GraduationCap,
} from "lucide-react";

function LandingHeader() {
  return (
    <header className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <Image
              src="/logo_mol.png"
              alt="MOL Logo"
              width={120}
              height={40}
              priority
            />
          </div>

          <nav className="hidden md:flex items-center gap-8">
            <a href="#funcionalidades" className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors">
              Funcionalidades
            </a>
            <a href="#numeros" className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors">
              Datos
            </a>
            <a href="#acceso" className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors">
              Acceso
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm font-semibold text-gray-700 hover:text-blue-600 transition-colors px-4 py-2"
            >
              Iniciar Sesi&oacute;n
            </Link>
            <Link
              href="/registro"
              className="text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 px-5 py-2.5 rounded-lg shadow-lg hover:shadow-xl transition-all"
            >
              Registrarse
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}

function HeroSection() {
  return (
    <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-200 text-blue-700 px-4 py-2 rounded-full text-sm font-medium mb-8">
          <Database className="w-4 h-4" />
          Monitor de Ofertas Laborales
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 tracking-tight leading-tight max-w-4xl mx-auto">
          Inteligencia del mercado laboral argentino en{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-blue-700">
            tiempo real
          </span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-gray-500 max-w-3xl mx-auto leading-relaxed">
          El Monitor de Ofertas Laborales (MOL) analiza miles de avisos de
          empleo con inteligencia artificial para revelar qu&eacute; busca el mercado:
          ocupaciones, competencias, requerimientos y tendencias.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/login"
            className="inline-flex items-center gap-2 text-base font-semibold text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 px-8 py-3.5 rounded-xl shadow-lg hover:shadow-xl transition-all"
          >
            Acceder al tablero
            <ArrowRight className="w-5 h-5" />
          </Link>
          <a
            href="#funcionalidades"
            className="inline-flex items-center gap-2 text-base font-semibold text-gray-700 border border-gray-300 hover:border-blue-300 hover:text-blue-600 px-8 py-3.5 rounded-xl transition-all"
          >
            Conocer m&aacute;s
          </a>
        </div>
      </div>
    </section>
  );
}

function DesafioSolucion() {
  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-red-50 border border-red-100 rounded-2xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <AlertTriangle className="w-6 h-6 text-red-500" />
              <h3 className="text-xl font-bold text-gray-900">El desaf&iacute;o</h3>
            </div>
            <ul className="space-y-4 text-gray-600">
              <li className="flex items-start gap-3">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-2 flex-shrink-0" />
                <span>Los datos de demanda laboral est&aacute;n dispersos en m&uacute;ltiples portales sin clasificaci&oacute;n est&aacute;ndar</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-2 flex-shrink-0" />
                <span>Sin procesamiento, es imposible identificar patrones de competencias y ocupaciones demandadas</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-2 flex-shrink-0" />
                <span>Las decisiones de pol&iacute;tica p&uacute;blica carecen de evidencia actualizada sobre el mercado laboral</span>
              </li>
            </ul>
          </div>

          <div className="bg-green-50 border border-green-100 rounded-2xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <Lightbulb className="w-6 h-6 text-green-500" />
              <h3 className="text-xl font-bold text-gray-900">La soluci&oacute;n MOL</h3>
            </div>
            <ul className="space-y-4 text-gray-600">
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span>Recopilaci&oacute;n autom&aacute;tica y clasificaci&oacute;n con taxonom&iacute;a internacional ESCO</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span>Extracci&oacute;n de competencias, requerimientos y condiciones con NLP avanzado</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span>Tablero interactivo con indicadores para investigadores, formadores y decisores</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}

function NumerosSection() {
  const stats = [
    { value: "13.000+", label: "Ofertas analizadas", icon: Database },
    { value: "300+", label: "Ocupaciones ESCO", icon: Cpu },
    { value: "1.200+", label: "Competencias identificadas", icon: GraduationCap },
  ];

  return (
    <section id="numeros" className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-blue-600 to-blue-700">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-white text-center mb-4">
          Datos que hablan
        </h2>
        <p className="text-blue-100 text-center mb-12 max-w-2xl mx-auto">
          Informaci&oacute;n estructurada y clasificada a partir de avisos reales del mercado laboral argentino
        </p>

        <div className="grid md:grid-cols-3 gap-8">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-8 text-center"
            >
              <stat.icon className="w-8 h-8 text-blue-200 mx-auto mb-4" />
              <div className="text-4xl font-bold text-white mb-2">{stat.value}</div>
              <div className="text-blue-100 font-medium">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FuncionalidadesSection() {
  const features = [
    {
      icon: Search,
      title: "Monitoreo continuo",
      description:
        "Recopilaci\u00f3n autom\u00e1tica de ofertas desde m\u00faltiples portales de empleo argentinos con detecci\u00f3n de duplicados y seguimiento temporal.",
    },
    {
      icon: Brain,
      title: "Clasificaci\u00f3n inteligente",
      description:
        "Cada oferta se clasifica seg\u00fan la taxonom\u00eda ESCO/ISCO con modelos de lenguaje y embeddings sem\u00e1nticos.",
    },
    {
      icon: BarChart3,
      title: "Tablero interactivo",
      description:
        "Visualizaciones por ocupaci\u00f3n, territorio, competencias, requerimientos y tendencias con filtros combinables.",
    },
    {
      icon: TrendingUp,
      title: "An\u00e1lisis de competencias",
      description:
        "Identificaci\u00f3n de skills t\u00e9cnicas y transversales demandadas, con mapeo a la clasificaci\u00f3n ESCO de competencias.",
    },
  ];

  return (
    <section id="funcionalidades" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Funcionalidades principales
          </h2>
          <p className="text-gray-500 max-w-2xl mx-auto">
            Herramientas dise&ntilde;adas para transformar datos dispersos en inteligencia accionable
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 hover:shadow-xl transition-shadow"
            >
              <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center mb-6">
                <feature.icon className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">
                {feature.title}
              </h3>
              <p className="text-gray-500 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function AccesoSection() {
  return (
    <section id="acceso" className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Niveles de acceso
          </h2>
          <p className="text-gray-500 max-w-2xl mx-auto">
            Informaci&oacute;n p&uacute;blica y herramientas avanzadas para diferentes necesidades
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <div className="bg-gray-50 border border-gray-200 rounded-2xl p-8">
            <div className="text-sm font-semibold text-blue-600 uppercase tracking-wide mb-2">
              Gratuito
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-4">Registrado</h3>
            <p className="text-gray-500 mb-8">
              Acceso a informes p&uacute;blicos y res&uacute;menes del mercado laboral.
            </p>
            <ul className="space-y-3 mb-8">
              {[
                "Informes peri\u00f3dicos descargables",
                "Res\u00famenes por ocupaci\u00f3n",
                "Datos agregados por territorio",
              ].map((item) => (
                <li key={item} className="flex items-center gap-3 text-gray-600">
                  <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
            <Link
              href="/registro"
              className="block w-full text-center text-sm font-semibold text-blue-600 border border-blue-300 hover:bg-blue-50 px-6 py-3 rounded-xl transition-all"
            >
              Crear cuenta gratuita
            </Link>
          </div>

          <div className="bg-gradient-to-br from-blue-600 to-blue-700 border border-blue-500 rounded-2xl p-8 text-white relative overflow-hidden">
            <div className="absolute top-4 right-4 bg-white/20 text-white text-xs font-semibold px-3 py-1 rounded-full">
              Completo
            </div>
            <div className="text-sm font-semibold text-blue-200 uppercase tracking-wide mb-2">
              Institucional
            </div>
            <h3 className="text-2xl font-bold mb-4">Tablero interactivo</h3>
            <p className="text-blue-100 mb-8">
              Acceso completo al tablero de an&aacute;lisis con filtros avanzados y descarga de datos.
            </p>
            <ul className="space-y-3 mb-8">
              {[
                "Tablero interactivo completo",
                "Filtros por ocupaci\u00f3n, territorio y skills",
                "Descarga de datos procesados",
                "An\u00e1lisis de brechas de competencias",
              ].map((item) => (
                <li key={item} className="flex items-center gap-3 text-blue-50">
                  <CheckCircle2 className="w-5 h-5 text-blue-200 flex-shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
            <Link
              href="/registro"
              className="block w-full text-center text-sm font-semibold text-blue-700 bg-white hover:bg-blue-50 px-6 py-3 rounded-xl transition-all"
            >
              Solicitar acceso
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-400 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <Image
              src="/logo_mol.png"
              alt="MOL Logo"
              width={100}
              height={33}
              className="brightness-0 invert opacity-60"
            />
          </div>

          <p className="text-sm text-center md:text-left">
            MOL &mdash; Monitor de Ofertas Laborales
          </p>

          <div className="flex items-center gap-6">
            <a href="#" className="text-sm hover:text-white transition-colors">
              T&eacute;rminos
            </a>
            <a href="#" className="text-sm hover:text-white transition-colors">
              Privacidad
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <LandingHeader />
      <HeroSection />
      <DesafioSolucion />
      <NumerosSection />
      <FuncionalidadesSection />
      <AccesoSection />
      <Footer />
    </div>
  );
}
