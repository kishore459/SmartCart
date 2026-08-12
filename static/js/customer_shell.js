(() => {
    if (document.getElementById('customer-shell')) return;

    const path = window.location.pathname;
    const isActive = (route) => path === route ? ' active' : '';
    const header = document.createElement('header');
    header.id = 'customer-shell';
    header.className = 'customer-shell';
    header.innerHTML = `
        <a class="customer-shell-logo" href="/user-dashboard"><b>Smart</b><span>Cart</span></a>
        <button class="customer-shell-menu-toggle" type="button" aria-label="Open menu" aria-controls="customer-navigation" aria-expanded="false"><span></span><span></span><span></span></button>
        <nav class="customer-shell-nav" id="customer-navigation" aria-label="Customer navigation">
            <a class="${isActive('/user-dashboard')}" href="/user-dashboard">Home</a>
            <a class="${isActive('/user/products')}" href="/user/products">Products</a>
            <a class="${isActive('/user/my-orders')}" href="/user/my-orders">My Orders</a>
            <a class="customer-mobile-only" href="/user/profile">My profile</a>
            <a class="customer-mobile-only customer-mobile-logout" href="/user-logout">Logout</a>
        </nav>
        <form class="customer-shell-search" method="GET" action="/user-dashboard">
            <input name="search" type="search" placeholder="Search products..." aria-label="Search products">
            <button type="submit" aria-label="Search">&#128269;</button>
        </form>
        <nav class="customer-shell-actions" aria-label="Account actions">
            <a class="${isActive('/user/cart')}" href="/user/cart">&#128722; Cart <span id="cart-count" class="cart-badge">${document.querySelector('#cart-count')?.textContent.trim() || '0'}</span></a>
            <a class="${isActive('/user/profile')}" href="/user/profile">&#128100; Profile</a>
            <a class="customer-shell-logout" href="/user-logout">Logout</a>
        </nav>`;

    const oldHeader = document.querySelector('body > header');
    if (oldHeader) oldHeader.remove();
    document.body.prepend(header);

    const menuButton = header.querySelector('.customer-shell-menu-toggle');
    const navigation = header.querySelector('#customer-navigation');
    menuButton.addEventListener('click', () => {
        const isOpen = navigation.classList.toggle('is-open');
        menuButton.classList.toggle('is-open', isOpen);
        menuButton.setAttribute('aria-expanded', isOpen);
    });
    document.addEventListener('click', (event) => {
        if (window.innerWidth <= 650 && navigation.classList.contains('is-open') && !navigation.contains(event.target) && !menuButton.contains(event.target)) menuButton.click();
    });

    const oldFooter = document.querySelector('body > footer');
    if (oldFooter) oldFooter.remove();
    const footer = document.createElement('footer');
    footer.id = 'customer-footer';
    footer.innerHTML = `
        <div class="footer-brand"><strong>Smart<span>Cart</span></strong><p>Big choice. Bright prices. Easy shopping.</p></div>
        <div class="footer-column"><b>Shop</b><a href="/user-dashboard">Featured products</a><a href="/user/products">All categories</a><a href="/user/cart">Your cart</a></div>
        <div class="footer-column"><b>Help</b><a href="/about">About SmartCart</a><a href="/contact">Contact support</a><a href="mailto:support@smartcart.com">support@smartcart.com</a></div>
        <div class="footer-bottom">&copy; 2026 SmartCart. Made for everyday shopping.</div>`;
    document.body.append(footer);
})();
