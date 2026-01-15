#!/usr/bin/env python3
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
conn = sqlite3.connect(str(db_path))

# Revertir falsos positivos
conn.execute('UPDATE ofertas_nlp SET sector_empresa = ? WHERE id_oferta = ?', ('Tecnologia', '1118028887'))
conn.execute('UPDATE ofertas_nlp SET sector_empresa = ? WHERE id_oferta = ?', ('Tecnologia', '2162667'))
conn.execute('UPDATE ofertas_nlp SET sector_empresa = ? WHERE id_oferta = ?', ('Servicios', '1118009703'))
conn.commit()
print('Revertidos 3 falsos positivos')
conn.close()
