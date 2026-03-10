# 1. Elección del dataset

Disponemos de 3 datasets. Vamos a analizarlos, extraer cualidades de cada uno y valorar si podríamos mezclarlos.

## A. Análisis de los datasets

| **Característica** | **Dataset 1: IMDb (Large Movie Review - 2011)** | **Dataset 2: Cornell (Polarity v2.0 - 2004)** | **Dataset 3: Stanford (SST v1.0 - 2013)** |
| :--- | :--- | :--- | :--- |
| **Tamaño (Etiquetado)** | 50,000 reseñas | 2,000 reseñas | 10,000 fragmentos |
| **Tipo de Clasificación** | Binaria (Positivo / Negativo) | Binaria (Positivo / Negativo) | Multiclase ( 5 niveles) |
| **Nivel de Análisis** | Documento completo (Reseña entera) | Documento completo | Sub-oración (Análisis subdetallado) |
| **Nivel de Complejidad** | Baja : Directo y estructurado | Baja: Pero requiere validación cruzada manual | Alta: Requiere manejar composición de frases |
| **Veredicto** | El estándar ideal para modelos prácticos. | Demasiado pequeño para los estándares modernos. | Demasiado complejo para un clasificador inicial. |


## B. Decisión final
Tras analizar las tres opciones, el Large Movie Review Dataset v1.0 (IMDb) es la mejor elección para entrenar un modelo práctico, robusto y moderno de clasificación de reseñas. Ya que:

- Tiene un gran volumen de datos: Cuenta con 50,000 reseñas etiquetadas, un tamaño ideal para prevenir el sobreajuste (overfitting) y permitir que los algoritmos modernos generalicen correctamente.

- Datos bien etiquetados: Tiene reseñas divididas en postivas y negativas, por lo que el modelo aprendenderá patrones de polaridad mucho más definidos y precisos.

- División limpia y sin sesgos: Viene con una partición perfecta de 25k reseñas para entrenamiento y 25k para prueba. Además, garantiza que las películas no se repitan entre ambos conjuntos, evitando que el modelo "haga trampa" memorizando nombres propios de actores o directores.


### *Conclusión*

- Dataset 2 (Cornell): Su principal problema es la cantidad de datos. Trabajar con solo 2,000 reseñas limitará severamente la capacidad de aprendizaje del modelo frente a vocabularios nuevos.

- Dataset 3 (Stanford): Es demasiado completo para un caso de uso estándar. Intenta predecir 5 niveles de sentimiento desarmando gramaticalmente cada oración. Y nuestro objetivo es detectar de forma general si a un usuario le gustó o no una película, por lo que este dataset aportará una complejidad técnica innecesaria.
 
 Debido a esto hemos decidio optar por el primer dataset.

## C. Cambios y modificaciones del primer dataset
### *Pasos de Limpieza y Control de Calidad*
Aunque la estructura de carpetas y la distribución son correctas, el texto de las reseñas sí necesita una limpieza profunda.

#### 1. Eliminar datos incorrectos o ruido en el texto
- Etiquetas HTML : Al ser datos extraídos directamente de la web de IMDb, este dataset está lleno de etiquetas de salto de línea como " < br /> ". Por lo que tenemos que eliminarlas.

- Carácteres especiales y puntuación: Hay que estandarizarlo todo a minúsculas.

- URLs: Aunque las URLs están en un archivo aparte, a veces los usuarios pegan links dentro de la reseña, por lo que conviene limpiarlos.

#### 2. Revisar incoherencias
Hay que revisar la consistencia entre nombre de archivo y carpeta: El formato del archivo es [id]_[rating].txt. Hay que hacer un script rápido para comprobar que ningún archivo dentro de la carpeta pos/ tenga un rating menor a 7 en su nombre, y que ninguno en neg/ tenga un rating mayor a 4.


#### 3. Detectar y tratar valores atípicos (Outliers)
Contaremos el número de palabras por reseña. Por si encontramos reseñas extremadamente cortas que no aporten suficiente contexto, o reseñas inusualmente largas que podrían truncarse.
