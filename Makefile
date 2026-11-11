# Artículo A5. Todo corre con nice (máquina compartida). Ver README.md y docs/REPLICACION.md.
PY = nice -n 10 python3
# determinismo (docs/REPLICACION.md): semilla de hash fija y un solo hilo en polars y BLAS
export PYTHONHASHSEED = 0
export POLARS_MAX_THREADS = 1
export OMP_NUM_THREADS = 1
export OPENBLAS_NUM_THREADS = 1
export MKL_NUM_THREADS = 1
NUEVOS ?= data/interim/a5/intermedios_b

.PHONY: insumos verificar-insumos bases-eevv intermedios nivel-a nivel-b comparar pruebas pruebas-eevv todo limpiar

insumos:             ## baja lo que falte (externos del artículo y microdatos del DANE) y verifica huellas
	$(PY) scripts/00_descargar_insumos.py

verificar-insumos:   ## solo verifica huellas
	$(PY) scripts/00_descargar_insumos.py --verificar

bases-eevv:          ## paquete común: zips del DANE -> data/processed/ (unos 10 minutos)
	$(PY) scripts/insumos_eevv/01_extraer.py
	$(PY) scripts/insumos_eevv/02_base_defunciones.py
	$(PY) scripts/insumos_eevv/03_base_nacimientos.py
	$(PY) scripts/insumos_eevv/04_poblacion.py

intermedios:         ## nivel B propio: data/processed (o $$PROCESADO) -> $(NUEVOS)
	$(PY) scripts/01_intermedios.py --salida $(NUEVOS)

comparar:            ## compara los intermedios reconstruidos con los versionados
	$(PY) scripts/02_comparar_intermedios.py --nuevo $(NUEVOS) --referencia data/intermedios

nivel-b: insumos bases-eevv pruebas-eevv intermedios comparar

nivel-a:             ## desde data/intermedios/ versionados: estimaciones, cuadros, figuras y verificación de cifras
	$(PY) scripts/03_estimar.py
	$(PY) scripts/04_figuras.py
	$(PY) pruebas/verificar_cifras.py

pruebas:             ## pruebas del artículo (nivel A) y cifras del texto
	$(PY) -m pytest pruebas/ -q -p no:cacheprovider --ignore=pruebas/insumos_eevv
	$(PY) pruebas/verificar_cifras.py

pruebas-eevv:        ## pruebas del paquete común (huellas de los zips, columnas, totales del DANE): requieren el nivel B
	$(PY) -m pytest pruebas/insumos_eevv -q -p no:cacheprovider


todo: nivel-b nivel-a pruebas

limpiar:
	rm -rf data/interim data/processed
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
