document.addEventListener("DOMContentLoaded", function () {
    const navbar = document.querySelector('.navbar');
    let lastScrollY = window.scrollY;
    const hideThreshold = 100; // Número de pixels que a navbar ficará fixa antes de desaparecer

    // Lógica de rolagem para ocultar a navbar
    window.addEventListener('scroll', () => {
        if (window.scrollY > hideThreshold) {
            if (window.scrollY > lastScrollY) {
                // Rolando para baixo
                navbar.classList.add('hidden');
            } else {
                // Rolando para cima
                navbar.classList.remove('hidden');
            }
        } else {
            // Se estiver acima do threshold, mantém a navbar visível
            navbar.classList.remove('hidden');
        }
        lastScrollY = window.scrollY;
    });

    // Lógica para abrir/fechar a sidebar
    document.getElementById('open_btn').addEventListener('click', function () {
        document.getElementById('sidebar').classList.toggle('open-sidebar');
    });

    // Lógica para selecionar o item ativo na sidebar
    const currentUrl = window.location.pathname; // Obtém o caminho da URL atual
    const sideItems = document.querySelectorAll('.side-item');

    // Remove a classe 'active' de todos os itens
    sideItems.forEach(item => item.classList.remove('active'));

    // Itera pelos itens da sidebar para marcar o ativo
    sideItems.forEach(item => {
        const link = item.querySelector('a'); // Encontra o link dentro do item
        if (link && link.getAttribute('href') === currentUrl) {
            item.classList.add('active'); // Marca como ativo
        }
    });
});
