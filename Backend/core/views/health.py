from django.db import connections
from django.db.utils import OperationalError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthzView(APIView):
    """Simple health check (is the app running)."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class ReadyView(APIView):
    """Readiness check (Postgres)."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        checks = {}

        # --- Check Postgres ---
        try:
            db_conn = connections["default"]
            db_conn.cursor()
            checks["database"] = "ok"
        except OperationalError:
            checks["database"] = "error"

        # --- Final status ---
        if all(v == "ok" for v in checks.values()):
            return Response(
                {"status": "ok", "checks": checks}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": "error", "checks": checks},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
