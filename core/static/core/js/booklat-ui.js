/* ============================================================
   Booklat UI — Interactive behaviors
   ============================================================ */

(function () {
  'use strict';

  /* ------------------------------------------------------
     Dark Mode Toggle
     ------------------------------------------------------ */

  const DARK_KEY = 'booklat-theme';

  function getTheme() {
    const stored = localStorage.getItem(DARK_KEY);
    if (stored) return stored;
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
    return 'light';
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(DARK_KEY, theme);
    updateThemeToggleUI(theme);
  }

  function updateThemeToggleUI(theme) {
    document.querySelectorAll('.theme-toggle__option').forEach(function (el) {
      el.classList.toggle('theme-toggle__option--active', el.dataset.theme === theme);
    });
  }

  function initThemeToggle() {
    if (document.documentElement.hasAttribute('data-theme-locked')) return;
    var current = getTheme();
    setTheme(current);

    document.addEventListener('click', function (e) {
      var option = e.target.closest('.theme-toggle__option');
      if (!option) return;
      var theme = option.dataset.theme;
      if (theme && theme !== getTheme()) {
        setTheme(theme);
      }
    });
  }

  /* ------------------------------------------------------
     Mobile Sidebar Toggle
     ------------------------------------------------------ */

  function initSidebar() {
    var hamburger = document.querySelector('.js-sidebar-toggle');
    var sidebar = document.querySelector('.js-sidebar');
    var backdrop = document.querySelector('.js-sidebar-backdrop');

    if (!hamburger || !sidebar || !backdrop) return;

    function open() {
      sidebar.classList.add('app-shell__sidebar--open');
      backdrop.classList.add('app-shell__sidebar-backdrop--visible');
      document.body.style.overflow = 'hidden';
    }

    function close() {
      sidebar.classList.remove('app-shell__sidebar--open');
      backdrop.classList.remove('app-shell__sidebar-backdrop--visible');
      document.body.style.overflow = '';
    }

    hamburger.addEventListener('click', function () {
      if (sidebar.classList.contains('app-shell__sidebar--open')) {
        close();
      } else {
        open();
      }
    });

    backdrop.addEventListener('click', close);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
    });
  }

  /* ------------------------------------------------------
     Toast System
     ------------------------------------------------------ */

  function showToast(title, message, type) {
    type = type || 'info';
    var icons = {
      success: '<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>',
      error: '<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>',
      warning: '<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>',
      info: '<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>'
    };

    var container = document.querySelector('.js-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container js-toast-container';
      document.body.appendChild(container);
    }

    var toast = document.createElement('div');
    toast.className = 'toast toast--' + type;
    toast.innerHTML =
      '<div class="toast__icon">' + (icons[type] || icons.info) + '</div>' +
      '<div class="toast__body">' +
        '<div class="toast__title">' + escapeHtml(title) + '</div>' +
        '<div class="toast__message">' + escapeHtml(message) + '</div>' +
      '</div>' +
      '<button class="toast__close" aria-label="Close">&times;</button>';

    container.appendChild(toast);

    var closeBtn = toast.querySelector('.toast__close');
    var timer = setTimeout(removeToast, 5000);
    var removed = false;

    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        clearTimeout(timer);
        removeToast();
      });
    }

    function removeToast() {
      if (removed) return;
      removed = true;
      clearTimeout(timer);
      toast.classList.add('toast--removing');
      toast.addEventListener('animationend', function () {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, { once: true });
      setTimeout(function () {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 100);
    }
  }

  /* Parse Django messages rendered as data attributes into toasts */
  function initDjangoMessages() {
    var container = document.querySelector('.js-django-messages');
    if (!container) return;
    var messages = container.querySelectorAll('[data-message]');
    messages.forEach(function (el) {
      var text = el.dataset.message;
      var type = el.dataset.type || 'info';
      showToast(capitalize(type), text, mapDjangoTags(type));
    });
    container.remove();
  }

  function mapDjangoTags(tag) {
    if (tag === 'success') return 'success';
    if (tag === 'error') return 'error';
    if (tag === 'warning') return 'warning';
    return 'info';
  }

  function capitalize(s) {
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  /* ------------------------------------------------------
     Skeleton Loader — swap on DOM ready
     ------------------------------------------------------ */

  function initSkeletonSwap() {
    document.querySelectorAll('[data-skeleton]').forEach(function (el) {
      var target = document.querySelector(el.dataset.skeleton);
      if (target) {
        target.style.display = target.dataset.skeletonDisplay || '';
        el.remove();
      }
    });
  }

  /* ------------------------------------------------------
     Active Nav State
     ------------------------------------------------------ */

  function initActiveNav() {
    var currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-nav__link').forEach(function (link) {
      var href = link.getAttribute('href');
      if (href && currentPath.startsWith(href) && href !== '/') {
        link.classList.add('sidebar-nav__link--active');
      }
    });
    document.querySelectorAll('.bottom-nav__item').forEach(function (item) {
      var href = item.getAttribute('href');
      if (href && currentPath.startsWith(href) && href !== '/') {
        item.classList.add('bottom-nav__item--active');
      }
    });
  }

  /* ------------------------------------------------------
     Book Search Widget
     ------------------------------------------------------ */

  function initBookSearch() {
    document.querySelectorAll('.book-search').forEach(function (container) {
      var input = container.querySelector('.book-search__input');
      var hidden = container.querySelector('input[type="hidden"]');
      var dropdown = container.querySelector('.book-search__dropdown');
      var searchUrl = container.dataset.searchUrl;
      var debounceTimer = null;
      var activeIndex = -1;
      var results = [];

      function clearDropdown() {
        dropdown.innerHTML = '';
        dropdown.classList.remove('book-search__dropdown--open');
        results = [];
        activeIndex = -1;
      }

      function renderResults() {
        dropdown.innerHTML = '';
        if (results.length === 0) {
          dropdown.innerHTML = '<div class="book-search__empty">No books found</div>';
        } else {
          results.forEach(function (book, idx) {
            var el = document.createElement('div');
            el.className = 'book-search__option' + (idx === activeIndex ? ' book-search__option--active' : '');
            el.innerHTML =
              '<span class="book-search__option-title">' + escapeHtml(book.title) + '</span>' +
              '<span class="book-search__option-meta">' + escapeHtml(book.isbn) + ' &middot; ' + escapeHtml(book.authors) + '</span>';
            el.addEventListener('mousedown', function (e) {
              e.preventDefault();
              selectBook(book);
            });
            dropdown.appendChild(el);
          });
        }
        dropdown.classList.add('book-search__dropdown--open');
      }

      function selectBook(book) {
        hidden.value = book.id;
        input.value = book.title;
        clearDropdown();
      }

      input.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        var val = input.value.trim();
        if (!val) {
          clearDropdown();
          return;
        }
        dropdown.innerHTML = '<div class="book-search__spinner">Searching...</div>';
        dropdown.classList.add('book-search__dropdown--open');
        debounceTimer = setTimeout(function () {
          var connector = searchUrl.indexOf('?') === -1 ? '?' : '&';
          fetch(searchUrl + connector + 'q=' + encodeURIComponent(val))
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
              if (data.results) {
                results = data.results;
                renderResults();
              }
            })
            .catch(function () {
              dropdown.innerHTML = '<div class="book-search__empty">Search failed</div>';
            });
        }, 250);
      });

      input.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          activeIndex = Math.min(activeIndex + 1, results.length - 1);
          renderResults();
          var activeEl = dropdown.querySelector('.book-search__option--active');
          if (activeEl) activeEl.scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          activeIndex = Math.max(activeIndex - 1, 0);
          renderResults();
          var activeEl2 = dropdown.querySelector('.book-search__option--active');
          if (activeEl2) activeEl2.scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'Enter') {
          e.preventDefault();
          if (activeIndex >= 0 && results[activeIndex]) {
            selectBook(results[activeIndex]);
          }
        } else if (e.key === 'Escape') {
          clearDropdown();
        }
      });

      input.addEventListener('blur', function () {
        setTimeout(function () {
          if (!container.contains(document.activeElement)) {
            clearDropdown();
          }
        }, 150);
      });
    });
  }

  /* ------------------------------------------------------
      User Search Widget
      ------------------------------------------------------ */

  function initUserSearch() {
    document.querySelectorAll('.user-search').forEach(function (container) {
      var input = container.querySelector('.user-search__input');
      var hidden = container.querySelector('input[type="hidden"]');
      var dropdown = container.querySelector('.user-search__dropdown');
      var searchUrl = container.dataset.searchUrl;
      var debounceTimer = null;
      var activeIndex = -1;
      var results = [];

      function clearDropdown() {
        dropdown.innerHTML = '';
        dropdown.classList.remove('user-search__dropdown--open');
        results = [];
        activeIndex = -1;
      }

      function renderResults() {
        dropdown.innerHTML = '';
        if (results.length === 0) {
          dropdown.innerHTML = '<div class="user-search__empty">No users found</div>';
        } else {
          results.forEach(function (user, idx) {
            var el = document.createElement('div');
            el.className = 'user-search__option' + (idx === activeIndex ? ' user-search__option--active' : '');
            el.innerHTML =
              '<span class="user-search__option-title">' + escapeHtml(user.name) + '</span>' +
              '<span class="user-search__option-meta">LRN: ' + escapeHtml(user.lrn) + '</span>';
            el.addEventListener('mousedown', function (e) {
              e.preventDefault();
              selectUser(user);
            });
            dropdown.appendChild(el);
          });
        }
        dropdown.classList.add('user-search__dropdown--open');
      }

      function selectUser(user) {
        hidden.value = user.id;
        input.value = user.name + ' (' + user.lrn + ')';
        clearDropdown();
      }

      input.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        var val = input.value.trim();
        if (!val) {
          clearDropdown();
          return;
        }
        dropdown.innerHTML = '<div class="user-search__spinner">Searching...</div>';
        dropdown.classList.add('user-search__dropdown--open');
        debounceTimer = setTimeout(function () {
          var connector = searchUrl.indexOf('?') === -1 ? '?' : '&';
          fetch(searchUrl + connector + 'q=' + encodeURIComponent(val))
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
              if (data.results) {
                results = data.results;
                renderResults();
              }
            })
            .catch(function () {
              dropdown.innerHTML = '<div class="user-search__empty">Search failed</div>';
            });
        }, 250);
      });

      input.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          activeIndex = Math.min(activeIndex + 1, results.length - 1);
          renderResults();
          var activeEl = dropdown.querySelector('.user-search__option--active');
          if (activeEl) activeEl.scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          activeIndex = Math.max(activeIndex - 1, 0);
          renderResults();
          var activeEl2 = dropdown.querySelector('.user-search__option--active');
          if (activeEl2) activeEl2.scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'Enter') {
          e.preventDefault();
          if (activeIndex >= 0 && results[activeIndex]) {
            selectUser(results[activeIndex]);
          }
        } else if (e.key === 'Escape') {
          clearDropdown();
        }
      });

      input.addEventListener('blur', function () {
        setTimeout(function () {
          if (!container.contains(document.activeElement)) {
            clearDropdown();
          }
        }, 150);
      });
    });
  }

  /* ------------------------------------------------------
      Copy Search Widget
      ------------------------------------------------------ */

  function initCopySearch() {
    document.querySelectorAll('.copy-search').forEach(function (container) {
      var input = container.querySelector('.copy-search__input');
      var hidden = container.querySelector('input[type="hidden"]');
      var dropdown = container.querySelector('.copy-search__dropdown');
      var searchUrl = container.dataset.searchUrl;
      var debounceTimer = null;
      var activeIndex = -1;
      var results = [];

      function clearDropdown() {
        dropdown.innerHTML = '';
        dropdown.classList.remove('copy-search__dropdown--open');
        results = [];
        activeIndex = -1;
      }

      function renderResults() {
        dropdown.innerHTML = '';
        if (results.length === 0) {
          dropdown.innerHTML = '<div class="copy-search__empty">No copies found</div>';
        } else {
          results.forEach(function (copy, idx) {
            var el = document.createElement('div');
            el.className = 'copy-search__option' + (idx === activeIndex ? ' copy-search__option--active' : '');
            el.innerHTML =
              '<span class="copy-search__option-title">' + escapeHtml(copy.copy_id) + '</span>' +
              '<span class="copy-search__option-meta">' + escapeHtml(copy.title) + '</span>';
            el.addEventListener('mousedown', function (e) {
              e.preventDefault();
              selectCopy(copy);
            });
            dropdown.appendChild(el);
          });
        }
        dropdown.classList.add('copy-search__dropdown--open');
      }

      function selectCopy(copy) {
        hidden.value = copy.id;
        input.value = copy.copy_id + ' — ' + copy.title;
        clearDropdown();
      }

      input.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        var val = input.value.trim();
        if (!val) {
          clearDropdown();
          return;
        }
        dropdown.innerHTML = '<div class="copy-search__spinner">Searching...</div>';
        dropdown.classList.add('copy-search__dropdown--open');
        debounceTimer = setTimeout(function () {
          var connector = searchUrl.indexOf('?') === -1 ? '?' : '&';
          fetch(searchUrl + connector + 'q=' + encodeURIComponent(val))
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
              if (data.results) {
                results = data.results;
                renderResults();
              }
            })
            .catch(function () {
              dropdown.innerHTML = '<div class="copy-search__empty">Search failed</div>';
            });
        }, 250);
      });

      input.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          activeIndex = Math.min(activeIndex + 1, results.length - 1);
          renderResults();
          var activeEl = dropdown.querySelector('.copy-search__option--active');
          if (activeEl) activeEl.scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          activeIndex = Math.max(activeIndex - 1, 0);
          renderResults();
          var activeEl2 = dropdown.querySelector('.copy-search__option--active');
          if (activeEl2) activeEl2.scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'Enter') {
          e.preventDefault();
          if (activeIndex >= 0 && results[activeIndex]) {
            selectCopy(results[activeIndex]);
          }
        } else if (e.key === 'Escape') {
          clearDropdown();
        }
      });

      input.addEventListener('blur', function () {
        setTimeout(function () {
          if (!container.contains(document.activeElement)) {
            clearDropdown();
          }
        }, 150);
      });
    });
  }

  /* ------------------------------------------------------
      Checkout Table — client-side filter + row selection
      ------------------------------------------------------ */

  function initCheckoutTable(config) {
    var searchInput = document.getElementById(config.searchInputId);
    var table = document.getElementById(config.tableId);
    var hiddenInput = document.querySelector('input[name="' + config.hiddenName + '"]');
    var submitBtn = document.getElementById(config.submitBtnId);
    if (!searchInput || !table || !hiddenInput || !submitBtn) return;

    var tbody = table.querySelector('tbody');
    var rows = table.querySelectorAll('tbody tr');
    var selectedRow = null;

    function clearSelection() {
      if (selectedRow) {
        selectedRow.classList.remove('data-table__row--selected');
        selectedRow = null;
      }
      hiddenInput.value = '';
      submitBtn.disabled = true;
    }

    function selectRow(row) {
      clearSelection();
      row.classList.add('data-table__row--selected');
      selectedRow = row;
      hiddenInput.value = row.dataset.id;
      submitBtn.disabled = false;
    }

    searchInput.addEventListener('input', function () {
      var val = searchInput.value.trim().toLowerCase();
      var visibleCount = 0;
      rows.forEach(function (row) {
        if (row.classList.contains('checkout-empty-row')) return;
        var searchData = (row.dataset.search || '').toLowerCase();
        if (!val || searchData.indexOf(val) !== -1) {
          row.style.display = '';
          visibleCount++;
        } else {
          row.style.display = 'none';
        }
      });
      var emptyRow = tbody.querySelector('.checkout-empty-row');
      if (emptyRow) {
        emptyRow.style.display = visibleCount === 0 ? '' : 'none';
      }
      if (selectedRow && selectedRow.style.display === 'none') {
        clearSelection();
      }
    });

    tbody.addEventListener('click', function (e) {
      var row = e.target.closest('tr');
      if (!row || row.classList.contains('checkout-empty-row')) return;
      selectRow(row);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initThemeToggle();
    initSidebar();
    initDjangoMessages();
    initSkeletonSwap();
    initActiveNav();
    initBookSearch();
    initUserSearch();
    initCopySearch();
    initCheckoutTable({
      searchInputId: 'checkout-user-search',
      tableId: 'checkout-user-table',
      hiddenName: 'user',
      submitBtnId: 'checkout-user-submit'
    });
    initCheckoutTable({
      searchInputId: 'checkout-copy-search',
      tableId: 'checkout-copy-table',
      hiddenName: 'copy',
      submitBtnId: 'checkout-copy-submit'
    });
  });

  /* Expose showToast globally for inline use */
  window.Booklat = {
    showToast: showToast,
    setTheme: setTheme,
    getTheme: getTheme,
    escapeHtml: escapeHtml
  };

})();