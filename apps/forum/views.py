import re
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from base.utils import add_form_errors_to_messages, filtrar_modelo
from forum import models
from forum.forms import PostagemForum, PostagemForumForm,PostagemForumComentarioForm
from forum.models import PostagemForumImagem
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


# Create your views here.
def lista_postagem_forum(request):
    form_dict = {}
    filtros = {}

    valor_busca = request.GET.get("titulo")
    if valor_busca:
        filtros["titulo"] = valor_busca
        filtros['descricao'] = valor_busca

    if request.path == '/forum/': # Pagina forum da home, mostrar tudo ativo.
        postagens = models.PostagemForum.objects.filter(ativo=True)
        template_view = 'forum/lista-postagem-forum.html' # lista de post da rota /forum/
    else: # Essa parte mostra no Dashboard
        user = request.user
        grupos = ['Administrador', 'Colaborador']
        template_view = 'dashboard/dash-lista-postagem-forum.html'
        if any(grupo.name in grupos for grupo in user.groups.all()) or user.is_superuser:
            # Usuário é administrador ou colaborador, pode ver todas as postagens
            postagens = models.PostagemForum.objects.filter(ativo=True)
        else:
            # Usuário é do grupo usuário, pode ver apenas suas próprias postagens
            postagens = models.PostagemForum.objects.filter(usuario=user)

    postagens = filtrar_modelo(postagens, **filtros).order_by('id')
    for el in postagens:
        form = PostagemForumForm(instance=el)
        form_dict[el] = form

    form_list = [(postagem, form) for postagem, form in form_dict.items()]

    paginacao = Paginator(form_list, 4)

    pagina_numero = request.GET.get("page")
    page_obj = paginacao.get_page(pagina_numero)

    form_dict = {postagem: form for postagem, form in page_obj}

    context = {'page_obj': page_obj, 'form_dict': form_dict}

    return render(request, template_view, context)

@login_required
def criar_postagem_forum(request):
    form = PostagemForumForm()
    if request.method == 'POST':
        form = PostagemForumForm(request.POST, request.FILES)
        if form.is_valid():
            postagem_imagens = request.FILES.getlist('postagem_imagens')
            if len(postagem_imagens) > 5:  # faz um count
                messages.error(request, 'Você só pode adicionar no máximo 5 imagens.')
            else:
                forum = form.save(commit=False)
                forum.usuario = request.user
                forum.save()
                for f in postagem_imagens:
                    models.PostagemForumImagem.objects.create(postagem=forum, imagem=f)
                # Redirecionar para uma página de sucesso ou fazer qualquer outra ação desejada
                messages.success(request, 'Seu Post foi cadastrado com sucesso!')
                return redirect('lista-postagem-forum')
        else:
            add_form_errors_to_messages(request,form)

    return render(request, 'forum/form-postagem-forum.html', {'form': form})


#Detalhes da Postagem (slug)
def detalhe_postagem_forum(request, slug):
    postagem = get_object_or_404(models.PostagemForum, slug=slug)
    form = PostagemForumForm(instance=postagem)
    form_comentario = PostagemForumComentarioForm()
    context = {'form': form,
                'postagem': postagem,
                'form_comentario':form_comentario}
    return render(request,'forum/detalhe-postagem-forum.html', context)

#Editar Postagem (slug)
@login_required
def editar_postagem_forum(request, slug):
    redirect_route = request.POST.get('redirect_route', '')
    postagem = get_object_or_404(models.PostagemForum, slug=slug)
    message = 'Seu Post ' + postagem.titulo + ' foi atualizado com sucesso!'
    # Verifica se o usuário autenticado é o autor da postagem
    lista_grupos = ['Administrador', 'Colaborador']
    if request.user != postagem.usuario and not (
            any(grupo.name in lista_grupos for grupo in request.user.groups.all()) or request.user.is_superuser):
        messages.warning(request, 'Seu usuário não tem permissões para acessar essa pagina.')
        return redirect('lista-postagem-forum')  # Redireciona para uma página de erro ou outra página adequada

    if request.method == 'POST':
        form = PostagemForumForm(request.POST, instance=postagem)
        if form.is_valid():

            contar_imagens = postagem.postagem_imagens.count()  # Quantidade de imagens sque já tenho no post
            postagem_imagens = request.FILES.getlist(
                'postagem_imagens')  # Quantidade de imagens que estou enviando para salvar

            if contar_imagens + len(postagem_imagens) > 5:
                messages.error(request, 'Você só pode adicionar no máximo 5 imagens.')
                return redirect(redirect_route)
            else:
                form.save()
                for f in postagem_imagens:  # for para pegar as imagens e salvar.
                    models.PostagemForumImagem.objects.create(postagem=form, imagem=f)

                messages.warning(request, message)
                return redirect(redirect_route)
        else:
            add_form_errors_to_messages(request, form)
    return JsonResponse({'status': message})  # Coloca por enquanto.



@login_required
def deletar_postagem_forum(request, slug):
    redirect_route = request.POST.get('redirect_route','')
    print(redirect_route)
    postagem = get_object_or_404(models.PostagemForum, slug=slug)
    print(postagem)
    message = 'Seu Post '+postagem.titulo+' foi deletado com sucesso!'
    if request.method == 'POST':
        postagem.delete()
        messages.error(request,message)

        if re.search(r'/forum/detalhe-postagem-forum/([^/]+)/', redirect_route):
            return redirect('lista-postagem-forum')
    return render(request, 'forum/detalhe-postagem-forum.html', {'postagem': postagem})

def remover_imagem(request):
    imagem_id = request.GET.get('imagem_id')
    verifica_imagem = models.PostagemForumImagem.objects.filter(id=imagem_id)
    if verifica_imagem:
        postagem_imagem = models.PostagemForumImagem.objects.get(id=imagem_id)
        postagem_imagem.imagem.delete()
        postagem_imagem.delete()
    return JsonResponse({'message': 'Imagem removida com sucesso.'})



def adicionar_comentario(request, slug):
    postagem = get_object_or_404(models.PostagemForum, slug=slug)
    message = 'Comentário Adcionado com sucesso!'
    if request.method == 'POST':
        form = PostagemForumComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.usuario = request.user
            comentario.postagem = postagem
            comentario.save()
            messages.warning(request, message)
            return redirect('forum/detalhe-postagem-forum', slug=postagem.slug)
    return JsonResponse({'status': message})


def editar_comentario(request,comentario_id):
    comentario = get_object_or_404(models.PostagemForumComentario,id=comentario_id)
    message = 'Comentário Editado com sucesso!'
    if request.method == 'POST':
        form = PostagemForumComentarioForm(request.POST,instance=comentario)
        if form.is_valid():
            form.save()
            messages.info(request, message)
            return redirect('detalhe-postagem-forum', slug=comentario.postagem.slug)

    return JsonResponse({'status':message})



