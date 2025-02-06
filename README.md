# sistema-coporativo-web

Sistema de Controle de Créditos Tributários - Rosa Neto Tributos
Bem-vindo ao Sistema de Controle de Créditos Tributários da Rosa Neto Tributos! Aqui, você acessa de forma segura e centralizada todas as informações sobre seus créditos fiscais. Faça login para visualizar saldos, acompanhar movimentações e garantir a gestão eficiente de suas obrigações tributárias.

Funcionalidades Implementadas
1. Registro e Aprovação de Usuários
Cadastro de Usuário: Os usuários podem se cadastrar na plataforma, mas suas contas não são ativadas automaticamente. O sistema exige a aprovação de um administrador.
Envio de E-mail de Confirmação: Após o cadastro, o usuário recebe um e-mail informando que seu registro será analisado e que será notificado assim que a conta for aprovada.
Aprovação de Conta: Após a aprovação do administrador, um e-mail é enviado ao usuário informando que sua conta foi ativada e está pronta para ser utilizada.
2. Geração e Envio de Senhas
Geração de Senha Aleatória: Quando um usuário é registrado, uma senha provisória de seis dígitos é gerada aleatoriamente.
Envio de Senha por E-mail: A senha gerada é enviada automaticamente para o e-mail do usuário, junto com instruções para mudar a senha após o primeiro login.
3. Validação e Tratamento de Erros
Tratamento de Erros em Formulários: Foi implementada uma função para exibir mensagens de erro personalizadas nos campos dos formulários, ajudando o usuário a entender o que está faltando ou incorreto.
Validação de Senha com Regex: As senhas devem conter no mínimo 8 caracteres, incluindo pelo menos uma letra maiúscula, uma letra minúscula e um caractere especial. Caso a senha não atenda a esses requisitos, o sistema gera um erro específico.
4. Organização do Código
Estrutura do Projeto: O projeto foi organizado em diferentes aplicativos dentro do Django, como o app contas para gerenciar os usuários e o app forum para gerenciar as postagens e discussões.
Reutilização de Templates: Os templates foram estruturados de forma a herdar de um template base, garantindo consistência e facilidade de manutenção no design da aplicação.

Como Executar o Projeto:

Requisitos
Python 3.x,
Django 4.x,
Outras dependências podem ser instaladas utilizando o arquivo requirements.txt.


Contribuições
Este é um projeto em andamento e novas funcionalidades podem ser adicionadas. Sugestões e melhorias são sempre bem-vindas!

Licença
Este projeto está licenciado sob a licença MIT.