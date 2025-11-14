"""
Script para verificar reglas de scraping antes de comenzar
Verifica robots.txt y ayuda a identificar restricciones
"""

import requests
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import time


class ScrapingRulesChecker:
    """Verifica si el scraping está permitido en un sitio"""

    def __init__(self, base_url: str):
        """
        Args:
            base_url: URL base del sitio (ej: https://www.zonajobs.com.ar)
        """
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.robots_url = urljoin(base_url, '/robots.txt')
        self.robot_parser = RobotFileParser()

    def check_robots_txt(self):
        """Verifica y muestra el contenido de robots.txt"""
        print("=" * 80)
        print("🤖 VERIFICANDO ROBOTS.TXT")
        print("=" * 80)
        print(f"URL: {self.robots_url}\n")

        try:
            response = requests.get(self.robots_url, timeout=10)

            if response.status_code == 200:
                print("✓ robots.txt encontrado\n")
                print("📄 CONTENIDO:")
                print("-" * 80)
                print(response.text)
                print("-" * 80)

                # Parsear robots.txt
                self.robot_parser.set_url(self.robots_url)
                self.robot_parser.read()

                return True
            else:
                print(f"⚠️  robots.txt no encontrado (Status: {response.status_code})")
                print("💡 Esto puede significar que no hay restricciones específicas")
                return False

        except Exception as e:
            print(f"❌ Error al obtener robots.txt: {e}")
            return False

    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """
        Verifica si una URL específica puede ser scrapeada

        Args:
            url: URL a verificar
            user_agent: User agent a usar

        Returns:
            True si se puede scrapear, False si no
        """
        if not self.robot_parser.url:
            self.check_robots_txt()

        can_fetch = self.robot_parser.can_fetch(user_agent, url)

        print(f"\n🔍 Verificando: {url}")
        print(f"   User-Agent: {user_agent}")
        print(f"   {'✅ PERMITIDO' if can_fetch else '❌ NO PERMITIDO'}")

        return can_fetch

    def get_crawl_delay(self, user_agent: str = "*") -> float:
        """
        Obtiene el crawl delay recomendado

        Args:
            user_agent: User agent

        Returns:
            Delay en segundos, o 0 si no está especificado
        """
        if not self.robot_parser.url:
            self.check_robots_txt()

        delay = self.robot_parser.crawl_delay(user_agent)

        print(f"\n⏱️  Crawl Delay para '{user_agent}':")
        if delay:
            print(f"   {delay} segundos (DEBE RESPETARSE)")
        else:
            print(f"   No especificado (se recomienda 1-2 segundos)")

        return delay or 1.0

    def check_common_paths(self):
        """Verifica si paths comunes están permitidos"""
        print("\n" + "=" * 80)
        print("🛣️  VERIFICANDO PATHS COMUNES")
        print("=" * 80)

        common_paths = [
            '/empleos',
            '/api/',
            '/api/jobs',
            '/api/search',
            '/buscar',
            '/ofertas',
        ]

        results = []

        for path in common_paths:
            url = urljoin(self.base_url, path)
            allowed = self.can_fetch(url)
            results.append((path, allowed))
            time.sleep(0.5)

        # Resumen
        print("\n📊 RESUMEN:")
        print("-" * 80)
        for path, allowed in results:
            status = "✅ PERMITIDO" if allowed else "❌ BLOQUEADO"
            print(f"   {path:<30} {status}")

        return results

    def check_terms_of_service(self):
        """Muestra información sobre términos de servicio"""
        print("\n" + "=" * 80)
        print("📜 TÉRMINOS DE SERVICIO")
        print("=" * 80)

        common_tos_urls = [
            '/terminos-y-condiciones',
            '/terms',
            '/terminos',
            '/legal/terms',
        ]

        print("\n💡 Verifica manualmente los términos de servicio en:")

        for path in common_tos_urls:
            url = urljoin(self.base_url, path)
            print(f"   • {url}")

            try:
                response = requests.head(url, timeout=5)
                if response.status_code == 200:
                    print(f"     ✓ Encontrado: {url}")
                    break
            except:
                pass

        print("\n⚠️  PUNTOS IMPORTANTES A VERIFICAR:")
        print("   1. ¿Está explícitamente prohibido el scraping/crawling?")
        print("   2. ¿Hay restricciones sobre uso automatizado?")
        print("   3. ¿Qué datos están permitidos extraer?")
        print("   4. ¿Hay límites de rate (requests por segundo/minuto)?")
        print("   5. ¿Se requiere atribución o permiso previo?")

    def generate_recommendations(self):
        """Genera recomendaciones de scraping ético"""
        print("\n" + "=" * 80)
        print("✅ RECOMENDACIONES DE SCRAPING ÉTICO")
        print("=" * 80)

        delay = self.get_crawl_delay()

        recommendations = f"""
1. 🕐 RATE LIMITING:
   • Implementar delay de al menos {delay} segundos entre requests
   • Considerar delays más largos durante horas pico
   • No hacer más de 1 request por segundo

2. 🎭 IDENTIFICACIÓN:
   • Usar un User-Agent descriptivo e identificable
   • Ejemplo: "MiBot/1.0 (Investigación académica; contacto@email.com)"
   • NO intentar ocultar que eres un bot

3. 📊 VOLUMEN DE DATOS:
   • No descargar TODO el sitio
   • Limitar a datos necesarios
   • Implementar caché para evitar re-scraping

4. ⏰ HORARIOS:
   • Preferir horarios de baja actividad
   • Evitar horarios pico (9-18hs en días laborales)

5. 🔄 MANEJO DE ERRORES:
   • Respetar códigos HTTP 429 (Too Many Requests)
   • Implementar exponential backoff en errores
   • No reintentar agresivamente

6. 💾 USO DE DATOS:
   • No redistribuir públicamente sin permiso
   • Respetar datos personales (GDPR, Ley de Protección de Datos)
   • Usar solo para propósitos legítimos declarados

7. 🔒 SEGURIDAD:
   • No intentar bypassear medidas de seguridad
   • No intentar acceder a áreas protegidas
   • Reportar vulnerabilidades de forma responsable

8. 📞 COMUNICACIÓN:
   • Considerar contactar al sitio antes de scrapear masivamente
   • Preguntar si tienen una API oficial
   • Estar abierto a feedback del sitio
        """

        print(recommendations)

    def full_check(self):
        """Ejecuta todas las verificaciones"""
        print("\n" + "=" * 80)
        print(f"🔍 ANÁLISIS COMPLETO DE REGLAS DE SCRAPING")
        print(f"Sitio: {self.base_url}")
        print("=" * 80 + "\n")

        # 1. Verificar robots.txt
        self.check_robots_txt()

        # 2. Verificar paths comunes
        self.check_common_paths()

        # 3. Información sobre términos
        self.check_terms_of_service()

        # 4. Recomendaciones
        self.generate_recommendations()

        print("\n" + "=" * 80)
        print("✅ VERIFICACIÓN COMPLETADA")
        print("=" * 80)


def main():
    """Función principal"""

    # ZonaJobs
    checker = ScrapingRulesChecker("https://www.zonajobs.com.ar")
    checker.full_check()

    print("\n\n💡 PRÓXIMOS PASOS:")
    print("   1. Lee cuidadosamente los términos de servicio")
    print("   2. Verifica que tu uso esté permitido")
    print("   3. Implementa las recomendaciones en tu scraper")
    print("   4. Mantén un registro de tus actividades de scraping")
    print("   5. Sé transparente sobre tu identidad y propósito")


if __name__ == "__main__":
    main()
