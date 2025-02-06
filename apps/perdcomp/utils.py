from perdcomp.models import PER, Dcomp
from django.db.models import Sum

def calcular_saldo_disponivel():
    # Soma o valor total de crédito de PER
    total_credito = PER.objects.aggregate(total=Sum('valor_original_do_credito_inicial'))['total'] or 0
    print(f"Total Crédito (PER): {total_credito}")

    # Soma o total de débitos em Dcomp
    total_debitos = Dcomp.objects.aggregate(total=Sum('total_dos_debitos'))['total'] or 0
    print(f"Total Débitos (Dcomp): {total_debitos}")

    # Calcula o saldo disponível
    saldo_disponivel = total_credito - total_debitos
    print(f"Saldo Disponível: {saldo_disponivel}")

    return saldo_disponivel



