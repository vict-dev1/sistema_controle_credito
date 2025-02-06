from django.contrib import messages
from django.db.models import Q

def add_form_errors_to_messages(request, form):
    for field, error_list in form.errors.items():
        for error in error_list:
            messages.error(request, f"Erro no campo '{form[field].label}': {error}")


# Filtro (OR)
def filtrar_modelo(queryset, **filtros):

    q_objects = Q()  # Inicializa um objeto Q vazio

    for campo, valor in filtros.items():
        q_objects |= Q(**{campo + '__icontains': valor})

    queryset = queryset.filter(q_objects)
    return queryset


