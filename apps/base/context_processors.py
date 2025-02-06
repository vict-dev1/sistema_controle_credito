# from myapp import models

from perfil.models import Perfil

def perfil_context(request):
    if request.user.is_authenticated:
        perfil = Perfil.objects.filter(usuario=request.user).first()  # Busca o perfil do usuário logado
        return {'obj': perfil}  # Retorna o perfil como `obj`
    return {}

def context_social(request):
    return {'social': 'Exibir este contexto em qualquer lugar!'}