"""Executa o notebook inteiro e grava as saídas somente após uma execução válida."""

from pathlib import Path
import os
import sys
from tempfile import TemporaryDirectory

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager


def executar():
    raiz = Path(__file__).resolve().parent
    caminho = raiz / "notebooks/01_qualidade_e_programas_rh.ipynb"
    notebook = nbformat.read(caminho, as_version=4)
    nbformat.validate(notebook)
    kernel = KernelManager(kernel_name="python3")
    kernel.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
    cliente = NotebookClient(notebook, km=kernel, timeout=120,
                             resources={"metadata": {"path": str(raiz)}})
    try:
        cliente.execute()
    finally:
        if kernel.has_kernel:
            kernel.shutdown_kernel(now=True)
    nbformat.validate(notebook)
    temporario = caminho.with_suffix(".ipynb.tmp")
    nbformat.write(notebook, temporario)
    temporario.replace(caminho)
    print("Notebook executado e salvo sem erros.")


if __name__ == "__main__":
    with TemporaryDirectory(prefix="rh-notebook-") as diretorio:
        for variavel, subpasta in [
            ("IPYTHONDIR", "ipython"), ("JUPYTER_RUNTIME_DIR", "runtime"),
            ("JUPYTER_CONFIG_DIR", "config"), ("JUPYTER_DATA_DIR", "data"),
            ("MPLCONFIGDIR", "matplotlib"),
        ]:
            os.environ.setdefault(variavel, str(Path(diretorio) / subpasta))
        executar()
