from django.shortcuts import render, redirect
from perdcomp.models import Empresa, PER, Dcomp
from perdcomp.views import calcular_saldo_e_dados_grafico
import logging
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

def index(request):
    # Renderiza o template index e passa os dados
    return render(request, 'pages/index.html')
@login_required
def internal_index(request):
    # Recupera todas as empresas
    empresas = Empresa.objects.all()
    empresa_selecionada = None
    saldo_disponivel = 0
    dados_grafico = {}
    # Captura o ID da empresa selecionada na requisição GET
    empresa_id = request.GET.get('empresa_id')
    if empresa_id:
        empresa_selecionada, saldo_disponivel, dados_grafico = calcular_saldo_e_dados_grafico(empresa_id)
    # Renderiza o template index e passa os dados
    return render(request, 'pages/index_interno.html', {
        'empresas': empresas,
        'empresa_selecionada': empresa_selecionada,
        'saldo_disponivel': saldo_disponivel,
        'dados_grafico': dados_grafico,
    })

