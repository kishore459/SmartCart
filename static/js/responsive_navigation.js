/* Adds the shared three-line mobile navigation to standard page headers. */
(() => {
    const header = document.querySelector('body > header');
    if (!header || header.classList.contains('customer-shell') || header.classList.contains('store-header') || header.classList.contains('admin-header')) return;

    const navigation = header.querySelector(':scope > nav');
    if (!navigation || header.querySelector('.responsive-menu-toggle')) return;
    const sidebar = document.querySelector('.dashboard-wrapper > .sidebar');

    // Older admin pages have a sidebar but predate the newer admin header.
    // Bring them into the same drawer pattern instead of leaving a wide menu
    // above the content on a phone.
    if (sidebar) {
        header.classList.add('admin-header');
        navigation.classList.add('admin-account-nav');
        const button = document.createElement('button');
        button.className = 'admin-menu-toggle responsive-menu-toggle';
        button.type = 'button';
        button.setAttribute('aria-label', 'Open navigation menu');
        button.setAttribute('aria-controls', 'admin-sidebar');
        button.setAttribute('aria-expanded', 'false');
        button.innerHTML = '<span></span><span></span><span></span>';
        sidebar.id = 'admin-sidebar';
        header.insertBefore(button, navigation);
        button.addEventListener('click', () => {
            const isOpen = sidebar.classList.toggle('is-open');
            button.classList.toggle('is-open', isOpen);
            button.setAttribute('aria-expanded', String(isOpen));
            document.body.classList.toggle('admin-menu-open', isOpen);
        });
        sidebar.addEventListener('click', (event) => {
            if (event.target.closest('a') && sidebar.classList.contains('is-open')) button.click();
        });
        document.addEventListener('click', (event) => {
            if (window.innerWidth <= 800 && sidebar.classList.contains('is-open') && !sidebar.contains(event.target) && !button.contains(event.target)) button.click();
        });
        return;
    }

    const menuId = `responsive-navigation-${Math.random().toString(36).slice(2, 8)}`;
    navigation.id = menuId;
    navigation.classList.add('responsive-navigation');

    const button = document.createElement('button');
    button.className = 'responsive-menu-toggle';
    button.type = 'button';
    button.setAttribute('aria-label', 'Open navigation menu');
    button.setAttribute('aria-controls', menuId);
    button.setAttribute('aria-expanded', 'false');
    button.innerHTML = '<span></span><span></span><span></span>';
    header.insertBefore(button, navigation);

    const closeMenu = () => {
        navigation.classList.remove('is-open');
        button.classList.remove('is-open');
        button.setAttribute('aria-expanded', 'false');
    };
    button.addEventListener('click', () => {
        const isOpen = navigation.classList.toggle('is-open');
        button.classList.toggle('is-open', isOpen);
        button.setAttribute('aria-expanded', String(isOpen));
    });
    navigation.addEventListener('click', (event) => {
        if (event.target.closest('a')) closeMenu();
    });
    document.addEventListener('click', (event) => {
        if (window.innerWidth <= 760 && navigation.classList.contains('is-open') && !header.contains(event.target)) closeMenu();
    });
    window.addEventListener('resize', () => {
        if (window.innerWidth > 760) closeMenu();
    });
})();
