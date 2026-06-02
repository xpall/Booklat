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

    closeBtn.addEventListener('click', function () {
      clearTimeout(timer);
      removeToast();
    });

    function removeToast() {
      clearTimeout(timer);
      toast.classList.add('toast--removing');
      toast.addEventListener('animationend', function () {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, { once: true });
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
     Bootstrap
     ------------------------------------------------------ */

  document.addEventListener('DOMContentLoaded', function () {
    initThemeToggle();
    initSidebar();
    initDjangoMessages();
    initSkeletonSwap();
    initActiveNav();
  });

  /* Expose showToast globally for inline use */
  window.Booklat = {
    showToast: showToast,
    setTheme: setTheme,
    getTheme: getTheme
  };

})();