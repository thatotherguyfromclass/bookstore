// static/js/main.js
const CART_KEY = "bookstore_cart_v1";

function getCart() {
  try { return JSON.parse(localStorage.getItem(CART_KEY)) || []; }
  catch (e) { console.error("Cart parse error:", e); return []; }
}

function saveCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  renderCartBadge();
}

// Cart helpers
function formatNGNFromKobo(kobo) {
  // kobo is integer; convert to NGN with 2 decimals
  const ngn = (Number(kobo) / 100).toFixed(2);
  // Add thousand separators
  return ngn.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function addToCart(item) {
  const cart = getCart();
  const exists = cart.find(i => i.id === item.id);

  if (exists) {
    alert("This book is already in your cart.");
    return;
  }

  // always save with qty = 1 (no multiples)
  cart.push({ ...item, qty: 1 });
  saveCart(cart);
}

function removeFromCart(id) {
  const cart = getCart().filter(i => i.id !== id);
  saveCart(cart);
}

function cartTotalKobo() {
  return getCart().reduce((sum, i) => sum + (Number(i.price_kobo) * Number(i.qty)), 0);
}

function renderCartBadge() {
  const count = getCart().reduce((n, i) => n + Number(i.qty), 0);
  const el = document.getElementById("cart-badge");
  if (el) el.textContent = count;
}

// Render price spans in catalog
function renderPricesOnPage() {
  document.querySelectorAll(".price-value[data-kobo]").forEach(sp => {
    const kobo = Number(sp.dataset.kobo || 0);
    sp.textContent = formatNGNFromKobo(kobo);
  });
}

// Attach add-to-cart handlers on catalog
function attachAddToCartButtons() {
  document.querySelectorAll(".book-card").forEach(card => {
    const btn = card.querySelector(".add-to-cart");
    if (!btn) return;
    btn.addEventListener("click", () => {
      const id = Number(card.dataset.id);
      const title = card.dataset.title;
      const price_kobo = Number(card.dataset.priceKobo || card.dataset.priceKobo || card.getAttribute("data-price-kobo") || 0);
      // support both dataset.priceKobo and data-price-kobo
      const item = { id, title, price_kobo };
      addToCart(item);
      btn.textContent = "Added ✓";
      setTimeout(() => btn.textContent = "Add to cart", 900);
    });
  });
}

// On cart page: render cart table
function renderCartPage() {
  const el = document.getElementById("cart-root");
  if (!el) return;
  const cart = getCart();

  if (cart.length === 0) {
    el.innerHTML = `<div class="cart-empty">Your cart is empty.</div>`;
    return;
  }

  let html = `<div class="table-wrapper"><table class="cart-table">
    <thead><tr><th>Book</th><th>Price</th><th></th></tr></thead><tbody>`;

  cart.forEach(item => {
    html += `<tr data-id="${item.id}">
      <td class="cart-title">${item.title}</td>
      <td class="cart-price">₦${formatNGNFromKobo(item.price_kobo)}</td>
      <td><button class="btn btn-outline remove-item">Remove</button></td>
    </tr>`;
  });

  html += `</tbody></table></div>
    <div class="cart-footer">
      <span class="cart-total">Total: ₦${formatNGNFromKobo(cartTotalKobo())}</span>
      <button id="proceed-to-checkout" class="btn btn-primary">Proceed to Checkout</button>
    </div>`;

  el.innerHTML = html;

  // wire remove buttons
  el.querySelectorAll(".remove-item").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const tr = e.target.closest("tr");
      const id = Number(tr.dataset.id);
      removeFromCart(id);
      renderCartPage();
    });
  });

  // checkout
  const checkoutBtn = document.getElementById("proceed-to-checkout");
  if (checkoutBtn) {
    checkoutBtn.addEventListener("click", () => {
      window.location.href = "/checkout/";
    });
  }
}


// Initializers
document.addEventListener("DOMContentLoaded", function () {
  renderCartBadge();
  renderPricesOnPage();
  attachAddToCartButtons();
  renderCartPage();
});


// == Bootstrap modal hookup for product modal ==
(function () {
  if (typeof document === 'undefined') return;
  const modalEl = document.getElementById('product-modal');
  if (!modalEl) {
    console.warn('[modal] #product-modal not found in DOM');
    return;
  }

  let bsModal = null;
  if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
    bsModal = new bootstrap.Modal(modalEl, { keyboard: true, backdrop: true });
  } else {
    console.warn('[modal] bootstrap Modal not found - ensure bootstrap.bundle.js is loaded before main.js');
  }

  function populateModal(data) {
    const titleEl = document.getElementById('modal-title');
    const authorEl = document.getElementById('modal-author');
    const priceEl = document.getElementById('modal-price');
    const coverEl = document.getElementById('modal-cover-img');
    const modalAdd = document.getElementById('modal-add');

    if (titleEl) titleEl.textContent = data.title || '';
    if (authorEl) authorEl.textContent = data.author ? ('By ' + data.author) : '';
    if (priceEl) {
      if (typeof formatNGNFromKobo === 'function') priceEl.textContent = '₦' + formatNGNFromKobo(data.price_kobo || 0);
      else priceEl.textContent = '₦' + ((data.price_kobo || 0)/100).toFixed(2);
    }
    if (coverEl) {
      if (data.cover) {
        coverEl.src = data.cover;
        coverEl.alt = data.title || 'cover';
        coverEl.style.display = '';
      } else {
        coverEl.src = '';
        coverEl.style.display = 'none';
      }
    }
    if (modalAdd) {
      modalAdd.dataset.bookId = data.id;
      modalAdd.dataset.title = data.title;
      modalAdd.dataset.priceKobo = data.price_kobo;
    }
  }

  document.addEventListener('click', function (ev) {
    const viewBtn = ev.target.closest('.view-details');
    const card = ev.target.closest('.book-card');
    if (viewBtn && card) {
      const data = {
        id: Number(card.dataset.id || card.getAttribute('data-id')),
        title: card.dataset.title || card.getAttribute('data-title'),
        author: card.dataset.author || card.getAttribute('data-author') || '',
        price_kobo: Number(card.dataset.priceKobo || card.getAttribute('data-price-kobo') || 0)
      };
      const img = card.querySelector('.cover');
      if (img && img.src) data.cover = img.src;
      populateModal(data);
      if (bsModal) bsModal.show();
      else modalEl.style.display = 'block';
    }
  });

  document.addEventListener('keydown', function (ev) {
    if (ev.key !== 'Enter') return;
    const active = document.activeElement;
    if (active && active.classList && active.classList.contains('book-card')) {
      const card = active;
      const data = {
        id: Number(card.dataset.id || card.getAttribute('data-id')),
        title: card.dataset.title || card.getAttribute('data-title'),
        author: card.dataset.author || card.getAttribute('data-author') || '',
        price_kobo: Number(card.dataset.priceKobo || card.getAttribute('data-price-kobo') || 0)
      };
      const img = card.querySelector('.cover');
      if (img && img.src) data.cover = img.src;
      populateModal(data);
      if (bsModal) bsModal.show();
    }
  });

  const modalAddBtn = document.getElementById('modal-add');
  if (modalAddBtn) {
    modalAddBtn.addEventListener('click', function () {
      const id = Number(modalAddBtn.dataset.bookId);
      const title = modalAddBtn.dataset.title;
      const price_kobo = Number(modalAddBtn.dataset.priceKobo);
      addToCart({ id, title, price_kobo });
      if (bsModal) bsModal.hide();
    });
  }

  if (modalEl) {
    modalEl.addEventListener('hidden.bs.modal', function () {
      const coverEl = document.getElementById('modal-cover-img');
      if (coverEl) coverEl.src = '';
    });
  }

  console.log('[modal] bootstrap modal hook initialized', !!bsModal);
})();