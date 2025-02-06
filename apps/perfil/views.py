#O método select_related é usado para pré-carregar os objetos relacionados em um modelo ForeignKey ou OneToOne de uma única consulta ao banco de dados, em vez de executar consultas adicionais para recuperar cada objeto relacionado.
#Por exemplo, se um objeto de modelo A tem uma ForeignKey para um objeto de modelo B e você usa select_related em A, o Django carregará B junto com A em uma única consulta ao banco de dados. Isso é útil quando você precisa acessar as informações de B, mas não deseja executar consultas adicionais para recuperá-las.
#Note que o select_related só funciona com chaves estrangeiras e não funciona com campos ManyToMany.

from django.shortcuts import render
from django.shortcuts import get_object_or_404, render
from apps.contas.models import MyUser
from django.contrib.auth.decorators import login_required
from forum.forms import PostagemForumForm
from django.core.paginator import Paginator
from base.utils import filtrar_modelo


@login_required()
def perfil_view(request, username):
    filtro = MyUser.objects.select_related('perfil').prefetch_related('user_postagem_forum')
    perfil = get_object_or_404(filtro, username=username)
    perfil_postagens = perfil.user_postagem_forum.all()
    form_dict = {}
    filtros = {}

    valor_busca = request.GET.get("titulo")
    if valor_busca:
        filtros["titulo"] = valor_busca
        filtros['descricao'] = valor_busca

        perfil_postagens = filtrar_modelo(perfil_postagens, **filtros)

    form_dict = {}
    for el in perfil_postagens:
        form = PostagemForumForm(instance=el)
        form_dict[el] = form


    #Criar uma lista de tuplas (postagem, form) a partir do form_dict
    form_list = [(postagem, form) for postagem, form in form_dict.items()]

    #Aplicar a paginação à lista de tuplas.
    paginacao = Paginator(form_list,3)

    #obter o número da página dos parâmetros da URL
    pagina_numero = request.GET.get("page")
    page_obj = paginacao.get_page(pagina_numero)

    #Criar um novo dicionário form_dict com base na página atual
    form_dict = {postagem: form for postagem, form in page_obj}
    context = {'page_obj': page_obj, 'form_dict': form_dict}
    return render(request, 'perfil/perfil.html', context)
