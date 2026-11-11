"""Insumos comunes de Estadísticas Vitales (EEVV) del DANE para los artículos A1 a A4.

Va de los zips originales del Archivo Nacional de Datos (ANDA) del DANE y de las proyecciones de población a las
bases que leen los artículos:

    data/processed/ext/def_<año>.parquet     defunciones no fetales 1979-2025, una fila por defunción
    data/processed/ext/nac_<año>.parquet     nacidos vivos 1998-2025, una fila por nacimiento
    data/processed/defunciones_eevv.parquet  las columnas de residencia de def_<año>, apiladas 1979-2025
    data/processed/poblacion_eevv.parquet    población departamental por área, sexo y edad simple, 1981-2025
    data/processed/mun_pob_edad.parquet      población municipal por área y edad simple, 1985-2025

Módulos:
    rutas          raíz y carpetas (sin rutas absolutas)
    manifiesto     lectura de data/raw/MANIFIESTO.csv y huellas SHA-256
    lectura        apertura de los zips del DANE (sav, dta, csv y texto con tabulador, zips anidados)
    defunciones    armonización de defunciones (antes scripts/30_base_defunciones.py y 50_base_extendida.py)
    nacimientos    armonización de nacimientos (antes scripts/37_base_nacimientos.py y 50_base_extendida.py)
    poblacion      proyecciones de población (antes scripts/31_poblacion.py y 31b_poblacion_municipal.py)
"""
__version__ = "1.0.0"
