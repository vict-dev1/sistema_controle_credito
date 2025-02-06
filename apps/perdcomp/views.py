# apps/perdcomp/views.py
from django.shortcuts import render, get_object_or_404
from .forms import PDFUploadForm
from django.http import JsonResponse
from perdcomp.models import PER, Dcomp, DcompDebitos, Empresa, PerCanc
from rest_framework import viewsets
from rest_framework.decorators import api_view
from django.db.models import Sum
import logging
from perdcomp.serializers import EmpresaSerializer, PERSerializer, DcompSerializer, DcompDebitosSerializer, PerCancSerializer


logger = logging.getLogger(__name__)

def calcular_saldo_e_dados_grafico(empresa_id):
    empresa_selecionada = Empresa.objects.filter(id=empresa_id).first()
    if not empresa_selecionada:
        return None, 0, {}

    # Calcular saldo disponível
    total_credito = PER.objects.filter(empresa=empresa_selecionada).aggregate(
        total=Sum('credito_original')
    )['total'] or 0

    total_debitos = Dcomp.objects.filter(empresa=empresa_selecionada).aggregate(
        total=Sum('total_dos_debitos')
    )['total'] or 0

    saldo_disponivel = total_credito - total_debitos

    logger.info(f"Empresa: {empresa_selecionada}, Total Crédito: {total_credito}, Total Débitos: {total_debitos}")

    # Dados para o gráfico
    dados_grafico = {
        'total_credito': float(total_credito),
        'total_debitos': float(total_debitos)
    }

    return empresa_selecionada, saldo_disponivel, dados_grafico


class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer

class PERViewSet(viewsets.ModelViewSet):
    queryset = PER.objects.all()
    serializer_class = PERSerializer

class DcompViewSet(viewsets.ModelViewSet):
    queryset = Dcomp.objects.all()
    serializer_class = DcompSerializer

class DcompDebitosViewSet(viewsets.ModelViewSet):
    queryset = DcompDebitos.objects.all()
    serializer_class = DcompDebitosSerializer

class PerCancViewSet(viewsets.ModelViewSet):
    queryset = PerCanc.objects.all()
    serializer_class = PerCancSerializer

