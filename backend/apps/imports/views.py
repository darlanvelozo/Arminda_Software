"""
Views HTTP do app imports (Onda 1.6b).

Por enquanto: apenas o importador CSV/XLSX de enriquecimento cadastral.
O importador Fiorilli SIP segue como management command (longo, requer
acesso a DB Firebird na rede do operador).
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.core.permissions import IsRHMunicipio
from apps.imports.services.csv_importer import importar_servidores_csv


class ImportadorCsvViewSet(ViewSet):
    """ViewSet de importação CSV/XLSX (Onda 1.6b).

    POST /api/imports/csv/servidores/  — preview ou aplicação real.
    """

    permission_classes = [IsRHMunicipio]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @action(detail=False, methods=["post"], url_path="servidores")
    def servidores(self, request):
        """POST /api/imports/csv/servidores/.

        Form multipart:
            arquivo: CSV ou XLSX
            coluna_identificador: "matricula" (default) ou "cpf"
            dry_run: "true" (default) ou "false"

        Resposta: mesmo shape do `importar_servidores_csv`.
        """
        arquivo = request.FILES.get("arquivo")
        if arquivo is None:
            return Response(
                {"detail": "Anexe o arquivo no campo 'arquivo'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        coluna = request.data.get("coluna_identificador") or "matricula"
        dry_run_raw = (request.data.get("dry_run") or "true").lower()
        dry_run = dry_run_raw not in ("false", "0", "no")
        try:
            resultado = importar_servidores_csv(
                conteudo_bytes=arquivo.read(),
                nome_arquivo=arquivo.name,
                coluna_identificador=coluna,
                dry_run=dry_run,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(resultado)
