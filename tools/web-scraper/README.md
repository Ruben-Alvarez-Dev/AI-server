# Web Scrapper para Documentación

Este script de Python descarga y convierte la documentación de un sitio web a un único archivo Markdown. Utiliza **Playwright** para manejar sitios web modernos con contenido dinámico.

---

## Requisitos

-   **Python 3:** Debería estar instalado en tu sistema.
-   **Navegador:** Playwright instalará un navegador (Chrome) por ti la primera vez que se ejecute.

---

## Cómo usar el script

1.  **Abre tu terminal** y navega a la carpeta donde está este proyecto (`web-scrapper`).
2.  **Activa el entorno virtual** usando el siguiente comando:
    ```bash
    source pdf_env/bin/activate
    ```
3.  **Ejecuta el script** pasando la URL de la documentación como parámetro. El script creará automáticamente un archivo Markdown con un nombre basado en la URL que proporciones.

    **Ejemplo:**
    ```bash
    python3 scraper.py [https://r2r-docs.sciphi.ai/](https://r2r-docs.sciphi.ai/)
    ```

El script creará un único archivo `.md`, por ejemplo `r2r-docs_sciphi_ai.md`, que contendrá toda la documentación.
