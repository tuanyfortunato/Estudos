"""Ponto de entrada da aplicação.

Sobe a API FastAPI com uvicorn. Em desenvolvimento:

    python main.py

Ou diretamente com uvicorn (recomendado, com reload):

    uvicorn app.presentation.api.app:app --reload
"""

from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run(
        "app.presentation.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
