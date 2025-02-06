from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib.auth.models import Group, User
from django.contrib.auth import logout
from apps.base.utils import add_form_errors_to_messages
from apps.contas.forms import UserChangeForm, CustomUserCreationForm
from django.shortcuts import get_object_or_404
from apps.contas.models import MyUser
from contas.permissions import grupo_colaborador_required
from perfil.models import Perfil
from perfil.forms import PerfilForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from core import settings
from django.core.mail import send_mail



# Rota de Timeout (Desconectado por inatividade)
def timeout_view(request):
    return render(request, 'contas/timeout.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# Login
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            if user.is_authenticated and user.requires_password_change():  # Verifica
                msg = 'Olá ' + user.first_name + ',Recomendamos fortemente \
            	              que você altere sua senha para garantir a segurança da sua conta. \
            	              É importante escolher uma senha forte e única que não seja fácil de adivinhar. \
            	              Obrigado pela sua atenção!'
                messages.warning(request, msg)
                return redirect('force_password_change')  # Vai para rota de alterar senha.
            else:
                return redirect('interno_index')
        else:
            messages.error(request, 'Combinação de e-mail e senha inválida. \
            	   Se o erro persistir, entre em contato com o administrador do sistema.')

    if request.user.is_authenticated:
        return redirect('interno_index')
    return render(request, 'contas/login.html')


# Mudança de Senha Force (first_login)
@login_required
def force_password_change_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.force_change_password = False # passa o parametro para False.
            user.save()
            update_session_auth_hash(request, user)
            return redirect('password_change_done')
    else:
        form = PasswordChangeForm(request.user)
    context = {'form': form}
    return render(request, 'registration/password_force_change_form.html', context)

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, user=request.user)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.is_valid = False
            usuario.is_active = False
            usuario.save()

            group = Group.objects.get(name='Usuário')
            usuario.groups.add(group)

            Perfil.objects.create(usuario=usuario) #Criar instancia perfil do usuário
            # Envia e-mail para usuário
            send_mail(  # Envia email para usuario
                'Cadastro Plataforma',
                f'Olá, {usuario.first_name}, em breve você receberá um e-mail de aprovação para usar a plataforma.',
                settings.DEFAULT_FROM_EMAIL,  # De (em produção usar o e-mail que está no settings)
                [usuario.email],  # para
                fail_silently=False,
            )

            messages.success(request, 'Registrado. Um e-mail foi enviado \
                para administrador aprovar. Aguarde contato')

            #messages.success(request, 'Registrado. Agora faça o login para começar!')
            return redirect('login')
        else:
            # Tratar quando usuario já existe, senhas... etc...
            add_form_errors_to_messages(request,form)

    form = CustomUserCreationForm(user=request.user)
    return render(request, "contas/register.html", {"form": form})


@login_required()
def atualizar_meu_usuario(request):
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user,user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso!')
            return redirect('interno_index')
    else:
        form = UserChangeForm(instance=request.user,user=request.user)
    return render(request, 'contas/user_update.html', {'form': form})


@login_required()
@grupo_colaborador_required(['Administrador','Colaborador'])
def atualizar_usuario(request, username):
    user = get_object_or_404(MyUser, username=username)
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=user, user=request.user)
        if form.is_valid():
            usuario = form.save()

            if user.is_active:  ## se usuario for ativado a gente muda o status para True e envia e-mail
                usuario.is_active = True  # muda status para True (Aprovado)

                # Envia e-mail avisando usuário.
                send_mail(  # Envia email para usuario
                    'Cadastro Aprovado',
                    f'Olá, {usuario.first_name}, seu e-mail foi aprovado na plataforma.',
                    settings.DEFAULT_FROM_EMAIL,  # De (em produção usar o e-mail que está no settings)
                    [usuario.email],  # para
                    fail_silently=False,
                )
                messages.success(request, 'O usuário ' + usuario.email + '\
                    foi atualizado com sucesso!')
                return redirect('lista_usuarios')

            usuario.save()
            messages.success(request, 'O perfil de usuário foi atualizado com sucesso!')
            return redirect('index_interno')

        else:
            add_form_errors_to_messages(request, form)
    else:
        form = UserChangeForm(instance=user, user=request.user)
    return render(request, 'contas/user_update.html', {'form': form})




@login_required()
@grupo_colaborador_required(['Administrador','Colaborador'])
def lista_usuarios(request):  # Lista Cliente

    # Adiciona uma ordenação explícita ao QuerySet
    lista_usuarios = MyUser.objects.select_related('perfil').filter(is_superuser=False).order_by('id')

    paginacao = Paginator(lista_usuarios, 10)
    pagina_numero = request.GET.get("page")
    page_obj = paginacao.get_page(pagina_numero)

    return render(request, 'contas/lista-usuarios.html', {'page_obj': page_obj})


@login_required
@grupo_colaborador_required(['Administrador', 'Colaborador'])
def adicionar_usuario(request):
    user_form = CustomUserCreationForm(user=request.user)
    perfil_form = PerfilForm(user=request.user)

    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST, user=request.user)
        perfil_form = PerfilForm(request.POST, request.FILES, user=request.user)

        if user_form.is_valid() and perfil_form.is_valid():
            # Salve o usuário
            usuario = user_form.save()

            group = Group.objects.get(name='Usuário')
            usuario.groups.add(group)

            # Crie um novo perfil para o usuário
            perfil = perfil_form.save(commit=False)
            perfil.usuario = usuario
            perfil.save()

            messages.success(request, 'Usuário adicionado com sucesso.')
            return redirect('lista_usuarios')
        else:
            #erros
            add_form_errors_to_messages(request, user_form)
            add_form_errors_to_messages(request, perfil_form)

    context = {'user_form': user_form, 'perfil_form': perfil_form}
    return render(request, "contas/adicionar-usuario.html", context)



